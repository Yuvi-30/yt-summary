# 🎥 AI YouTube Summary Generator

A powerful web application that converts YouTube videos into comprehensive, AI-generated blog articles using advanced transcription and natural language processing.

## ✨ Features

### Core Functionality
- **Smart Transcription**: Dual-method approach for maximum reliability
  - **Fast Method**: Uses YouTube's built-in captions
  - **Fallback Method**: Downloads audio + AssemblyAI transcription for videos without captions
- **AI Blog Generation**: Powered by Google Gemini AI for high-quality content creation
- **User Authentication**: Secure login/signup system
- **Blog Management**: Save, view, and manage generated blogs
- **Responsive Design**: Modern cyber-themed UI with animations

### Technical Highlights
- **Django REST API**: Full REST API endpoints for future mobile integration
- **PostgreSQL Database**: Supabase-powered cloud database
- **Smart Error Handling**: Graceful fallbacks and user-friendly error messages
- **Optimized Performance**: Intelligent caching and processing strategies


## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.x
- **API**: Django REST Framework (appended endpoints for future use)
- **Database**: PostgreSQL (Supabase)
- **Authentication**: Django built-in auth system

### Frontend
- **HTML5 + CSS3**: Modern responsive design
- **JavaScript**: Vanilla JS with async/await
- **UI Theme**: Cyberpunk-inspired design with particles.js

### AI & External APIs
- **Google Gemini AI**: Blog content generation
- **AssemblyAI**: Advanced audio transcription
- **YouTube Transcript API**: Fast caption extraction
- **yt-dlp**: YouTube audio download

### Deployment
- **Database**: Supabase PostgreSQL and SQLlite
- **Environment**: Production-ready with environment variables

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git

## 🔧 Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-blog-generator.git
cd ai-blog-generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:password@host:5432/postgres

# Django Configuration
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

## 🔑 API Keys Setup

### Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/)
2. Create new API key
3. Add to `.env` as `GEMINI_API_KEY`

### AssemblyAI
1. Sign up at [AssemblyAI](https://www.assemblyai.com/)
2. Get free API key (3 hours/month free tier)
3. Add to `.env` as `ASSEMBLYAI_API_KEY`

### Supabase Database
1. Create account at [Supabase](https://supabase.com/)
2. Create new project
3. Get connection string from Settings > Database
4. Add to `.env` as `DATABASE_URL`

## 📚 API Documentation

The application includes a complete REST API for future mobile app integration:

### Authentication Required
All API endpoints require user authentication via session authentication.

### Endpoints

#### Generate Blog
```http
POST /api/generate-blog/
Content-Type: application/json

{
    "link": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
    "success": true,
    "content": "Generated blog content...",
    "method": "fast_captions",
    "blog_id": 123,
    "metadata": {
        "title": "Video Title",
        "channel": "Channel Name",
        "duration": "10m 30s",
        "word_count": 1500
    }
}
```

#### List User Blogs
```http
GET /api/blogs/
```

#### Get Blog Details
```http
GET /api/blogs/{id}/
```

#### Delete Blog
```http
DELETE /api/blogs/{id}/delete/
```

### API Features (Ready for Future Use)
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Responses**: Consistent data format
- **Error Handling**: Detailed error messages
- **Authentication**: Session-based authentication
- **Serialization**: Django REST Framework serializers
- **Permissions**: User-scoped data access

*Note: REST API endpoints are implemented but currently used for future mobile app development. The web application uses traditional Django views.*

## 🏗️ Architecture

### Smart Processing Flow
```
YouTube URL Input
    ↓
1. Try YouTube Captions (Fast)
    ↓ (if fails)
2. Download Audio + AssemblyAI (Slow - 30-60 seconds)
    ↓
3. Generate Blog with Gemini AI
    ↓
4. Save to Database
```

## 🚨 Known Issues & Solutions

### Database Connection Issues
**Problem**: Empty database or connection failures
**Cause**: University WiFi DNS restrictions blocking external database connections
**Solutions**:
1. Switch to personal WiFi/mobile hotspot
2. For development: Use local SQLite database

## 🔮 Future Enhancements

### Planned Features
- **Flutter Mobile App**: Using existing REST API endpoints
- **Blog Editing**: In-app content editing capabilities
- **Export Options**: PDF, Word, and Markdown export
- **Blog Categories**: Organize blogs by topics
- **Social Sharing**: Direct social media integration
- **Batch Processing**: Multiple video processing
- **Advanced Analytics**: View counts, reading time


## 📊 Project Stats

- **Lines of Code**: ~2,000+
- **API Endpoints**: 4 REST endpoints
- **Processing Methods**: 2 (fast + fallback)
- **Average Generation Time**: 60 - 90 seconds
- **Supported Video Length**: Up to 2 hours
- **Blog Length**: 500-1000 words

---

⭐ **Star this repository if it helped you create amazing blog content from YouTube videos!**
