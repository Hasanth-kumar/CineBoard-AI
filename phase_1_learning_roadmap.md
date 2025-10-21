# Phase 1 MVP Learning Roadmap

## 🎯 Phase 1 Overview (Months 1-3)

**What we're building**: Basic video generation platform with core functionality
**Team size**: 9 people
**Your goal**: Be able to contribute meaningfully to MVP development

## 🔄 CURRENT STATUS: PHASE 1 MVP IN PROGRESS + SRP REFACTOR (September 2025 Project Start)
- **MVP Status**: 🔄 IN PROGRESS with Single Responsibility Principle refactoring for input-processing-service
- **Project Timeline**: Started September 2025, Target Completion Q1 2026
- **Input Processing Service**: 🔄 Being properly implemented with SRP-compliant architecture
- **Database Schema**: 🔄 Planned schema with proper Unicode support
- **Language Detection**: 🔄 Planned for Telugu, Hindi, and English with proper Unicode handling
- **Translation Pipeline**: 🔄 Planned Google Translate API → NLLB-200 fallback system
- **API Endpoints**: 🔄 Planned input-processing endpoints with proper error handling
- **Critical Issues**: 🔄 Unicode character handling, Redis compatibility, PowerShell encoding planned for resolution
- **Docker Infrastructure**: 🔄 Planned containerization with PostgreSQL and Redis
- **Production Readiness**: 🔄 Planned for Phase 2 development and production deployment

## ⚠️ PHASE 2 GENAI WORKFLOW - PLANNED (Q2-Q3 2026)
- **Current Focus**: Complete Phase 1 MVP Foundation first
- **Next Priority**: Character Generation Service with Whisk AI integration (after MVP completion)
- **Workflow Discovery**: Manual workflow validated (Characters → Keyframes → Video Clips → Voiceover → Final Video)
- **Architecture**: SRP-compliant microservices ready for new services
- **Database**: Extended schema planned for GenAI workflow tables

## 📚 Essential Learning Path (Priority Order) 🔄 MVP IN PROGRESS + SRP REFACTOR

### 1. 🏗️ **System Design Fundamentals** 🔄 **IN PROGRESS**
**Why**: You need to understand how all pieces fit together
**🎉 STATUS**: In progress with SRP-compliant architecture for input-processing-service

#### What to Learn:
```json
{
  "client_server_architecture": {
    "concept": "How frontend talks to backend",
    "practical": "HTTP requests, REST APIs, JSON data exchange",
    "time_needed": "3-5 days"
  },
  "database_basics": {
    "concept": "How data is stored and retrieved",
    "practical": "SQL queries, table relationships, CRUD operations",
    "time_needed": "5-7 days"
  },
  "api_design": {
    "concept": "How to design endpoints for communication",
    "practical": "RESTful APIs, HTTP methods, status codes",
    "time_needed": "3-4 days"
  }
}
```

#### Learning Resources:
- **YouTube**: "System Design Interview" by Tech Dummies
- **Course**: "System Design Primer" on GitHub
- **Practice**: Design a simple blog system (users, posts, comments)

### 2. 🐍 **Python Programming** (Week 2-4)
**Why**: Our backend is built with Python/FastAPI

#### What to Learn:
```python
# Essential Python concepts for our project
# 1. Basic syntax and data structures
user_data = {
    "name": "John",
    "email": "john@example.com",
    "generations": []
}

# 2. Functions and classes
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.generations = []
    
    def add_generation(self, generation):
        self.generations.append(generation)

# 3. Working with APIs and JSON
import requests
import json

def call_ai_service(prompt):
    response = requests.post("https://api.nanobanana.com/generate", 
                           json={"prompt": prompt})
    return response.json()

# 4. Error handling
try:
    result = call_ai_service(user_input)
except requests.exceptions.RequestException as e:
    print(f"API call failed: {e}")
```

#### Learning Resources:
- **Course**: "Python for Everybody" (Coursera) - Free
- **Book**: "Automate the Boring Stuff with Python" - Free online
- **Practice**: Build a simple API client

### 3. ⚡ **FastAPI Framework** (Week 4-5)
**Why**: This is our backend framework

