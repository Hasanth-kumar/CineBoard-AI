# Video Generation Platform - System Architecture

## Executive Summary

This document defines the comprehensive system architecture for the multilingual video generation platform. The architecture is designed as a scalable, microservices-based system that can handle high-volume concurrent requests while maintaining performance and reliability.

## 1. High-Level System Architecture

### 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Web App   │  │  Mobile App │  │   Admin UI  │             │
│  │  (Next.js)  │  │  (React)    │  │  (React)    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Auth      │  │   Rate      │  │   Load      │             │
│  │   Service   │  │   Limiting  │  │   Balancer  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Microservices Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Language  │  │   Scene     │  │   Prompt    │             │
│  │   Service   │  │   Analysis  │  │   Service   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Generation  │  │   Media     │  │   User      │             │
│  │   Service   │  │   Service   │  │   Service   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │    Redis    │  │   Elastic   │             │
│  │  Database   │  │    Cache    │  │   Search    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │   AWS S3    │  │   RabbitMQ  │                              │
│  │   Storage   │  │    Queue    │                              │
│  └─────────────┘  └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Principles

1. **Microservices Architecture**: Each service has a single responsibility
2. **Event-Driven Communication**: Services communicate via events and messages
3. **Horizontal Scalability**: Services can scale independently
4. **Fault Tolerance**: System continues operating despite individual service failures
5. **Data Consistency**: Eventual consistency with strong consistency where needed
6. **Security First**: Authentication, authorization, and data protection at every layer

## 2. Frontend Architecture

### 2.1 Web Application Architecture

#### 2.1.1 Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Headless UI
- **State Management**: Zustand
- **Real-time**: Socket.io client
- **File Upload**: React Dropzone
- **Video Player**: Video.js

#### 2.1.2 Component Architecture

```typescript
// Component Structure
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth routes
│   ├── dashboard/          # Main dashboard
│   ├── generate/           # Generation interface
│   └── api/               # API routes
├── components/             # Reusable components
│   ├── ui/                # Base UI components
│   ├── forms/             # Form components
│   ├── video/             # Video-related components
│   └── layout/            # Layout components
├── hooks/                 # Custom React hooks
├── stores/                # Zustand stores
├── services/              # API services
├── utils/                 # Utility functions
└── types/                 # TypeScript types
```

#### 2.1.3 State Management Architecture

```typescript
// Zustand Store Structure
interface AppState {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  
  // Generation state
  currentGeneration: GenerationState | null;
  generationHistory: Generation[];
  
  // UI state
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  
  // Actions
  setUser: (user: User) => void;
  startGeneration: (input: string) => void;
  updateGeneration: (id: string, updates: Partial<GenerationState>) => void;
}

// Generation State
interface GenerationState {
  id: string;
  status: 'processing' | 'generating' | 'completed' | 'failed';
  progress: number;
  currentPhase: string;
  input: string;
  output?: {
    images: string[];
    video: string;
  };
  error?: string;
}
```

### 2.2 Mobile Application Architecture

#### 2.2.1 Technology Stack
- **Framework**: React Native with Expo
- **Navigation**: React Navigation 6
- **State Management**: Redux Toolkit
- **Video Player**: React Native Video
- **Camera**: Expo Camera

#### 2.2.2 Mobile-Specific Features
- **Offline Support**: Cache generated content for offline viewing
- **Push Notifications**: Real-time generation updates
- **Camera Integration**: Direct video recording and upload
- **Biometric Authentication**: Touch ID/Face ID support

## 3. Backend Architecture

### 3.1 Microservices Architecture

#### 3.1.1 Core Services - Improved Single Responsibility Design

