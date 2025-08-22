"""
Scout Indexer Service
Background service for maintaining codebase index and enabling fast lookups
"""

import os
import sqlite3
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from threading import Thread, Lock
from dataclasses import dataclass, asdict
import fnmatch

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from agents.enhanced.scout import CodeAnalyzer


@dataclass
class IndexedFile:
    """Represents an indexed file"""
    file_path: str
    language: str
    size_lines: int
    size_bytes: int
    last_modified: float
    content_hash: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    patterns: List[Dict[str, str]]
    complexity: int
    indexed_at: float


@dataclass
class DuplicationResult:
    """Result of duplication analysis"""
    original_file: str
    duplicate_file: str
    similarity_score: float
    function_name: str
    line_start: int
    line_end: int
    duplicate_lines: List[str]


class CodebaseWatcher(FileSystemEventHandler):
    """File system watcher for real-time index updates"""
    
    def __init__(self, indexer):
        self.indexer = indexer
        
    def on_modified(self, event):
        if not event.is_directory:
            self.indexer.queue_file_for_indexing(event.src_path)
    
    def on_created(self, event):
        if not event.is_directory:
            self.indexer.queue_file_for_indexing(event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.indexer.remove_file_from_index(event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.indexer.remove_file_from_index(event.src_path)
            self.indexer.queue_file_for_indexing(event.dest_path)


class ScoutIndexer:
    """
    Background indexer service for maintaining codebase knowledge
    Provides fast lookups for duplication detection and pattern matching
    """
    
    def __init__(self, project_root: str, db_path: str = None):
        self.project_root = Path(project_root).resolve()
        self.db_path = db_path or str(self.project_root / ".scout" / "index.db")
        self.analyzer = CodeAnalyzer()
        self.lock = Lock()
        self.indexing_queue = set()
        self.is_running = False
        self.observer = None
        self.indexing_thread = None
        
        # File patterns to include/exclude
        self.include_patterns = [
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx',
            '*.java', '*.go', '*.rs', '*.cpp', '*.c',
            '*.cs', '*.php', '*.rb'
        ]
        self.exclude_patterns = [
            '*/node_modules/*', '*/.git/*', '*/.venv/*', 
            '*/venv/*', '*/__pycache__/*', '*/dist/*',
            '*/build/*', '*/.next/*', '*/.nuxt/*'
        ]
        
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for index storage"""
        
        # Create .scout directory
        os.makedirs(Path(self.db_path).parent, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS indexed_files (
                    file_path TEXT PRIMARY KEY,
                    language TEXT,
                    size_lines INTEGER,
                    size_bytes INTEGER,
                    last_modified REAL,
                    content_hash TEXT,
                    indexed_at REAL,
                    data TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS functions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    function_name TEXT,
                    signature_hash TEXT,
                    line_start INTEGER,
                    line_end INTEGER,
                    complexity INTEGER,
                    content_hash TEXT,
                    FOREIGN KEY (file_path) REFERENCES indexed_files (file_path)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS duplicates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_file TEXT,
                    duplicate_file TEXT,
                    function_name TEXT,
                    similarity_score REAL,
                    line_start INTEGER,
                    line_end INTEGER,
                    detected_at REAL
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_functions_signature ON functions(signature_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_functions_file ON functions(file_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_duplicates_score ON duplicates(similarity_score)")
    
    def start(self):
        """Start the indexing service"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start file watcher
        self.observer = Observer()
        handler = CodebaseWatcher(self)
        self.observer.schedule(handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        # Start indexing thread
        self.indexing_thread = Thread(target=self._indexing_worker, daemon=True)
        self.indexing_thread.start()
        
        print(f"Scout indexer started for {self.project_root}")
    
    def stop(self):
        """Stop the indexing service"""
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        print("Scout indexer stopped")
    
    def queue_file_for_indexing(self, file_path: str):
        """Queue a file for indexing"""
        file_path = str(Path(file_path).resolve())
        
        if not self._should_index_file(file_path):
            return
            
        with self.lock:
            self.indexing_queue.add(file_path)
    
    def remove_file_from_index(self, file_path: str):
        """Remove file from index"""
        file_path = str(Path(file_path).resolve())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM indexed_files WHERE file_path = ?", (file_path,))
            conn.execute("DELETE FROM functions WHERE file_path = ?", (file_path,))
            conn.execute("DELETE FROM duplicates WHERE original_file = ? OR duplicate_file = ?", 
                        (file_path, file_path))
    
    def _should_index_file(self, file_path: str) -> bool:
        """Check if file should be indexed"""
        
        # Ensure the file is within the project root
        try:
            resolved_path = Path(file_path).resolve()
            if not resolved_path.is_relative_to(self.project_root):
                return False
        except (ValueError, OSError):
            # Handles cases like invalid paths or symlink loops
            return False

        rel_path = str(Path(file_path).relative_to(self.project_root))
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern) or any(fnmatch.fnmatch(part, pattern.strip('*/')) for part in Path(rel_path).parts):
                return False
        
        # Check include patterns
        for pattern in self.include_patterns:
            if fnmatch.fnmatch(Path(file_path).name, pattern):
                return True
                
        return False
    
    def _indexing_worker(self):
        """Background worker for processing indexing queue"""
        
        while self.is_running:
            files_to_process = []
            
            with self.lock:
                if self.indexing_queue:
                    files_to_process = list(self.indexing_queue)
                    self.indexing_queue.clear()
            
            for file_path in files_to_process:
                try:
                    self._index_file(file_path)
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")
            
            time.sleep(1)  # Check queue every second
    
    def _index_file(self, file_path: str):
        """Index a single file"""
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return
        
        # Check if file needs reindexing
        stat = file_path_obj.stat()
        current_mtime = stat.st_mtime
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT last_modified FROM indexed_files WHERE file_path = ?", 
                (file_path,)
            )
            row = cursor.fetchone()
            
            if row and row[0] >= current_mtime:
                return  # File hasn't changed
        
        # Analyze file
        analysis = self.analyzer.analyze_file(file_path_obj)
        if 'error' in analysis:
            return
        
        # Calculate content hash
        with open(file_path, 'rb') as f:
            content_hash = hashlib.md5(f.read()).hexdigest()
        
        # Store in database
        indexed_file = IndexedFile(
            file_path=file_path,
            language=analysis['language'],
            size_lines=analysis['size_lines'],
            size_bytes=analysis['size_bytes'],
            last_modified=current_mtime,
            content_hash=content_hash,
            functions=analysis['functions'],
            classes=analysis['classes'],
            imports=analysis['imports'],
            patterns=analysis['patterns'],
            complexity=analysis['complexity'],
            indexed_at=time.time()
        )
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert/update indexed file
            conn.execute("""
                INSERT OR REPLACE INTO indexed_files 
                (file_path, language, size_lines, size_bytes, last_modified, 
                 content_hash, indexed_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                indexed_file.file_path,
                indexed_file.language,
                indexed_file.size_lines,
                indexed_file.size_bytes,
                indexed_file.last_modified,
                indexed_file.content_hash,
                indexed_file.indexed_at,
                json.dumps(asdict(indexed_file))
            ))
            
            # Delete old function entries
            conn.execute("DELETE FROM functions WHERE file_path = ?", (file_path,))
            
            # Insert function entries
            for func in analysis['functions']:
                signature = f"{func['name']}({','.join(func.get('parameters', []))})"
                signature_hash = hashlib.md5(signature.encode()).hexdigest()
                
                conn.execute("""
                    INSERT INTO functions 
                    (file_path, function_name, signature_hash, line_start, line_end, complexity, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path,
                    func['name'],
                    signature_hash,
                    func.get('line', 0),
                    func.get('line', 0) + func.get('lines', 1),
                    func.get('complexity', 1),
                    hashlib.md5(func.get('body', '').encode()).hexdigest()
                ))
        
        print(f"Indexed: {file_path}")
    
    def full_index(self):
        """Perform full codebase indexing"""
        print(f"Starting full index of {self.project_root}")
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                self.queue_file_for_indexing(str(file_path))
        
        # Wait for queue to be processed
        while self.indexing_queue:
            time.sleep(0.1)
        
        print("Full indexing complete")
    
    def find_duplicates(self, similarity_threshold: float = 0.8) -> List[DuplicationResult]:
        """Find duplicate functions in the codebase"""
        
        duplicates = []
        
        with sqlite3.connect(self.db_path) as conn:
            # Find functions with same signature hash
            cursor = conn.execute("""
                SELECT f1.file_path, f1.function_name, f1.content_hash, f1.line_start, f1.line_end,
                       f2.file_path, f2.function_name, f2.content_hash, f2.line_start, f2.line_end
                FROM functions f1
                JOIN functions f2 ON f1.signature_hash = f2.signature_hash
                WHERE f1.file_path < f2.file_path
                AND f1.content_hash = f2.content_hash
            """)
            
            for row in cursor.fetchall():
                duplicate = DuplicationResult(
                    original_file=row[0],
                    duplicate_file=row[5],
                    similarity_score=1.0,  # Exact match
                    function_name=row[1],
                    line_start=row[3],
                    line_end=row[4],
                    duplicate_lines=[]
                )
                duplicates.append(duplicate)
        
        # Store duplicates in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM duplicates")  # Clear old results
            
            for dup in duplicates:
                conn.execute("""
                    INSERT INTO duplicates 
                    (original_file, duplicate_file, function_name, similarity_score, 
                     line_start, line_end, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    dup.original_file,
                    dup.duplicate_file,
                    dup.function_name,
                    dup.similarity_score,
                    dup.line_start,
                    dup.line_end,
                    time.time()
                ))
        
        return duplicates
    
    def get_file_info(self, file_path: str) -> Optional[IndexedFile]:
        """Get indexed information for a file"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM indexed_files WHERE file_path = ?",
                (str(Path(file_path).resolve()),)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row[0])
                return IndexedFile(**data)
                
        return None
    
    def search_similar_functions(self, function_signature: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar functions"""
        
        signature_hash = hashlib.md5(function_signature.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT file_path, function_name, signature_hash, line_start, line_end, complexity
                FROM functions 
                WHERE signature_hash = ?
                LIMIT ?
            """, (signature_hash, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'file_path': row[0],
                    'function_name': row[1],
                    'signature_hash': row[2],
                    'line_start': row[3],
                    'line_end': row[4],
                    'complexity': row[5]
                })
            
            return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM indexed_files")
            total_files = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM functions")
            total_functions = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM duplicates")
            total_duplicates = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT language, COUNT(*) FROM indexed_files GROUP BY language")
            languages = dict(cursor.fetchall())
            
            cursor = conn.execute("SELECT SUM(size_lines) FROM indexed_files")
            total_lines = cursor.fetchone()[0] or 0
            
            return {
                'total_files': total_files,
                'total_functions': total_functions,
                'total_duplicates': total_duplicates,
                'total_lines': total_lines,
                'languages': languages,
                'last_updated': time.time()
            }


# Global indexer instance
scout_indexer: Optional[ScoutIndexer] = None

def initialize_indexer(project_root: str):
    """Initialize the global Scout indexer"""
    global scout_indexer
    scout_indexer = ScoutIndexer(project_root)
    scout_indexer.start()
    return scout_indexer

def get_indexer() -> Optional[ScoutIndexer]:
    """Get the global Scout indexer"""
    return scout_indexer