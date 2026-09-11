# Architecture Quick Reference

## 🚀 Quick Start

```bash
# 1. Copy environment template
cp env.example .env

# 2. Edit .env with your keys
# - EMBEDDING__API_KEY (OpenAI/Cohere key)
# - STARGATE_API_KEY (Stargate LLM key)
# - STARGATE_BASE_URL (Stargate endpoint)

# 3. Start all services
docker-compose up -d

# 4. Access UI
# http://localhost:8501
```

## 📊 Component Ports

| Service | Port | URL |
|---------|------|-----|
| Streamlit UI | 8501 | http://localhost:8501 |
| FastAPI Backend | 8000 | http://localhost:8000 |
| LiteLLM Proxy | 4000 | http://localhost:4000 |
| Postgres + PGVector | 5432 | localhost:5432 |

## 🔑 Required Environment Variables

### Minimum Required
```env
EMBEDDING__API_KEY=sk-your-openai-key
STARGATE_API_KEY=your-stargate-key
STARGATE_BASE_URL=https://your-stargate-host/api
```

### Full Configuration
See `env.example` for complete list.

## 🔄 Data Flow Summary

1. **Ingest**: UI → API → LiteLLM → Embeddings → PGVector
2. **Search**: UI → API → LiteLLM → PGVector → Results
3. **RAG**: UI → Search → Build Context → Stargate LLM → Answer

## 📁 Key Files

- `ARCHITECTURE.md` - Full architecture documentation
- `docker-compose.yml` - Service orchestration
- `main.py` - FastAPI backend
- `ui.py` - Streamlit UI
- `env.example` - Environment template

## 🐛 Troubleshooting

### Services won't start
```bash
docker-compose logs -f [service-name]
```

### Database connection issues
```bash
docker-compose exec db psql -U postgres -d vectordb
```

### Check health
```bash
curl http://localhost:8000/health
curl http://localhost:4000/health
```

## 📚 API Endpoints

### Vector Stores
- `POST /v1/vector_stores` - Create store
- `GET /v1/vector_stores` - List stores

### Embeddings
- `POST /v1/vector_stores/{id}/embeddings` - Single embedding
- `POST /v1/vector_stores/{id}/embeddings/batch` - Batch embeddings

### Search
- `POST /v1/vector_stores/{id}/search` - Semantic search

### Health
- `GET /health` - Health check

## 🔐 Authentication

All API endpoints require:
```
Authorization: Bearer <OPENAI_API_KEY>
```

## 🎯 UI Tabs

1. **Stores** - Manage vector stores
2. **Ingest** - Add policies (paste/upload/MCP)
3. **Search** - Semantic search interface
4. **RAG Chat** - Ask questions with RAG

## 📈 Performance Tips

1. Use batch endpoints for bulk ingestion
2. Create IVFFLAT index after bulk load
3. Adjust chunk size based on document type
4. Use metadata filters to narrow search

## 🔗 External Services

- **LiteLLM**: Embedding generation (required)
- **Stargate**: LLM for RAG answers (required)
- **MCP Server**: Optional policy source
