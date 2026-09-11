"""
Streamlit UI for Policy Q&A System
Provides interface for managing vector stores, ingesting policies, searching, and RAG chat.
"""
import streamlit as st
import os
import json
import httpx
from typing import List, Dict, Any, Optional
from openai import OpenAI
import docx
try:
    import pypdf
except ImportError:
    try:
        import PyPDF2 as pypdf
    except ImportError:
        pypdf = None
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Policy Q&A System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration from environment variables
API_BASE_URL = os.getenv("STREAMLIT__API_BASE", "http://localhost:8000")
API_KEY = os.getenv("STREAMLIT__API_KEY", os.getenv("OPENAI_API_KEY", "sk-local-xyz"))
EMBED_BASE_URL = os.getenv("STREAMLIT__EMBED_BASE", "http://localhost:4000")
EMBED_MODEL = os.getenv("STREAMLIT__EMBED_MODEL", "text-embedding-ada-002")
STARGATE_API_KEY = os.getenv("STARGATE_API_KEY", "")
STARGATE_BASE_URL = os.getenv("STARGATE_BASE_URL", "")
STARGATE_MODEL = os.getenv("STARGATE_MODEL", "gptoss-20b")
MCP_BASE_URL = os.getenv("MCP__BASE_URL", "http://localhost:7070")
MCP_SEARCH_TOOL = os.getenv("MCP__SEARCH_TOOL", "policy_search")
MCP_FETCH_TOOL = os.getenv("MCP__FETCH_TOOL", "policy_fetch")

# Initialize OpenAI client for API calls
api_client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY
)

# Initialize Stargate client if configured
stargate_client = None
if STARGATE_API_KEY and STARGATE_BASE_URL:
    stargate_client = OpenAI(
        base_url=STARGATE_BASE_URL,
        api_key=STARGATE_API_KEY
    )


def make_api_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None):
    """Make authenticated API request"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    with httpx.Client(timeout=30.0) as client:
        if method == "GET":
            response = client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = client.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()


def list_vector_stores():
    """List all vector stores"""
    try:
        response = make_api_request("GET", "/v1/vector_stores", params={"limit": 100})
        return response.get("data", [])
    except Exception as e:
        st.error(f"Error listing vector stores: {str(e)}")
        return []


def create_vector_store(name: str, metadata: Optional[Dict] = None):
    """Create a new vector store"""
    try:
        data = {"name": name}
        if metadata:
            data["metadata"] = metadata
        response = make_api_request("POST", "/v1/vector_stores", data=data)
        return response
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None


def add_embeddings_batch(vector_store_id: str, embeddings_data: List[Dict]):
    """Add embeddings in batch"""
    try:
        data = {"embeddings": embeddings_data}
        response = make_api_request(
            "POST", 
            f"/v1/vector_stores/{vector_store_id}/embeddings/batch",
            data=data
        )
        return response
    except Exception as e:
        st.error(f"Error adding embeddings: {str(e)}")
        return None


def search_vector_store(vector_store_id: str, query: str, limit: int = 10):
    """Search vector store"""
    try:
        data = {
            "query": query,
            "limit": limit,
            "return_metadata": True
        }
        response = make_api_request(
            "POST",
            f"/v1/vector_stores/{vector_store_id}/search",
            data=data
        )
        return response
    except Exception as e:
        st.error(f"Error searching: {str(e)}")
        return None


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


def parse_docx(file) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error parsing DOCX: {str(e)}")
        return ""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def mcp_search(query: str) -> List[Dict]:
    """Search policies via MCP server"""
    try:
        url = f"{MCP_BASE_URL}/search"
        headers = {"Content-Type": "application/json"}
        data = {"query": query, "tool": MCP_SEARCH_TOOL}
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("results", [])
    except Exception as e:
        st.warning(f"MCP search failed: {str(e)}")
        return []


def mcp_fetch(doc_id: str) -> Optional[str]:
    """Fetch policy document via MCP server"""
    try:
        url = f"{MCP_BASE_URL}/fetch"
        headers = {"Content-Type": "application/json"}
        data = {"doc_id": doc_id, "tool": MCP_FETCH_TOOL}
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("content", "")
    except Exception as e:
        st.warning(f"MCP fetch failed: {str(e)}")
        return None


def generate_rag_answer(context: str, question: str) -> str:
    """Generate RAG answer using Stargate LLM"""
    if not stargate_client:
        return "Stargate API not configured. Please set STARGATE_API_KEY and STARGATE_BASE_URL in .env"
    
    try:
        prompt = f"""You are a helpful assistant that answers questions based on company policy documents.

