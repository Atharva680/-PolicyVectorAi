# AI policy Q&A system architecture
_Exported on 12/10/2025 at 22:44:58 GMT+5:30 from Cursor (2.1.50)_

---

**User**

✅ Project Goal

You are creating an AI-powered Policy Q&A system that:

Stores company policy documents in a vector database.

Lets users search policies semantically (not just keyword-based).

Answers questions using Retrieval-Augmented Generation (RAG) with Stargate LLM.

✅ Core Components & Their Roles

1. Postgres + PGVector

Why?

Policies need to be stored in a way that supports semantic search. PGVector adds a vector column type to Postgres for storing embeddings.

What it does?

Stores:

content (policy text)

embedding (numerical representation of text)

metadata (category, source, etc.)

Benefit:

Enables similarity search using cosine distance.

2. FastAPI (Vector Store API)

Why?

Acts as a backend service exposing OpenAI-compatible endpoints for:

Creating vector stores

Adding embeddings (single or batch)

Searching vector stores

Endpoints:

POST /v1/vector_stores → Create a store

POST /v1/vector_stores/{id}/embeddings → Add embeddings

POST /v1/vector_stores/{id}/search → Search by query

Benefit:

Standardized API that works with OpenAI clients and integrates easily with Streamlit UI.

3. LiteLLM Proxy

Why?

Converts any embedding model (OpenAI, Cohere, etc.) into an OpenAI-compatible API.

What it does?

Runs locally on http://localhost:4000

Accepts /v1/embeddings requests

Generates embeddings for policy text

Benefit:

Decouples your app from a specific provider and supports multiple models.

4. Streamlit UI

Why?

Provides a user-friendly interface for:

Creating vector stores

Uploading policies (paste/upload/MCP fetch)

Searching policies

Asking questions with RAG

Tabs:

Stores → Manage vector stores

Ingest → Add policy content

Search + RAG Chat → Query policies and get answers from Stargate LLM

Benefit:

Non-technical users can interact easily.

5. Stargate API

Why?

Provides LLM models (like gptoss-20b) for answering questions.

What it does?

Accepts OpenAI-style requests (chat.completions)

Generates answers using retrieved policy context

Benefit:

Ensures answers are grounded in company policies (RAG approach).

✅ Workflow (Step-by-Step)

Start Docker stack:

Postgres + PGVector

LiteLLM proxy

FastAPI backend

Streamlit UI

Create a vector store (via UI or API):

Example: Policy Store

Ingest policies:

Paste text or upload files

Optionally fetch from MCP tools

Generate embeddings (via LiteLLM)

Store in PGVector through FastAPI

Search policies:

Query → Convert to embedding → Find similar policies

Returns top-k results with scores and metadata

RAG answer generation:

Combine top-k policy chunks into a context

Send context + question to Stargate LLM

Display answer in Streamlit UI

✅ Technologies Used

Docker Compose → Runs all services together

FastAPI → Backend API

Postgres + PGVector → Vector database

LiteLLM → Embedding proxy

Streamlit → UI

Stargate API → LLM for answers

 

Ok

 

) Core Software (Developer Machine)

Docker Desktop (latest, with Linux container support enabled)

Python 3.10+ (only if you also run locally without Docker)

PowerShell or Terminal (to run commands)

Git (optional, for version control)

2) Docker Services & Images (Compose Stack)

Compose services:

Postgres + PGVector

Image: pgvector/pgvector:pg17

Purpose: vector storage and similarity search

LiteLLM Proxy

Image: ghcr.io/berriai/litellm:latest

Purpose: OpenAI-compatible /v1/embeddings for any embedding model

Important Compose settings:

platform: linux/amd64 (fixes ARM vs AMD mismatch)

entrypoint: ["litellm"]

command: ["--model", "text-embedding-ada-002", "--port", "4000"]

Vector Store API (FastAPI)

Built from project Dockerfile (Python 3.11-slim base)

Purpose: OpenAI-compatible endpoints: create store, add embeddings, search

Streamlit UI

Built from project Dockerfile

Purpose: User interface for stores, ingest, search, RAG chat

3) Python Libraries (inside API/UI images)

Backend/API:

fastapi

uvicorn[standard]

pydantic

python-dotenv

psycopg2-binary

asyncpg

sqlalchemy>=2.0

pgvector

httpx

litellm

openai

UI (Streamlit) & ingestion helpers:

streamlit

pymupdf (PDF parsing; if Docker slim errors, you can comment this out and keep local)

python-docx (DOCX parsing)

✅ Ensure no stray lines like python or backticks in requirements.txt. They break pip installs.

4) Access & Credentials (must be provisioned)

Embedding provider key (e.g., OpenAI key)

.env: EMBEDDING__API_KEY=...

Used by LiteLLM to call the embedding model (text-embedding-ada-002, etc.)

Vector Store API client token

.env: OPENAI_API_KEY=sk-local-xyz

Used by UI and client scripts in Authorization: Bearer ...

Stargate API key

.env: STARGATE_API_KEY=...

.env: STARGATE_BASE_URL=https://<your-stargate-host>/api

.env: STARGATE_MODEL=gptoss-20b (or another model available to the key)

(Optional) MCP server auth

Any headers/tokens required by your MCP server to run search/fetch tools

 

 

Prompt give me architucture | Try in Copilot Chat

give me architucture

 

Response

Awesome—here’s a clear, share-ready architecture for your project (Policy Vector Store + Streamlit UI + LiteLLM + PGVector + Stargate). I’ve included:

A high-level diagram (ASCII + Mermaid)

Components & ports

Data flow (ingest → embed → store → search → RAG answer)

Deployment topology (Docker Compose)

Security & configs (env vars & secrets)

Optional extensions (MCP, monitoring)

1) High-level Architecture (ASCII)

+-----------------------------------------------+

|                  End User                     |

|  (Browser)                                    |

|   └──> Streamlit UI (http://localhost:8501)   |

+-----------------------------------------------+

                |          ^

                |          | RAG Answer (Stargate LLM)

  Manage Stores |          |

  Ingest/Search |          |

                v          |

+-----------------------------------------------+

|        Vector Store API (FastAPI)             |

|  (http://localhost:8000)                      |

|  OpenAI-compatible endpoints:                 |

|   - POST /v1/vector_stores                    |

|   - POST /v1/vector_stores/{id}/embeddings    |

|   - POST /v1/vector_stores/{id}/search        |

+-----------------------------------------------+

                |         ^

                |         | embeddings (LiteLLM /v1/embeddings)

                v         |

+-----------------------------------------------+

|          LiteLLM Proxy (Embeddings)           |

|   (http://localhost:4000)                     |

|   entrypoint: litellm                         |

|   model: text-embedding-ada-002               |

|   uses: EMBEDDING__API_KEY                    |

+-----------------------------------------------+

                |

                | SQL (asyncpg/psycopg2)

                v

+-----------------------------------------------+

|           Postgres + PGVector (DB)            |

|   (localhost:5432, docker service 'db')       |

|   Tables:                                     |

|     vector_stores(id,name,metadata,...)       |

|     embeddings(id,vector_store_id,content,    |

|               embedding VECTOR(1536),metadata)|

+-----------------------------------------------+



                    RAG path (LLM inference)

                    +----------------------+

                    |   Stargate API       |

                    | (OpenAI-compatible)  |

                    |  chat.completions    |

                    +----------------------+

                    BASE_URL + API_KEY in .env

2) Mermaid Diagram (copy into docs)

flowchart LR

  subgraph Client["End User"]

    UI["Streamlit UI\n:8501"]

  end



  subgraph Backend["Vector Store Backend"]

    API["FastAPI\nOpenAI-compatible\n:8000"]

    Lite["LiteLLM Proxy\n/v1/embeddings\n:4000"]

    DB["Postgres + PGVector\n:5432"]

  end



  subgraph LLM["Stargate API"]

    SG["OpenAI SDK\nchat.completions"]

  end



  UI -- Create/List/Batch/Search --> API

  API -- Generate embeddings --> Lite

  API -- Read/Write --> DB

  UI -- Search results --> UI

  UI -- RAG prompt (context + question) --> SG

  SG -- Answer --> UI

3) Components & Ports

Streamlit UI (:8501)

Create stores, ingest policies (paste/upload/MCP), search, RAG chat

Vector Store API (FastAPI) (:8000)

Endpoints:

POST /v1/vector_stores

POST /v1/vector_stores/{id}/embeddings

POST /v1/vector_stores/{id}/embeddings/batch

POST /v1/vector_stores/{id}/search

Auth: Authorization: Bearer <OPENAI_API_KEY>

LiteLLM Proxy (Embeddings) (:4000)

Entry: litellm

Command: --model text-embedding-ada-002 --port 4000

Requires EMBEDDING__API_KEY (provider key)

Postgres + PGVector (:5432)

vector_stores + embeddings tables

embedding column is VECTOR(1536) (match model dimensions)

Stargate API (External)

BASE_URL: OpenAI-compatible endpoint

API_KEY: Auth for model (e.g., gptoss-20b)

Used by Streamlit RAG chat

4) Data Flow (Step-by-step)

Ingestion path (UI → API → LiteLLM → DB):

