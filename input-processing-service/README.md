# Input Processing Service

## Overview
This microservice handles the first phase of our video generation pipeline: processing user input text in multiple languages, detecting language, translating when necessary, and preparing the text for scene analysis.

## Architecture
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for session management and translation caching
- **Language Processing**: langdetect + polyglot (detection), Google Translate API → IndicTrans2 → NLLB-200 (translation)
- **Containerization**: Docker with health checks

## Services
1. **Input Validation Service**: Content policy, length validation, format checks
2. **Language Detection Service**: langdetect + polyglot (primary), Google Translate API (fallback)
3. **Translation Service**: Google Translate API (primary), IndicTrans2 (fallback-1), NLLB-200 (fallback-2)
4. **Text Preprocessing Service**: Cleaning, normalization, formatting
5. **Storage Service**: Database operations and caching

## API Endpoints
- `POST /api/v1/input/validate` - Validate input text
- `POST /api/v1/input/process` - Complete input processing pipeline
- `GET /api/v1/input/status/{id}` - Get processing status
- `GET /health` - Health check endpoint

## Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Docker Compose
docker-compose up -d

# Run locally
uvicorn main:app --reload --port 8002
```

## Environment Variables
```env
DATABASE_URL=postgresql://user:password@localhost:5432/input_processing
REDIS_URL=redis://localhost:6379/0
GOOGLE_TRANSLATE_API_KEY=your_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
INDIC_TRANS2_ENDPOINT=https://api-inference.huggingface.co/models/ai4bharat/indictrans2-indic-en-1B
NLLB_ENDPOINT=https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M
JWT_SECRET=your_jwt_secret
```

## Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```