Policy Context:
{context}

Question: {question}

Please provide a clear, accurate answer based only on the policy context provided above. If the context doesn't contain enough information to answer the question, say so."""

        response = stargate_client.chat.completions.create(
            model=STARGATE_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on company policy documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"


# Sidebar
with st.sidebar:
    st.title("📚 Policy Q&A System")
    st.markdown("---")
    
    # Configuration status
    st.subheader("Configuration")
    st.write(f"**API:** {API_BASE_URL}")
    st.write(f"**Embeddings:** {EMBED_BASE_URL}")
    if stargate_client:
        st.success("✅ Stargate LLM configured")
    else:
        st.warning("⚠️ Stargate LLM not configured")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["Stores", "Ingest", "Search", "RAG Chat"],
        label_visibility="collapsed"
    )


# Main content based on selected page
if page == "Stores":
    st.title("📦 Vector Stores Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Existing Stores")
        stores = list_vector_stores()
        
        if stores:
            for store in stores:
                with st.expander(f"📁 {store['name']} ({store['id'][:8]}...)"):
                    st.json(store)
        else:
            st.info("No vector stores found. Create one below.")
    
    with col2:
        st.subheader("Create New Store")
        with st.form("create_store"):
            store_name = st.text_input("Store Name", placeholder="e.g., HR Policies")
            metadata_json = st.text_area("Metadata (JSON)", placeholder='{"category": "hr"}', height=100)
            
            submitted = st.form_submit_button("Create Store", type="primary")
            
            if submitted:
                if store_name:
                    metadata = None
                    if metadata_json:
                        try:
                            metadata = json.loads(metadata_json)
                        except json.JSONDecodeError:
                            st.error("Invalid JSON in metadata field")
                            metadata = None
                    
                    result = create_vector_store(store_name, metadata)
                    if result:
                        st.success(f"✅ Created store: {result['name']}")
                        st.rerun()
                else:
                    st.error("Please provide a store name")