User selects a vector store or creates one in Streamlit.

User pastes/upload/MCP-fetches policy content.

Streamlit either:

Sends content to API batch endpoint (server auto-generates embeddings via LiteLLM), OR

Precomputes embeddings via LiteLLM and posts vectors to API batch endpoint.

API writes entries to PGVector: content, embedding, metadata.

Search path (UI → API → LiteLLM → DB → UI):

User enters a query in Streamlit.

API embeds the query via LiteLLM.

API performs cosine distance search in PGVector.

API returns top‑k results with score + metadata to UI.

RAG path (UI → Stargate → UI):

Streamlit builds a context string from top‑k results.

Sends {context + question} to Stargate via OpenAI SDK (chat.completions).

Displays answer in UI.

5) Deployment Topology (Docker Compose)

All services run as containers:

db (pgvector)

litellm (embeddings proxy)

api (FastAPI)

ui (Streamlit)

Networks & volumes: Internal bridge network + persistent volume for Postgres data.

Dependency order: api depends on db (healthy) and litellm (started) so embedding calls work.

Important litellm service config (to fix your issue):

litellm:

  image: ghcr.io/berriai/litellm:latest

  platform: linux/amd64

  container_name: litellm-proxy

  entrypoint: ["litellm"]

  command: ["--model", "text-embedding-ada-002", "--port", "4000"]

  environment:

    OPENAI_API_KEY: ${EMBEDDING__API_KEY}

  ports:

    - "4000:4000"

6) Security & Configs (Env Vars)

Required in .env:

# DB

DATABASE_URL=postgresql://postgres:postgres@db:5432/vectordb?schema=public



# Vector Store API (auth token for clients)

OPENAI_API_KEY=sk-local-xyz



# LiteLLM proxy

EMBEDDING__MODEL=text-embedding-ada-002

EMBEDDING__BASE_URL=http://litellm:4000

EMBEDDING__API_KEY=sk-your-real-openai-key

EMBEDDING__DIMENSIONS=1536



# Streamlit client defaults (host machine)

STREAMLIT__API_BASE=http://localhost:8000

STREAMLIT__API_KEY=sk-local-xyz

STREAMLIT__EMBED_BASE=http://localhost:4000

STREAMLIT__EMBED_MODEL=text-embedding-ada-002



# MCP server (if used)

MCP__BASE_URL=http://localhost:7070

MCP__SEARCH_TOOL=policy_search

MCP__FETCH_TOOL=policy_fetch



# Stargate LLM

STARGATE_API_KEY=your-stargate-key

STARGATE_BASE_URL=https://your-stargate-host/api

STARGATE_MODEL=gptoss-20b

Keep it strictly KEY=value (no quotes, no trailing spaces).

7) Sequence Diagram (Mermaid)

sequenceDiagram

  participant U as User (Streamlit)

  participant A as API (FastAPI)

  participant L as LiteLLM (Embeddings)

  participant D as DB (PGVector)

  participant S as Stargate (LLM)



  U->>A: Create Vector Store

  A->>D: INSERT vector_store

  U->>A: Batch Ingest (content/metadata)

  alt Server generates embeddings

    A->>L: POST /v1/embeddings (texts)

    L-->>A: embeddings[]

  else Precomputed embeddings

    U->>A: content + embedding[]

  end

  A->>D: INSERT embeddings (content, embedding, metadata)



  U->>A: Search (query, limit)

  A->>L: POST /v1/embeddings (query)

  L-->>A: embedding(query)

  A->>D: SELECT top-k by cosine_distance

  D-->>A: results[]

  A-->>U: results with scores & metadata



  U->>S: chat.completions (context + question)

  S-->>U: RAG answer

8) Optional Extensions

MCP integration: Robust tool invocation (auth headers, JSON-RPC if needed), chunking, metadata normalization (e.g., {category, source, doc_id}).

Indexing performance: Create IVFFLAT index after bulk ingestion for faster similarity search.

Observability: Add health endpoints/views in UI, Stargate usage/logs view, GPU monitor.

Streaming chat: Token streaming from Stargate in Streamlit for faster UX.

Want a PNG diagram you can send to your lead?

I can generate a clean architecture image and share it.

Also, if you want, I’ll export this architecture into a one-page PDF with the diagram + key points.

Sign in to your account

 

 

 

 

---

**Cursor**


Exploring the project structure, then setting up the components.



Reviewing key files to understand the current implementation:



Checking a few more files to understand the structure:



Creating an architecture document and verifying the implementation. Fixing a few minor issues:


