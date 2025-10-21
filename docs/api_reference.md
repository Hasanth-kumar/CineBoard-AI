# API Reference

## 🌐 API Overview

The CinBoard AI platform provides a comprehensive REST API for video generation. The API follows RESTful principles and uses JSON for data exchange. All endpoints are versioned under `/api/v1/`.

### Base URL
```
https://api.cinboard.ai/api/v1/
```

### Authentication
All API requests require authentication using JWT tokens:
```http
Authorization: Bearer <your_jwt_token>
```

### Rate Limiting
- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1,000 requests/hour
- **Enterprise**: Custom limits

## 📋 Current API Endpoints

### Input Processing Service ✅ **IMPLEMENTED**

**Base URL**: `https://api.cinboard.ai/api/v1/input/`  
**Service Port**: 8002  
**Status**: Fully operational

#### 1. Input Validation

**Endpoint**: `POST /api/v1/input/validate`  
**Description**: Validate input text for content policy, length, and format  
**Status**: ✅ Implemented

**Request Body**:
```json
{
  "text": "నాకు ఎగరాలి అని ఉంది",
  "user_id": 1,
  "session_id": "test-session"
}
```

**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "content_policy_check": {
    "passed": true,
    "violations": []
  },
  "length_check": {
    "passed": true,
    "character_count": 20,
    "word_count": 4
  },
  "format_check": {
    "passed": true,
    "encoding": "utf-8"
  }
}
```

**Error Response**:
```json
{
  "is_valid": false,
  "errors": [
    {
      "type": "content_policy",
      "message": "Content violates policy guidelines",
      "details": "Inappropriate content detected"
    }
  ],
  "warnings": []
}
```

#### 2. Input Processing

**Endpoint**: `POST /api/v1/input/process`  
**Description**: Complete input processing pipeline (validation, language detection, translation, preprocessing)  
**Status**: ✅ Implemented

**Request Body**:
```json
{
  "text": "నాకు ఎగరాలి అని ఉంది",
  "user_id": 1,
  "session_id": "test-session"
}
```

**Response**:
```json
{
  "input_id": 41,
  "status": "pending",
  "message": "Input processing started successfully"
}
```

**Processing Status Response** (after completion):
```json
{
  "input_id": 41,
  "status": "completed",
  "detected_language": "te",
  "language_confidence": 1.0,
  "translation_result": "I want to fly.",
  "translation_confidence": 0.9
}
```

#### 3. Processing Status

**Endpoint**: `GET /api/v1/input/status/{input_id}`  
**Description**: Get processing status for a specific input  
**Status**: ✅ Implemented

**Query Parameters**:
- `detailed` (boolean, optional): Return detailed phase information

**Response** (Default):
```json
{
  "input_id": 41,
  "status": "completed",
  "current_phase": "translation",
  "progress_percentage": 100
}
```

**Response** (Detailed):
```json
{
  "input_id": 41,
  "status": "completed",
  "current_phase": "translation",
  "progress_percentage": 100,
  "phases": [
    {
      "phase": "validation",
      "status": "completed",
      "progress_percentage": 100,
      "started_at": "2024-12-01T10:00:00Z",
      "completed_at": "2024-12-01T10:00:01Z",
      "duration_seconds": 1
    },
    {
      "phase": "language_detection",
      "status": "completed",
      "progress_percentage": 100,
      "phase_data": {
        "detected_language": "te",
        "confidence": 1.0,
        "method": "langid"
      }
    },
    {
      "phase": "translation",
      "status": "completed",
      "progress_percentage": 100,
      "phase_data": {
        "translated_text": "I want to fly.",
        "confidence": 0.9,
        "method": "google_translate"
      }
    }
  ]
}
```

#### 4. Health Check

**Endpoint**: `GET /health`  
**Description**: Service health check  
**Status**: ✅ Implemented

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-01T10:00:00Z",
  "service": "input-processing-service",
  "version": "1.0.0"
}
```

**Endpoint**: `GET /ready`  
**Description**: Service readiness check  
**Status**: ✅ Implemented

**Response**:
```json
{
  "status": "ready"
}
```

## 🔄 Planned API Endpoints

### Scene Analysis Service 🔄 **PLANNED**

**Base URL**: `https://api.cinboard.ai/api/v1/scene/`  
**Service Port**: 8020  
**Status**: Planned but not implemented

#### 1. Scene Analysis

**Endpoint**: `POST /api/v1/scene/analyze`  
**Description**: Analyze processed text for entities, mood, camera cues, and temporal sequence  
**Status**: 🔄 Planned