elif page == "Ingest":
    st.title("📥 Ingest Policy Documents")
    
    # Select vector store
    stores = list_vector_stores()
    if not stores:
        st.warning("Please create a vector store first in the Stores tab.")
        st.stop()
    
    store_options = {f"{s['name']} ({s['id'][:8]}...)": s['id'] for s in stores}
    selected_store_name = st.selectbox("Select Vector Store", list(store_options.keys()))
    selected_store_id = store_options[selected_store_name]
    
    st.markdown("---")
    
    # Ingest method selection
    ingest_method = st.radio(
        "Ingest Method",
        ["Paste Text", "Upload File", "MCP Fetch"],
        horizontal=True
    )
    
    if ingest_method == "Paste Text":
        st.subheader("Paste Policy Text")
        policy_text = st.text_area("Policy Content", height=300, placeholder="Paste your policy text here...")
        
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.number_input("Chunk Size", min_value=100, max_value=5000, value=1000, step=100)
        with col2:
            chunk_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=500, value=200, step=50)
        
        metadata_json = st.text_area("Metadata (JSON)", placeholder='{"category": "hr", "source": "manual"}', height=100)
        
        if st.button("Ingest Policy", type="primary"):
            if policy_text:
                # Parse metadata
                metadata = {}
                if metadata_json:
                    try:
                        metadata = json.loads(metadata_json)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in metadata field")
                        metadata = {}
                
                # Chunk text
                chunks = chunk_text(policy_text, chunk_size, chunk_overlap)
                
                # Prepare embeddings data
                embeddings_data = [
                    {
                        "content": chunk,
                        "metadata": {**metadata, "chunk_index": i, "total_chunks": len(chunks)}
                    }
                    for i, chunk in enumerate(chunks)
                ]
                
                # Show progress
                with st.spinner(f"Ingesting {len(chunks)} chunks..."):
                    result = add_embeddings_batch(selected_store_id, embeddings_data)
                    if result:
                        st.success(f"✅ Ingested {len(result.get('data', []))} chunks successfully!")
            else:
                st.error("Please provide policy text")
    
    elif ingest_method == "Upload File":
        st.subheader("Upload Policy File")
        uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
        
        if uploaded_file:
            file_type = uploaded_file.name.split(".")[-1].lower()
            st.write(f"**File:** {uploaded_file.name} ({file_type})")
            
            # Extract text based on file type
            text = ""
            if file_type == "txt":
                text = str(uploaded_file.read(), "utf-8")
            elif file_type == "pdf":
                text = parse_pdf(uploaded_file)
            elif file_type == "docx":
                text = parse_docx(uploaded_file)
            else:
                st.error(f"Unsupported file type: {file_type}")
                text = ""
            
            if text:
                st.text_area("Extracted Text", text[:1000] + "..." if len(text) > 1000 else text, height=200, disabled=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    chunk_size = st.number_input("Chunk Size", min_value=100, max_value=5000, value=1000, step=100, key="upload_chunk")
                with col2:
                    chunk_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=500, value=200, step=50, key="upload_overlap")
                
                metadata_json = st.text_area("Metadata (JSON)", placeholder=f'{{"category": "hr", "source": "{uploaded_file.name}"}}', height=100)
                
                if st.button("Ingest File", type="primary"):
                    # Parse metadata
                    metadata = {"filename": uploaded_file.name}
                    if metadata_json:
                        try:
                            metadata.update(json.loads(metadata_json))
                        except json.JSONDecodeError:
                            st.error("Invalid JSON in metadata field")
                    
                    # Chunk text
                    chunks = chunk_text(text, chunk_size, chunk_overlap)
                    
                    # Prepare embeddings data
                    embeddings_data = [
                        {
                            "content": chunk,
                            "metadata": {**metadata, "chunk_index": i, "total_chunks": len(chunks)}
                        }
                        for i, chunk in enumerate(chunks)
                    ]
                    
                    # Show progress
                    with st.spinner(f"Ingesting {len(chunks)} chunks..."):
                        result = add_embeddings_batch(selected_store_id, embeddings_data)
                        if result:
                            st.success(f"✅ Ingested {len(result.get('data', []))} chunks successfully!")
    
    elif ingest_method == "MCP Fetch":
        st.subheader("Fetch from MCP Server")
        search_query = st.text_input("Search Query", placeholder="Search for policies...")
        
        if st.button("Search MCP", type="primary"):
            if search_query:
                with st.spinner("Searching MCP server..."):
                    results = mcp_search(search_query)
                    
                    if results:
                        st.success(f"Found {len(results)} results")
                        for i, result in enumerate(results):
                            with st.expander(f"Result {i+1}: {result.get('title', 'Untitled')}"):
                                st.json(result)
                                
                                if st.button(f"Fetch & Ingest", key=f"fetch_{i}"):
                                    doc_id = result.get("id") or result.get("doc_id")
                                    if doc_id:
                                        content = mcp_fetch(doc_id)
                                        if content:
                                            # Chunk and ingest
                                            chunks = chunk_text(content, 1000, 200)
                                            embeddings_data = [
                                                {
                                                    "content": chunk,
                                                    "metadata": {
                                                        "source": "mcp",
                                                        "doc_id": doc_id,
                                                        "title": result.get("title", ""),
                                                        "chunk_index": j,
                                                        "total_chunks": len(chunks)
                                                    }
                                                }
                                                for j, chunk in enumerate(chunks)
                                            ]
                                            
                                            with st.spinner(f"Ingesting {len(chunks)} chunks..."):
                                                ingest_result = add_embeddings_batch(selected_store_id, embeddings_data)
                                                if ingest_result:
                                                    st.success(f"✅ Ingested {len(ingest_result.get('data', []))} chunks!")
                    else:
                        st.info("No results found")


