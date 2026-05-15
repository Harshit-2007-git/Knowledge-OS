"""
Text splitting utilities for chunking documents.
"""

import re
from typing import List

class RecursiveCharacterTextSplitter:
    """
    Splits text recursively by a list of characters to keep chunks below a max size.
    Similar to LangChain's RecursiveCharacterTextSplitter.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        
        # Base case
        if len(text) <= self.chunk_size:
            return [text] if text else []
            
        separator = self.separators[-1]
        for s in self.separators:
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                break

        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
            
        # Merge splits
        current_chunk = []
        current_len = 0
        
        for split in splits:
            split_len = len(split) + (len(separator) if separator else 0)
            if current_len + split_len > self.chunk_size and current_chunk:
                # Chunk is full, join and save
                chunk_str = separator.join(current_chunk)
                if chunk_str.strip():
                    final_chunks.append(chunk_str.strip())
                
                # Start new chunk with overlap
                # Backtrack to include overlap
                overlap_len = 0
                overlap_chunk = []
                for prev_split in reversed(current_chunk):
                    if overlap_len + len(prev_split) > self.chunk_overlap and overlap_chunk:
                        break
                    overlap_chunk.insert(0, prev_split)
                    overlap_len += len(prev_split) + (len(separator) if separator else 0)
                
                current_chunk = overlap_chunk
                current_len = overlap_len
                
            current_chunk.append(split)
            current_len += split_len
            
        # Add the last chunk
        if current_chunk:
            chunk_str = separator.join(current_chunk)
            if chunk_str.strip():
                final_chunks.append(chunk_str.strip())
                
        return final_chunks
