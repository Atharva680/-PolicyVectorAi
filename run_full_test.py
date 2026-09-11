"""
Complete test runner for the Vector Store API.
This script will:
1. Check if services are running
2. Create test data
3. Run comprehensive accuracy tests
4. Display detailed results
"""
import requests
import time
import json
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass

API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

# Test documents with known semantic relationships
TEST_DOCUMENTS = [
    {
        "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
        "metadata": {"topic": "programming", "language": "python", "category": "general", "id": "doc1"}
    },
    {
        "content": "FastAPI is a modern, fast web framework for building APIs with Python. It's based on standard Python type hints and provides automatic interactive API documentation with Swagger UI.",
        "metadata": {"topic": "web development", "framework": "fastapi", "language": "python", "id": "doc2"}
    },
    {
        "content": "PostgreSQL is a powerful open-source relational database management system. It supports advanced data types, ACID compliance, and offers excellent performance, reliability, and data integrity.",
        "metadata": {"topic": "database", "type": "relational", "category": "backend", "id": "doc3"}
    },
    {
        "content": "Vector embeddings are numerical representations of text that capture semantic meaning. They enable semantic search and similarity matching in high-dimensional space using cosine similarity.",
        "metadata": {"topic": "machine learning", "concept": "embeddings", "category": "ai", "id": "doc4"}
    },
    {
        "content": "PGVector is a PostgreSQL extension that adds vector data type and similarity search operators. It enables efficient storage and retrieval of vector embeddings using indexes like IVFFLAT and HNSW.",
        "metadata": {"topic": "database", "extension": "pgvector", "category": "backend", "id": "doc5"}
    },
    {
        "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It includes supervised learning, unsupervised learning, and reinforcement learning.",
        "metadata": {"topic": "machine learning", "category": "ai", "concept": "introduction", "id": "doc6"}
    },
    {
        "content": "Natural Language Processing (NLP) is a branch of AI that focuses on the interaction between computers and human language. It includes tasks like text classification, sentiment analysis, machine translation, and question answering.",
        "metadata": {"topic": "nlp", "category": "ai", "concept": "introduction", "id": "doc7"}
    },
    {
        "content": "Docker is a containerization platform that allows applications to run in isolated environments called containers. It simplifies deployment and ensures consistency across different development and production environments.",
        "metadata": {"topic": "devops", "tool": "docker", "category": "infrastructure", "id": "doc8"}
    },
    {
        "content": "REST API is an architectural style for designing web services. It uses HTTP methods like GET, POST, PUT, DELETE and follows stateless communication principles with resource-based URLs.",
        "metadata": {"topic": "web development", "concept": "rest", "category": "backend", "id": "doc9"}
    },
    {
        "content": "JSON (JavaScript Object Notation) is a lightweight data interchange format. It's easy to read and write for humans and easy to parse and generate for machines. It's widely used in web APIs.",
        "metadata": {"topic": "data format", "format": "json", "category": "general", "id": "doc10"}
    },
    {
        "content": "OpenAI's GPT models are large language models trained on vast amounts of text data. They can generate human-like text, answer questions, write code, and perform various natural language tasks.",
        "metadata": {"topic": "ai", "model": "gpt", "company": "openai", "id": "doc11"}
    },
    {
        "content": "SQL (Structured Query Language) is a domain-specific language used for managing and manipulating relational databases. It allows users to query, insert, update, and delete data from databases.",
        "metadata": {"topic": "database", "language": "sql", "category": "backend", "id": "doc12"}
    }
]


@dataclass
class TestCase:
    """Test case definition"""
    query: str
    expected_doc_ids: List[str]  # Expected document IDs in top results
    min_score: float = 0.6
    description: str = ""


