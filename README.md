# PolicyVector AI

PolicyVector AI is an enterprise-grade, AI-powered Policy Q&A system designed for semantic search and Retrieval-Augmented Generation (RAG) over corporate policy documents. It provides a complete pipeline from document ingestion and vectorization to high-fidelity answer generation.

## 🌟 System Overview

PolicyVector AI transforms static policy documents into a queryable intelligence layer. By combining a high-performance vector database (PGVector) with an OpenAI-compatible API and a sophisticated RAG pipeline, it enables users to find precise answers grounded in official documentation.

### Core Capabilities
- **Semantic Policy Search**: Find information based on intent and meaning, transcending simple keyword matching.
- **High-Fidelity RAG**: Generate grounded answers using the Stargate LLM, complete with citations and similarity scores.
- **OpenAI-Compatible Vector API**: A standardized backend for managing vector stores and embeddings, ensuring interoperability.
- **Multi-Modal Ingestion**: Support for direct text pasting, file uploads (PDF, DOCX, TXT), and MCP server integration.
- **Enterprise Scaling**: Built with FastAPI and PGVector for asynchronous, low-latency performance.

---

## 🏗️ Architecture

PolicyVector AI follows a decoupled, microservice-oriented architecture:

### 1. The Intelligence Layer (RAG & LLM)
- **Stargate API**: The primary LLM engine used to synthesize final answers from retrieved context.
- **LiteLLM Proxy**: A unification layer that provides a consistent `/v1/embeddings` interface regardless of the underlying embedding model.

### 2. The Orchestration Layer (FastAPI)
- **Vector Store API**: A production-ready API that handles:
    - **Store Management**: Creating and listing isolated knowledge bases.
    - **Embedding Ingestion**: Processing text into vectors via LiteLLM and storing them in Postgres.
    - **Similarity Search**: Executing cosine similarity queries against PGVector indexes.

### 3. The Data Layer (PostgreSQL + PGVector)
- **PGVector**: Utilizes `vector(1536)` types and `IVFFLAT` indexes for millisecond-scale similarity search.
- **Metadata Filtering**: Employs GIN indexes on JSONB fields to allow hybrid search (semantic + attribute filtering).

### 4. The User Interface (Streamlit)
- **Policy Management**: Interface for creating stores and ingesting documents.
- **RAG Chat**: An interactive chat experience that combines retrieved policy chunks with user questions for grounded responses.

---

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd PYVECTOR
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env to set your API keys and database credentials
   ```

3. **Deploy the stack:**
   ```bash
   docker-compose up -d
   ```

4. **Access the components:**
   - **UI**: `http://localhost:8501`
   - **API**: `http://localhost:8000`
   - **Health Check**: `curl http://localhost:8000/health`

---

## 🔌 API Specification

All endpoints are prefixed with `/v1/vector_stores` and require `Authorization: Bearer <token>`.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/vector_stores` | `POST` | Create a new isolated policy store |
| `/v1/vector_stores` | `GET` | List all existing stores |
| `/v1/vector_stores/{id}/embeddings` | `POST` | Add a single text chunk (auto-embeds) |
| `/v1/vector_stores/{id}/embeddings/batch` | `POST` | Batch ingest multiple document chunks |
| `/v1/vector_stores/{id}/search` | `POST` | Perform semantic search on the store |

---

## 📁 Project Structure

```
PYVECTOR/
├── main.py                 # FastAPI application (Core API)
├── models.py               # Pydantic schemas for the Vector API
├── config.py               # Configuration management
├── embedding_service.py    # LiteLLM integration service
├── database.sql            # SQL schema for PGVector
├── requirements.txt        # Backend dependencies
├── Dockerfile              # Backend container definition
├── docker-compose.yml      # Multi-service orchestration
├── litellm_config.yaml     # Proxy configuration for embeddings
├── migrations/             # Database evolution scripts
└── scripts/                # Utility and test clients
```

---

## ⚙️ Configuration

Key environment variables in `.env`:

- `DATABASE_URL`: Postgres connection string with PGVector.
- `SERVER_API_KEY`: Security token for API access.
- `EMBEDDING__MODEL`: The embedding model (e.g., `text-embedding-ada-002`).
- `STARGATE_API_KEY`: Key for the RAG answer generation LLM.
- `STREAMLIT__API_BASE`: The internal URL for the FastAPI backend.