```python
# Service Registry - Domain-Driven Architecture
DOMAINS = {
    'user_management': {
        'services': {
            'auth-service': {
                'port': 8001,
                'responsibilities': ['authentication', 'authorization', 'token management'],
                'dependencies': ['postgresql', 'redis']
            },
            'user-service': {
                'port': 8002,
                'responsibilities': ['user profiles', 'user preferences', 'account management'],
                'dependencies': ['postgresql', 'redis']
            },
            'session-service': {
                'port': 8003,
                'responsibilities': ['session management', 'user state tracking'],
                'dependencies': ['redis']
            }
        }
    },
    'content_processing': {
        'services': {
            'language-detection-service': {
                'port': 8010,
                'responsibilities': ['language detection', 'confidence scoring'],
                'dependencies': ['redis', 'langdetect', 'polyglot']
            },
            'translation-service': {
                'port': 8011,
                'responsibilities': ['text translation', 'translation caching'],
                'dependencies': ['redis', 'google-translate', 'nllb']
            },
            'text-preprocessing-service': {
                'port': 8012,
                'responsibilities': ['text cleaning', 'normalization', 'formatting'],
                'dependencies': ['redis']
            }
        }
    },
    'scene_analysis': {
        'services': {
            'entity-extraction-service': {
                'port': 8020,
                'responsibilities': ['character extraction', 'object extraction', 'location extraction'],
                'dependencies': ['redis', 'google-translate', 'indic-trans2', 'nllb']
            },
            'mood-analysis-service': {
                'port': 8021,
                'responsibilities': ['emotional tone analysis', 'atmosphere detection'],
                'dependencies': ['redis', 'google-translate', 'indic-trans2', 'nllb']
            },
            'camera-analysis-service': {
                'port': 8022,
                'responsibilities': ['camera movement detection', 'shot type analysis'],
                'dependencies': ['redis', 'google-translate', 'indic-trans2', 'nllb']
            },
            'temporal-analysis-service': {
                'port': 8023,
                'responsibilities': ['sequence analysis', 'timing detection'],
                'dependencies': ['redis', 'google-translate', 'indic-trans2', 'nllb']
            },
            'scene-analysis-orchestrator': {
                'port': 8024,
                'responsibilities': ['workflow coordination', 'result aggregation'],
                'dependencies': ['rabbitmq', 'redis']
            }
        }
    },
    'prompt_generation': {
        'services': {
            'prompt-structuring-service': {
                'port': 8030,
                'responsibilities': ['template filling', 'prompt formatting'],
                'dependencies': ['redis', 'postgresql']
            },
            'prompt-validation-service': {
                'port': 8031,
                'responsibilities': ['prompt validation', 'quality checking'],
                'dependencies': ['redis']
            },
            'prompt-enhancement-service': {
                'port': 8032,
                'responsibilities': ['prompt optimization', 'technical specifications'],
                'dependencies': ['redis', 'google-translate', 'indic-trans2', 'nllb']
            }
        }
    },
    'generation': {
        'services': {
            'image-generation-service': {
                'port': 8040,
                'responsibilities': ['Nano Banana integration', 'image processing'],
                'dependencies': ['rabbitmq', 'aws-s3']
            },
            'video-generation-service': {
                'port': 8041,
                'responsibilities': ['Veo4 integration', 'video processing'],
                'dependencies': ['rabbitmq', 'aws-s3']
            },
            'generation-orchestrator': {
                'port': 8042,
                'responsibilities': ['workflow coordination', 'progress tracking'],
                'dependencies': ['rabbitmq', 'redis']
            }
        }
    },
    'media_management': {
        'services': {
            'storage-service': {
                'port': 8050,
                'responsibilities': ['file storage', 'file retrieval', 'CDN management'],
                'dependencies': ['aws-s3', 'cloudfront']
            },
            'post-processing-service': {
                'port': 8051,
                'responsibilities': ['video enhancement', 'format conversion'],
                'dependencies': ['aws-s3', 'ffmpeg']
            },
            'quality-assurance-service': {
                'port': 8052,
                'responsibilities': ['quality checking', 'validation'],
                'dependencies': ['aws-s3', 'redis']
            }
        }
    },
    'voice_processing': {
        'services': {
            'audio-preprocessing-service': {
                'port': 8060,
                'responsibilities': ['audio cleaning', 'noise reduction', 'format conversion'],
                'dependencies': ['aws-s3', 'ffmpeg']
            },
            'speech-recognition-service': {
                'port': 8061,
                'responsibilities': ['voice-to-text transcription'],
                'dependencies': ['whisper', 'redis']
            },
            'voice-language-detection-service': {
                'port': 8062,
                'responsibilities': ['language detection from voice'],
                'dependencies': ['whisper', 'redis']
            },
            'voice-processing-orchestrator': {
                'port': 8063,
                'responsibilities': ['voice workflow coordination'],
                'dependencies': ['rabbitmq', 'redis']
            }
        }
    },
    'communication': {
        'services': {
            'notification-service': {
                'port': 8070,
                'responsibilities': ['push notifications', 'email notifications'],
                'dependencies': ['socketio', 'redis', 'sendgrid']
            },
            'real-time-service': {
                'port': 8071,
                'responsibilities': ['WebSocket management', 'real-time updates'],
                'dependencies': ['socketio', 'redis']
            }
        }
    }
}
```

#### 3.1.2 Enhanced Event-Driven Communication Patterns