**Request Body**:
```json
{
  "input_id": 41,
  "processed_text": "I want to fly.",
  "language_info": {
    "detected_language": "te",
    "confidence": 1.0
  }
}
```

**Response**:
```json
{
  "analysis_id": "analysis_123",
  "status": "completed",
  "entities": {
    "characters": [
      {
        "name": "protagonist",
        "description": "person wanting to fly",
        "attributes": ["human", "aspiring"]
      }
    ],
    "objects": [],
    "locations": [],
    "actions": ["fly", "want"]
  },
  "mood_analysis": {
    "emotional_tone": "aspirational",
    "atmosphere": "hopeful",
    "visual_style": "uplifting"
  },
  "camera_cues": {
    "shot_types": ["medium_shot", "wide_shot"],
    "movements": ["static", "slow_zoom"],
    "transitions": ["fade_in", "fade_out"]
  },
  "temporal_analysis": {
    "scenes": [
      {
        "scene_id": 1,
        "start_time": 0,
        "duration_seconds": 8,
        "description": "Person expressing desire to fly"
      }
    ],
    "total_duration": 8
  }
}
```

#### 2. Storyboard Generation

**Endpoint**: `POST /api/v1/scene/storyboard`  
**Description**: Generate structured storyboard from scene analysis  
**Status**: 🔄 Planned

**Request Body**:
```json
{
  "analysis_id": "analysis_123",
  "scene_analysis": {
    "entities": {...},
    "mood_analysis": {...},
    "camera_cues": {...},
    "temporal_analysis": {...}
  }
}
```

**Response**:
```json
{
  "storyboard_id": "storyboard_123",
  "status": "completed",
  "scenes": [
    {
      "scene_id": 1,
      "description": "Person expressing desire to fly",
      "duration_seconds": 8,
      "keyframe_count": 2,
      "character_descriptions": [
        {
          "character_id": "char_1",
          "name": "protagonist",
          "description": "A person with hopeful expression, looking upward",
          "consistency_key": "protagonist_main"
        }
      ],
      "keyframe_descriptions": [
        {
          "keyframe_id": "kf_1",
          "sequence": 0,
          "description": "Medium shot of person looking up with hopeful expression",
          "timing_seconds": 0
        },
        {
          "keyframe_id": "kf_2",
          "sequence": 1,
          "description": "Wide shot showing person in open space, arms slightly raised",
          "timing_seconds": 4
        }
      ]
    }
  ],
  "visual_style": {
    "mood": "uplifting",
    "color_palette": "warm",
    "lighting": "soft_natural"
  }
}
```

### Character Generation Service ⚠️ **NEW REQUIREMENT**

**Base URL**: `https://api.cinboard.ai/api/v1/character/`  
**Service Port**: 8030  
**Status**: New requirement from GenAI workflow

#### 1. Character Generation

**Endpoint**: `POST /api/v1/character/generate`  
**Description**: Generate consistent character images using Whisk AI  
**Status**: ⚠️ New Requirement

**Request Body**:
```json
{
  "storyboard_id": "storyboard_123",
  "character_descriptions": [
    {
      "character_id": "char_1",
      "name": "protagonist",
      "description": "A person with hopeful expression, looking upward",
      "consistency_key": "protagonist_main"
    }
  ],
  "visual_style": {
    "mood": "uplifting",
    "color_palette": "warm",
    "lighting": "soft_natural"
  }
}
```

**Response**:
```json
{
  "generation_id": "char_gen_123",
  "status": "completed",
  "characters": [
    {
      "character_id": "char_1",
      "name": "protagonist",
      "image_url": "https://cdn.cinboard.ai/characters/char_1.jpg",
      "quality_score": 0.95,
      "generation_params": {
        "style": "realistic",
        "quality": "high",
        "consistency_key": "protagonist_main"
      }
    }
  ]
}
```

#### 2. Character Consistency Check

**Endpoint**: `GET /api/v1/character/consistency/{character_id}`  
**Description**: Check character consistency across generated images  
**Status**: ⚠️ New Requirement

**Response**:
```json
{
  "character_id": "char_1",
  "consistency_score": 0.92,
  "generated_images": [
    {
      "image_url": "https://cdn.cinboard.ai/characters/char_1_scene_1.jpg",
      "scene_id": 1,
      "quality_score": 0.95
    },
    {
      "image_url": "https://cdn.cinboard.ai/characters/char_1_scene_2.jpg",
      "scene_id": 2,
      "quality_score": 0.89
    }
  ]
}
```

### Keyframe Generation Service ⚠️ **NEW REQUIREMENT**

