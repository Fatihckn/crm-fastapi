# CRM Backend API

FastAPI-based REST API with authentication, AI summarization, and Docker support.

## 🚀 Quick Start

### Run with Docker (Recommended)

```bash
# Start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

API: `http://localhost:8000`  
Documentation: `http://localhost:8000/docs`

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create database
python migrate.py

# Start application
uvicorn main:app --reload
```

## 📋 API Endpoints

### Authentication
- `POST /users/register` - User registration
- `POST /users/login` - User login
- `GET /users/me` - Profile information

### Notes
- `POST /notes` - Create note (queues AI summarization)
- `GET /notes` - List notes
- `GET /notes/{id}` - Get note details
- `GET /notes/{id}/status` - Check note status

## 🔐 Roles

- **ADMIN**: Can see all notes
- **AGENT**: Can only see their own notes

## 🐳 Docker Services

- **app**: FastAPI application (Port 8000)
- **mysql**: Database (Port 3306)
- **redis**: Celery broker (Port 6379)
- **celery**: Background worker

## ⚙️ Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://crm_user:crm_password@localhost:3306/crm_db

# MySQL Database Credentials (for Docker Compose)
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=crm_db
MYSQL_USER=crm_user
MYSQL_PASSWORD=crm_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## 🧪 Testing

```bash
# API test file
test_main.http
```

## 📦 Features

- ✅ JWT authentication
- ✅ Role-based access control
- ✅ AI-powered note summarization
- ✅ Asynchronous background processing
- ✅ Docker support
- ✅ Swagger documentation
- ✅ Database migrations