```python
# Granular Event Definitions
EVENTS = {
    # User Management Events
    'user_registered': {
        'publisher': 'auth-service',
        'subscribers': ['notification-service', 'analytics-service', 'user-service'],
        'data': ['user_id', 'email', 'registration_timestamp']
    },
    'user_authenticated': {
        'publisher': 'auth-service',
        'subscribers': ['session-service', 'analytics-service'],
        'data': ['user_id', 'session_id', 'auth_timestamp']
    },
    'user_profile_updated': {
        'publisher': 'user-service',
        'subscribers': ['analytics-service', 'notification-service'],
        'data': ['user_id', 'profile_changes', 'update_timestamp']
    },
    
    # Content Processing Events
    'language_detected': {
        'publisher': 'language-detection-service',
        'subscribers': ['translation-service', 'analytics-service'],
        'data': ['text_hash', 'detected_language', 'confidence_score']
    },
    'text_translated': {
        'publisher': 'translation-service',
        'subscribers': ['text-preprocessing-service', 'analytics-service'],
        'data': ['original_text_hash', 'translated_text', 'source_language', 'target_language']
    },
    'text_preprocessed': {
        'publisher': 'text-preprocessing-service',
        'subscribers': ['scene-analysis-orchestrator'],
        'data': ['processed_text', 'preprocessing_steps', 'text_hash']
    },
    
    # Scene Analysis Events
    'entities_extracted': {
        'publisher': 'entity-extraction-service',
        'subscribers': ['scene-analysis-orchestrator', 'analytics-service'],
        'data': ['text_hash', 'entities', 'confidence_score', 'extraction_method']
    },
    'mood_analyzed': {
        'publisher': 'mood-analysis-service',
        'subscribers': ['scene-analysis-orchestrator', 'analytics-service'],
        'data': ['text_hash', 'mood_result', 'confidence_score', 'emotional_cues']
    },
    'camera_cues_extracted': {
        'publisher': 'camera-analysis-service',
        'subscribers': ['scene-analysis-orchestrator', 'analytics-service'],
        'data': ['text_hash', 'camera_movements', 'shot_types', 'confidence_score']
    },
    'temporal_analyzed': {
        'publisher': 'temporal-analysis-service',
        'subscribers': ['scene-analysis-orchestrator', 'analytics-service'],
        'data': ['text_hash', 'temporal_sequence', 'timing_info', 'confidence_score']
    },
    'scene_analysis_completed': {
        'publisher': 'scene-analysis-orchestrator',
        'subscribers': ['prompt-structuring-service', 'analytics-service'],
        'data': ['analysis_id', 'scene_data', 'confidence_scores', 'processing_time']
    },
    
    # Prompt Generation Events
    'prompt_structured': {
        'publisher': 'prompt-structuring-service',
        'subscribers': ['prompt-validation-service', 'analytics-service'],
        'data': ['prompt_id', 'structured_prompt', 'template_used']
    },
    'prompt_validated': {
        'publisher': 'prompt-validation-service',
        'subscribers': ['prompt-enhancement-service', 'analytics-service'],
        'data': ['prompt_id', 'validation_result', 'quality_score']
    },
    'prompt_enhanced': {
        'publisher': 'prompt-enhancement-service',
        'subscribers': ['generation-orchestrator', 'analytics-service'],
        'data': ['prompt_id', 'enhanced_prompt', 'optimization_applied']
    },
    
    # Generation Events
    'generation_started': {
        'publisher': 'generation-orchestrator',
        'subscribers': ['notification-service', 'analytics-service'],
        'data': ['generation_id', 'user_id', 'prompt_id', 'start_timestamp']
    },
    'image_generation_started': {
        'publisher': 'generation-orchestrator',
        'subscribers': ['image-generation-service', 'analytics-service'],
        'data': ['generation_id', 'image_prompt', 'generation_params']
    },
    'image_generation_completed': {
        'publisher': 'image-generation-service',
        'subscribers': ['generation-orchestrator', 'storage-service', 'analytics-service'],
        'data': ['generation_id', 'image_urls', 'quality_scores', 'processing_time']
    },
    'video_generation_started': {
        'publisher': 'generation-orchestrator',
        'subscribers': ['video-generation-service', 'analytics-service'],
        'data': ['generation_id', 'video_prompt', 'image_urls', 'generation_params']
    },
    'video_generation_completed': {
        'publisher': 'video-generation-service',
        'subscribers': ['generation-orchestrator', 'post-processing-service', 'analytics-service'],
        'data': ['generation_id', 'video_url', 'thumbnail_url', 'duration', 'quality_score']
    },
    'generation_completed': {
        'publisher': 'generation-orchestrator',
        'subscribers': ['notification-service', 'analytics-service', 'user-service'],
        'data': ['generation_id', 'user_id', 'final_urls', 'total_processing_time', 'quality_scores']
    },
    
    # Media Management Events
    'file_stored': {
        'publisher': 'storage-service',
        'subscribers': ['analytics-service'],
        'data': ['file_id', 'file_url', 'file_type', 'file_size', 'storage_location']
    },
    'post_processing_started': {
        'publisher': 'post-processing-service',
        'subscribers': ['analytics-service'],
        'data': ['generation_id', 'input_file_url', 'processing_type']
    },
    'post_processing_completed': {
        'publisher': 'post-processing-service',
        'subscribers': ['quality-assurance-service', 'analytics-service'],
        'data': ['generation_id', 'processed_file_url', 'processing_applied', 'processing_time']
    },
    'quality_check_completed': {
        'publisher': 'quality-assurance-service',
        'subscribers': ['generation-orchestrator', 'analytics-service'],
        'data': ['generation_id', 'quality_score', 'quality_metrics', 'pass_fail_status']
    },
    
    # Voice Processing Events
    'voice_processing_started': {
        'publisher': 'voice-processing-orchestrator',
        'subscribers': ['analytics-service'],
        'data': ['voice_id', 'user_id', 'audio_file_url', 'start_timestamp']
    },
    'audio_preprocessed': {
        'publisher': 'audio-preprocessing-service',
        'subscribers': ['speech-recognition-service', 'voice-language-detection-service'],
        'data': ['voice_id', 'processed_audio_url', 'preprocessing_applied']
    },
    'speech_transcribed': {
        'publisher': 'speech-recognition-service',
        'subscribers': ['voice-processing-orchestrator', 'analytics-service'],
        'data': ['voice_id', 'transcribed_text', 'confidence_score', 'processing_time']
    },
    'voice_language_detected': {
        'publisher': 'voice-language-detection-service',
        'subscribers': ['voice-processing-orchestrator', 'analytics-service'],
        'data': ['voice_id', 'detected_language', 'confidence_score']
    },
    'voice_processing_completed': {
        'publisher': 'voice-processing-orchestrator',
        'subscribers': ['text-preprocessing-service', 'analytics-service'],
        'data': ['voice_id', 'final_text', 'language', 'confidence_score', 'total_processing_time']
    },
    
    # Communication Events
    'notification_sent': {
        'publisher': 'notification-service',
        'subscribers': ['analytics-service'],
        'data': ['user_id', 'notification_type', 'delivery_method', 'delivery_status']
    },
    'real_time_update_sent': {
        'publisher': 'real-time-service',
        'subscribers': ['analytics-service'],
        'data': ['user_id', 'update_type', 'update_data', 'delivery_status']
    }
}

# Event Bus Implementation
class EventBus:
    def __init__(self):
        self.rabbitmq = RabbitMQConnection()
        self.redis = RedisConnection()
        self.event_schema_validator = EventSchemaValidator()
    
    async def publish_event(self, event_type: str, data: dict, routing_key: str = None):
        """Publish event with validation and routing"""
        # Validate event schema
        if not self.event_schema_validator.validate(event_type, data):
            raise EventValidationError(f"Invalid event schema for {event_type}")
        
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4()),
            'version': '1.0'
        }
        
        # Publish to RabbitMQ for reliable delivery
        await self.rabbitmq.publish('events', event, routing_key or event_type)
        
        # Publish to Redis for real-time updates
        await self.redis.publish('events:realtime', event)
        
        # Log event for analytics
        await self._log_event(event)
    
    async def subscribe_to_events(self, service_name: str, event_types: list, callback: callable):
        """Subscribe to specific event types with error handling"""
        queue = await self.channel.declare_queue(
            f"{service_name}_queue_{uuid.uuid4()}",
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'dlx',
                'x-message-ttl': 300000,  # 5 minutes
                'x-max-retries': 3
            }
        )
        
        for event_type in event_types:
            await queue.bind(self.events_exchange, event_type)
        
        async def message_handler(message: aio_pika.IncomingMessage):
            try:
                async with message.process():
                    event = json.loads(message.body.decode())
                    await callback(event)
            except Exception as e:
                logger.error(f"Error processing event {event_type}: {e}")
                # Event will be sent to DLX after max retries
        
        await queue.consume(message_handler)

#### 3.1.3 Orchestrator Services Implementation

```python
# Scene Analysis Orchestrator
class SceneAnalysisOrchestrator:
    """Coordinates scene analysis workflow across multiple specialized services"""
    
    def __init__(self):
        self.entity_service = EntityExtractionService()
        self.mood_service = MoodAnalysisService()
        self.camera_service = CameraAnalysisService()
        self.temporal_service = TemporalAnalysisService()
        self.event_bus = EventBus()
        self.cache = RedisCache()
    
    async def analyze_scene(self, text: str, user_id: str) -> SceneAnalysisResult:
        """Orchestrate complete scene analysis workflow"""
        analysis_id = str(uuid.uuid4())
        
        try:
            # Check cache for similar analysis
            cache_key = f"scene_analysis:{hash(text)}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return self._use_cached_result(cached_result, analysis_id)
            
            # Start parallel analysis tasks
            tasks = [
                self.entity_service.extract_entities(text),
                self.mood_service.analyze_mood(text),
                self.camera_service.extract_camera_cues(text),
                self.temporal_service.analyze_temporal(text)
            ]
            
            # Wait for all analysis tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any failures
            analysis_result = self._process_analysis_results(results, text)
            
            # Cache the result
            await self.cache.set(cache_key, analysis_result, ttl=7200)
            
            # Publish completion event
            await self.event_bus.publish_event('scene_analysis_completed', {
                'analysis_id': analysis_id,
                'scene_data': analysis_result,
                'confidence_scores': self._calculate_confidence_scores(results),
                'processing_time': self._get_processing_time()
            })
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Scene analysis failed: {e}")
            await self.event_bus.publish_event('scene_analysis_failed', {
                'analysis_id': analysis_id,
                'error': str(e),
                'text_hash': hash(text)
            })
            raise SceneAnalysisError(f"Analysis failed: {e}")
    
    def _process_analysis_results(self, results: list, text: str) -> SceneAnalysisResult:
        """Process and combine analysis results from all services"""
        entities_result, mood_result, camera_result, temporal_result = results
        
        return SceneAnalysisResult(
            text=text,
            entities=self._extract_successful_result(entities_result),
            mood=self._extract_successful_result(mood_result),
            camera_cues=self._extract_successful_result(camera_result),
            temporal=self._extract_successful_result(temporal_result),
            overall_confidence=self._calculate_overall_confidence(results)
        )