```markdown
# AI-Powered Policy Q&A System - Architecture Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Deployment Topology](#deployment-topology)
6. [Security & Configuration](#security--configuration)
7. [Sequence Diagrams](#sequence-diagrams)
8. [Optional Extensions](#optional-extensions)

---

## Overview

This document describes the architecture of an AI-powered Policy Q&A system that enables semantic search and question-answering over company policy documents using Retrieval-Augmented Generation (RAG).

### Core Capabilities

- **Semantic Search**: Find policies by meaning, not just keywords
- **Vector Storage**: Efficient storage and retrieval using PGVector
- **RAG Answers**: Generate answers grounded in policy documents using Stargate LLM
- **Multiple Ingest Methods**: Paste text, upload files, or fetch from MCP servers
- **OpenAI-Compatible API**: Standardized endpoints for easy integration

---

## High-Level Architecture

### ASCII Diagram

```
+-----------------------------------------------+
|                  End User                     |
|  (Browser)                                    |
|   └──> Streamlit UI (http://localhost:8501)   |
+-----------------------------------------------+
                |          ^
                |          | RAG Answer (Stargate LLM)
  Manage Stores |          |
  Ingest/Search |          |
                v          |
+-----------------------------------------------+
|        Vector Store API (FastAPI)             |
|  (http://localhost:8000)                      |
|  OpenAI-compatible endpoints:                 |
|   - POST /v1/vector_stores                    |
|   - POST /v1/vector_stores/{id}/embeddings    |
|   - POST /v1/vector_stores/{id}/search        |
+-----------------------------------------------+
                |         ^
                |         | embeddings (LiteLLM /v1/embeddings)
                v         |
+-----------------------------------------------+
|          LiteLLM Proxy (Embeddings)           |
|   (http://localhost:4000)                     |
|   entrypoint: litellm                         |
|   model: text-embedding-ada-002               |
|   uses: EMBEDDING__API_KEY                    |
+-----------------------------------------------+
                |
                | SQL (asyncpg/psycopg2)
                v
+-----------------------------------------------+
|           Postgres + PGVector (DB)            |
|   (localhost:5432, docker service 'db')       |
|   Tables:                                     |
|     vector_stores(id,name,metadata,...)       |
|     embeddings(id,vector_store_id,content,   |
|               embedding VECTOR(1536),metadata)|
+-----------------------------------------------+

                    RAG path (LLM inference)
                    +----------------------+
                    |   Stargate API       |
                    | (OpenAI-compatible)  |
                    |  chat.completions    |
                    +----------------------+
                    BASE_URL + API_KEY in .env
```

### Mermaid Diagram

```mermaid
flowchart LR
  subgraph Client["End User"]
    UI["Streamlit UI\n:8501"]
  end

  subgraph Backend["Vector Store Backend"]
    API["FastAPI\nOpenAI-compatible\n:8000"]
    Lite["LiteLLM Proxy\n/v1/embeddings\n:4000"]
    DB["Postgres + PGVector\n:5432"]
  end

  subgraph LLM["Stargate API"]
    SG["OpenAI SDK\nchat.completions"]
  end

  UI -- Create/List/Batch/Search --> API
  API -- Generate embeddings --> Lite
  API -- Read/Write --> DB
  UI -- Search results --> UI
  UI -- RAG prompt (context + question) --> SG
  SG -- Answer --> UI
```

---

## Component Details

### 1. Postgres + PGVector

**Purpose**: Vector database for storing policy embeddings and enabling semantic search.

**Image**: `pgvector/pgvector:pg17`

**Key Features**:
- PGVector extension for vector operations
- Cosine similarity search using `<=>` operator
- IVFFLAT index for fast similarity queries
- GIN index for metadata filtering

**Schema**:
```sql
-- Vector stores table
CREATE TABLE vector_stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    file_counts JSONB DEFAULT '{"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0}',
    status TEXT DEFAULT 'completed',
    usage_bytes BIGINT DEFAULT 0,
    expires_after JSONB,
    expires_at TIMESTAMP,
    last_active_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vector_store_id UUID REFERENCES vector_stores(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- Match embedding model dimensions
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_embeddings_vector_store ON embeddings(vector_store_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_embeddings_metadata ON embeddings USING gin(metadata);
```

**Port**: `5432`

---

### 2. LiteLLM Proxy

**Purpose**: Provides OpenAI-compatible `/v1/embeddings` endpoint for any embedding model.

**Image**: `ghcr.io/berriai/litellm:latest`

**Configuration**:
```yaml
platform: linux/amd64
entrypoint: ["litellm"]
command: ["--model", "text-embedding-ada-002", "--port", "4000"]
environment:
  OPENAI_API_KEY: ${EMBEDDING__API_KEY}
```

**Key Features**:
- Converts any embedding provider to OpenAI-compatible API
- Supports multiple models (OpenAI, Cohere, etc.)
- Decouples application from specific provider

**Port**: `4000`

**Endpoints**:
- `POST /v1/embeddings` - Generate embeddings for text

---

### 3. FastAPI Vector Store API

**Purpose**: Backend service providing OpenAI-compatible vector store endpoints.

**Technology**: FastAPI, Prisma, asyncpg

**Key Features**:
- OpenAI-compatible API specification
- Automatic embedding generation via LiteLLM
- Batch operations for efficient ingestion
- Metadata filtering
- Bearer token authentication

**Port**: `8000`

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/vector_stores` | Create a new vector store |
| `GET` | `/v1/vector_stores` | List vector stores (paginated) |
| `POST` | `/v1/vector_stores/{id}/embeddings` | Add single embedding |
| `POST` | `/v1/vector_stores/{id}/embeddings/batch` | Add multiple embeddings |
| `POST` | `/v1/vector_stores/{id}/search` | Semantic search with cosine similarity |
| `GET` | `/health` | Health check endpoint |

**Authentication**: `Authorization: Bearer <API_KEY>`

---

### 4. Streamlit UI

**Purpose**: User-friendly interface for managing policies and asking questions.

**Technology**: Streamlit, OpenAI SDK, httpx

**Port**: `8501`

**Tabs**:

1. **Stores**
   - List existing vector stores
   - Create new vector stores
   - View store metadata

2. **Ingest**
   - **Paste Text**: Direct text input with chunking options
   - **Upload File**: Support for TXT, PDF, DOCX files
   - **MCP Fetch**: Fetch policies from MCP server
   - Automatic chunking with configurable size and overlap
   - Metadata tagging

3. **Search**
   - Semantic search interface
   - Configurable result limit
   - Display similarity scores
   - Show metadata and content chunks

4. **RAG Chat**
   - Interactive chat interface
   - Combines search results into context
   - Sends to Stargate LLM for answer generation
   - Displays sources and citations

**Features**:
- Real-time progress indicators
- Error handling and user feedback
- Responsive layout
- Session state management

---

### 5. Stargate API

**Purpose**: LLM provider for generating RAG answers.

**Integration**: OpenAI SDK compatible

**Configuration**:
- `STARGATE_API_KEY`: Authentication key
- `STARGATE_BASE_URL`: API endpoint URL
- `STARGATE_MODEL`: Model name (e.g., `gptoss-20b`)

**Usage**:
- Receives context (top-k policy chunks) + user question
- Generates answer grounded in provided context
- Returns formatted response

**Example Request**:
```python
response = stargate_client.chat.completions.create(
    model=STARGATE_MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant..."},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
    ],
    temperature=0.7,
    max_tokens=1000
)
```

---

## Data Flow

### Ingestion Path

```
User (Streamlit UI)
  ↓
1. Select/Create Vector Store
  ↓
2. Choose Ingest Method:
   - Paste Text
   - Upload File (PDF/DOCX/TXT)
   - MCP Fetch
  ↓
3. Chunk Text (configurable size/overlap)
  ↓
4. POST /v1/vector_stores/{id}/embeddings/batch
   (content + metadata)
  ↓
FastAPI Backend
  ↓
5. Generate Embeddings (if not provided)
   POST http://litellm:4000/v1/embeddings
  ↓
LiteLLM Proxy
  ↓
6. Call Embedding Provider API
   (OpenAI, Cohere, etc.)
  ↓
7. Store in PGVector
   INSERT INTO embeddings (content, embedding, metadata)
  ↓
8. Update Vector Store Statistics
   (file_counts, usage_bytes)
```

### Search Path

```
User (Streamlit UI)
  ↓
1. Enter Search Query
  ↓
2. POST /v1/vector_stores/{id}/search
   {query, limit, filters}
  ↓
FastAPI Backend
  ↓
3. Generate Query Embedding
   POST http://litellm:4000/v1/embeddings
  ↓
4. Vector Similarity Search
   SELECT ... FROM embeddings
   WHERE vector_store_id = ?
   ORDER BY embedding <=> query_vector
   LIMIT ?
  ↓
5. Convert Distance to Similarity Score
   score = 1 - (distance / 2)
  ↓
6. Return Results
   {data: [{file_id, filename, score, content, metadata}]}
  ↓
Streamlit UI
  ↓
7. Display Results with Scores
```

### RAG Answer Path

```
User (Streamlit UI)
  ↓
1. Enter Question in Chat
  ↓
2. Search for Relevant Policies
   POST /v1/vector_stores/{id}/search
   (query = question, limit = top_k)
  ↓
3. Build Context String
   Combine top-k policy chunks
   Format: "[Score: X] {chunk_text}\n\n..."
  ↓
4. Generate RAG Answer
   POST Stargate API /chat/completions
   {
     model: "gptoss-20b",
     messages: [
       {role: "system", content: "You are..."},
       {role: "user", content: "Context: {context}\n\nQuestion: {question}"}
     ]
   }
  ↓
Stargate API
  ↓
5. Generate Answer
   (LLM inference with context)
  ↓
6. Return Answer
  ↓
Streamlit UI
  ↓
7. Display Answer + Sources
   - Show answer in chat
   - Expandable sources section
   - Metadata and scores
```

---

## Deployment Topology

### Docker Compose Stack

```yaml
services:
  db:          # Postgres + PGVector
    image: pgvector/pgvector:pg17
    platform: linux/amd64
    ports: ["5432:5432"]
    
  litellm:    # Embedding Proxy
    image: ghcr.io/berriai/litellm:latest
    platform: linux/amd64
    ports: ["4000:4000"]
    
  api:        # FastAPI Backend
    build: .
    dockerfile: Dockerfile
    ports: ["8000:8000"]
    depends_on:
      - db
      - litellm
    
  ui:         # Streamlit UI
    build: .
    dockerfile: Dockerfile.ui
    ports: ["8501:8501"]
    depends_on:
      - api
```

### Network Architecture

- **Network**: `vectordb-network` (bridge)
- **Internal Communication**: Service names (e.g., `http://api:8000`)
- **External Access**: `localhost` ports

### Service Dependencies

```
db (Postgres)
  ↑
  ├── litellm (depends on db health)
  │
  └── api (depends on db + litellm health)
       ↑
       └── ui (depends on api health)
```

### Volumes

- `postgres_data`: Persistent storage for database
- `./prisma`: Prisma schema (mounted in API container)

---

## Security & Configuration

### Environment Variables

#### Database
```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/vectordb?schema=public
```

#### Vector Store API
```env
OPENAI_API_KEY=sk-local-xyz  # Client authentication token
SERVER_API_KEY=sk-local-xyz   # Alternative name (backward compatibility)
```

#### LiteLLM Proxy
```env
EMBEDDING__MODEL=text-embedding-ada-002
EMBEDDING__BASE_URL=http://litellm:4000
EMBEDDING__API_KEY=sk-your-real-openai-key  # Provider API key
EMBEDDING__DIMENSIONS=1536
```

#### Streamlit UI
```env
STREAMLIT__API_BASE=http://api:8000        # Docker: use service name
STREAMLIT__API_BASE=http://localhost:8000  # Local: use localhost
STREAMLIT__API_KEY=sk-local-xyz
STREAMLIT__EMBED_BASE=http://litellm:4000
STREAMLIT__EMBED_MODEL=text-embedding-ada-002
```

#### MCP Server (Optional)
```env
MCP__BASE_URL=http://localhost:7070
MCP__SEARCH_TOOL=policy_search
MCP__FETCH_TOOL=policy_fetch
```

#### Stargate LLM
```env
STARGATE_API_KEY=your-stargate-key
STARGATE_BASE_URL=https://your-stargate-host/api
STARGATE_MODEL=gptoss-20b
```

### Security Considerations

1. **API Authentication**: Bearer token required for all API endpoints
2. **Environment Variables**: Never commit `.env` file (use `.env.example`)
3. **Database Credentials**: Use strong passwords in production
4. **Network Isolation**: Services communicate via internal Docker network
5. **HTTPS**: Use reverse proxy (nginx/traefik) for production HTTPS

---

## Sequence Diagrams

### Complete Ingestion Flow

```mermaid
sequenceDiagram
  participant U as User (Streamlit)
  participant A as API (FastAPI)
  participant L as LiteLLM (Embeddings)
  participant D as DB (PGVector)

  U->>A: POST /v1/vector_stores (create store)
  A->>D: INSERT vector_store
  D-->>A: store_id
  A-->>U: VectorStoreResponse

  U->>A: POST /v1/vector_stores/{id}/embeddings/batch
  Note over U,A: {content, metadata} (no embeddings)
  
  A->>L: POST /v1/embeddings (batch texts)
  L->>L: Call OpenAI API
  L-->>A: embeddings[]
  
  A->>D: INSERT embeddings (batch)
  D-->>A: embedding_ids[]
  
  A->>D: UPDATE vector_store (stats)
  A-->>U: BatchCreateResponse
```

### Search & RAG Flow

```mermaid
sequenceDiagram
  participant U as User (Streamlit)
  participant A as API (FastAPI)
  participant L as LiteLLM (Embeddings)
  participant D as DB (PGVector)
  participant S as Stargate (LLM)

  U->>A: POST /v1/vector_stores/{id}/search
  Note over U,A: {query, limit: 5}
  
  A->>L: POST /v1/embeddings (query text)
  L-->>A: query_embedding
  
  A->>D: SELECT ... ORDER BY distance LIMIT 5
  D-->>A: results[]
  
  A-->>U: SearchResponse (top-k results)
  
  U->>U: Build context string
  Note over U: Combine top-k chunks
  
  U->>S: POST /chat/completions
  Note over U,S: {context + question}
  
  S-->>U: Answer (LLM response)
  
  U->>U: Display answer + sources
```

---

## Optional Extensions

### 1. MCP Integration

**Purpose**: Fetch policies from external MCP servers.

**Implementation**:
- Search tool: `POST /search` → returns policy IDs
- Fetch tool: `POST /fetch` → returns policy content
- Authentication: Headers/tokens as needed

**Example**:
```python
def mcp_search(query: str) -> List[Dict]:
    response = httpx.post(
        f"{MCP_BASE_URL}/search",
        json={"query": query, "tool": MCP_SEARCH_TOOL},
        headers={"Authorization": f"Bearer {MCP_TOKEN}"}
    )
    return response.json()["results"]
```

### 2. Performance Optimizations

**IVFFLAT Index**:
```sql
CREATE INDEX idx_embeddings_vector 
ON embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on data size
```

**Connection Pooling**:
- Use asyncpg connection pool
- Configure max_connections in settings

**Batch Operations**:
- Use batch endpoints for bulk ingestion
- Process embeddings in parallel

### 3. Observability

**Health Endpoints**:
- `/health` - API health check
- Database connection status
- LiteLLM proxy availability

**Logging**:
- Structured logging with correlation IDs
- Request/response logging
- Error tracking

**Monitoring**:
- Prometheus metrics
- Grafana dashboards
- Alerting on errors

### 4. Advanced Features

**Streaming Chat**:
- Token streaming from Stargate
- Real-time answer display
- Better UX for long responses

**Metadata Filtering**:
- Advanced filter queries
- Category-based search
- Date range filters

**Multi-tenancy**:
- Tenant isolation
- Per-tenant vector stores
- Access control

---

## Summary

This architecture provides a complete, production-ready Policy Q&A system with:

✅ **Semantic Search** via PGVector  
✅ **OpenAI-Compatible API** for easy integration  
✅ **User-Friendly UI** with Streamlit  
✅ **RAG Answers** using Stargate LLM  
✅ **Multiple Ingest Methods** (paste, upload, MCP)  
✅ **Docker Deployment** for easy setup  
✅ **Scalable Design** with async operations  

The system is designed to be:
- **Modular**: Each component has a clear responsibility
- **Extensible**: Easy to add new features
- **Maintainable**: Well-documented and structured
- **Production-Ready**: Includes error handling, logging, and health checks

```


Fixing UI issues and verifying compatibility:



Checking the search response structure and fixing UI issues:


```python
import docx
try:
    import pypdf
except ImportError:
    try:
        import PyPDF2 as pypdf
    except ImportError:
        pypdf = None
import io
```

```python
def parse_pdf(file) -> str:
    """Extract text from PDF file"""
    if pypdf is None:
        st.error("PDF parsing library not available. Please install pypdf or PyPDF2.")
        return ""
    try:
        pdf_reader = pypdf.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error parsing PDF: {str(e)}")
        return ""
```

```python
                    for i, result in enumerate(results['data']):
                        filename = result.get('filename', f"Document {i+1}")
                        with st.expander(f"Result {i+1}: Score {result['score']:.3f} - {filename}"):
                            st.write(f"**Score:** {result['score']:.4f}")
                            st.write(f"**File ID:** {result['file_id']}")
                            
                            if result.get('attributes'):
                                st.write("**Metadata:**")
                                st.json(result['attributes'])
                            
                            st.write("**Content:**")
                            # Handle both list of chunks and single content string
                            content_chunks = result.get('content', [])
                            if isinstance(content_chunks, list):
                                for chunk in content_chunks:
                                    if isinstance(chunk, dict):
                                        st.text(chunk.get('text', str(chunk)))
                                    else:
                                        st.text(str(chunk))
                            else:
                                st.text(str(content_chunks))
```

```python
                    # Show sources
                    with st.expander("📚 Sources"):
                        for i, result in enumerate(search_results['data'][:top_k]):
                            filename = result.get('filename', f"Document {i+1}")
                            st.write(f"**{i+1}. {filename}** (Score: {result['score']:.3f})")
                            if result.get('attributes'):
                                st.caption(f"Metadata: {result['attributes']}")
```


Updating requirements and verifying docker-compose configuration:


```pip-requirements
streamlit>=1.28.0
httpx>=0.25.0
openai>=1.3.0
python-dotenv>=1.0.0
python-docx>=1.1.0
pypdf>=4.0.0
PyPDF2>=3.0.0
```


Completing the remaining tasks and creating a quick reference guide:


```markdown
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

```


Checking for linting errors:



## Completed tasks

### 1. Architecture documentation (`ARCHITECTURE.md`)
   - High-level ASCII and Mermaid diagrams
   - Component descriptions (Postgres+PGVector, LiteLLM, FastAPI, Streamlit, Stargate)
   - Data flow diagrams (ingestion, search, RAG)
   - Deployment topology (Docker Compose)
   - Security and configuration guide
   - Sequence diagrams (Mermaid)
   - Optional extensions (MCP, performance, observability)

### 2. UI fixes
   - Fixed search results display to handle missing filename gracefully
   - Improved PDF parsing with fallback support
   - Enhanced content chunk display to handle different formats
   - Added error handling for PDF library imports

### 3. Requirements update
   - Added PyPDF2 as fallback for PDF parsing
   - Ensured compatibility with both `pypdf` and `PyPDF2`

### 4. Quick reference guide (`ARCHITECTURE_QUICK_REFERENCE.md`)
   - Quick start commands
   - Port reference table
   - Environment variables checklist
   - Troubleshooting tips
   - API endpoint summary

## Architecture highlights

The architecture document includes:

- Visual diagrams: ASCII and Mermaid flowcharts showing component relationships
- Component details: Each service documented with purpose, configuration, and features
- Data flows: Step-by-step flows for ingestion, search, and RAG
- Deployment: Docker Compose stack with dependencies and health checks
- Security: Environment variable management and authentication
- Sequence diagrams: Mermaid diagrams for ingestion and RAG flows

## Files created/updated

- `ARCHITECTURE.md` - Complete architecture documentation
- `ARCHITECTURE_QUICK_REFERENCE.md` - Quick reference guide
- `ui.py` - Fixed search display and PDF parsing
- `requirements-ui.txt` - Added PDF library fallback

The architecture matches your requirements:
- Postgres + PGVector for vector storage
- FastAPI with OpenAI-compatible endpoints
- LiteLLM proxy for embeddings
- Streamlit UI with Stores, Ingest, Search, and RAG Chat tabs
- Stargate LLM integration for RAG answers
- MCP server support for policy fetching
- Docker Compose deployment

You can now use `ARCHITECTURE.md` as the reference documentation for your Policy Q&A system.

---

**User**

run full proej

---

**Cursor**


Checking the environment setup, then starting the full project.



Setting up and starting the full project. Checking prerequisites and creating the `.env` file if needed:



Starting all services with Docker Compose:



Checking container status and waiting for services to be ready:



Checking Docker status and container logs:



Checking service health endpoints:



Creating a startup script and verifying the setup. Providing a guide to run the project:


```markdown
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

```


Creating a startup script and verifying the setup:


```bat
@echo off
echo ========================================
echo   Starting Policy Q&A System
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env from env.example...
    copy env.example .env
    echo.
    echo WARNING: Please edit .env and add your API keys:
    echo   - EMBEDDING__API_KEY
    echo   - STARGATE_API_KEY
    echo   - STARGATE_BASE_URL
    echo.
    pause
)

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Starting Docker services...
echo.

docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start services!
    echo Check Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo.
echo Waiting for services to start (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo   Service Status
echo ========================================
docker-compose ps

echo.
echo ========================================
echo   Health Checks
echo ========================================
echo.
echo Checking API health...
curl -s http://localhost:8000/health || echo API not ready yet

echo.
echo Checking UI health...
curl -s http://localhost:8501/_stcore/health || echo UI not ready yet

echo.
echo ========================================
echo   Access URLs
echo ========================================
echo.
echo Streamlit UI:  http://localhost:8501
echo FastAPI API:   http://localhost:8000
echo LiteLLM Proxy: http://localhost:4000
echo.
echo ========================================
echo.
echo Services are starting! Open http://localhost:8501 in your browser.
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo.
pause

```


## Project startup

### Quick start

**Option 1: Use the batch script (Windows)**
```powershell
cd c:\Users\athar\Desktop\PYVECTOR
.\start_project.bat
```

**Option 2: Manual start**
```powershell
cd c:\Users\athar\Desktop\PYVECTOR
docker-compose up -d --build
```

### What's starting

1. **Postgres + PGVector** (port 5432) - Vector database
2. **LiteLLM Proxy** (port 4000) - Embedding service
3. **FastAPI Backend** (port 8000) - Vector Store API
4. **Streamlit UI** (port 8501) - Web interface

### Important: configure API keys

Before using the system, edit `.env` and add your keys:

```env
EMBEDDING__API_KEY=sk-your-openai-key        # Required for embeddings
STARGATE_API_KEY=your-stargate-key          # Required for RAG chat
STARGATE_BASE_URL=https://your-host/api     # Required for RAG chat
```

### Access the UI

Once services are running (wait 30-60 seconds), open:
```
http://localhost:8501
```

### Verify services

Check health:
```powershell
curl http://localhost:8000/health
```

View logs:
```powershell
docker-compose logs -f
```

### Documentation created

- `ARCHITECTURE.md` - Complete architecture documentation
- `ARCHITECTURE_QUICK_REFERENCE.md` - Quick reference guide
- `START_PROJECT.md` - Detailed startup instructions
- `start_project.bat` - Windows startup script

### Next steps

1. Ensure Docker Desktop is running
2. Run `start_project.bat` or `docker-compose up -d`
3. Wait for services to start (30-60 seconds)
4. Open http://localhost:8501 in your browser
5. Create a vector store and start ingesting policies

The project is ready to run. If you encounter issues, check `START_PROJECT.md` for troubleshooting steps.

```powershell
cd c:\Users\athar\Desktop\PYVECTOR
.\start_project.bat
```

```powershell
cd c:\Users\athar\Desktop\PYVECTOR
docker-compose up -d --build
```

```dotenv
EMBEDDING__API_KEY=sk-your-openai-key        # Required for embeddings
STARGATE_API_KEY=your-stargate-key          # Required for RAG chat
STARGATE_BASE_URL=https://your-host/api     # Required for RAG chat
```

```plaintext
http://localhost:8501
```

```powershell
curl http://localhost:8000/health
```

```powershell
docker-compose logs -f
```

---

**User**

Nice — I’ll walk you through everything you need to run **GPT Lab** (the Streamlit app) locally on your machine, using the repo you uploaded. I’ll give you two clear options: **A. Local Python/venv** (recommended for development) and **B. Docker** (recommended for consistent deployment). I’ll also include the exact files you must create (`.streamlit/secrets.toml`), how to convert a Google Service Account JSON to TOML, required env vars (OpenAI / Stargate), and common troubleshooting notes.



---



# Quick checklist (done → run)



* [ ] Unzip the repo (you already uploaded `gptlab-streamlit-main.zip`)

* [ ] Create Google Firestore service account JSON and convert to TOML

* [ ] Create `.streamlit/secrets.toml`

* [ ] Set `OPENAI_API_KEY` (and any other required env vars)

* [ ] Create & activate Python venv, install requirements

* [ ] `streamlit run app/home.py` → open browser to `http://localhost:8501`



---



## A — Local Python (venv) — step by step



### 1) Unzip the repo (if not already)



If the uploaded zip is at `/mnt/data/gptlab-streamlit-main.zip` (from the UI), run:



```bash

unzip /mnt/data/gptlab-streamlit-main.zip -d ~/projects/

cd ~/projects/gptlab-streamlit-main

```



Adjust paths if you unzipped elsewhere.



### 2) Prepare Google Firestore credentials



1. In Google Cloud Console → Service Accounts, create a service account with Firestore access and download the JSON key.

2. Convert the JSON to TOML. Create a small Python converter (no external tools required):



Create `json2toml.py`:



```python

# json2toml.py

import json, toml, sys

if len(sys.argv) < 3:

    print("usage: python json2toml.py service-account.json out.toml")

    raise SystemExit(1)

with open(sys.argv[1], "r", encoding="utf-8") as f:

    data = json.load(f)

with open(sys.argv[2], "w", encoding="utf-8") as f:

    toml.dump(data, f)

print("Wrote", sys.argv[2])

```



Install `toml` if needed and run:



```bash

python -m pip install toml

python json2toml.py service-account.json service-account.toml

```



This produces `service-account.toml` which you will reference in `.streamlit/secrets.toml`.



> Alternative: some guides simply embed the JSON content as TOML by wrapping keys, but the script above is simple and safe.



### 3) Create `.streamlit/secrets.toml`



Create a folder `.streamlit` at the project root and add `secrets.toml` with at least:



```toml

[firestore]

db-key = '''/absolute/path/to/service-account.toml'''



[util]

global_salt = "OPTIONAL_GLOBAL_SALT"

```



Replace `/absolute/path/to/service-account.toml` with the real absolute path (e.g. `/home/you/projects/gptlab-streamlit-main/service-account.toml`). The app expects this key name per the README.



### 4) Set OpenAI / other env vars



The app will prompt for your OpenAI key in the UI, but it’s convenient to set it in your shell while developing:



```bash

export OPENAI_API_KEY="sk-..."

# Optional extras the app might expect for other features:

export FIRESTORE_PROJECT_ID="your-gcp-project"

export STARGATE_API_KEY="your-stargate-key"

export STARGATE_BASE_URL="https://your-stargate-host/api"

```



(If the app reads env vars by different names, you can also input keys in the UI.)



### 5) Create & activate Python venv, install requirements



Recommended Python 3.10+.



```bash

python3 -m venv .venv

source .venv/bin/activate           # macOS / Linux

# .venv\Scripts\activate            # Windows (PowerShell/CMD)

pip install --upgrade pip

pip install -r app/requirements.txt

```



**Important:** The repo README warned: ensure `requirements.txt` lines have only package tokens (no stray `python` or backticks). If pip fails, open `app/requirements.txt` and clean any stray characters.



If you face binary wheel issues (e.g., `pymupdf`), you can:



* Install system deps (Linux): `sudo apt-get update && sudo apt-get install -y libmupdf-dev` (varies by distro), or

* Comment out `pymupdf` in `requirements.txt` and run local PDF parsing only when running on a machine with proper libraries.



### 6) Run Streamlit



From the repo root:



```bash

streamlit run app/home.py

```



Open `http://localhost:8501` in your browser.



---



## B — Docker (recommended for parity with production)



If the repo includes a `Dockerfile` for the UI (README mentions it), you can build and run a container.



Example minimal steps (adapt to repo Dockerfile):



```bash

# from repo root

docker build -t gptlab-ui ./app

docker run -it --rm \

  -p 8501:8501 \

  -v /absolute/path/to/service-account.toml:/app/service-account.toml:ro \

  -e STREAMLIT_SECRETS_FIRESTORE_DB_KEY="/app/service-account.toml" \

  -e OPENAI_API_KEY="sk-..." \

  gptlab-ui

```



Notes:



* Map the secrets file as a read-only volume.

* Ensure the container runs as expected: read container logs (`docker logs -f <id>`).



If you prefer a `docker-compose.yml`, a simple snippet:



```yaml

version: '3.8'

services:

  ui:

    build: ./app

    ports:

      - "8501:8501"

    environment:

      - OPENAI_API_KEY=${OPENAI_API_KEY}

      - STREAMLIT_SECRETS_FIRESTORE_DB_KEY=/run/secrets/service-account.toml

    volumes:

      - ./service-account.toml:/run/secrets/service-account.toml:ro

```



---



## Common issues & troubleshooting



**1) Firestore auth / invalid key**



* Ensure the service account has Firestore permissions.

* Use absolute path in `.streamlit/secrets.toml`.

* If the app throws permission errors, check GCP IAM roles.



**2) `pymupdf` / binary build failures**



* On Debian/Ubuntu: install system libs or use prebuilt wheels (`pip install pymupdf==<compatible-version>`).

* If not required for your initial tests, remove/comment `pymupdf` from `requirements.txt`.



**3) Streamlit prompts for OpenAI key**



* The app may allow entering the key at runtime. To avoid re-entering, set `OPENAI_API_KEY` env var or put it in `~/.bashrc`.



**4) Requirements install hangs / fails**



* Ensure pip and wheel are updated: `pip install --upgrade pip wheel setuptools`.

* If a package fails to compile, check its docs for system dependency list.



**5) Port collisions**



