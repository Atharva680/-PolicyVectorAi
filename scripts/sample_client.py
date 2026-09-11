"""
Sample client script for testing the OpenAI Vector Stores API.
Demonstrates how to use all the endpoints.
"""
import requests
import json
import time
from typing import Optional, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Change this to match your SERVER_API_KEY


class VectorStoreClient:
    """Client for interacting with the Vector Store API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_vector_store(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """Create a new vector store"""
        url = f"{self.base_url}/v1/vector_stores"
        payload = {
            "name": name,
            "metadata": metadata or {}
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_vector_stores(self, limit: int = 20, after: Optional[str] = None) -> Dict:
        """List vector stores"""
        url = f"{self.base_url}/v1/vector_stores"
        params = {"limit": limit}
        if after:
            params["after"] = after
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def create_embedding(
        self,
        vector_store_id: str,
        content: str,
        embedding: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Add a single embedding to a vector store"""
        url = f"{self.base_url}/v1/vector_stores/{vector_store_id}/embeddings"
        payload = {
            "content": content,
            "metadata": metadata or {}
        }
        if embedding:
            payload["embedding"] = embedding
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_embeddings_batch(
        self,
        vector_store_id: str,
        embeddings: list
    ) -> Dict:
        """Add multiple embeddings in batch"""
        url = f"{self.base_url}/v1/vector_stores/{vector_store_id}/embeddings/batch"
        payload = {"embeddings": embeddings}
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search(
        self,
        vector_store_id: str,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        return_metadata: bool = True
    ) -> Dict:
        """Search a vector store"""
        url = f"{self.base_url}/v1/vector_stores/{vector_store_id}/search"
        payload = {
            "query": query,
            "limit": limit,
            "return_metadata": return_metadata
        }
        if filters:
            payload["filters"] = filters
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict:
        """Check API health"""
        url = f"{self.base_url}/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the Vector Store API"""
    client = VectorStoreClient(API_BASE_URL, API_KEY)
    
    print("=" * 60)
    print("OpenAI Vector Stores API - Sample Client")
    print("=" * 60)
    
    # Health check
    print("\n1. Health Check")
    try:
        health = client.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Database: {health.get('database')}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Create a vector store
    print("\n2. Creating Vector Store")
    try:
        vector_store = client.create_vector_store(
            name="Sample Knowledge Base",
            metadata={"category": "documentation", "version": "1.0"}
        )
        vector_store_id = vector_store["id"]
        print(f"   Created vector store: {vector_store_id}")
        print(f"   Name: {vector_store['name']}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Add embeddings (without providing embeddings - they will be generated)
    print("\n3. Adding Embeddings (text-only, embeddings will be generated)")
    documents = [
        {
            "content": "Python is a high-level programming language known for its simplicity.",
            "metadata": {"topic": "programming", "language": "python"}
        },
        {
            "content": "FastAPI is a modern web framework for building APIs with Python.",
            "metadata": {"topic": "web development", "framework": "fastapi"}
        },
        {
            "content": "PostgreSQL is a powerful open-source relational database system.",
            "metadata": {"topic": "database", "type": "relational"}
        },
        {
            "content": "Vector embeddings represent text as numerical vectors in high-dimensional space.",
            "metadata": {"topic": "machine learning", "concept": "embeddings"}
        },
        {
            "content": "PGVector is a PostgreSQL extension for storing and searching vector embeddings.",
            "metadata": {"topic": "database", "extension": "pgvector"}
        }
    ]
    
    embeddings_list = []
    for doc in documents:
        embeddings_list.append({
            "content": doc["content"],
            "metadata": doc["metadata"]
            # Note: embedding is not provided - will be generated by the API
        })
    
    try:
        batch_response = client.create_embeddings_batch(
            vector_store_id=vector_store_id,
            embeddings=embeddings_list
        )
        print(f"   Added {len(batch_response['data'])} embeddings")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Wait a bit for indexing
    print("\n4. Waiting for indexing...")
    time.sleep(2)
    
    # Search
    print("\n5. Searching Vector Store")
    search_queries = [
        "What is Python?",
        "Tell me about databases",
        "What frameworks are available?"
    ]
    
    for query in search_queries:
        try:
            results = client.search(
                vector_store_id=vector_store_id,
                query=query,
                limit=3
            )
            print(f"\n   Query: '{query}'")
            print(f"   Found {len(results['data'])} results:")
            for i, result in enumerate(results['data'], 1):
                print(f"   {i}. Score: {result['score']:.3f}")
                print(f"      Content: {result['content'][0]['text'][:80]}...")
                if result.get('attributes'):
                    print(f"      Metadata: {result['attributes']}")
        except Exception as e:
            print(f"   Error searching: {e}")
    
    # Search with filters
    print("\n6. Searching with Metadata Filters")
    try:
        results = client.search(
            vector_store_id=vector_store_id,
            query="database systems",
            limit=5,
            filters={"topic": "database"}
        )
        print(f"   Found {len(results['data'])} results with topic='database':")
        for i, result in enumerate(results['data'], 1):
            print(f"   {i}. {result['content'][0]['text'][:80]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # List vector stores
    print("\n7. Listing Vector Stores")
    try:
        stores = client.list_vector_stores(limit=10)
        print(f"   Found {len(stores['data'])} vector stores:")
        for store in stores['data']:
            print(f"   - {store['name']} (ID: {store['id']})")
            print(f"     Files: {store['file_counts']['total']}, Bytes: {store['usage_bytes']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Sample client demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

