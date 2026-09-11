"""
Embedding service for generating embeddings using LiteLLM proxy.
Supports both single and batch embedding generation.
"""
from typing import List, Optional
import logging
import asyncio
from config import settings, EmbeddingConfig
import litellm
from litellm.types.utils import EmbeddingResponse

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using LiteLLM proxy"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or settings.embedding
        logger.info(
            f"Initialized EmbeddingService with model={self.config.model}, "
            f"base_url={self.config.base_url}, dimensions={self.config.dimensions}"
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using LiteLLM proxy
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            RuntimeError: If embedding generation fails
            ValueError: If embedding dimensions don't match expected dimensions
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            logger.debug(f"Generating embedding for text (length: {len(text)})")
            
            response: EmbeddingResponse = await litellm.aembedding(
                model=self.config.model,
                input=[text],
                api_base=self.config.base_url,
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            
            if not response or not response.data:
                raise RuntimeError("Empty response from embedding service")
            
            # Extract embedding from response
            embedding = response.data[0].embedding
            
            # Validate embedding dimensions
            if len(embedding) != self.config.dimensions:
                raise ValueError(
                    f"Expected embedding dimension {self.config.dimensions}, "
                    f"got {len(embedding)}"
                )
            
            logger.debug(f"Successfully generated embedding (dimensions: {len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If embedding generation fails
            ValueError: If embedding dimensions don't match expected dimensions
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if not all(text and text.strip() for text in texts):
            raise ValueError("All texts must be non-empty")
        
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            
            # Generate embeddings using LiteLLM
            response = await litellm.aembedding(
                model=self.config.model,
                input=texts,
                api_base=self.config.base_url,
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            
            if not response or not response.data:
                raise RuntimeError("Empty response from embedding service")
            
            # Extract embeddings from response
            embeddings = []
            for item in response.data:
                embedding = item.embedding
                # Validate embedding dimensions
                if len(embedding) != self.config.dimensions:
                    raise ValueError(
                        f"Expected embedding dimension {self.config.dimensions}, "
                        f"got {len(embedding)}"
                    )
                embeddings.append(embedding)
            
            logger.debug(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate that an embedding has the correct dimensions
        
        Args:
            embedding: Embedding vector to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        if not isinstance(embedding, list):
            raise ValueError(f"Embedding must be a list, got {type(embedding)}")
        
        if len(embedding) != self.config.dimensions:
            raise ValueError(
                f"Expected embedding dimension {self.config.dimensions}, "
                f"got {len(embedding)}"
            )
        
        if not all(isinstance(x, (int, float)) for x in embedding):
            raise ValueError("All embedding values must be numbers")
        
        return True
    
    def update_config(self, new_config: EmbeddingConfig):
        """Update the embedding configuration"""
        self.config = new_config
        logger.info(f"Updated embedding configuration: model={self.config.model}")


# Global embedding service instance
embedding_service = EmbeddingService()