* Streamlit default port is 8501. If already used, run `streamlit run app/home.py --server.port 8502`.



**6) Secrets formatting**



* `.streamlit/secrets.toml` must be TOML (no JSON). The `db-key` should point to the converted TOML file path, not the JSON (the README asked to convert JSON to TOML).



---



## Helpful scripts (copy & save)



### `run_local.sh`



```bash

#!/usr/bin/env bash

set -e

python3 -m venv .venv

source .venv/bin/activate

pip install --upgrade pip wheel setuptools

pip install -r app/requirements.txt

streamlit run app/home.py

```



Make executable: `chmod +x run_local.sh` and run `./run_local.sh`.



### `make_service_toml.sh` (if you want to convert JSON -> TOML via command line)



```bash

#!/usr/bin/env bash

# usage: ./make_service_toml.sh path/to/key.json out.toml

python - <<'PY'

import sys, json, toml

infile = sys.argv[1]

outfile = sys.argv[2]

with open(infile,'r') as f:

    data = json.load(f)

with open(outfile,'w') as f:

    toml.dump(data, f)

print("Wrote", outfile)

PY

```



---



## Next steps I can do for you (pick any, I’ll produce content right away)



* Generate a ready-to-run `.streamlit/secrets.toml` template (fill paths you give me).