# Generation Orchestrator
class GenerationOrchestrator:
    """Coordinates the complete video generation workflow"""
    
    def __init__(self):
        self.image_service = ImageGenerationService()
        self.video_service = VideoGenerationService()
        self.storage_service = StorageService()
        self.post_processing_service = PostProcessingService()
        self.quality_service = QualityAssuranceService()
        self.event_bus = EventBus()
        self.cache = RedisCache()
    
    async def generate_video(self, prompt_data: dict, user_id: str) -> GenerationResult:
        """Orchestrate complete video generation workflow"""
        generation_id = str(uuid.uuid4())
        
        try:
            # Publish generation started event
            await self.event_bus.publish_event('generation_started', {
                'generation_id': generation_id,
                'user_id': user_id,
                'prompt_id': prompt_data['prompt_id'],
                'start_timestamp': datetime.utcnow().isoformat()
            })
            
            # Phase 1: Image Generation
            image_result = await self._generate_images(prompt_data, generation_id)
            
            # Phase 2: Video Generation
            video_result = await self._generate_video_from_images(
                image_result, prompt_data, generation_id
            )
            
            # Phase 3: Post-Processing
            processed_result = await self._post_process_video(
                video_result, generation_id
            )
            
            # Phase 4: Quality Assurance
            quality_result = await self._quality_check(
                processed_result, generation_id
            )
            
            # Final result
            final_result = GenerationResult(
                generation_id=generation_id,
                user_id=user_id,
                images=image_result.image_urls,
                video_url=processed_result.video_url,
                thumbnail_url=processed_result.thumbnail_url,
                quality_score=quality_result.quality_score,
                processing_time=self._get_total_processing_time(),
                status='completed'
            )
            
            # Publish completion event
            await self.event_bus.publish_event('generation_completed', {
                'generation_id': generation_id,
                'user_id': user_id,
                'final_urls': {
                    'video': final_result.video_url,
                    'thumbnail': final_result.thumbnail_url,
                    'images': final_result.images
                },
                'total_processing_time': final_result.processing_time,
                'quality_scores': {
                    'overall': final_result.quality_score,
                    'images': image_result.quality_scores,
                    'video': quality_result.quality_score
                }
            })
            
            return final_result
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            await self.event_bus.publish_event('generation_failed', {
                'generation_id': generation_id,
                'user_id': user_id,
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            })
            raise GenerationError(f"Generation failed: {e}")
    
    async def _generate_images(self, prompt_data: dict, generation_id: str) -> ImageResult:
        """Generate images using specialized service"""
        await self.event_bus.publish_event('image_generation_started', {
            'generation_id': generation_id,
            'image_prompt': prompt_data['image_prompt'],
            'generation_params': prompt_data.get('image_params', {})
        })
        
        result = await self.image_service.generate_images(
            prompt_data['image_prompt'],
            num_images=prompt_data.get('num_images', 4)
        )
        
        await self.event_bus.publish_event('image_generation_completed', {
            'generation_id': generation_id,
            'image_urls': result.image_urls,
            'quality_scores': result.quality_scores,
            'processing_time': result.processing_time
        })
        
        return result