#### What to Learn:
```python
# FastAPI basics for our project
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# 1. Basic API structure
@app.get("/")
def read_root():
    return {"message": "Video Generation API"}

# 2. Data models (Pydantic)
class GenerationRequest(BaseModel):
    text: str
    language: str = "en"
    quality: str = "standard"

class GenerationResponse(BaseModel):
    id: str
    status: str
    video_url: str = None

# 3. API endpoints
@app.post("/api/generate", response_model=GenerationResponse)
async def create_generation(request: GenerationRequest):
    # Process the request
    generation_id = generate_unique_id()
    
    # Start generation process
    await start_generation_process(generation_id, request.text)
    
    return GenerationResponse(
        id=generation_id,
        status="processing"
    )

# 4. Error handling
@app.get("/api/generation/{generation_id}")
async def get_generation(generation_id: str):
    generation = await get_generation_by_id(generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation
```

#### Learning Resources:
- **Official Docs**: FastAPI.tiangolo.com - Excellent documentation
- **Tutorial**: "FastAPI Tutorial" by freeCodeCamp on YouTube
- **Practice**: Build a simple todo API

### 4. 🗄️ **Database with SQLAlchemy** (Week 5-6)
**Why**: We use PostgreSQL with SQLAlchemy ORM

#### What to Learn:
```python
# SQLAlchemy for our database models
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# 1. User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to generations
    generations = relationship("Generation", back_populates="user")

# 2. Generation model
class Generation(Base):
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_text = Column(Text)
    status = Column(String(50), default="processing")
    video_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="generations")

# 3. Database operations
from sqlalchemy.orm import Session

def create_user(db: Session, email: str, password_hash: str):
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()
```

#### Learning Resources:
- **Course**: "SQLAlchemy Tutorial" on Real Python
- **Practice**: Build a simple blog with user posts

### 5. ⚛️ **React.js Fundamentals** (Week 6-8)
**Why**: Our frontend is built with React/Next.js

#### What to Learn:
```javascript
// React basics for our frontend
import React, { useState, useEffect } from 'react';

// 1. Component structure
function GenerationForm() {
    const [inputText, setInputText] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState(null);

    // 2. Event handling
    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsGenerating(true);
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: inputText })
            });
            
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Generation failed:', error);
        } finally {
            setIsGenerating(false);
        }
    };

    // 3. Conditional rendering
    return (
        <div>
            <form onSubmit={handleSubmit}>
                <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Describe your video scene..."
                />
                <button type="submit" disabled={isGenerating}>
                    {isGenerating ? 'Generating...' : 'Generate Video'}
                </button>
            </form>
            
            {result && (
                <div>
                    <h3>Generation Status: {result.status}</h3>
                    {result.video_url && (
                        <video src={result.video_url} controls />
                    )}
                </div>
            )}
        </div>
    );
}

export default GenerationForm;
```

#### Learning Resources:
- **Course**: "React Tutorial" on React.js official website
- **Course**: "React for Beginners" by freeCodeCamp
- **Practice**: Build a simple todo app with React

### 6. 🎨 **Next.js Framework** (Week 8-9)
**Why**: We use Next.js for our frontend framework

#### What to Learn:
```javascript
// Next.js structure for our project
// pages/index.js - Homepage
import Head from 'next/head';
import GenerationForm from '../components/GenerationForm';

export default function Home() {
    return (
        <div>
            <Head>
                <title>Video Generation Platform</title>
            </Head>
            
            <main>
                <h1>Create AI Videos from Text</h1>
                <GenerationForm />
            </main>
        </div>
    );
}

// pages/api/generate.js - API route
export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method not allowed' });
    }
    
    const { text } = req.body;
    
    try {
        // Call backend API
        const response = await fetch('http://backend:8000/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        res.status(500).json({ message: 'Generation failed' });
    }
}

// components/GenerationForm.js - Reusable component
import { useState } from 'react';

export default function GenerationForm() {
    // Component logic here
}
```

#### Learning Resources:
- **Official Docs**: Nextjs.org - Excellent documentation
- **Tutorial**: "Next.js Tutorial" by Net Ninja on YouTube
- **Practice**: Build a simple blog with Next.js

### 7. 🔐 **Authentication Basics** (Week 9-10)
**Why**: Users need to register and login

#### What to Learn:
```python
# JWT Authentication for our backend
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# 1. Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 2. JWT token creation
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 3. Token verification
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### Learning Resources:
- **Tutorial**: "JWT Authentication" by freeCodeCamp
- **Practice**: Add authentication to your todo app

### 8. 🤖 **AI Service Integration** (Week 10-11)
**Why**: We need to integrate with AI services for video generation

#### What to Learn:
```python
# AI service integration for our project
import requests
import asyncio
from typing import Optional

class AIServiceClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nanobanana.com/v1"
    
    async def generate_images(self, prompt: str, num_images: int = 4):
        """Generate images using Nano Banana API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'prompt': prompt,
            'num_images': num_images,
            'quality': 'high'
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/images/generate',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"AI service error: {e}")
    
    async def generate_video(self, images: list, prompt: str):
        """Generate video using Veo4 API"""
        # Similar implementation for video generation
        pass

# Usage in our application
async def process_generation_request(text: str, user_id: int):
    # 1. Analyze the text
    analyzed_text = await analyze_scene_text(text)
    
    # 2. Generate images
    ai_client = AIServiceClient(api_key="your-api-key")
    images = await ai_client.generate_images(analyzed_text)
    
    # 3. Generate video
    video = await ai_client.generate_video(images, analyzed_text)
    
    # 4. Store result
    await store_generation_result(user_id, video)
    
    return video
```

#### Learning Resources:
- **Documentation**: Nano Banana API docs, Veo4 API docs
- **Practice**: Build a simple image generator

### 9. 🎤 **Voice Input Processing** (Week 11-12)
**Why**: Phase 2 will include voice input capabilities for enhanced user experience

#### What to Learn:
```python
# Voice input processing for Phase 2
import speech_recognition as sr
import whisper
from pydub import AudioSegment
import io

class VoiceInputProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.whisper_model = whisper.load_model("base")
    
    async def process_voice_input(self, audio_file: bytes) -> str:
        """Convert voice input to text"""
        try:
            # Convert audio to format suitable for processing
            audio = AudioSegment.from_file(io.BytesIO(audio_file))
            
            # Use Whisper for high-quality transcription
            result = self.whisper_model.transcribe(audio.raw_data)
            
            return result["text"]
        except Exception as e:
            raise Exception(f"Voice processing error: {e}")
    
    async def detect_language_from_voice(self, audio_file: bytes) -> str:
        """Detect language from voice input"""
        # Implementation for language detection
        pass
    
    async def validate_voice_input(self, text: str) -> bool:
        """Validate transcribed text"""
        # Check for minimum length, content quality, etc.
        return len(text.strip()) >= 10

# Integration with existing text processing
async def process_voice_generation_request(audio_file: bytes, user_id: int):
    # 1. Convert voice to text
    voice_processor = VoiceInputProcessor()
    text = await voice_processor.process_voice_input(audio_file)
    
    # 2. Continue with existing text processing pipeline
    analyzed_text = await analyze_scene_text(text)
    
    # 3. Generate content
    ai_client = AIServiceClient(api_key="your-api-key")
    images = await ai_client.generate_images(analyzed_text)
    video = await ai_client.generate_video(images, analyzed_text)
    
    return video
```

#### Learning Resources:
- **Library**: SpeechRecognition, Whisper, PyDub
- **Tutorial**: "Speech Recognition with Python" by Real Python
- **Practice**: Build a simple voice-to-text converter

### 10. 🐳 **Docker Basics** (Week 12-13)
**Why**: We use Docker for deployment and development

#### What to Learn:
```dockerfile
# Dockerfile for our backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml for development
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/videogen
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=videogen
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Learning Resources:
- **Course**: "Docker Tutorial" by freeCodeCamp
- **Practice**: Dockerize your todo app

## 🎯 Phase 1 Specific Skills

### Core MVP Features You'll Work On:

#### 1. **User Authentication System**
```python
# What you'll build
- User registration endpoint
- User login endpoint  
- Password hashing and verification
- JWT token management
- Protected routes
```

#### 2. **Text Processing Pipeline**
```python
# What you'll build
- Language detection service
- Translation service (if needed)
- Text preprocessing
- Scene analysis extraction
```

#### 3. **AI Generation Integration**
```python
# What you'll build
- Nano Banana API integration
- Veo4 API integration
- Generation queue management
- Progress tracking
- Error handling and retries
```

#### 4. **Frontend Interface**
```javascript
// What you'll build
- User registration/login forms
- Text input interface
- Progress tracking UI
- Video player component
- User dashboard
```

#### 5. **Database Operations**
```python
// What you'll build
- User data models
- Generation data models
- Database migrations
- CRUD operations
- Data relationships
```

#### 6. **Voice Input Processing** (Phase 2 Preparation)
```python
# What you'll prepare for Phase 2
- Voice-to-text conversion
- Audio file processing
- Language detection from voice
- Voice input validation
- Integration with text processing pipeline
```

## 📅 12-Week Learning Schedule

### **Weeks 1-2: Foundation**
- System design concepts
- HTTP and REST APIs
- Basic Python programming

### **Weeks 3-4: Backend Development**
- Advanced Python
- FastAPI framework
- API design and development

### **Weeks 5-6: Database**
- SQL basics
- SQLAlchemy ORM
- Database design

### **Weeks 7-8: Frontend Development**
- JavaScript fundamentals
- React.js basics
- Component development

### **Weeks 9-10: Integration**
- Next.js framework
- Authentication systems
- Frontend-backend communication

### **Weeks 11-12: AI Integration & Voice Prep**
- AI service integration
- Voice input processing basics
- Testing and debugging

### **Weeks 13-14: Deployment & Phase 2 Prep**
- Docker containerization
- Phase 2 feature planning
- Voice input architecture design

## 🛠️ Practical Projects to Build

### **Project 1: Simple Blog API** (Week 4)
```python
# Build a REST API with FastAPI
- User registration/login
- Create/read/update/delete posts
- User authentication
- Database integration
```

### **Project 2: Todo App Frontend** (Week 8)
```javascript
// Build a React frontend
- User authentication
- Todo CRUD operations
- API integration
- State management
```

### **Project 3: Full-Stack Video Generator** (Week 12)
```python
// Build a mini version of our platform
- User authentication
- Text input processing
- AI service integration (mock)
- Video display
- Database storage
```

## 📚 Recommended Learning Resources

### **Free Resources:**
1. **Python**: "Python for Everybody" (Coursera)
2. **FastAPI**: Official FastAPI documentation
3. **React**: React.js official tutorial
4. **Next.js**: Next.js official documentation
5. **Docker**: Docker official tutorial
6. **SQL**: SQLBolt (interactive SQL tutorial)

### **Paid Resources (Optional):**
1. **System Design**: "Grokking the System Design Interview"
2. **Python**: "Python Crash Course" book
3. **React**: "React - The Complete Guide" (Udemy)
4. **Full-Stack**: "The Web Developer Bootcamp" (Udemy)

### **Practice Platforms:**
1. **LeetCode**: For algorithm practice
2. **HackerRank**: For Python practice
3. **CodePen**: For frontend experimentation
4. **GitHub**: For version control practice

## 🎯 Success Metrics for Phase 1

### **Technical Skills:**
- [ ] Can build a REST API with FastAPI
- [ ] Can create React components
- [ ] Can design database schemas
- [ ] Can integrate external APIs
- [ ] Can implement authentication
- [ ] Can deploy applications with Docker

### **Project Contributions:**
- [ ] Can implement user authentication
- [ ] Can build text processing services
- [ ] Can integrate AI generation APIs
- [ ] Can create frontend interfaces
- [ ] Can write database operations
- [ ] Can debug and test code

## 🚀 Getting Started Today

### **Week 1 Action Plan:**
1. **Day 1-2**: Learn system design basics
2. **Day 3-4**: Start Python programming
3. **Day 5-7**: Build a simple Python script

### **Daily Learning Routine:**
- **Morning (1 hour)**: Theory and concepts
- **Afternoon (1 hour)**: Hands-on coding
- **Evening (30 minutes)**: Review and practice

### **Weekly Goals:**
- Complete one major concept per week
- Build one small project per week
- Review and practice previous concepts

## 💡 Pro Tips for Success

### **Learning Strategy:**
1. **Learn by doing**: Always code while learning
2. **Build projects**: Apply concepts immediately
3. **Ask questions**: Join developer communities
4. **Practice daily**: Consistency is key
5. **Review regularly**: Reinforce learning

### **Common Pitfalls to Avoid:**
1. **Skipping basics**: Don't rush to advanced topics
2. **Not practicing**: Reading isn't enough
3. **Isolating concepts**: Learn how pieces fit together
4. **Perfectionism**: Build, then improve
5. **Comparison**: Focus on your own progress

---

## 🎉 Ready to Start?

This roadmap will get you ready to contribute to Phase 1 MVP development in 12 weeks. The key is to **start today** and **practice consistently**. 

**Your first step**: Begin with system design basics and Python programming. Set aside 2-3 hours daily for learning and coding.

**Remember**: You don't need to master everything perfectly. Focus on understanding the concepts and being able to build basic functionality. You'll learn more advanced techniques as you work on the actual project.

Good luck with your learning journey! 🚀