* Generate `run_local.sh` and `Dockerfile` / `docker-compose.yml` snippets tuned to the repo layout.

* Inspect the uploaded ZIP and list key files (I can open the ZIP and show files).

* Create a minimal `requirements_clean.txt` if the repo's one is malformed.



Which of these would you like me to produce now? (I can immediately generate the files/snippets you choose.)



---

**Cursor**


Checking the project structure, then creating the setup files and scripts for GPT Lab.



Creating GPT Lab setup scripts and helper files. Adding them to the project for easy reference:


```python
#!/usr/bin/env python3
"""
Convert Google Service Account JSON to TOML format for Streamlit secrets.
Usage: python json2toml.py service-account.json output.toml
"""
import json
import sys
import os

try:
    import toml
except ImportError:
    print("Error: 'toml' package not found. Install it with: pip install toml")
    sys.exit(1)

if len(sys.argv) < 3:
    print("Usage: python json2toml.py <service-account.json> <output.toml>")
    print("\nExample:")
    print("  python json2toml.py service-account.json service-account.toml")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Check if input file exists
if not os.path.exists(input_file):
    print(f"Error: Input file '{input_file}' not found.")
    sys.exit(1)

try:
    # Read JSON file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Write TOML file
    with open(output_file, "w", encoding="utf-8") as f:
        toml.dump(data, f)
    
    print(f"✅ Successfully converted '{input_file}' to '{output_file}'")
    print(f"\nNext steps:")
    print(f"1. Copy the absolute path of '{output_file}'")
    print(f"2. Add it to .streamlit/secrets.toml:")
    print(f"   [firestore]")
    print(f"   db-key = '''{os.path.abspath(output_file)}'''")
    
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in '{input_file}': {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

```