# Voice Processing Orchestrator
class VoiceProcessingOrchestrator:
    """Coordinates voice processing workflow"""
    
    def __init__(self):
        self.audio_preprocessing = AudioPreprocessingService()
        self.speech_recognition = SpeechRecognitionService()
        self.voice_language_detection = VoiceLanguageDetectionService()
        self.event_bus = EventBus()
        self.cache = RedisCache()
    
    async def process_voice_input(self, audio_data: bytes, user_id: str) -> VoiceProcessingResult:
        """Orchestrate complete voice processing workflow"""
        voice_id = str(uuid.uuid4())
        
        try:
            # Publish processing started event
            await self.event_bus.publish_event('voice_processing_started', {
                'voice_id': voice_id,
                'user_id': user_id,
                'audio_file_url': await self._store_temp_audio(audio_data),
                'start_timestamp': datetime.utcnow().isoformat()
            })
            
            # Phase 1: Audio Preprocessing
            processed_audio = await self.audio_preprocessing.preprocess_audio(audio_data)
            
            await self.event_bus.publish_event('audio_preprocessed', {
                'voice_id': voice_id,
                'processed_audio_url': processed_audio.url,
                'preprocessing_applied': processed_audio.applied_filters
            })
            
            # Phase 2: Parallel Processing
            tasks = [
                self.speech_recognition.transcribe_audio(processed_audio),
                self.voice_language_detection.detect_language(processed_audio)
            ]
            
            transcription_result, language_result = await asyncio.gather(*tasks)
            
            # Publish individual completion events
            await self.event_bus.publish_event('speech_transcribed', {
                'voice_id': voice_id,
                'transcribed_text': transcription_result.text,
                'confidence_score': transcription_result.confidence,
                'processing_time': transcription_result.processing_time
            })
            
            await self.event_bus.publish_event('voice_language_detected', {
                'voice_id': voice_id,
                'detected_language': language_result.language,
                'confidence_score': language_result.confidence
            })
            
            # Final result
            final_result = VoiceProcessingResult(
                voice_id=voice_id,
                user_id=user_id,
                transcribed_text=transcription_result.text,
                detected_language=language_result.language,
                confidence_score=min(transcription_result.confidence, language_result.confidence),
                processing_time=self._get_total_processing_time(),
                status='completed'
            )
            
            # Publish completion event
            await self.event_bus.publish_event('voice_processing_completed', {
                'voice_id': voice_id,
                'final_text': final_result.transcribed_text,
                'language': final_result.detected_language,
                'confidence_score': final_result.confidence_score,
                'total_processing_time': final_result.processing_time
            })
            
            return final_result
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            await self.event_bus.publish_event('voice_processing_failed', {
                'voice_id': voice_id,
                'user_id': user_id,
                'error': str(e)
            })
            raise VoiceProcessingError(f"Voice processing failed: {e}")
    
    async def register_service(self, service_name: str, port: int):
        """Register service with Consul"""
        await self.consul.agent.service.register({
            'name': service_name,
            'port': port,
            'check': {
                'http': f'http://localhost:{port}/health',
                'interval': '10s'
            }
        })
    
    async def discover_service(self, service_name: str):
        """Discover service instances"""
        services = await self.consul.health.service(service_name)
        return [service['Service'] for service in services]
```

### 3.2 API Gateway Architecture

#### 3.2.1 Gateway Configuration

```yaml
# Kong Gateway Configuration
services:
  - name: user-service
    url: http://user-service:8001
    routes:
      - name: user-routes
        paths: ["/api/users", "/api/auth"]
        methods: ["GET", "POST", "PUT", "DELETE"]
  
  - name: generation-service
    url: http://generation-service:8005
    routes:
      - name: generation-routes
        paths: ["/api/generate"]
        methods: ["POST"]
        plugins:
          - name: rate-limiting
            config:
              minute: 10
              hour: 100
  
  - name: voice-processing-service
    url: http://voice-processing-service:8008
    routes:
      - name: voice-routes
        paths: ["/api/voice"]
        methods: ["POST"]
        plugins:
          - name: rate-limiting
            config:
              minute: 5
              hour: 50

