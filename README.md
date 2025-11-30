# Plan IQ - Supply Chain Intelligence Platform

Enterprise-grade, AI-powered supply chain intelligence platform with multi-agent GenAI system.

## 🏗️ Architecture

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS (PWC Theme)
- **Backend**: FastAPI + Python 3.11+
- **AI**: Azure OpenAI (GPT-4) + Multi-Agent System
- **Databases**: PostgreSQL + Neo4j + Azure AI Search
- **RAG Pipeline**: Azure Embeddings + Vector Search

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 📋 Environment Variables

See `backend/.env.example` for required configuration.

## 🧪 API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🏢 Production Deployment

1. Set `DEBUG=False` and `ENVIRONMENT=production`
2. Use strong `SECRET_KEY`
3. Enable HTTPS
4. Configure reverse proxy (Nginx/Traefik)
5. Set up monitoring (Prometheus/Grafana)

## 📊 Features

- ✅ Multi-agent AI system (5 specialized agents)
- ✅ RAG pipeline with Azure AI Search
- ✅ Knowledge graph (Neo4j)
- ✅ Real-time chat interface
- ✅ Analytics dashboard
- ✅ Weather impact analysis
- ✅ Demand forecasting
- ✅ PWC-themed UI

## 🔒 Security

- JWT authentication
- bcrypt password hashing
- CORS protection
- Rate limiting ready
- Input validation

## 📄 License

Proprietary - Enterprise License
