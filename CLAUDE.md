# Black Diamond Salesforce Service - AI Context

## Project Overview
A Flask-based microservice that integrates with Salesforce Bulk API 2.0 to perform bulk data extraction, normalization, deduplication, and storage operations.

## Architecture

### Core Flow
1. **Extraction**: `extraction_service.py` orchestrates the bulk job lifecycle
2. **Polling**: `polling_service.py` handles async status polling for long-running jobs
3. **Normalization**: Converts CSV results to Parquet format
4. **Deduplication**: Removes duplicate records by Salesforce ID
5. **Storage**: Publishes to Kafka and uploads to MinIO

### Key Components

#### Authentication (`auth/salesforce_auth.py`)
- JWT Bearer token manager
- Handles OAuth2 token lifecycle
- Manages token refresh and expiration

#### Clients (`app/clients/`)
- `bulk_api_client.py`: Wrapper around Salesforce Bulk API 2.0
  - Job creation and monitoring
  - CSV upload/download
  - Status tracking

#### Models (`app/models/`)
- `scan.py`: Scan state model tracking extraction progress
- `job.py`: Salesforce Bulk API job model

#### Services (`app/services/`)
- `extraction_service.py`: Orchestration layer (main business logic)
- `polling_service.py`: Async polling for job completion
- `normalization_service.py`: CSV → Parquet conversion
- `deduplication_service.py`: Duplicate record removal by SF ID
- `maintenance_service.py`: Cleanup of old scan records

#### Storage (`app/storage/`)
- `minio_client.py`: S3-compatible object storage (MinIO)
- `kafka_producer.py`: Async Kafka message publishing

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Local development with Docker
docker-compose up

# Run tests
pytest tests/

# Run with type checking
mypy app/
```

## Configuration
- Settings defined in `app/config.py` using Pydantic
- Load from `.env` file or environment variables
- See `.env.example` for required variables

## Testing Strategy
- **Unit**: `tests/unit/` - isolated component testing
- **Integration**: `tests/integration/` - service-level and external API testing
- Use `testcontainers` for Kafka and MinIO in integration tests

## Deployment
- Nomad job definitions in `nomad/` directory
  - `dev/`: Development environment
  - `stage/`: Staging environment
  - `prod/`: Production environment

## API Endpoints
See `app/routes.py` for endpoint definitions.

## Notes
- Async operations use Celery + Redis for background jobs
- Long-running bulk jobs use polling pattern for status tracking
- Kafka publishes scan completion events for downstream consumers
