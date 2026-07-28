"""
Dynamic chunk size calculator based on record count
Optimizes chunk size for efficient processing based on data volume
"""

from typing import Optional

class ChunkCalculator:
    """Calculates optimal chunk size based on record count and system resources"""
    
    @staticmethod
    def calculate_chunk_size(record_count: int, min_chunk: int = 100, max_chunk: int = 10000) -> int:
        """
        Calculate optimal chunk size based on record count
        
        Args:
            record_count: Total number of records to process
            min_chunk: Minimum chunk size (default: 100)
            max_chunk: Maximum chunk size (default: 10000)
            
        Returns:
            Optimal chunk size for processing
        """
        if record_count <= 0:
            return min_chunk
        
        # Small datasets: use smaller chunks for better progress tracking
        if record_count < 1000:
            return min_chunk
        
        # Medium datasets: moderate chunk size
        if record_count < 10000:
            return 500
        
        # Large datasets: larger chunks for efficiency
        if record_count < 100000:
            return 1000
        
        # Very large datasets: maximum chunk size
        if record_count < 1000000:
            return 5000
        
        # Massive datasets: use maximum chunk size
        return max_chunk
    
    @staticmethod
    def estimate_chunks(record_count: int, chunk_size: Optional[int] = None) -> int:
        """
        Estimate number of chunks needed for processing
        
        Args:
            record_count: Total number of records
            chunk_size: Chunk size (if None, will be calculated dynamically)
            
        Returns:
            Estimated number of chunks
        """
        if chunk_size is None:
            chunk_size = ChunkCalculator.calculate_chunk_size(record_count)
        
        return (record_count + chunk_size - 1) // chunk_size  # Ceiling division
    
    @staticmethod
    def get_progress_percentage(current_chunk: int, total_chunks: int) -> float:
        """
        Calculate progress percentage based on chunk completion
        
        Args:
            current_chunk: Current chunk number (1-based)
            total_chunks: Total number of chunks
            
        Returns:
            Progress percentage (0-100)
        """
        if total_chunks <= 0:
            return 0.0
        
        percentage = (current_chunk / total_chunks) * 100
        return min(percentage, 100.0)

# Global chunk calculator instance
chunk_calculator = ChunkCalculator()