plugins:
  - name: jwt
    config:
      secret_is_base64: false
      key_claim_name: iss
      algorithm: HS256
  
  - name: cors
    config:
      origins: ["https://app.videogen.com", "https://admin.videogen.com"]
      methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      headers: ["Accept", "Authorization", "Content-Type"]
```

#### 3.2.2 Authentication & Authorization

```python
# JWT Authentication Service
class AuthenticationService:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET')
        self.redis = RedisConnection()
    
    async def authenticate_user(self, token: str) -> User:
        """Validate JWT token and return user"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Check if token is blacklisted
            if await self.redis.get(f"blacklist:{token}"):
                raise AuthenticationError("Token is blacklisted")
            
            # Get user from database
            user = await self.get_user_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found")
            
            return user
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    async def authorize_action(self, user: User, action: str, resource: str) -> bool:
        """Check if user is authorized to perform action on resource"""
        # Role-based access control
        if user.role == 'admin':
            return True
        
        # Resource-based permissions
        if action == 'generate' and user.tier in ['free', 'pro', 'enterprise']:
            return True
        
        if action == 'delete' and resource.startswith(f"user:{user.id}"):
            return True
        
        return False
```

## 4. Database Architecture

### 4.1 Database Design

#### 4.1.1 PostgreSQL Schema

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    tier VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generations Table
CREATE TABLE generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    input_text TEXT NOT NULL,
    language_detected VARCHAR(10),
    translation_result JSONB,
    entities_extracted JSONB,
    mood_analysis JSONB,
    camera_analysis JSONB,
    temporal_analysis JSONB,
    structured_prompt JSONB,
    status VARCHAR(20) DEFAULT 'processing',
    progress INTEGER DEFAULT 0,
    current_phase VARCHAR(50),
    output_urls JSONB,
    quality_scores JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- User Sessions Table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback Table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_id UUID REFERENCES generations(id),
    user_id UUID REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    satisfaction_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_status ON generations(status);
CREATE INDEX idx_generations_created_at ON generations(created_at);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_feedback_generation_id ON feedback(generation_id);
```

#### 4.1.2 Redis Cache Strategy

```python
# Cache Configuration
CACHE_CONFIG = {
    'user_sessions': {
        'ttl': 3600,  # 1 hour
        'prefix': 'session:'
    },
    'generation_results': {
        'ttl': 86400,  # 24 hours
        'prefix': 'generation:'
    },
    'translation_cache': {
        'ttl': 7200,  # 2 hours
        'prefix': 'translation:'
    },
    'entity_extraction': {
        'ttl': 14400,  # 4 hours
        'prefix': 'entities:'
    }
}

# Cache Service Implementation
class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='redis', port=6379, db=0)
        self.config = CACHE_CONFIG
    
    async def get(self, key: str, cache_type: str) -> Any:
        """Get value from cache"""
        full_key = f"{self.config[cache_type]['prefix']}{key}"
        value = await self.redis.get(full_key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, cache_type: str):
        """Set value in cache"""
        full_key = f"{self.config[cache_type]['prefix']}{key}"
        ttl = self.config[cache_type]['ttl']
        await self.redis.setex(full_key, ttl, json.dumps(value))
    
    async def invalidate(self, key: str, cache_type: str):
        """Invalidate cache entry"""
        full_key = f"{self.config[cache_type]['prefix']}{key}"
        await self.redis.delete(full_key)
```

### 4.2 Data Storage Architecture

#### 4.2.1 File Storage Strategy

```python
# AWS S3 Storage Configuration
STORAGE_CONFIG = {
    'buckets': {
        'user-uploads': 'videogen-user-uploads',
        'generated-content': 'videogen-generated-content',
        'thumbnails': 'videogen-thumbnails',
        'temp-files': 'videogen-temp-files'
    },
    'regions': {
        'primary': 'us-east-1',
        'secondary': 'eu-west-1'
    },
    'cdn': {
        'domain': 'cdn.videogen.com',
        'cache_ttl': 86400
    }
}

# Storage Service Implementation
class StorageService:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.config = STORAGE_CONFIG
    
    async def upload_file(self, file_path: str, bucket: str, key: str) -> str:
        """Upload file to S3"""
        try:
            self.s3.upload_file(file_path, bucket, key)
            return f"https://{bucket}.s3.amazonaws.com/{key}"
        except Exception as e:
            raise StorageError(f"Upload failed: {str(e)}")
    
    async def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file access"""
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
    
    async def delete_file(self, bucket: str, key: str):
        """Delete file from S3"""
        self.s3.delete_object(Bucket=bucket, Key=key)
```

#### 4.2.2 Voice Processing Service Implementation

```python
# Voice Processing Service
import whisper
import speech_recognition as sr
from pydub import AudioSegment
import io
import asyncio
from typing import Dict, Any

