#!/usr/bin/env python3
"""
Document Ingestion Pipeline for RAG System
Continuously monitors and ingests new documents into the knowledge base
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass
import re
import requests
from bs4 import BeautifulSoup
import markdown
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.vector_store import create_vector_store, VectorDocument
from knowledge.rag_system import EnterpriseRAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IngestConfig:
    """Configuration for document ingestion"""
    watch_directories: List[str]
    file_patterns: List[str]
    excluded_patterns: List[str]
    batch_size: int = 10
    batch_timeout: int = 30  # seconds
    max_document_size: int = 1_000_000  # 1MB
    chunk_size: int = 1000  # characters
    chunk_overlap: int = 200  # characters

class DocumentProcessor:
    """Processes different document types for ingestion"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.supported_extensions = {
            '.md': self.process_markdown,
            '.txt': self.process_text,
            '.py': self.process_python,
            '.js': self.process_javascript,
            '.ts': self.process_typescript,
            '.yaml': self.process_yaml,
            '.yml': self.process_yaml,
            '.json': self.process_json,
            '.html': self.process_html
        }
    
    async def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a file and return document chunks"""
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        ext = file_path.suffix.lower()
        if ext not in self.supported_extensions:
            logger.warning(f"Unsupported file type: {ext}")
            return []
        
        try:
            processor = self.supported_extensions[ext]
            return await processor(file_path)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    async def process_markdown(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process Markdown files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML for better structure parsing
        html = markdown.markdown(content, extensions=['extra', 'codehilite'])
        soup = BeautifulSoup(html, 'html.parser')
        
        chunks = []
        current_chunk = []
        current_size = 0
        current_header = ""
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'pre', 'ul', 'ol']):
            if element.name in ['h1', 'h2', 'h3']:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'metadata': {
                            'file_path': str(file_path),
                            'section': current_header,
                            'type': 'markdown',
                            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                    })
                    current_chunk = []
                    current_size = 0
                
                current_header = element.get_text().strip()
                current_chunk.append(f"## {current_header}")
                current_size = len(current_header)
            else:
                text = element.get_text().strip()
                if current_size + len(text) > self.chunk_size:
                    # Save current chunk
                    if current_chunk:
                        chunks.append({
                            'content': '\n'.join(current_chunk),
                            'metadata': {
                                'file_path': str(file_path),
                                'section': current_header,
                                'type': 'markdown',
                                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            }
                        })
                    current_chunk = [text]
                    current_size = len(text)
                else:
                    current_chunk.append(text)
                    current_size += len(text)
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'metadata': {
                    'file_path': str(file_path),
                    'section': current_header,
                    'type': 'markdown',
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            })
        
        return chunks
    
    async def process_text(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process plain text files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = self._chunk_text(content)
        return [
            {
                'content': chunk,
                'metadata': {
                    'file_path': str(file_path),
                    'type': 'text',
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            }
            for chunk in chunks
        ]
    
    async def process_python(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process Python files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract docstrings and function/class definitions
        chunks = []
        
        # Extract module docstring
        module_doc_match = re.match(r'^"""(.*?)"""', content, re.DOTALL)
        if module_doc_match:
            chunks.append({
                'content': f"Python Module: {file_path.name}\n{module_doc_match.group(1)}",
                'metadata': {
                    'file_path': str(file_path),
                    'type': 'python',
                    'element': 'module_doc',
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            })
        
        # Extract classes and functions
        class_pattern = re.compile(r'^class\s+(\w+).*?:\s*\n(.*?)(?=^class\s|\Z)', re.MULTILINE | re.DOTALL)
        function_pattern = re.compile(r'^def\s+(\w+)\((.*?)\).*?:\s*\n(.*?)(?=^def\s|^class\s|\Z)', re.MULTILINE | re.DOTALL)
        
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            class_body = match.group(2)[:self.chunk_size]
            chunks.append({
                'content': f"Python Class: {class_name}\n{class_body}",
                'metadata': {
                    'file_path': str(file_path),
                    'type': 'python',
                    'element': 'class',
                    'name': class_name,
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            })
        
        for match in function_pattern.finditer(content):
            func_name = match.group(1)
            func_params = match.group(2)
            func_body = match.group(3)[:self.chunk_size]
            chunks.append({
                'content': f"Python Function: {func_name}({func_params})\n{func_body}",
                'metadata': {
                    'file_path': str(file_path),
                    'type': 'python',
                    'element': 'function',
                    'name': func_name,
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            })
        
        return chunks
    
    async def process_javascript(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process JavaScript files"""
        return await self._process_code_file(file_path, 'javascript')
    
    async def process_typescript(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process TypeScript files"""
        return await self._process_code_file(file_path, 'typescript')
    
    async def _process_code_file(self, file_path: Path, language: str) -> List[Dict[str, Any]]:
        """Generic code file processor"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = self._chunk_text(content)
        return [
            {
                'content': f"{language.capitalize()} Code:\n{chunk}",
                'metadata': {
                    'file_path': str(file_path),
                    'type': language,
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            }
            for chunk in chunks
        ]
    
    async def process_yaml(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process YAML files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            data = yaml.safe_load(content)
            formatted_content = yaml.dump(data, default_flow_style=False)
        except:
            formatted_content = content
        
        return [{
            'content': f"YAML Configuration:\n{formatted_content[:self.chunk_size]}",
            'metadata': {
                'file_path': str(file_path),
                'type': 'yaml',
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
        }]
    
    async def process_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process JSON files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            data = json.loads(content)
            formatted_content = json.dumps(data, indent=2)
        except:
            formatted_content = content
        
        return [{
            'content': f"JSON Data:\n{formatted_content[:self.chunk_size]}",
            'metadata': {
                'file_path': str(file_path),
                'type': 'json',
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
        }]
    
    async def process_html(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process HTML files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text(separator='\n', strip=True)
        
        chunks = self._chunk_text(text_content)
        return [
            {
                'content': chunk,
                'metadata': {
                    'file_path': str(file_path),
                    'type': 'html',
                    'title': soup.title.string if soup.title else file_path.name,
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            }
            for chunk in chunks
        ]
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks

class FileWatcher(FileSystemEventHandler):
    """Watches directories for new or modified files"""
    
    def __init__(self, ingestion_queue: asyncio.Queue, config: IngestConfig):
        self.ingestion_queue = ingestion_queue
        self.config = config
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
    
    def should_process(self, file_path: str) -> bool:
        """Check if file should be processed"""
        path = Path(file_path)
        
        # Check file patterns
        matches_pattern = any(
            path.match(pattern) for pattern in self.config.file_patterns
        )
        
        # Check excluded patterns
        is_excluded = any(
            path.match(pattern) for pattern in self.config.excluded_patterns
        )
        
        return matches_pattern and not is_excluded
    
    def get_file_hash(self, file_path: str) -> str:
        """Get hash of file contents"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if not event.is_directory and self.should_process(event.src_path):
            logger.info(f"New file detected: {event.src_path}")
            asyncio.run(self.ingestion_queue.put(event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if not event.is_directory and self.should_process(event.src_path):
            # Check if content actually changed
            try:
                current_hash = self.get_file_hash(event.src_path)
                if event.src_path in self.file_hashes:
                    if self.file_hashes[event.src_path] == current_hash:
                        return  # Content unchanged
                
                self.file_hashes[event.src_path] = current_hash
                logger.info(f"Modified file detected: {event.src_path}")
                asyncio.run(self.ingestion_queue.put(event.src_path))
            except Exception as e:
                logger.error(f"Error processing modified file {event.src_path}: {e}")

class DocumentIngestionPipeline:
    """Main document ingestion pipeline"""
    
    def __init__(self, config: IngestConfig, vector_store_config: Dict[str, Any]):
        self.config = config
        self.vector_store = create_vector_store(vector_store_config)
        self.processor = DocumentProcessor(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        self.ingestion_queue: asyncio.Queue = asyncio.Queue()
        self.file_watcher = FileWatcher(self.ingestion_queue, config)
        self.observer = Observer()
        self.running = False
        self.processed_count = 0
        self.error_count = 0
    
    async def start(self):
        """Start the ingestion pipeline"""
        logger.info("Starting document ingestion pipeline...")
        self.running = True
        
        # Set up file watchers
        for directory in self.config.watch_directories:
            if Path(directory).exists():
                self.observer.schedule(self.file_watcher, directory, recursive=True)
                logger.info(f"Watching directory: {directory}")
            else:
                logger.warning(f"Directory not found: {directory}")
        
        self.observer.start()
        
        # Start processing queue
        asyncio.create_task(self.process_queue())
        
        # Initial scan of directories
        await self.initial_scan()
        
        logger.info("Document ingestion pipeline started")
    
    async def stop(self):
        """Stop the ingestion pipeline"""
        logger.info("Stopping document ingestion pipeline...")
        self.running = False
        self.observer.stop()
        self.observer.join()
        logger.info("Document ingestion pipeline stopped")
    
    async def initial_scan(self):
        """Scan directories for existing files"""
        logger.info("Performing initial directory scan...")
        
        for directory in self.config.watch_directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
            
            for pattern in self.config.file_patterns:
                for file_path in dir_path.rglob(pattern):
                    if not any(file_path.match(exc) for exc in self.config.excluded_patterns):
                        await self.ingestion_queue.put(str(file_path))
        
        logger.info("Initial scan complete")
    
    async def process_queue(self):
        """Process files from the ingestion queue"""
        batch = []
        last_batch_time = datetime.now()
        
        while self.running:
            try:
                # Wait for files with timeout
                try:
                    file_path = await asyncio.wait_for(
                        self.ingestion_queue.get(),
                        timeout=1.0
                    )
                    batch.append(file_path)
                except asyncio.TimeoutError:
                    pass
                
                # Process batch if size or timeout reached
                should_process = (
                    len(batch) >= self.config.batch_size or
                    (len(batch) > 0 and 
                     (datetime.now() - last_batch_time).seconds >= self.config.batch_timeout)
                )
                
                if should_process and batch:
                    await self.process_batch(batch)
                    batch = []
                    last_batch_time = datetime.now()
                    
            except Exception as e:
                logger.error(f"Error in processing queue: {e}")
                self.error_count += 1
    
    async def process_batch(self, file_paths: List[str]):
        """Process a batch of files"""
        logger.info(f"Processing batch of {len(file_paths)} files")
        
        all_documents = []
        all_metadata = []
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                
                # Check file size
                if path.stat().st_size > self.config.max_document_size:
                    logger.warning(f"File too large, skipping: {file_path}")
                    continue
                
                # Process file
                chunks = await self.processor.process_file(path)
                
                for chunk in chunks:
                    all_documents.append(chunk['content'])
                    
                    # Enhance metadata
                    metadata = chunk['metadata']
                    metadata['ingested_at'] = datetime.now().isoformat()
                    metadata['file_name'] = path.name
                    metadata['file_size'] = path.stat().st_size
                    
                    # Determine service and category
                    metadata['service'] = self._determine_service(path)
                    metadata['category'] = self._determine_category(path)
                    
                    all_metadata.append(metadata)
                
                self.processed_count += 1
                logger.info(f"Processed: {file_path} ({len(chunks)} chunks)")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.error_count += 1
        
        # Add to vector store
        if all_documents:
            try:
                doc_ids = await self.vector_store.add_documents(all_documents, all_metadata)
                logger.info(f"Added {len(doc_ids)} document chunks to vector store")
            except Exception as e:
                logger.error(f"Error adding documents to vector store: {e}")
                self.error_count += 1
    
    def _determine_service(self, file_path: Path) -> str:
        """Determine service based on file path"""
        path_str = str(file_path).lower()
        
        if 'agents' in path_str:
            return 'BMAD Agents'
        elif 'api' in path_str:
            return 'API'
        elif 'guardian' in path_str:
            return 'Guardian'
        elif 'scout' in path_str:
            return 'Scout'
        elif 'knowledge' in path_str or 'rag' in path_str:
            return 'Knowledge Base'
        elif 'test' in path_str:
            return 'Testing'
        elif 'doc' in path_str:
            return 'Documentation'
        else:
            return 'General'
    
    def _determine_category(self, file_path: Path) -> str:
        """Determine category based on file type and content"""
        ext = file_path.suffix.lower()
        
        if ext in ['.py']:
            return 'code'
        elif ext in ['.md', '.txt']:
            return 'documentation'
        elif ext in ['.yaml', '.yml', '.json']:
            return 'configuration'
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            return 'frontend'
        elif ext in ['.html', '.css']:
            return 'web'
        else:
            return 'other'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            'processed_files': self.processed_count,
            'error_count': self.error_count,
            'queue_size': self.ingestion_queue.qsize(),
            'watched_directories': self.config.watch_directories,
            'running': self.running
        }

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Document Ingestion Pipeline')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--watch', nargs='+', help='Directories to watch')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config_data = yaml.safe_load(f) if args.config.endswith('.yaml') else json.load(f)
    else:
        config_data = {
            'watch_directories': args.watch or ['./docs', './src'],
            'file_patterns': ['*.md', '*.txt', '*.py', '*.js', '*.ts', '*.yaml', '*.json'],
            'excluded_patterns': ['*test*', '*__pycache__*', '*.pyc', 'node_modules/*'],
            'batch_size': 10,
            'batch_timeout': 30,
            'max_document_size': 1_000_000,
            'chunk_size': 1000,
            'chunk_overlap': 200
        }
    
    config = IngestConfig(**config_data)
    
    # Vector store configuration
    vector_config = {
        'store_type': 'faiss',
        'dimension': 768,
        'vertex_ai': {
            'project_id': os.environ.get('GCP_PROJECT_ID', 'gemini-enterprise-architect'),
            'region': 'us-central1'
        }
    }
    
    # Create and start pipeline
    pipeline = DocumentIngestionPipeline(config, vector_config)
    
    try:
        await pipeline.start()
        
        if args.daemon:
            logger.info("Running in daemon mode. Press Ctrl+C to stop.")
            while pipeline.running:
                await asyncio.sleep(10)
                stats = pipeline.get_statistics()
                logger.info(f"Pipeline stats: {stats}")
        else:
            # Run for a short time then exit
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await pipeline.stop()
        
        # Final statistics
        stats = pipeline.get_statistics()
        logger.info(f"Final statistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main()