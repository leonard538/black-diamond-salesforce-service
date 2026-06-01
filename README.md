# Black Diamond Salesforce Service

A high-performance microservice for bulk Salesforce data extraction, processing, and storage. This service integrates with Salesforce Bulk API 2.0 to orchestrate large-scale data operations with deduplication, normalization, and event-driven architecture.

## Features

- ✅ **Bulk API Integration**: Direct integration with Salesforce Bulk API 2.0
- ✅ **Async Processing**: Non-blocking job polling with Celery background tasks
- ✅ **Data Normalization**: CSV to Parquet conversion for optimized storage
- ✅ **Deduplication**: Automatic removal of duplicate records by Salesforce ID
- ✅ **Event Publishing**: Kafka integration for event-driven workflows
- ✅ **Cloud Storage**: MinIO (S3-compatible) for distributed data storage
- ✅ **Maintenance**: Automatic cleanup of stale scan records

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Flask API (REST Routes)               │
│           /api/scans /api/jobs                │
└────────┬────────────────────────────────────┬──┘
         │                                   │
    ┌────▼──────────────┐          ┌────────▼─────┐
    │ Extraction Service│          │ Polling Service
    │ (Orchestration)  │          │ (Async Status) │
    └────┬──────────────┘          └────────┬──────┘
         │                                   │
    ┌────▼──────────────────────────────────▼────┐
    │     Salesforce Bulk API 2.0 Client         │
    │   (Job Mgmt, Upload, Download, Status)    │
    └──────────────────────────────────────────┬─┘
                                               │
                 ┌─────────────────────────────┼─────────────────┐
                 │                             │                 │
         ┌───────▼───────┐         ┌───────────▼────────┐  ┌─────▼──────┐
         │ Normalization │         │  Deduplication    │  │ Maintenance│
         │ (CSV→Parquet) │         │  (SF ID Unique)   │  │  (Cleanup) │
         └───────┬───────┘         └───────────┬────────┘  └─────┬──────┘
                 │                             │                │
         ┌───────▼─────────────────────────────▼─────────┬──────▼──────┐
         │                                               │             │
    ┌────▼──────────────┐                        ┌───────▼─────┐ ┌──▼────┐
    │   Kafka Producer  │                        │ MinIO Client│ │ Logger│
    │  (Events/Topics)  │                        │  (Upload)   │ └───────┘
    └───────────────────┘                        └─────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Salesforce connected app credentials
- MinIO or AWS S3 bucket
- Kafka broker

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/black-diamond-salesforce-service.git
cd black-diamond-salesforce-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your Salesforce and MinIO credentials
```

### Local Development

```bash
# Start dependencies (Kafka, MinIO, Zookeeper)
docker-compose up -d

# Run the Flask app
python -m app.main

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Docker Deployment

```bash
# Build image
docker build -t black-diamond-salesforce-service:latest .

# Run container
docker run -p 5000:5000 \
  -e SALESFORCE_CLIENT_ID=your_id \
  -e SALESFORCE_CLIENT_SECRET=your_secret \
  black-diamond-salesforce-service:latest
```

## API Endpoints

### Scans
- `POST /api/scans` - Create a new extraction scan
- `GET /api/scans/{scan_id}` - Get scan status and progress
- `GET /api/scans` - List all scans
- `DELETE /api/scans/{scan_id}` - Cancel a scan

### Jobs
- `GET /api/jobs/{job_id}` - Get Salesforce bulk job details
- `GET /api/jobs` - List all jobs

### Health
- `GET /health` - Service health check

## Configuration

Configuration is managed through `app/config.py` using Pydantic settings.

### Environment Variables

```env
# Flask
FLASK_ENV=development
DEBUG=True

# Salesforce
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_USERNAME=your_username
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com

# Kafka
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC_SCAN_COMPLETE=scan-complete-events

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=scans

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=sqlite:///./app.db  # Or PostgreSQL for production
```

## Project Structure

```
app/
├── __init__.py
├── main.py                      # Flask app factory
├── config.py                    # Pydantic settings
├── routes.py                    # API route definitions
├── auth/
│   ├── __init__.py
│   └── salesforce_auth.py       # JWT token management
├── clients/
│   ├── __init__.py
│   └── bulk_api_client.py       # Salesforce Bulk API wrapper
├── services/
│   ├── __init__.py
│   ├── extraction_service.py    # Orchestration logic
│   ├── polling_service.py       # Async polling
│   ├── normalization_service.py # CSV → Parquet conversion
│   ├── deduplication_service.py # Duplicate removal
│   └── maintenance_service.py   # Cleanup tasks
├── storage/
│   ├── __init__.py
│   ├── minio_client.py          # Object storage client
│   └── kafka_producer.py        # Event publishing
└── models/
    ├── __init__.py
    ├── scan.py                  # Scan state model
    └── job.py                   # Bulk job model

tests/
├── conftest.py                  # Pytest fixtures
├── unit/                        # Unit tests
└── integration/                 # Integration tests

nomad/
├── dev/                         # Dev deployment configs
├── stage/                       # Staging deployment configs
└── prod/                        # Production deployment configs
```

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Coverage Report
```bash
pytest --cov=app --cov-report=html tests/
```

## Development Workflow

1. **Feature Branch**: Create feature branch from `main`
2. **Local Testing**: Run full test suite locally
3. **Type Checking**: Run `mypy app/`
4. **Linting**: Run `black` and `flake8`
5. **Pull Request**: Submit PR with test results
6. **CI/CD**: GitHub Actions runs full suite
7. **Merge**: Merge to main after approval

## Deployment

### Development (Nomad)
```bash
nomad run nomad/dev/salesforce-service.hcl
```

### Staging
```bash
nomad run nomad/stage/salesforce-service.hcl
```

### Production
```bash
nomad run nomad/prod/salesforce-service.hcl
```

## Monitoring & Logging

- Logs: JSON format via `python-json-logger`
- Metrics: Prometheus-compatible endpoints
- Traces: OpenTelemetry integration ready

## Performance Considerations

- **Bulk Jobs**: Optimized for 1M+ record extractions
- **Polling**: Exponential backoff for status checks
- **Storage**: Parquet format reduces storage by ~80%
- **Deduplication**: In-memory tracking for 100K+ records

## Known Limitations

- Salesforce Bulk API batch size: 10M records max
- MinIO performance: Scale to S3 for production
- Kafka topics: Single partition for order guarantee

## Troubleshooting

### Job Timeout
- Increase `POLLING_MAX_RETRIES` in config
- Check Salesforce job status in UI

### Memory Issues
- Reduce batch size in `extraction_service.py`
- Scale horizontally with multiple workers

### Kafka Connection Failed
- Verify broker is running: `docker-compose ps`
- Check network connectivity

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/name`
5. Submit Pull Request

## License

Proprietary - Black Diamond Partners

## Support

For issues and questions:
- Email: engineering@blackdiamond.com
- Slack: #salesforce-service
- Jira: PROJ-1234
