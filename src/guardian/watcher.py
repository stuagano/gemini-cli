"""
Guardian File System Watcher Service
Monitors project files for changes and triggers validation pipeline
"""

import os
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Set, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

logger = logging.getLogger(__name__)

@dataclass
class FileChange:
    """Represents a file change event"""
    path: str
    event_type: str  # created, modified, deleted, moved
    timestamp: datetime
    size: int
    content_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    is_code_file: bool = False
    language: Optional[str] = None

@dataclass
class ValidationRequest:
    """Request for file validation"""
    file_path: str
    change_type: str
    priority: int  # 0 = low, 1 = normal, 2 = high, 3 = critical
    validators: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    requested_at: datetime = field(default_factory=datetime.now)

@dataclass 
class ValidationResult:
    """Result from validation pipeline"""
    file_path: str
    validator: str
    status: str  # passed, failed, warning, error
    messages: List[str]
    severity: str  # info, warning, error, critical
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validated_at: datetime = field(default_factory=datetime.now)

class ChangeDebouncer:
    """Debounce rapid file changes to avoid excessive validation"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.pending_changes: Dict[str, asyncio.Task] = {}
        self.lock = asyncio.Lock()
    
    async def debounce(self, path: str, callback: Callable, *args, **kwargs):
        """Debounce changes for a given path"""
        async with self.lock:
            # Cancel existing task if present
            if path in self.pending_changes:
                self.pending_changes[path].cancel()
            
            # Schedule new task
            task = asyncio.create_task(self._delayed_call(path, callback, *args, **kwargs))
            self.pending_changes[path] = task
    
    async def _delayed_call(self, path: str, callback: Callable, *args, **kwargs):
        """Execute callback after delay"""
        try:
            await asyncio.sleep(self.delay)
            await callback(*args, **kwargs)
        finally:
            async with self.lock:
                if path in self.pending_changes:
                    del self.pending_changes[path]

class GuardianWatcher(FileSystemEventHandler):
    """
    File system watcher that monitors changes and triggers validation
    """
    
    def __init__(self, 
                 project_root: str,
                 validation_callback: Optional[Callable] = None,
                 debounce_delay: float = 1.0):
        self.project_root = Path(project_root).resolve()
        self.validation_callback = validation_callback
        self.debouncer = ChangeDebouncer(debounce_delay)
        self.observer = Observer()
        self.is_running = False
        self.file_hashes: Dict[str, str] = {}
        self.change_queue: asyncio.Queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # File patterns to monitor
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', 
            '.rs', '.cpp', '.c', '.cs', '.php', '.rb', '.swift',
            '.kt', '.scala', '.sql', '.sh', '.yaml', '.yml', '.json'
        }
        
        # Directories to ignore
        self.ignore_dirs = {
            '.git', 'node_modules', '__pycache__', '.venv', 'venv',
            'dist', 'build', 'target', '.idea', '.vscode', '.DS_Store'
        }
        
        # Validation priorities by file type
        self.file_priorities = {
            '.py': 2,  # High priority for Python files
            '.ts': 2,  # High priority for TypeScript
            '.js': 2,  # High priority for JavaScript
            '.go': 2,  # High priority for Go
            '.java': 2,  # High priority for Java
            '.sql': 3,  # Critical for database files
            '.yaml': 1,  # Normal for config files
            '.json': 1,  # Normal for config files
            '.md': 0,  # Low for documentation
        }
    
    def should_watch_path(self, path: str) -> bool:
        """Check if path should be watched"""
        path_obj = Path(path)
        
        # Skip ignored directories
        for part in path_obj.parts:
            if part in self.ignore_dirs:
                return False
        
        # Check if it's a code file
        if path_obj.is_file():
            return path_obj.suffix in self.code_extensions
        
        return True
    
    def get_file_hash(self, path: str) -> Optional[str]:
        """Calculate hash of file contents"""
        try:
            with open(path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {path}: {e}")
            return None
    
    def get_file_language(self, path: str) -> Optional[str]:
        """Determine programming language from file extension"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sql': 'sql',
            '.sh': 'shell',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json'
        }
        return ext_to_lang.get(Path(path).suffix)
    
    def on_modified(self, event):
        """Handle file modification"""
        if event.is_directory or not self.should_watch_path(event.src_path):
            return
        
        # Get file info
        path = Path(event.src_path)
        current_hash = self.get_file_hash(str(path))
        previous_hash = self.file_hashes.get(str(path))
        
        # Skip if content hasn't changed
        if current_hash == previous_hash:
            return
        
        # Update hash
        self.file_hashes[str(path)] = current_hash
        
        # Create change event
        change = FileChange(
            path=str(path),
            event_type='modified',
            timestamp=datetime.now(),
            size=path.stat().st_size if path.exists() else 0,
            content_hash=current_hash,
            previous_hash=previous_hash,
            is_code_file=True,
            language=self.get_file_language(str(path))
        )
        
        # Queue for validation (with debouncing)
        asyncio.create_task(
            self.debouncer.debounce(
                str(path),
                self.queue_validation,
                change
            )
        )
    
    def on_created(self, event):
        """Handle file creation"""
        if event.is_directory or not self.should_watch_path(event.src_path):
            return
        
        path = Path(event.src_path)
        current_hash = self.get_file_hash(str(path))
        self.file_hashes[str(path)] = current_hash
        
        change = FileChange(
            path=str(path),
            event_type='created',
            timestamp=datetime.now(),
            size=path.stat().st_size if path.exists() else 0,
            content_hash=current_hash,
            is_code_file=True,
            language=self.get_file_language(str(path))
        )
        
        asyncio.create_task(self.queue_validation(change))
    
    def on_deleted(self, event):
        """Handle file deletion"""
        if event.is_directory:
            return
        
        path = str(Path(event.src_path))
        if path in self.file_hashes:
            del self.file_hashes[path]
        
        change = FileChange(
            path=path,
            event_type='deleted',
            timestamp=datetime.now(),
            size=0,
            previous_hash=self.file_hashes.get(path)
        )
        
        asyncio.create_task(self.queue_validation(change))
    
    async def queue_validation(self, change: FileChange):
        """Queue a file change for validation"""
        # Determine priority
        ext = Path(change.path).suffix
        priority = self.file_priorities.get(ext, 1)
        
        # Determine validators based on file type
        validators = self.get_validators_for_file(change.path)
        
        # Create validation request
        request = ValidationRequest(
            file_path=change.path,
            change_type=change.event_type,
            priority=priority,
            validators=validators,
            context={
                'language': change.language,
                'size': change.size,
                'content_hash': change.content_hash
            }
        )
        
        # Add to queue
        await self.change_queue.put(request)
        
        # Trigger validation callback if configured
        if self.validation_callback:
            await self.validation_callback(request)
    
    def get_validators_for_file(self, file_path: str) -> List[str]:
        """Determine which validators to run for a file"""
        validators = []
        ext = Path(file_path).suffix
        
        # Common validators for all code files
        validators.extend(['syntax', 'style', 'complexity'])
        
        # Language-specific validators
        if ext == '.py':
            validators.extend(['python_type_check', 'python_imports'])
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            validators.extend(['eslint', 'typescript_check'])
        elif ext == '.go':
            validators.extend(['go_vet', 'go_fmt'])
        elif ext == '.sql':
            validators.extend(['sql_syntax', 'sql_injection'])
        
        # Security validators for all files
        validators.append('security_scan')
        
        return validators
    
    def start(self):
        """Start watching the file system"""
        if self.is_running:
            logger.warning("Watcher is already running")
            return
        
        # Schedule observer for project root
        self.observer.schedule(self, self.project_root, recursive=True)
        self.observer.start()
        self.is_running = True
        
        logger.info(f"Guardian watcher started for: {self.project_root}")
        
        # Start validation processor
        asyncio.create_task(self.process_validation_queue())
    
    def stop(self):
        """Stop watching the file system"""
        if not self.is_running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        self.executor.shutdown(wait=True)
        
        logger.info("Guardian watcher stopped")
    
    async def process_validation_queue(self):
        """Process queued validation requests"""
        while self.is_running:
            try:
                # Get request from queue with timeout
                request = await asyncio.wait_for(
                    self.change_queue.get(),
                    timeout=1.0
                )
                
                # Process validation request
                logger.info(f"Processing validation for: {request.file_path}")
                
                # Here you would trigger actual validation
                # For now, just log it
                logger.debug(f"Validators to run: {request.validators}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing validation queue: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics"""
        return {
            'is_running': self.is_running,
            'project_root': str(self.project_root),
            'files_monitored': len(self.file_hashes),
            'queue_size': self.change_queue.qsize(),
            'code_extensions': list(self.code_extensions),
            'ignore_dirs': list(self.ignore_dirs)
        }

# Singleton instance management
_watcher_instance: Optional[GuardianWatcher] = None

def initialize_watcher(project_root: str, 
                       validation_callback: Optional[Callable] = None) -> GuardianWatcher:
    """Initialize the Guardian watcher singleton"""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = GuardianWatcher(project_root, validation_callback)
    return _watcher_instance

def get_watcher() -> Optional[GuardianWatcher]:
    """Get the Guardian watcher instance"""
    return _watcher_instance

def start_watcher():
    """Start the watcher if initialized"""
    if _watcher_instance:
        _watcher_instance.start()
    else:
        raise RuntimeError("Watcher not initialized. Call initialize_watcher first.")

def stop_watcher():
    """Stop the watcher if running"""
    if _watcher_instance:
        _watcher_instance.stop()