**Base URL**: `https://api.cinboard.ai/api/v1/keyframe/`  
**Service Port**: 8040  
**Status**: New requirement from GenAI workflow

#### 1. Keyframe Generation

**Endpoint**: `POST /api/v1/keyframe/generate`  
**Description**: Generate 1-3 keyframes per 8-second video clip  
**Status**: ⚠️ New Requirement

**Request Body**:
```json
{
  "storyboard_id": "storyboard_123",
  "characters": [
    {
      "character_id": "char_1",
      "image_url": "https://cdn.cinboard.ai/characters/char_1.jpg"
    }
  ],
  "scenes": [
    {
      "scene_id": 1,
      "keyframe_descriptions": [
        {
          "keyframe_id": "kf_1",
          "sequence": 0,
          "description": "Medium shot of person looking up with hopeful expression",
          "timing_seconds": 0
        },
        {
          "keyframe_id": "kf_2",
          "sequence": 1,
          "description": "Wide shot showing person in open space, arms slightly raised",
          "timing_seconds": 4
        }
      ]
    }
  ]
}
```

**Response**:
```json
{
  "generation_id": "kf_gen_123",
  "status": "completed",
  "keyframes": [
    {
      "keyframe_id": "kf_1",
      "scene_id": 1,
      "sequence": 0,
      "image_url": "https://cdn.cinboard.ai/keyframes/kf_1.jpg",
      "timing_seconds": 0,
      "quality_score": 0.93
    },
    {
      "keyframe_id": "kf_2",
      "scene_id": 1,
      "sequence": 1,
      "image_url": "https://cdn.cinboard.ai/keyframes/kf_2.jpg",
      "timing_seconds": 4,
      "quality_score": 0.91
    }
  ]
}
```

### Video Generation Service 🔄 **PLANNED**

**Base URL**: `https://api.cinboard.ai/api/v1/video/`  
**Service Port**: 8050  
**Status**: Planned but not implemented

#### 1. Video Generation

**Endpoint**: `POST /api/v1/video/generate`  
**Description**: Generate video clips from keyframes using Veo4 API  
**Status**: 🔄 Planned

**Request Body**:
```json
{
  "keyframes": [
    {
      "keyframe_id": "kf_1",
      "image_url": "https://cdn.cinboard.ai/keyframes/kf_1.jpg",
      "timing_seconds": 0
    },
    {
      "keyframe_id": "kf_2",
      "image_url": "https://cdn.cinboard.ai/keyframes/kf_2.jpg",
      "timing_seconds": 4
    }
  ],
  "characters": [
    {
      "character_id": "char_1",
      "image_url": "https://cdn.cinboard.ai/characters/char_1.jpg"
    }
  ],
  "scene_duration": 8,
  "visual_style": {
    "mood": "uplifting",
    "color_palette": "warm",
    "lighting": "soft_natural"
  }
}
```

**Response**:
```json
{
  "generation_id": "video_gen_123",
  "status": "completed",
  "video_clips": [
    {
      "clip_id": "clip_1",
      "scene_id": 1,
      "video_url": "https://cdn.cinboard.ai/videos/clip_1.mp4",
      "duration_seconds": 8,
      "quality_score": 0.94,
      "file_size_mb": 12.5
    }
  ]
}
```

### Voiceover Generation Service ⚠️ **NEW REQUIREMENT**

**Base URL**: `https://api.cinboard.ai/api/v1/voiceover/`  
**Service Port**: 8060  
**Status**: New requirement from GenAI workflow

#### 1. Voiceover Generation

**Endpoint**: `POST /api/v1/voiceover/generate`  
**Description**: Generate voiceover using Eleven Labs API  
**Status**: ⚠️ New Requirement

**Request Body**:
```json
{
  "text": "I want to fly.",
  "language_info": {
    "detected_language": "te",
    "confidence": 1.0
  },
  "voice_settings": {
    "language": "en",
    "voice_id": "voice_001",
    "speed": 1.0,
    "pitch": 1.0,
    "emotion": "hopeful"
  }
}
```

**Response**:
```json
{
  "generation_id": "voice_gen_123",
  "status": "completed",
  "voiceover": {
    "audio_url": "https://cdn.cinboard.ai/voiceovers/voice_gen_123.mp3",
    "duration_seconds": 3.2,
    "voice_settings": {
      "voice_id": "voice_001",
      "language": "en",
      "speed": 1.0,
      "pitch": 1.0,
      "emotion": "hopeful"
    },
    "quality_score": 0.96
  }
}
```

### Video Composition Service ⚠️ **NEW REQUIREMENT**