class VoiceProcessingService:
    def __init__(self):
        self.whisper_model = whisper.load_model("base")
        self.recognizer = sr.Recognizer()
        self.storage_service = StorageService()
        self.cache_service = CacheService()
    
    async def process_voice_input(self, audio_data: bytes, user_id: int) -> Dict[str, Any]:
        """Process voice input and return structured data"""
        try:
            # 1. Audio preprocessing
            processed_audio = await self.preprocess_audio(audio_data)
            
            # 2. Check cache for similar audio
            audio_hash = self.generate_audio_hash(audio_data)
            cached_result = await self.cache_service.get(audio_hash, 'voice_processing')
            if cached_result:
                return cached_result
            
            # 3. Speech recognition
            transcribed_text = await self.transcribe_audio(processed_audio)
            
            # 4. Language detection
            detected_language = await self.detect_language(processed_audio)
            
            # 5. Text validation
            validated_text = await self.validate_transcription(transcribed_text)
            
            # 6. Store result
            result = {
                "text": validated_text,
                "language": detected_language,
                "confidence": self.calculate_confidence(processed_audio),
                "processing_time": self.get_processing_time(),
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            await self.cache_service.set(audio_hash, result, 'voice_processing')
            
            return result
            
        except Exception as e:
            raise VoiceProcessingError(f"Voice processing failed: {e}")
    
    async def preprocess_audio(self, audio_data: bytes) -> AudioSegment:
        """Preprocess audio for optimal recognition"""
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        
        # Normalize audio levels
        audio = audio.normalize()
        
        # Remove silence
        audio = audio.strip_silence()
        
        # Convert to optimal format for Whisper
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        return audio
    
    async def transcribe_audio(self, audio: AudioSegment) -> str:
        """Transcribe audio to text using Whisper"""
        result = self.whisper_model.transcribe(audio.raw_data)
        return result["text"]
    
    async def detect_language(self, audio: AudioSegment) -> str:
        """Detect language from audio"""
        result = self.whisper_model.transcribe(audio.raw_data, language=None)
        return result["language"]
    
    async def validate_transcription(self, text: str) -> str:
        """Validate and clean transcribed text"""
        # Remove extra whitespace
        text = text.strip()
        
        # Check minimum length
        if len(text) < 10:
            raise ValidationError("Transcribed text too short")
        
        # Check for profanity or inappropriate content
        if self.contains_inappropriate_content(text):
            raise ValidationError("Inappropriate content detected")
        
        return text
    
    def calculate_confidence(self, audio: AudioSegment) -> float:
        """Calculate confidence score for transcription"""
        # Simple confidence calculation based on audio quality
        duration = len(audio) / 1000.0  # Convert to seconds
        volume = audio.dBFS
        
        # Higher confidence for longer, louder audio
        confidence = min(1.0, (duration * 0.1) + ((volume + 60) / 60))
        return round(confidence, 2)
    
    def generate_audio_hash(self, audio_data: bytes) -> str:
        """Generate hash for audio data for caching"""
        import hashlib
        return hashlib.md5(audio_data).hexdigest()
```

## 5. API Architecture

### 5.1 RESTful API Design

#### 5.1.1 API Endpoints Structure

```python
# API Routes Configuration
API_ROUTES = {
    'v1': {
        'auth': {
            'POST /auth/login': 'AuthenticationService.login',
            'POST /auth/register': 'AuthenticationService.register',
            'POST /auth/logout': 'AuthenticationService.logout',
            'POST /auth/refresh': 'AuthenticationService.refresh_token'
        },
        'users': {
            'GET /users/profile': 'UserService.get_profile',
            'PUT /users/profile': 'UserService.update_profile',
            'GET /users/generations': 'UserService.get_generations',
            'DELETE /users/account': 'UserService.delete_account'
        },
        'generations': {
            'POST /generations': 'GenerationService.create_generation',
            'GET /generations/{id}': 'GenerationService.get_generation',
            'GET /generations': 'GenerationService.list_generations',
            'DELETE /generations/{id}': 'GenerationService.delete_generation'
        },
        'media': {
            'GET /media/{id}/download': 'MediaService.download_media',
            'GET /media/{id}/stream': 'MediaService.stream_media',
            'POST /media/upload': 'MediaService.upload_media'
        },
        'voice': {
            'POST /voice/process': 'VoiceProcessingService.process_voice',
            'POST /voice/upload': 'VoiceProcessingService.upload_audio',
            'GET /voice/status/{id}': 'VoiceProcessingService.get_status',
            'POST /voice/generate': 'VoiceProcessingService.generate_from_voice'
        }
    }
}
```

#### 5.1.2 API Response Standards

```python
# Standard API Response Format
class APIResponse:
    def __init__(self, data: Any = None, message: str = "", status: str = "success"):
        self.data = data
        self.message = message
        self.status = status
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'data': self.data,
            'message': self.message,
            'status': self.status,
            'timestamp': self.timestamp
        }

# Error Response Format
class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)
    
    def to_response(self) -> dict:
        return {
            'error': {
                'message': self.message,
                'code': self.error_code,
                'status_code': self.status_code
            },
            'timestamp': datetime.utcnow().isoformat()
        }
```

### 5.2 Real-time Communication

#### 5.2.1 WebSocket Implementation

```python
# Socket.IO Server Configuration
class SocketIOServer:
    def __init__(self):
        self.app = FastAPI()
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.redis = RedisConnection()
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.socketio.on('connect')
        async def on_connect(sid, environ):
            user_id = self.get_user_from_token(environ.get('HTTP_AUTHORIZATION'))
            if user_id:
                await self.socketio.enter_room(sid, f"user:{user_id}")
                await self.socketio.emit('connected', {'status': 'success'}, room=sid)
            else:
                await self.socketio.disconnect(sid)
        
        @self.socketio.on('disconnect')
        async def on_disconnect(sid):
            await self.socketio.leave_room(sid, f"user:{user_id}")
        
        @self.socketio.on('subscribe_generation')
        async def on_subscribe_generation(sid, data):
            generation_id = data['generation_id']
            await self.socketio.enter_room(sid, f"generation:{generation_id}")
    
    async def broadcast_generation_update(self, generation_id: str, update: dict):
        """Broadcast generation update to subscribed clients"""
        await self.socketio.emit('generation_update', update, room=f"generation:{generation_id}")
    
    async def broadcast_user_notification(self, user_id: str, notification: dict):
        """Send notification to specific user"""
        await self.socketio.emit('notification', notification, room=f"user:{user_id}")