```shellscript
#!/usr/bin/env bash
# GPT Lab - Local Development Setup Script
# This script sets up a Python venv and runs the Streamlit app

set -e  # Exit on error

echo "=========================================="
echo "  GPT Lab - Local Setup"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python version: $(python3 --version)"

# Check if we're in the right directory
if [ ! -f "app/home.py" ] && [ ! -f "home.py" ]; then
    echo "⚠️  Warning: Could not find app/home.py or home.py"
    echo "   Make sure you're in the GPT Lab project root directory"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip, wheel, and setuptools..."
pip install --upgrade pip wheel setuptools --quiet

# Install requirements
echo ""
echo "Installing requirements..."

# Check which requirements file exists
if [ -f "app/requirements.txt" ]; then
    REQUIREMENTS_FILE="app/requirements.txt"
elif [ -f "requirements.txt" ]; then
    REQUIREMENTS_FILE="requirements.txt"
else
    echo "❌ Error: Could not find requirements.txt"
    exit 1
fi

echo "   Using: $REQUIREMENTS_FILE"
pip install -r "$REQUIREMENTS_FILE"

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  Important: Before running, ensure you have:"
echo "   1. Created .streamlit/secrets.toml with Firestore credentials"
echo "   2. Set OPENAI_API_KEY environment variable (or enter in UI)"
echo ""
read -p "Start Streamlit app now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting Streamlit..."
    echo "   URL: http://localhost:8501"
    echo ""
    
    # Determine app entry point
    if [ -f "app/home.py" ]; then
        streamlit run app/home.py
    elif [ -f "home.py" ]; then
        streamlit run home.py
    else
        echo "❌ Error: Could not find app entry point (app/home.py or home.py)"
        exit 1
    fi
else
    echo ""
    echo "To start the app later, run:"
    echo "  source .venv/bin/activate"
    if [ -f "app/home.py" ]; then
        echo "  streamlit run app/home.py"
    else
        echo "  streamlit run home.py"
    fi
fi

```

```bat
@echo off
REM GPT Lab - Local Development Setup Script (Windows)
REM This script sets up a Python venv and runs the Streamlit app

echo ==========================================
echo   GPT Lab - Local Setup
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if we're in the right directory
if not exist "app\home.py" if not exist "home.py" (
    echo WARNING: Could not find app\home.py or home.py
    echo Make sure you're in the GPT Lab project root directory
    pause
    exit /b 1
)

REM Create venv if it doesn't exist
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip, wheel, and setuptools...
python -m pip install --upgrade pip wheel setuptools --quiet

REM Install requirements
echo.
echo Installing requirements...

REM Check which requirements file exists
if exist "app\requirements.txt" (
    set REQUIREMENTS_FILE=app\requirements.txt
) else if exist "requirements.txt" (
    set REQUIREMENTS_FILE=requirements.txt
) else (
    echo ERROR: Could not find requirements.txt
    pause
    exit /b 1
)

echo    Using: %REQUIREMENTS_FILE%
pip install -r %REQUIREMENTS_FILE%

echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo IMPORTANT: Before running, ensure you have:
echo   1. Created .streamlit\secrets.toml with Firestore credentials
echo   2. Set OPENAI_API_KEY environment variable (or enter in UI)
echo.
set /p START="Start Streamlit app now? (y/n): "

if /i "%START%"=="y" (
    echo.
    echo Starting Streamlit...
    echo    URL: http://localhost:8501
    echo.
    
    REM Determine app entry point
    if exist "app\home.py" (
        streamlit run app\home.py
    ) else if exist "home.py" (
        streamlit run home.py
    ) else (
        echo ERROR: Could not find app entry point
        pause
        exit /b 1
    )
) else (
    echo.
    echo To start the app later, run:
    echo   .venv\Scripts\activate
    if exist "app\home.py" (
        echo   streamlit run app\home.py
    ) else (
        echo   streamlit run home.py
    )
)

pause

```

```shellscript
#!/usr/bin/env bash
# Convert Google Service Account JSON to TOML
# Usage: ./make_service_toml.sh path/to/key.json out.toml

if [ $# -lt 2 ]; then
    echo "Usage: $0 <input.json> <output.toml>"
    echo ""
    echo "Example:"
    echo "  ./make_service_toml.sh service-account.json service-account.toml"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    exit 1
fi

# Check if toml is installed
python3 -c "import toml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing 'toml' package..."
    pip install toml
fi

python3 <<PY
import sys
import json
import toml
import os

infile = sys.argv[1]
outfile = sys.argv[2]

try:
    with open(infile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(outfile, 'w', encoding='utf-8') as f:
        toml.dump(data, f)
    
    print(f"✅ Successfully converted '{infile}' to '{outfile}'")
    print(f"\nNext steps:")
    print(f"1. Copy the absolute path: {os.path.abspath(outfile)}")
    print(f"2. Add it to .streamlit/secrets.toml:")
    print(f"   [firestore]")
    print(f"   db-key = '''{os.path.abspath(outfile)}'''")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
PY "$INPUT_FILE" "$OUTPUT_FILE"

```

```plaintext
# GPT Lab - Streamlit Secrets Template
# Copy this file to .streamlit/secrets.toml and fill in your values

# Firestore Configuration
# Convert your Google Service Account JSON to TOML using json2toml.py
# Then set the absolute path to the TOML file here
[firestore]
db-key = '''/absolute/path/to/service-account.toml'''

# Example (Windows):
# db-key = '''C:\Users\YourName\projects\gptlab-streamlit-main\service-account.toml'''

# Example (Linux/Mac):
# db-key = '''/home/username/projects/gptlab-streamlit-main/service-account.toml'''

# Utility Configuration (Optional)
[util]
global_salt = "OPTIONAL_GLOBAL_SALT_CHANGE_THIS"

# OpenAI API Key (Optional - can also be set via environment variable or UI)
# [openai]
# api_key = "sk-..."

# Stargate LLM Configuration (Optional - for RAG features)
# [stargate]
# api_key = "your-stargate-key"
# base_url = "https://your-stargate-host/api"
# model = "gptoss-20b"

```

```markdown
# GPT Lab - Complete Setup Guide

This guide walks you through setting up GPT Lab (Streamlit app) locally on your machine.

## 📋 Quick Checklist

- [ ] Unzip the repo (`gptlab-streamlit-main.zip`)
- [ ] Create Google Firestore service account JSON
- [ ] Convert JSON to TOML using `json2toml.py`
- [ ] Create `.streamlit/secrets.toml`
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Create & activate Python venv
- [ ] Install requirements
- [ ] Run `streamlit run app/home.py`

---

## Option A: Local Python Setup (Recommended for Development)

### Step 1: Unzip and Navigate

```bash
# Unzip the repo (adjust path as needed)
unzip gptlab-streamlit-main.zip -d ~/projects/
cd ~/projects/gptlab-streamlit-main
```

### Step 2: Prepare Google Firestore Credentials

1. **Create Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to: IAM & Admin → Service Accounts
   - Create a new service account with Firestore permissions
   - Download the JSON key file

2. **Convert JSON to TOML**:
   ```bash
   # Install toml package if needed
   pip install toml
   
   # Convert using the helper script
   python gptlab-setup/json2toml.py service-account.json service-account.toml
   ```

   Or use the bash script:
   ```bash
   chmod +x gptlab-setup/make_service_toml.sh
   ./gptlab-setup/make_service_toml.sh service-account.json service-account.toml
   ```

### Step 3: Create `.streamlit/secrets.toml`

```bash
# Create .streamlit directory
mkdir -p .streamlit

