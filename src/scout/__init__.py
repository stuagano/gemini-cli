"""
Scout Module
Codebase analysis and duplication detection
"""

from .indexer import ScoutIndexer, IndexedFile, DuplicationResult, initialize_indexer, get_indexer

__all__ = [
    'ScoutIndexer',
    'IndexedFile', 
    'DuplicationResult',
    'initialize_indexer',
    'get_indexer'
]