**Base URL**: `https://api.cinboard.ai/api/v1/composition/`  
**Service Port**: 8070  
**Status**: New requirement from GenAI workflow

#### 1. Video Composition

**Endpoint**: `POST /api/v1/composition/compose`  
**Description**: Stitch video clips and add voiceover to create final video  
**Status**: ⚠️ New Requirement

**Request Body**:
```json
{
  "video_clips": [
    {
      "clip_id": "clip_1",
      "video_url": "https://cdn.cinboard.ai/videos/clip_1.mp4",
      "duration_seconds": 8
    }
  ],
  "voiceover": {
    "audio_url": "https://cdn.cinboard.ai/voiceovers/voice_gen_123.mp3",
    "duration_seconds": 3.2
  },
  "composition_settings": {
    "transitions": ["fade_in", "fade_out"],
    "audio_sync": "automatic",
    "quality": "high"
  }
}
```

**Response**:
```json
{
  "composition_id": "comp_123",
  "status": "completed",
  "final_video": {
    "video_url": "https://cdn.cinboard.ai/final/final_video_123.mp4",
    "duration_seconds": 8,
    "quality_score": 0.95,
    "file_size_mb": 45.2,
    "thumbnails": [
      "https://cdn.cinboard.ai/thumbnails/thumb_1.jpg",
      "https://cdn.cinboard.ai/thumbnails/thumb_2.jpg"
    ]
  }
}
```

## 🔄 Complete Workflow API

### End-to-End Video Generation

**Endpoint**: `POST /api/v1/generate/video`  
**Description**: Complete end-to-end video generation workflow  
**Status**: 🔄 Planned

**Request Body**:
```json
{
  "text": "నాకు ఎగరాలి అని ఉంది",
  "user_id": 1,
  "session_id": "test-session",
  "generation_settings": {
    "quality": "high",
    "language": "auto",
    "voice_style": "natural",
    "visual_style": "realistic"
  }
}
```

**Response**:
```json
{
  "generation_id": "gen_123",
  "status": "processing",
  "estimated_completion": "2024-12-01T10:05:00Z",
  "workflow_stages": [
    {
      "stage": "input_processing",
      "status": "completed",
      "progress": 100
    },
    {
      "stage": "scene_analysis",
      "status": "completed",
      "progress": 100
    },
    {
      "stage": "character_generation",
      "status": "completed",
      "progress": 100
    },
    {
      "stage": "keyframe_generation",
      "status": "completed",
      "progress": 100
    },
    {
      "stage": "video_generation",
      "status": "processing",
      "progress": 60
    },
    {
      "stage": "voiceover_generation",
      "status": "pending",
      "progress": 0
    },
    {
      "stage": "video_composition",
      "status": "pending",
      "progress": 0
    }
  ]
}
```

**Final Response** (when completed):
```json
{
  "generation_id": "gen_123",
  "status": "completed",
  "final_video": {
    "video_url": "https://cdn.cinboard.ai/final/final_video_123.mp4",
    "duration_seconds": 8,
    "quality_score": 0.95,
    "file_size_mb": 45.2,
    "thumbnails": [
      "https://cdn.cinboard.ai/thumbnails/thumb_1.jpg",
      "https://cdn.cinboard.ai/thumbnails/thumb_2.jpg"
    ]
  },
  "generation_metadata": {
    "total_processing_time": 120,
    "characters_generated": 1,
    "keyframes_generated": 2,
    "video_clips_generated": 1,
    "voiceover_generated": true
  }
}
```

## 📊 Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": {
      "field": "text",
      "issue": "Content violates policy guidelines"
    },
    "timestamp": "2024-12-01T10:00:00Z",
    "request_id": "req_123"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `PROCESSING_ERROR` | 500 | Internal processing error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 🔧 SDK and Integration

### Python SDK Example

```python
from cinboard_ai import CinBoardClient

client = CinBoardClient(api_key="your_api_key")

# Generate video
result = client.generate_video(
    text="నాకు ఎగరాలి అని ఉంది",
    user_id=1,
    quality="high"
)

print(f"Video URL: {result.final_video.video_url}")
```

### JavaScript SDK Example

```javascript
import { CinBoardClient } from '@cinboard-ai/sdk';

const client = new CinBoardClient('your_api_key');

// Generate video
const result = await client.generateVideo({
  text: 'నాకు ఎగరాలి అని ఉంది',
  userId: 1,
  quality: 'high'
});

console.log(`Video URL: ${result.finalVideo.videoUrl}`);
```

---

This API reference provides comprehensive documentation for all current and planned endpoints, enabling developers to integrate with the CinBoard AI platform effectively.