elif page == "Search":
    st.title("🔍 Semantic Search")
    
    # Select vector store
    stores = list_vector_stores()
    if not stores:
        st.warning("Please create a vector store first in the Stores tab.")
        st.stop()
    
    store_options = {f"{s['name']} ({s['id'][:8]}...)": s['id'] for s in stores}
    selected_store_name = st.selectbox("Select Vector Store", list(store_options.keys()))
    selected_store_id = store_options[selected_store_name]
    
    st.markdown("---")
    
    # Search interface
    query = st.text_input("Search Query", placeholder="Enter your search query...")
    limit = st.slider("Number of Results", min_value=1, max_value=50, value=10)
    
    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Searching..."):
                results = search_vector_store(selected_store_id, query, limit)
                
                if results and results.get("data"):
                    st.success(f"Found {len(results['data'])} results")
                    
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
                else:
                    st.info("No results found")
        else:
            st.error("Please enter a search query")


elif page == "RAG Chat":
    st.title("💬 RAG Chat with Stargate LLM")
    
    if not stargate_client:
        st.error("⚠️ Stargate LLM not configured. Please set STARGATE_API_KEY and STARGATE_BASE_URL in .env")
        st.stop()
    
    # Select vector store
    stores = list_vector_stores()
    if not stores:
        st.warning("Please create a vector store first in the Stores tab.")
        st.stop()
    
    store_options = {f"{s['name']} ({s['id'][:8]}...)": s['id'] for s in stores}
    selected_store_name = st.selectbox("Select Vector Store", list(store_options.keys()))
    selected_store_id = store_options[selected_store_name]
    
    st.markdown("---")
    
    # Configuration
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("Top K Results", min_value=1, max_value=20, value=5)
    with col2:
        max_context_length = st.number_input("Max Context Length", min_value=500, max_value=8000, value=2000, step=500)
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about company policies..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate answer
        with st.chat_message("assistant"):
            with st.spinner("Searching policies and generating answer..."):
                # Search for relevant context
                search_results = search_vector_store(selected_store_id, prompt, top_k)
                
                if search_results and search_results.get("data"):
                    # Build context from top results
                    context_parts = []
                    total_length = 0
                    
                    for result in search_results['data']:
                        for chunk in result.get('content', []):
                            chunk_text = chunk.get('text', '')
                            if total_length + len(chunk_text) <= max_context_length:
                                context_parts.append(f"[Score: {result['score']:.3f}] {chunk_text}")
                                total_length += len(chunk_text)
                            else:
                                break
                        if total_length >= max_context_length:
                            break
                    
                    context = "\n\n".join(context_parts)
                    
                    # Generate answer using Stargate
                    answer = generate_rag_answer(context, prompt)
                    
                    # Display answer
                    st.markdown(answer)
                    
                    # Show sources
                    with st.expander("📚 Sources"):
                        for i, result in enumerate(search_results['data'][:top_k]):
                            filename = result.get('filename', f"Document {i+1}")
                            st.write(f"**{i+1}. {filename}** (Score: {result['score']:.3f})")
                            if result.get('attributes'):
                                st.caption(f"Metadata: {result['attributes']}")
                    
                    # Add assistant message
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = "No relevant policies found. Please try rephrasing your question."
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

