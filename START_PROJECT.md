# 🚀 Starting the Full Project

## Prerequisites Check

1. **Docker Desktop** must be running
   - Check: Docker Desktop icon in system tray should be running
   - If not running, start Docker Desktop and wait for it to fully start

2. **Environment File** (`.env`)
   - Already created from `env.example`
   - **IMPORTANT**: Edit `.env` and add your actual API keys:
     - `EMBEDDING__API_KEY` - Your OpenAI/Cohere API key
     - `STARGATE_API_KEY` - Your Stargate API key  
     - `STARGATE_BASE_URL` - Your Stargate endpoint URL

## Step-by-Step Startup

### 1. Start All Services

```powershell
cd c:\Users\athar\Desktop\PYVECTOR
docker-compose up -d
```

This will start:
- ✅ Postgres + PGVector (port 5432)
- ✅ LiteLLM Proxy (port 4000)
- ✅ FastAPI Backend (port 8000)
- ✅ Streamlit UI (port 8501)

### 2. Wait for Services to Start

Wait 30-60 seconds for all services to initialize. You can check status:

```powershell
docker-compose ps
```

All services should show "Up" status.

### 3. Check Health

**API Health:**
```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","database":"healthy","timestamp":1234567890}
```

**UI Health:**
```powershell
curl http://localhost:8501/_stcore/health
```

### 4. Access the UI

Open your browser and navigate to:
```
http://localhost:8501
```

You should see the Policy Q&A System interface with tabs:
- **Stores** - Manage vector stores
- **Ingest** - Add policies
- **Search** - Semantic search
- **RAG Chat** - Ask questions

## Troubleshooting

### Services Won't Start

```powershell
# Check logs
docker-compose logs

# Check specific service logs
docker-compose logs api
docker-compose logs ui
docker-compose logs db
docker-compose logs litellm
```

### Database Connection Issues

```powershell
# Check database is running
docker-compose exec db psql -U postgres -d vectordb -c "SELECT 1;"
```

### Port Already in Use

If ports 5432, 4000, 8000, or 8501 are already in use:

1. Stop conflicting services, OR
2. Edit `docker-compose.yml` and change port mappings:
   ```yaml
   ports:
     - "8502:8501"  # Change external port
   ```

### Missing API Keys

If you see errors about API keys:

1. Edit `.env` file
2. Add your actual keys:
   ```env
   EMBEDDING__API_KEY=sk-your-actual-openai-key
   STARGATE_API_KEY=your-actual-stargate-key
   STARGATE_BASE_URL=https://your-stargate-host/api
   ```
3. Restart services:
   ```powershell
   docker-compose restart
   ```

## Quick Commands

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f api

# Stop and remove everything (including volumes)
docker-compose down -v
```

## Next Steps

Once services are running:

1. **Create a Vector Store**
   - Go to "Stores" tab
   - Click "Create Store"
   - Enter a name (e.g., "HR Policies")

2. **Ingest Policies**
   - Go to "Ingest" tab
   - Select your vector store
   - Choose ingest method:
     - Paste text directly
     - Upload PDF/DOCX/TXT file
     - Fetch from MCP server

3. **Search Policies**
   - Go to "Search" tab
   - Enter a query
   - View semantic search results

4. **Ask Questions (RAG)**
   - Go to "RAG Chat" tab
   - Ask questions about policies
   - Get AI-generated answers based on your documents

## Verification Checklist

- [ ] Docker Desktop is running
- [ ] `.env` file exists and has API keys
- [ ] All services show "Up" in `docker-compose ps`
- [ ] API health check returns `{"status":"healthy"}`
- [ ] UI accessible at http://localhost:8501
- [ ] Can create a vector store in UI
- [ ] Can ingest a test document
- [ ] Can perform a search query

## Support

If you encounter issues:

1. Check service logs: `docker-compose logs`
2. Verify Docker Desktop is running
3. Ensure ports are not in use
4. Verify API keys in `.env` are correct
5. Check network connectivity