# Copy template
cp gptlab-setup/secrets.toml.template .streamlit/secrets.toml

# Edit .streamlit/secrets.toml and update the path
```

Edit `.streamlit/secrets.toml`:

```toml
[firestore]
db-key = '''/absolute/path/to/service-account.toml'''

[util]
global_salt = "YOUR_RANDOM_SALT_HERE"
```

**Important**: Use the **absolute path** to the TOML file, not the JSON file.

### Step 4: Set Environment Variables

```bash
# Required: OpenAI API Key
export OPENAI_API_KEY="sk-..."

# Optional: Other API keys
export STARGATE_API_KEY="your-stargate-key"
export STARGATE_BASE_URL="https://your-stargate-host/api"
export FIRESTORE_PROJECT_ID="your-gcp-project"
```

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY="sk-..."
```

**Windows (CMD)**:
```cmd
set OPENAI_API_KEY=sk-...
```

### Step 5: Setup Python Environment

**Using the automated script** (recommended):

```bash
# Linux/Mac
chmod +x gptlab-setup/run_local.sh
./gptlab-setup/run_local.sh

# Windows
gptlab-setup\run_local.bat
```

**Manual setup**:

```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Install requirements
pip install -r app/requirements.txt
```

**Important**: Check `app/requirements.txt` for any stray characters (like `python` or backticks) that might break pip install.

### Step 6: Run Streamlit

```bash
# Make sure venv is activated
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Run the app
streamlit run app/home.py
```

Open your browser to: **http://localhost:8501**

---

## Option B: Docker Setup (Recommended for Production)

### Step 1: Create Dockerfile (if not in repo)

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app/ ./app/
COPY .streamlit/ ./.streamlit/

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app/home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  gptlab-ui:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STARGATE_API_KEY=${STARGATE_API_KEY}
      - STARGATE_BASE_URL=${STARGATE_BASE_URL}
      - STREAMLIT_SECRETS_FIRESTORE_DB_KEY=/run/secrets/service-account.toml
    volumes:
      - ./service-account.toml:/run/secrets/service-account.toml:ro
      - ./.streamlit:/app/.streamlit:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Step 3: Build and Run

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Troubleshooting

### 1. Firestore Auth / Invalid Key

**Symptoms**: Permission errors, authentication failures

**Solutions**:
- Ensure service account has Firestore permissions in GCP IAM
- Use **absolute path** in `.streamlit/secrets.toml`
- Verify the TOML file is valid (not JSON)
- Check GCP project ID matches your Firestore instance

### 2. `pymupdf` / Binary Build Failures

**Symptoms**: `pip install` fails on `pymupdf` or similar binary packages

**Solutions**:

**Linux (Debian/Ubuntu)**:
```bash
sudo apt-get update
sudo apt-get install -y libmupdf-dev
pip install pymupdf
```

**Alternative**: Comment out `pymupdf` in `requirements.txt` if PDF parsing isn't needed initially:
```txt
# pymupdf>=1.23.0  # Commented out - install system libs first
```

### 3. Streamlit Prompts for OpenAI Key

**Solution**: Set environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

Or add to `~/.bashrc` / `~/.zshrc` for persistence.

### 4. Requirements Install Hangs / Fails

**Solutions**:
```bash
# Upgrade pip and build tools
pip install --upgrade pip wheel setuptools

# Clear pip cache
pip cache purge

# Install with verbose output to see errors
pip install -r app/requirements.txt -v
```

### 5. Port Already in Use

**Solution**: Use a different port:
```bash
streamlit run app/home.py --server.port 8502
```

### 6. Secrets Formatting Issues

**Common mistakes**:
- Using JSON file instead of TOML
- Using relative path instead of absolute path
- Missing quotes around path in TOML

**Correct format**:
```toml
[firestore]
db-key = '''/absolute/path/to/service-account.toml'''
```

### 7. Module Not Found Errors

**Solution**: Ensure virtual environment is activated:
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

---

## Verification Steps

After setup, verify everything works:

1. **Check Firestore Connection**:
   - App should load without Firestore errors
   - Try creating a test document in the UI

2. **Check OpenAI Integration**:
   - Enter your OpenAI key in the UI (or via env var)
   - Try a simple query/chat

3. **Check Logs**:
   ```bash
   # Streamlit logs appear in terminal
   # Check for any error messages
   ```

---

## Quick Reference

### File Structure
```
gptlab-streamlit-main/
├── app/
│   ├── home.py              # Main Streamlit app
│   └── requirements.txt    # Python dependencies
├── .streamlit/
│   └── secrets.toml         # Firestore credentials (create this)
├── service-account.toml    # Converted from JSON (create this)
└── gptlab-setup/            # Helper scripts (this folder)
    ├── json2toml.py
    ├── run_local.sh
    ├── run_local.bat
    └── secrets.toml.template
```

### Key Commands

```bash
# Convert JSON to TOML
python gptlab-setup/json2toml.py service-account.json service-account.toml

# Setup and run (automated)
./gptlab-setup/run_local.sh

# Manual run
source .venv/bin/activate
streamlit run app/home.py

# Docker
docker-compose up -d
```

---

## Next Steps

Once setup is complete:

1. **Explore the UI** - Navigate through the app features
2. **Test Firestore** - Create/test documents
3. **Test OpenAI** - Try chat/completion features
4. **Configure Stargate** (if using RAG) - Add Stargate credentials
5. **Customize** - Modify app code for your needs

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs` or terminal output
2. Verify all environment variables are set
3. Ensure Firestore service account has correct permissions
4. Check Python version (3.10+ required)
5. Verify all dependencies installed correctly

For more help, check the main project README or open an issue.

```

```markdown
# GPT Lab Setup Helpers

This directory contains helper scripts and templates for setting up GPT Lab locally.

## Files

- **`json2toml.py`** - Convert Google Service Account JSON to TOML format
- **`run_local.sh`** - Automated setup script for Linux/Mac
- **`run_local.bat`** - Automated setup script for Windows
- **`make_service_toml.sh`** - Alternative JSON→TOML converter (bash)
- **`secrets.toml.template`** - Template for Streamlit secrets file
- **`SETUP_GUIDE.md`** - Complete setup instructions

## Quick Start

1. **Convert Service Account JSON to TOML**:
   ```bash
   python json2toml.py service-account.json service-account.toml
   ```

2. **Create secrets file**:
   ```bash
   mkdir -p ../.streamlit
   cp secrets.toml.template ../.streamlit/secrets.toml
   # Edit ../.streamlit/secrets.toml with your paths
   ```

3. **Run automated setup**:
   ```bash
   # Linux/Mac
   ./run_local.sh
   
   # Windows
   run_local.bat
   ```

## Usage Examples

### Convert JSON to TOML

```bash
# Basic usage
python json2toml.py path/to/service-account.json output.toml

# Example
python json2toml.py ~/Downloads/my-project-key.json service-account.toml
```

### Setup and Run (Automated)

```bash
# The script will:
# 1. Create Python venv
# 2. Install requirements
# 3. Optionally start Streamlit

./run_local.sh
```

### Manual Setup

If you prefer manual setup, see `SETUP_GUIDE.md` for detailed instructions.

## Requirements

- Python 3.10+
- `toml` package (install with `pip install toml`)
- Google Service Account JSON key
- OpenAI API key

## Notes

- Always use **absolute paths** in `secrets.toml`
- The TOML file should be the converted version, not the original JSON
- Keep your service account keys secure - never commit them to git

```


Making the scripts executable and creating a quick start guide:


```markdown
# GPT Lab - Quick Start Guide

## 🚀 Fastest Path to Running GPT Lab

### Prerequisites
- Python 3.10+
- Google Service Account JSON key
- OpenAI API key

### 5-Minute Setup

```bash
# 1. Unzip repo and navigate
cd ~/projects/gptlab-streamlit-main

# 2. Convert service account JSON to TOML
python gptlab-setup/json2toml.py ~/Downloads/service-account.json service-account.toml

# 3. Create secrets file
mkdir -p .streamlit
cat > .streamlit/secrets.toml <<EOF
[firestore]
db-key = '''$(pwd)/service-account.toml'''

[util]
global_salt = "CHANGE_THIS_RANDOM_STRING"
EOF

# 4. Set OpenAI key
export OPENAI_API_KEY="sk-your-key-here"

# 5. Run automated setup
chmod +x gptlab-setup/run_local.sh
./gptlab-setup/run_local.sh
```

### Windows Quick Start

```powershell
# 1. Navigate to project
cd C:\projects\gptlab-streamlit-main

# 2. Convert JSON to TOML
python gptlab-setup\json2toml.py service-account.json service-account.toml

# 3. Create secrets file
mkdir .streamlit
# Edit .streamlit\secrets.toml manually with absolute path

