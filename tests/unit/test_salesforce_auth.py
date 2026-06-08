from __future__ import annotations

import threading

from app.auth.salesforce_auth import SalesforceTokenManager


def test_get_token_refreshes_and_caches_token(monkeypatch):
    manager = SalesforceTokenManager(
        consumer_key="client-id",
        private_key_pem="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        username="user@example.com",
        login_url="https://login.salesforce.com",
    )

    encoded_claims = {}

    def fake_encode(claims, private_key, algorithm):
        encoded_claims["claims"] = claims
        encoded_claims["private_key"] = private_key
        encoded_claims["algorithm"] = algorithm
        return "signed.jwt"

    post_calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "access_token": "access-token-1",
                "instance_url": "https://example.my.salesforce.com",
            }

    def fake_post(url, data, timeout):
        post_calls.append((url, data, timeout))
        return FakeResponse()

    monkeypatch.setattr("app.auth.salesforce_auth.jwt.encode", fake_encode)
    monkeypatch.setattr("app.auth.salesforce_auth.requests.post", fake_post)
    monkeypatch.setattr("app.auth.salesforce_auth.time.time", lambda: 1_000)

    access_token, instance_url = manager.get_token()

    assert access_token == "access-token-1"
    assert instance_url == "https://example.my.salesforce.com"
    assert encoded_claims["claims"]["iss"] == "client-id"
    assert encoded_claims["claims"]["sub"] == "user@example.com"
    assert encoded_claims["claims"]["aud"] == "https://login.salesforce.com"
    assert encoded_claims["claims"]["exp"] == 1_180
    assert post_calls == [
        (
            "https://login.salesforce.com/services/oauth2/token",
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": "signed.jwt",
            },
            30,
        )
    ]

    monkeypatch.setattr("app.auth.salesforce_auth.time.time", lambda: 1_100)
    cached_token, cached_instance_url = manager.get_token()

    assert cached_token == "access-token-1"
    assert cached_instance_url == "https://example.my.salesforce.com"
    assert len(post_calls) == 1


def test_get_token_refreshes_once_for_concurrent_calls(monkeypatch):
    manager = SalesforceTokenManager(
        consumer_key="client-id",
        private_key_pem="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        username="user@example.com",
        login_url="https://test.salesforce.com/",
    )

    monkeypatch.setattr("app.auth.salesforce_auth.jwt.encode", lambda *args, **kwargs: "signed.jwt")
    monkeypatch.setattr("app.auth.salesforce_auth.time.time", lambda: 1_000)

    post_calls = []
    start_refresh = threading.Event()
    release_refresh = threading.Event()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "access_token": "access-token-2",
                "instance_url": "https://example.test.salesforce.com",
            }

    def fake_post(url, data, timeout):
        post_calls.append((url, data, timeout))
        start_refresh.set()
        release_refresh.wait(timeout=5)
        return FakeResponse()

    monkeypatch.setattr("app.auth.salesforce_auth.requests.post", fake_post)

    results = []

    def call_get_token():
        results.append(manager.get_token())

    first_thread = threading.Thread(target=call_get_token)
    second_thread = threading.Thread(target=call_get_token)

    first_thread.start()
    start_refresh.wait(timeout=5)
    second_thread.start()
    release_refresh.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert results == [
        ("access-token-2", "https://example.test.salesforce.com"),
        ("access-token-2", "https://example.test.salesforce.com"),
    ]
    assert len(post_calls) == 1