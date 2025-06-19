"""
RAG (Retrieval Augmented Generation) utilities for enhancing prompts with relevant content.
"""
from typing import List, Dict, Any, Optional
import os
import re
import time
import logging

# Configure logging
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("rag_utils")

class RagContentProvider:
    """
    A class that provides RAG (Retrieval Augmented Generation) capabilities
    by retrieving relevant content from existing files.
    """
    
    def __init__(self, content_files: Dict[str, str]):
        """
        Initialize the RAG content provider with a dictionary of content files.
        
        Args:
            content_files: Dictionary mapping content types to file paths
                           e.g., {"outline": "path/to/outline.txt", "draft": "path/to/draft.txt"}
        """
        self.content_files = content_files
        self.content_cache = {}
    
    def get_file_content(self, file_type: str) -> Optional[str]:
        """
        Get the content of a specific file type.
        
        Args:
            file_type: The type of content to retrieve (e.g., "outline", "draft")
            
        Returns:
            The content of the file, or None if the file doesn't exist or can't be read
        """
        start_time = time.time()
        logger.info(f"Getting file content for {file_type}")
        
        # Check if we have this file type
        if file_type not in self.content_files:
            logger.warning(f"File type {file_type} not found in content_files")
            return None
            
        file_path = self.content_files[file_type]
        logger.info(f"File path: {file_path}")
        # Check if we've already cached this content
        if file_path in self.content_cache:
            logger.info(f"Returning cached content for {file_type} ({time.time() - start_time:.2f}s)")
            return self.content_cache[file_path]
        
        # Read the file
        if os.path.exists(file_path):
            try:
                file_read_start = time.time()
                with open(file_path, 'r') as f:
                    content = f.read()
                logger.info(f"File read took {time.time() - file_read_start:.2f}s")
                
                self.content_cache[file_path] = content
                logger.info(f"Total get_file_content took {time.time() - start_time:.2f}s")
                return content
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return None
        else:
            logger.warning(f"File not found: {file_path}")
            return None
    
    # def get_all_content(self) -> Dict[str, str]:
    #     """
    #     Get all available content.
        
    #     Returns:
    #         Dictionary mapping content types to their content
    #     """
    #     result = {}
    #     for content_type, file_path in self.content_files.items():
    #         content = self.get_file_content(content_type)
    #         if content:
    #             result[content_type] = content
    #     return result
    
    def find_relevant_content(self, query: str, content_types: Optional[List[str]] = None, 
                             max_chunks: int = 5, chunk_size: int = 1000) -> List[str]:
        """
        Find content chunks relevant to a query.
        
        Args:
            query: The query to search for
            content_types: List of content types to search in (if None, search all)
            max_chunks: Maximum number of chunks to return
            chunk_size: Size of each chunk in characters
            
        Returns:
            List of relevant content chunks
        """
        start_time = time.time()
        logger.info(f"Finding relevant content for query: {query}")
        
        # Simple implementation - in a real system, you'd use embeddings and vector search
        relevant_chunks = []
        
        # Determine which content types to search
        types_to_search = content_types if content_types else list(self.content_files.keys())
        logger.info(f"Searching in content types: {types_to_search}")
        
        # Process each content type
        for content_type in types_to_search:
            content_start = time.time()
            content = self.get_file_content(content_type)
            if not content:
                logger.warning(f"No content found for {content_type}")
                continue
                
            # Split content into chunks
            split_start = time.time()
            chunks = self._split_into_chunks(content, chunk_size)
            logger.info(f"Split into {len(chunks)} chunks in {time.time() - split_start:.2f}s")
            
            # Simple keyword matching (in a real system, use embeddings)
            match_start = time.time()
            query_terms = re.findall(r'\w+', query.lower())
            for chunk in chunks:
                chunk_lower = chunk.lower()
                # Count how many query terms appear in the chunk
                matches = sum(1 for term in query_terms if term in chunk_lower)
                if matches > 0:
                    relevant_chunks.append((matches, chunk, content_type))
            logger.info(f"Matching took {time.time() - match_start:.2f}s")
        
        # Sort by relevance (number of matches)
        relevant_chunks.sort(reverse=True, key=lambda x: x[0])
        
        # Return the top chunks
        result = [f"[From {chunk[2]}]: {chunk[1]}" for chunk in relevant_chunks[:max_chunks]]
        logger.info(f"Found {len(result)} relevant chunks out of {len(relevant_chunks)} total matches")
        logger.info(f"Total find_relevant_content took {time.time() - start_time:.2f}s")
        return result
    
    def _split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """
        Split text into chunks of approximately chunk_size characters.
        Tries to split at paragraph boundaries when possible.
        
        Args:
            text: The text to split
            chunk_size: Target size of each chunk
            
        Returns:
            List of text chunks
        """
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph would exceed chunk size and we already have content,
            # add the current chunk to results and start a new one
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = para
            else:
                # Add to current chunk with a paragraph separator if needed
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    
    # def enhance_prompt(self, prompt: str, query: str, content_types: Optional[List[str]] = None,
    #                   max_chunks: int = 3) -> str:
    #     """
    #     Enhance a prompt with relevant content.
        
    #     Args:
    #         prompt: The original prompt
    #         query: Query to find relevant content
    #         content_types: List of content types to search in (if None, search all)
    #         max_chunks: Maximum number of content chunks to include
            
    #     Returns:
    #         Enhanced prompt with relevant content
    #     """
    #     start_time = time.time()
    #     logger.info(f"Enhancing prompt with query: {query}")
        
    #     # Find relevant content
    #     find_content_start = time.time()
    #     relevant_chunks = self.find_relevant_content(query, content_types, max_chunks)
    #     logger.info(f"Finding relevant content took {time.time() - find_content_start:.2f}s")
        
    #     if not relevant_chunks:
    #         logger.info("No relevant chunks found, returning original prompt")
    #         return prompt
            
    #     # Add relevant content to the prompt
    #     rag_section = "\n\nRELEVANT CONTENT:\n" + "\n\n".join(relevant_chunks)
        
    #     # Add instructions for using the relevant content
    #     instructions = """
    #     Use the RELEVANT CONTENT provided above to inform your response. 
    #     This content includes existing materials that should guide your writing.
    #     Maintain consistency with the style, terminology, and approach in these materials.
    #     """
        
    #     # Combine everything
    #     enhanced_prompt = prompt + rag_section + instructions
        
    #     logger.info(f"Total enhance_prompt took {time.time() - start_time:.2f}s")
    #     logger.info(f"Enhanced prompt length: {len(enhanced_prompt)} chars")
    #     return enhanced_prompt