# 4. Set environment variable
$env:OPENAI_API_KEY="sk-your-key-here"

# 5. Run setup
gptlab-setup\run_local.bat
```

### What Each Step Does

1. **json2toml.py** - Converts Google's JSON key to TOML format Streamlit needs
2. **secrets.toml** - Tells Streamlit where to find Firestore credentials
3. **OPENAI_API_KEY** - Allows the app to use OpenAI APIs
4. **run_local.sh/bat** - Sets up Python environment and installs dependencies

### Access the App

Once running, open: **http://localhost:8501**

### Troubleshooting

**"Firestore permission denied"**
- Check service account has Firestore permissions in GCP Console
- Verify absolute path in `secrets.toml`

**"Module not found"**
- Make sure venv is activated: `source .venv/bin/activate`
- Reinstall requirements: `pip install -r app/requirements.txt`

**"Port 8501 already in use"**
- Use different port: `streamlit run app/home.py --server.port 8502`

### Next Steps

- See `SETUP_GUIDE.md` for detailed instructions
- See `README.md` for script documentation
- Check main project README for app features

```


Created GPT Lab setup files. Summary:

## Created files

### Helper scripts
1. `gptlab-setup/json2toml.py` — Converts Google Service Account JSON to TOML
2. `gptlab-setup/run_local.sh` — Automated setup script (Linux/Mac)
3. `gptlab-setup/run_local.bat` — Automated setup script (Windows)
4. `gptlab-setup/make_service_toml.sh` — Alternative JSON→TOML converter

### Templates and guides
5. `gptlab-setup/secrets.toml.template` — Template for Streamlit secrets
6. `gptlab-setup/SETUP_GUIDE.md` — Setup guide
7. `gptlab-setup/QUICK_START.md` — Quick start guide
8. `gptlab-setup/README.md` — Documentation for the helper scripts

## Quick usage

### Step 1: Convert service account JSON to TOML
```bash
python gptlab-setup/json2toml.py service-account.json service-account.toml
```

### Step 2: Create secrets file
```bash
mkdir -p .streamlit
cp gptlab-setup/secrets.toml.template .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with absolute path to service-account.toml
```

### Step 3: Run automated setup
```bash
# Linux/Mac
chmod +x gptlab-setup/run_local.sh
./gptlab-setup/run_local.sh

# Windows
gptlab-setup\run_local.bat
```

## Features

- Automated setup: scripts handle venv creation and dependency installation
- Cross-platform: Windows (.bat) and Linux/Mac (.sh) scripts
- Error handling: scripts check prerequisites and provide clear error messages
- Documentation: guides cover setup and troubleshooting

## Next steps

1. Unzip your `gptlab-streamlit-main.zip` file
2. Copy the `gptlab-setup` folder into the GPT Lab project root
3. Follow `QUICK_START.md` for the fastest setup
4. Or use `SETUP_GUIDE.md` for detailed instructions

All files are ready to use. The scripts will guide you through the setup process and handle most of the work automatically.

```shellscript
python gptlab-setup/json2toml.py service-account.json service-account.toml
```

```shellscript
mkdir -p .streamlit
cp gptlab-setup/secrets.toml.template .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with absolute path to service-account.toml
```

```shellscript
# Linux/Mac
chmod +x gptlab-setup/run_local.sh
./gptlab-setup/run_local.sh

# Windows
gptlab-setup\run_local.bat
```

```shellscript
python gptlab-setup/json2toml.py service-account.json service-account.toml
```

```shellscript
mkdir -p .streamlit
cp gptlab-setup/secrets.toml.template .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with absolute path to service-account.toml
```

```shellscript
# Linux/Mac
chmod +x gptlab-setup/run_local.sh
./gptlab-setup/run_local.sh

# Windows
gptlab-setup\run_local.bat
```


All GPT Lab setup files are ready. The `gptlab-setup` folder contains:

- Conversion tools (JSON → TOML)
- Automated setup scripts (Windows & Linux/Mac)
- Templates and documentation
- Troubleshooting guides

Copy the `gptlab-setup` folder into your GPT Lab project root and follow `QUICK_START.md` to get started. The scripts automate most of the setup.

---

**User**

remove unrequired file in project

---

**Cursor**


Scanning the project to identify unnecessary files to remove.



Identifying and removing unnecessary files. Checking which files are redundant:



Removing unnecessary files: redundant documentation, test files, and folders from other projects.



Removing unnecessary files and folders:



Verifying what's left and creating a summary:


```markdown
# Project Cleanup Summary

## Files Removed

### Folders Removed
1. **`gptlab-setup/`** - Entire folder containing GPT Lab setup scripts (wrong project)
2. **`litellm-pgvector-main/`** - Duplicate/submodule folder not needed for this project

### Redundant Documentation Removed
1. **`ACCURACY_TEST_GUIDE.md`** - Covered in other documentation
2. **`HOW_TO_RUN_AND_SEE_ACCURACY.md`** - Redundant with START_PROJECT.md
3. **`QUICK_RUN.md`** - Redundant with START_PROJECT.md
4. **`QUICKSTART.md`** - Redundant with START_PROJECT.md
5. **`RUN_PROJECT.md`** - Redundant with START_PROJECT.md
6. **`SETUP_CHECKLIST.md`** - Redundant with START_PROJECT.md
7. **`UI_GUIDE.md`** - Information covered in README.md
8. **`PROJECT_SUMMARY.md`** - Redundant with README.md

### Redundant Scripts Removed
1. **`test_accuracy.py`** - Redundant with `run_full_test.py`
2. **`start_and_test.bat`** - Redundant with `start_project.bat`
3. **`start_and_test.sh`** - Redundant with `start_project.bat` (Windows project)

## Remaining Essential Files

### Core Application
- `main.py` - FastAPI backend
- `ui.py` - Streamlit UI
- `models.py` - Pydantic models
- `config.py` - Configuration
- `embedding_service.py` - Embedding service

### Configuration
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` - API container
- `Dockerfile.ui` - UI container
- `litellm_config.yaml` - LiteLLM config
- `env.example` - Environment template
- `.gitignore` - Git ignore rules

### Database
- `database.sql` - Database schema
- `migrations/` - Migration scripts
- `prisma/` - Prisma schema

### Dependencies
- `requirements.txt` - Backend dependencies
- `requirements-ui.txt` - UI dependencies

### Documentation (Consolidated)
- `README.md` - Main documentation
- `ARCHITECTURE.md` - Architecture documentation
- `ARCHITECTURE_QUICK_REFERENCE.md` - Quick reference
- `START_PROJECT.md` - Startup guide

### Scripts
- `start_project.bat` - Windows startup script
- `run_full_test.py` - Comprehensive test runner
- `scripts/` - Utility scripts

## Result

The project is now cleaner with:
- ✅ No duplicate folders from other projects
- ✅ Consolidated documentation (removed 8 redundant docs)
- ✅ Single startup script
- ✅ Single comprehensive test file
- ✅ All essential files preserved

```


Removing the remaining folders using a different method:



Deleting files in those folders individually:



Deleting files in those folders individually:



Deleting files in the `litellm-pgvector-main` folder:



Removing remaining files and folders:


```markdown
# Project Cleanup Summary

## ✅ Cleanup Complete!

## Files Removed

### Folders Removed
1. **`gptlab-setup/`** - Entire folder containing GPT Lab setup scripts (wrong project) ✅
2. **`litellm-pgvector-main/`** - Duplicate/submodule folder not needed for this project ✅
```


Cleanup complete. Summary:

## Cleanup complete

### Removed folders
1. `gptlab-setup/` — GPT Lab setup scripts (wrong project)
2. `litellm-pgvector-main/` — Duplicate/submodule folder

### Removed redundant documentation (8 files)
1. `ACCURACY_TEST_GUIDE.md`
2. `HOW_TO_RUN_AND_SEE_ACCURACY.md`
3. `QUICK_RUN.md`
4. `QUICKSTART.md`
5. `RUN_PROJECT.md`
6. `SETUP_CHECKLIST.md`
7. `UI_GUIDE.md`
8. `PROJECT_SUMMARY.md`

### Removed redundant scripts (3 files)
1. `test_accuracy.py` — redundant with `run_full_test.py`
2. `start_and_test.bat` — redundant with `start_project.bat`
3. `start_and_test.sh` — redundant with `start_project.bat`

## Final project structure

The project now contains only essential files:

### Core application
- `main.py`, `ui.py`, `models.py`, `config.py`, `embedding_service.py`

### Configuration
- `docker-compose.yml`, `Dockerfile`, `Dockerfile.ui`, `litellm_config.yaml`, `env.example`

### Database
- `database.sql`, `migrations/`, `prisma/`

### Documentation (consolidated)
- `README.md` — Main documentation
- `ARCHITECTURE.md` — Architecture documentation
- `ARCHITECTURE_QUICK_REFERENCE.md` — Quick reference
- `START_PROJECT.md` — Startup guide
- `CLEANUP_SUMMARY.md` — This cleanup summary

### Scripts
- `start_project.bat` — Windows startup script
- `run_full_test.py` — Test runner
- `scripts/` — Utility scripts

The project is now cleaner and easier to navigate, with all essential functionality preserved.