```

## 6. Security Architecture

### 6.1 Security Layers

#### 6.1.1 Authentication & Authorization

```python
# Multi-layer Security Implementation
class SecurityManager:
    def __init__(self):
        self.jwt_manager = JWTManager()
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        self.encryption = EncryptionService()
    
    async def validate_request(self, request: Request) -> SecurityContext:
        """Validate incoming request"""
        # Rate limiting
        await self.rate_limiter.check_rate_limit(request.client.host)
        
        # Input validation
        await self.input_validator.validate_input(request.json())
        
        # Authentication
        token = self.extract_token(request.headers.get('Authorization'))
        user = await self.jwt_manager.validate_token(token)
        
        # Authorization
        await self.check_permissions(user, request.path, request.method)
        
        return SecurityContext(user=user, request=request)
    
    async def encrypt_sensitive_data(self, data: dict) -> dict:
        """Encrypt sensitive data before storage"""
        encrypted_data = {}
        for key, value in data.items():
            if key in SENSITIVE_FIELDS:
                encrypted_data[key] = await self.encryption.encrypt(str(value))
            else:
                encrypted_data[key] = value
        return encrypted_data
```

#### 6.1.2 Data Protection

```python
# Data Encryption Service
class EncryptionService:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(self.key)
    
    async def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    async def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    async def hash_password(self, password: str) -> str:
        """Hash user password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
    
    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verify user password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

## 7. Monitoring & Observability

### 7.1 Application Monitoring

#### 7.1.1 Metrics Collection

```python
# Prometheus Metrics Configuration
class MetricsCollector:
    def __init__(self):
        self.prometheus = PrometheusClient()
        self.setup_metrics()
    
    def setup_metrics(self):
        # Request metrics
        self.request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
        self.request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
        
        # Generation metrics
        self.generation_count = Counter('generations_total', 'Total generations', ['status', 'user_tier'])
        self.generation_duration = Histogram('generation_duration_seconds', 'Generation duration', ['phase'])
        
        # System metrics
        self.active_users = Gauge('active_users_total', 'Active users')
        self.queue_size = Gauge('queue_size_total', 'Queue size')
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_generation(self, status: str, user_tier: str, duration: float, phase: str):
        """Record generation metrics"""
        self.generation_count.labels(status=status, user_tier=user_tier).inc()
        self.generation_duration.labels(phase=phase).observe(duration)
```

#### 7.1.2 Logging Strategy

```python
# Structured Logging Configuration
class LoggingService:
    def __init__(self):
        self.logger = logging.getLogger('videogen')
        self.setup_logging()
    
    def setup_logging(self):
        # JSON formatter for structured logs
        formatter = JsonFormatter()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # File handler
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_request(self, request_id: str, method: str, endpoint: str, user_id: str, duration: float):
        """Log HTTP request"""
        self.logger.info({
            'event': 'http_request',
            'request_id': request_id,
            'method': method,
            'endpoint': endpoint,
            'user_id': user_id,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def log_generation(self, generation_id: str, user_id: str, phase: str, status: str):
        """Log generation event"""
        self.logger.info({
            'event': 'generation',
            'generation_id': generation_id,
            'user_id': user_id,
            'phase': phase,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        })
```

## 8. Deployment Architecture

### 8.1 Container Orchestration

#### 8.1.1 Kubernetes Deployment

```yaml
# Kubernetes Deployment Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: videogen-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: videogen-api
  template:
    metadata:
      labels:
        app: videogen-api
    spec:
      containers:
      - name: api
        image: videogen/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: videogen-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: videogen-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: videogen-api-service
spec:
  selector:
    app: videogen-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 8.1.2 Infrastructure as Code

```terraform
# Terraform Configuration
resource "aws_eks_cluster" "videogen" {
  name     = "videogen-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = [
      aws_subnet.private_1.id,
      aws_subnet.private_2.id,
      aws_subnet.private_3.id
    ]
    endpoint_private_access = true
    endpoint_public_access  = true
  }
}

resource "aws_rds_cluster" "postgresql" {
  cluster_identifier      = "videogen-postgresql"
  engine                 = "aurora-postgresql"
  engine_version         = "13.7"
  database_name          = "videogen"
  master_username        = "videogen"
  master_password        = var.database_password
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  preferred_maintenance_window = "sun:05:00-sun:06:00"
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.videogen.name
  skip_final_snapshot    = true
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "videogen-redis"
  description                = "Redis cluster for Videogen"
  node_type                 = "cache.t3.micro"
  port                      = 6379
  parameter_group_name      = "default.redis7"
  num_cache_clusters        = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  subnet_group_name         = aws_elasticache_subnet_group.videogen.name
  security_group_ids        = [aws_security_group.redis.id]
}
```

This comprehensive system architecture provides the technical foundation for implementing the video generation platform. The architecture is designed to be scalable, maintainable, and secure while supporting the complex workflow requirements we defined earlier.

Would you like me to proceed with the next task in our todo list, or would you like me to elaborate on any specific aspect of this system architecture?
