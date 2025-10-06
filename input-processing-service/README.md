# Input Processing Service

## Overview
This microservice handles the first phase of our video generation pipeline: processing user input text in multiple languages, detecting language, translating when necessary, and preparing the text for scene analysis.

## ✅ CURRENT STATUS: MVP COMPLETED + SRP REFACTOR (December 2024)
- **Service Status**: Fully operational with Single Responsibility Principle compliance
- **Database Schema**: Fixed and optimized (language_confidence VARCHAR(20) issue resolved)
- **Language Detection**: Verified working for Telugu, Hindi, and English with proper Unicode handling
- **Translation Pipeline**: Google Translate API → NLLB-200 fallback system operational
- **API Endpoints**: All endpoints tested and verified with proper error handling
- **API Enhancement**: Status endpoint now supports detailed phase data retrieval
- **Critical Issues Resolved**: Unicode character handling, Redis compatibility, PowerShell encoding
- **Docker Infrastructure**: Complete containerization with PostgreSQL and Redis
- **Production Readiness**: Ready for Phase 2 development and scaling

## Architecture
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for session management and translation caching
- **Language Processing**: langdetect + langid (detection), Google Translate API → NLLB-200 (translation) - MVP 2-layer system
- **Containerization**: Docker with health checks
- **Redis Client**: redis[hiredis] with redis.asyncio (aioredis removed for Python 3.11 compatibility)

## Services
1. **Input Validation Service**: Content policy, length validation, format checks
2. **Language Detection Service**: langdetect (primary), langid (fallback)
3. **Translation Service**: Google Translate API (primary), NLLB-200 (fallback) - MVP 2-layer system
   - **TODO (Production Phase)**: Re-enable IndicTrans2 as Fallback Layer 1
   - **Future 3-layer system**: Google → IndicTrans2 → NLLB
4. **Text Preprocessing Service**: Cleaning, normalization, formatting
5. **Storage Service**: Database operations and caching

## API Endpoints
- `POST /api/v1/input/validate` - Validate input text
- `POST /api/v1/input/process` - Complete input processing pipeline
- `GET /api/v1/input/status/{id}` - Get processing status (supports `?detailed=true` for complete phase data)
- `GET /health` - Health check endpoint

### Status Endpoint Enhancement
The status endpoint now supports two response modes:
- **Default mode**: Returns latest status only (backward compatible)
- **Detailed mode**: Returns complete phase data including language detection results, translation results, and confidence scores

**Usage Examples:**
```bash
# Quick status check (existing behavior)
GET /api/v1/input/status/123

# Complete detailed response (new feature)
GET /api/v1/input/status/123?detailed=true
```

## Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Docker Compose
docker-compose up -d

# Run locally
uvicorn main:app --reload --port 8002
```

## Environment Variables - MVP Configuration
```env
DATABASE_URL=postgresql://user:password@localhost:5432/input_processing
REDIS_URL=redis://localhost:6379/0
GOOGLE_TRANSLATE_API_KEY=your_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
NLLB_ENDPOINT=https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M
# TODO (Production Phase): Re-enable IndicTrans2 as Fallback Layer 1
# INDIC_TRANS2_ENDPOINT=https://api-inference.huggingface.co/models/ai4bharat/indictrans2-indic-en-1B
JWT_SECRET=your_jwt_secret
```

## Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```