class VectorStoreTester:
    """Complete test suite for vector store API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def check_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"✓ API Health: {health.get('status')}")
                print(f"✓ Database: {health.get('database')}")
                return True
            return False
        except Exception as e:
            print(f"✗ API not reachable: {e}")
            return False
    
    def create_vector_store(self, name: str) -> str:
        """Create a vector store"""
        response = requests.post(
            f"{self.base_url}/v1/vector_stores",
            headers=self.headers,
            json={"name": name, "metadata": {"test": True}}
        )
        response.raise_for_status()
        return response.json()["id"]
    
    def add_documents(self, store_id: str, documents: List[Dict]) -> int:
        """Add documents in batch"""
        embeddings = []
        for doc in documents:
            embeddings.append({
                "content": doc["content"],
                "metadata": doc.get("metadata", {})
            })
        
        response = requests.post(
            f"{self.base_url}/v1/vector_stores/{store_id}/embeddings/batch",
            headers=self.headers,
            json={"embeddings": embeddings}
        )
        response.raise_for_status()
        return len(response.json()["data"])
    
    def search(self, store_id: str, query: str, limit: int = 10) -> Dict:
        """Perform search"""
        response = requests.post(
            f"{self.base_url}/v1/vector_stores/{store_id}/search",
            headers=self.headers,
            json={"query": query, "limit": limit, "return_metadata": True}
        )
        response.raise_for_status()
        return response.json()
    
    def run_accuracy_tests(self, store_id: str, test_cases: List[TestCase]) -> Dict:
        """Run comprehensive accuracy tests"""
        print("\n" + "=" * 80)
        print("ACCURACY TEST RESULTS")
        print("=" * 80)
        
        results = []
        total_score = 0.0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[Test {i}/{len(test_cases)}] {test_case.description}")
            print(f"  Query: '{test_case.query}'")
            
            try:
                search_result = self.search(store_id, test_case.query, limit=5)
                search_data = search_result.get("data", [])
                
                if not search_data:
                    print(f"  ❌ FAILED: No results")
                    results.append({
                        "query": test_case.query,
                        "status": "FAILED",
                        "score": 0.0,
                        "reason": "No results"
                    })
                    continue
                
                # Get top result
                top_result = search_data[0]
                top_score = top_result.get("score", 0.0)
                top_id = top_result.get("attributes", {}).get("id", "")
                top_content = top_result.get("content", [{}])[0].get("text", "")
                
                # Check if expected doc is in top results
                found_ids = [r.get("attributes", {}).get("id", "") for r in search_data[:3]]
                matched = any(doc_id in found_ids for doc_id in test_case.expected_doc_ids)
                score_ok = top_score >= test_case.min_score
                
                passed = matched and score_ok
                status = "✅ PASSED" if passed else "❌ FAILED"
                
                total_score += top_score
                
                print(f"  {status}")
                print(f"  Top Score: {top_score:.4f} (min: {test_case.min_score:.4f})")
                print(f"  Top Result ID: {top_id}")
                print(f"  Expected IDs: {test_case.expected_doc_ids}")
                print(f"  Found IDs (top 3): {found_ids}")
                print(f"  Content Preview: {top_content[:60]}...")
                
                results.append({
                    "query": test_case.query,
                    "status": "PASSED" if passed else "FAILED",
                    "score": top_score,
                    "matched": matched,
                    "score_ok": score_ok,
                    "top_doc_id": top_id,
                    "expected_ids": test_case.expected_doc_ids,
                    "found_ids": found_ids
                })
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                results.append({
                    "query": test_case.query,
                    "status": "ERROR",
                    "error": str(e)
                })
            
            time.sleep(0.3)  # Small delay
        
        accuracy = sum(1 for r in results if r.get("status") == "PASSED")
        accuracy_rate = (accuracy / len(test_cases)) * 100
        avg_score = total_score / len(test_cases) if test_cases else 0
        
        print("\n" + "=" * 80)
        print("OVERALL ACCURACY METRICS")
        print("=" * 80)
        print(f"Total Tests: {len(test_cases)}")
        print(f"Passed: {accuracy}")
        print(f"Failed: {len(test_cases) - accuracy}")
        print(f"🎯 Accuracy Rate: {accuracy_rate:.2f}%")
        print(f"⭐ Average Similarity Score: {avg_score:.4f}")
        print("=" * 80)
        
        return {
            "total_tests": len(test_cases),
            "passed": accuracy,
            "failed": len(test_cases) - accuracy,
            "accuracy_rate": accuracy_rate,
            "average_score": avg_score,
            "results": results
        }


def main():
    """Run complete test suite"""
    print("=" * 80)
    print("VECTOR STORE API - COMPREHENSIVE ACCURACY TEST")
    print("=" * 80)
    
    # Initialize tester
    tester = VectorStoreTester(API_BASE_URL, API_KEY)
    
    # Check health
    print("\n[Step 1/5] Checking API health...")
    if not tester.check_health():
        print("\n❌ API is not accessible. Please ensure:")
        print("   1. Docker services are running: docker-compose up -d")
        print("   2. API is accessible at:", API_BASE_URL)
        sys.exit(1)
    
    # Create vector store
    print("\n[Step 2/5] Creating test vector store...")
    try:
        store_id = tester.create_vector_store("Accuracy Test Store")
        print(f"✓ Created store: {store_id}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    # Add documents
    print(f"\n[Step 3/5] Adding {len(TEST_DOCUMENTS)} test documents...")
    try:
        added = tester.add_documents(store_id, TEST_DOCUMENTS)
        print(f"✓ Added {added} documents")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    # Wait for indexing
    print("\n[Step 4/5] Waiting for vector indexing (5 seconds)...")
    time.sleep(5)
    
    # Define test cases
    test_cases = [
        TestCase(
            query="What is Python programming language?",
            expected_doc_ids=["doc1"],
            min_score=0.75,
            description="Exact topic match - Python"
        ),
        TestCase(
            query="Tell me about web frameworks for Python",
            expected_doc_ids=["doc2"],
            min_score=0.70,
            description="Semantic match - FastAPI"
        ),
        TestCase(
            query="Explain database management systems",
            expected_doc_ids=["doc3", "doc5"],
            min_score=0.65,
            description="Semantic match - PostgreSQL"
        ),
        TestCase(
            query="What are vector embeddings and how do they work?",
            expected_doc_ids=["doc4"],
            min_score=0.75,
            description="Exact topic match - Embeddings"
        ),
        TestCase(
            query="How to store vectors in PostgreSQL?",
            expected_doc_ids=["doc5"],
            min_score=0.70,
            description="Specific match - PGVector"
        ),
        TestCase(
            query="What is machine learning?",
            expected_doc_ids=["doc6"],
            min_score=0.75,
            description="Exact topic match - ML"
        ),
        TestCase(
            query="Explain natural language processing",
            expected_doc_ids=["doc7"],
            min_score=0.70,
            description="Topic match - NLP"
        ),
        TestCase(
            query="What is containerization and Docker?",
            expected_doc_ids=["doc8"],
            min_score=0.70,
            description="Topic match - Docker"
        ),
        TestCase(
            query="How do REST APIs work?",
            expected_doc_ids=["doc9"],
            min_score=0.70,
            description="Topic match - REST API"
        ),
        TestCase(
            query="What is JSON format used for?",
            expected_doc_ids=["doc10"],
            min_score=0.75,
            description="Exact match - JSON"
        )
    ]
    
    # Run tests
    print(f"\n[Step 5/5] Running {len(test_cases)} accuracy tests...")
    results = tester.run_accuracy_tests(store_id, test_cases)
    
    # Save results
    output_file = "accuracy_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Detailed results saved to: {output_file}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"🎯 Overall Accuracy Rate: {results['accuracy_rate']:.2f}%")
    print(f"✅ Tests Passed: {results['passed']}/{results['total_tests']}")
    print(f"⭐ Average Similarity Score: {results['average_score']:.4f}")
    
    if results['accuracy_rate'] >= 80:
        print("🌟 Excellent accuracy! The vector search is working very well.")
    elif results['accuracy_rate'] >= 60:
        print("✓ Good accuracy. The vector search is functioning correctly.")
    else:
        print("⚠️  Accuracy is below expected. Check embedding generation and indexing.")
    
    print("=" * 80)
    
    return 0 if results['accuracy_rate'] >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())

