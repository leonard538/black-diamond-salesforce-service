"""Salesforce authentication helpers."""

from __future__ import annotations

import time
from threading import Lock

import jwt
import requests


class SalesforceTokenManager:
	"""Manage Salesforce OAuth 2.0 JWT Bearer tokens with refresh safety."""

	def __init__(
		self,
		consumer_key: str,
		private_key_pem: str,
		username: str,
		login_url: str,
	) -> None:
		self._consumer_key = consumer_key
		self._private_key = private_key_pem
		self._username = username
		self._login_url = login_url.rstrip("/")
		self._access_token: str | None = None
		self._instance_url: str | None = None
		self._expires_at = 0
		self._lock = Lock()

	def get_token(self) -> tuple[str, str]:
		"""Return the current access token and instance URL, refreshing if needed."""
		with self._lock:
			if time.time() > (self._expires_at - 300):
				self._refresh()

			if self._access_token is None or self._instance_url is None:
				raise RuntimeError("Salesforce token refresh did not produce credentials")

			return self._access_token, self._instance_url

	def _refresh(self) -> None:
		now = int(time.time())
		claim = {
			"iss": self._consumer_key,
			"sub": self._username,
			"aud": self._login_url,
			"exp": now + 180,
		}

		signed_jwt = jwt.encode(claim, self._private_key, algorithm="RS256")

		response = requests.post(
			f"{self._login_url}/services/oauth2/token",
			data={
				"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
				"assertion": signed_jwt,
			},
			timeout=30,
		)
		response.raise_for_status()
		data = response.json()

		self._access_token = data["access_token"]
		self._instance_url = data["instance_url"]
		self._expires_at = now + 7200
