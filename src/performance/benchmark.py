"""
Performance Benchmarking Suite
Validates and measures performance optimizations
Epic 7: Performance Optimization Validation
"""

import asyncio
import time
import random
import statistics
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Result from a benchmark run"""
    name: str
    iterations: int
    duration_seconds: float
    operations_per_second: float
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    p95_time: float
    p99_time: float
    errors: int
    timestamp: datetime

class PerformanceBenchmark:
    """Performance benchmarking suite"""
    
    def __init__(self):
        self.results = []
        self.current_benchmark = None
    
    async def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
        concurrent: bool = False,
        concurrency: int = 10
    ) -> BenchmarkResult:
        """Run a performance benchmark"""
        logger.info(f"Starting benchmark: {name}")
        self.current_benchmark = name
        
        # Warmup phase
        logger.debug(f"Running {warmup} warmup iterations")
        for _ in range(warmup):
            try:
                await func()
            except Exception as e:
                logger.warning(f"Warmup error: {e}")
        
        # Benchmark phase
        times = []
        errors = 0
        start_time = time.time()
        
        if concurrent:
            # Run concurrent benchmark
            times, errors = await self._run_concurrent(func, iterations, concurrency)
        else:
            # Run sequential benchmark
            times, errors = await self._run_sequential(func, iterations)
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if times:
            result = BenchmarkResult(
                name=name,
                iterations=iterations,
                duration_seconds=total_duration,
                operations_per_second=len(times) / total_duration,
                min_time=min(times),
                max_time=max(times),
                avg_time=statistics.mean(times),
                median_time=statistics.median(times),
                p95_time=self._percentile(times, 95),
                p99_time=self._percentile(times, 99),
                errors=errors,
                timestamp=datetime.now()
            )
        else:
            # All operations failed
            result = BenchmarkResult(
                name=name,
                iterations=iterations,
                duration_seconds=total_duration,
                operations_per_second=0,
                min_time=0,
                max_time=0,
                avg_time=0,
                median_time=0,
                p95_time=0,
                p99_time=0,
                errors=errors,
                timestamp=datetime.now()
            )
        
        self.results.append(result)
        logger.info(f"Benchmark '{name}' completed: {result.operations_per_second:.2f} ops/sec")
        
        return result
    
    async def _run_sequential(
        self,
        func: Callable,
        iterations: int
    ) -> tuple[List[float], int]:
        """Run sequential benchmark"""
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                start = time.perf_counter()
                await func()
                duration = time.perf_counter() - start
                times.append(duration)
            except Exception as e:
                errors += 1
                logger.debug(f"Benchmark error in iteration {i}: {e}")
        
        return times, errors
    
    async def _run_concurrent(
        self,
        func: Callable,
        iterations: int,
        concurrency: int
    ) -> tuple[List[float], int]:
        """Run concurrent benchmark"""
        times = []
        errors = 0
        
        async def timed_func():
            try:
                start = time.perf_counter()
                await func()
                return time.perf_counter() - start
            except Exception as e:
                logger.debug(f"Concurrent benchmark error: {e}")
                return None
        
        # Run in batches
        for batch_start in range(0, iterations, concurrency):
            batch_size = min(concurrency, iterations - batch_start)
            tasks = [timed_func() for _ in range(batch_size)]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                elif result is None:
                    errors += 1
                else:
                    times.append(result)
        
        return times, errors
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        
        if index >= len(sorted_data):
            return sorted_data[-1]
        
        return sorted_data[index]
    
    def compare_results(
        self,
        baseline_name: str,
        comparison_name: str
    ) -> Dict[str, Any]:
        """Compare two benchmark results"""
        baseline = next((r for r in self.results if r.name == baseline_name), None)
        comparison = next((r for r in self.results if r.name == comparison_name), None)
        
        if not baseline or not comparison:
            return {"error": "Results not found"}
        
        improvement = {
            "operations_per_second": (
                (comparison.operations_per_second - baseline.operations_per_second) 
                / baseline.operations_per_second * 100
            ),
            "avg_time": (
                (baseline.avg_time - comparison.avg_time) 
                / baseline.avg_time * 100
            ),
            "p95_time": (
                (baseline.p95_time - comparison.p95_time) 
                / baseline.p95_time * 100
            ),
            "p99_time": (
                (baseline.p99_time - comparison.p99_time) 
                / baseline.p99_time * 100
            )
        }
        
        return {
            "baseline": baseline_name,
            "comparison": comparison_name,
            "improvement_percentage": improvement,
            "baseline_ops_per_sec": baseline.operations_per_second,
            "comparison_ops_per_sec": comparison.operations_per_second
        }
    
    def generate_report(self) -> str:
        """Generate benchmark report"""
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        for result in self.results:
            report.append(f"\nBenchmark: {result.name}")
            report.append("-" * 40)
            report.append(f"Iterations: {result.iterations}")
            report.append(f"Total Duration: {result.duration_seconds:.2f} seconds")
            report.append(f"Operations/Second: {result.operations_per_second:.2f}")
            report.append(f"Average Time: {result.avg_time * 1000:.2f} ms")
            report.append(f"Median Time: {result.median_time * 1000:.2f} ms")
            report.append(f"Min Time: {result.min_time * 1000:.2f} ms")
            report.append(f"Max Time: {result.max_time * 1000:.2f} ms")
            report.append(f"P95 Time: {result.p95_time * 1000:.2f} ms")
            report.append(f"P99 Time: {result.p99_time * 1000:.2f} ms")
            report.append(f"Errors: {result.errors}")
        
        return "\n".join(report)
    
    def export_results(self, filepath: str):
        """Export results to JSON file"""
        data = []
        for result in self.results:
            data.append({
                "name": result.name,
                "iterations": result.iterations,
                "duration_seconds": result.duration_seconds,
                "operations_per_second": result.operations_per_second,
                "min_time": result.min_time,
                "max_time": result.max_time,
                "avg_time": result.avg_time,
                "median_time": result.median_time,
                "p95_time": result.p95_time,
                "p99_time": result.p99_time,
                "errors": result.errors,
                "timestamp": result.timestamp.isoformat()
            })
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results exported to {filepath}")

class CacheBenchmark:
    """Benchmark cache performance"""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
    
    async def run_all_benchmarks(self):
        """Run all cache benchmarks"""
        from ..performance.cache_manager import cache_manager
        
        # Initialize cache
        await cache_manager.initialize()
        
        # Prepare test data
        test_data = {"key": "value", "nested": {"data": "test"}}
        
        # Benchmark cache set
        async def cache_set():
            key = f"benchmark_{random.randint(0, 1000)}"
            await cache_manager.set(key, test_data, ttl=60)
        
        await self.benchmark.run_benchmark(
            "cache_set",
            cache_set,
            iterations=1000
        )
        
        # Benchmark cache get (hits)
        await cache_manager.set("benchmark_hit", test_data, ttl=60)
        
        async def cache_get_hit():
            await cache_manager.get("benchmark_hit")
        
        await self.benchmark.run_benchmark(
            "cache_get_hit",
            cache_get_hit,
            iterations=1000
        )
        
        # Benchmark cache get (misses)
        async def cache_get_miss():
            await cache_manager.get(f"nonexistent_{random.randint(0, 1000)}")
        
        await self.benchmark.run_benchmark(
            "cache_get_miss",
            cache_get_miss,
            iterations=1000
        )
        
        # Benchmark concurrent operations
        await self.benchmark.run_benchmark(
            "cache_concurrent",
            cache_set,
            iterations=1000,
            concurrent=True,
            concurrency=50
        )
        
        # Generate report
        report = self.benchmark.generate_report()
        print(report)
        
        # Export results
        self.benchmark.export_results("cache_benchmark_results.json")
        
        # Cleanup
        await cache_manager.close()

class VectorSearchBenchmark:
    """Benchmark vector search performance"""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
    
    async def run_all_benchmarks(self):
        """Run all vector search benchmarks"""
        from ..performance.vector_search_optimizer import vector_optimizer
        
        # Prepare test documents
        documents = []
        for i in range(1000):
            documents.append({
                'id': f'doc_{i}',
                'content': f'Test document {i} with random content {random.random()}',
                'metadata': {'category': random.choice(['A', 'B', 'C'])}
            })
        
        # Add documents
        await vector_optimizer.add_documents(documents)
        
        # Benchmark vector search
        async def vector_search():
            query = f"test query {random.randint(0, 100)}"
            await vector_optimizer.search(query, k=10)
        
        await self.benchmark.run_benchmark(
            "vector_search",
            vector_search,
            iterations=500
        )
        
        # Benchmark hybrid search
        async def hybrid_search():
            query = f"test document {random.randint(0, 100)}"
            await vector_optimizer.hybrid_search(query, k=10)
        
        await self.benchmark.run_benchmark(
            "hybrid_search",
            hybrid_search,
            iterations=500
        )
        
        # Benchmark concurrent searches
        await self.benchmark.run_benchmark(
            "vector_search_concurrent",
            vector_search,
            iterations=500,
            concurrent=True,
            concurrency=20
        )
        
        # Generate report
        report = self.benchmark.generate_report()
        print(report)
        
        # Export results
        self.benchmark.export_results("vector_search_benchmark_results.json")

class EndToEndBenchmark:
    """End-to-end system benchmark"""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
    
    async def run_all_benchmarks(self):
        """Run end-to-end benchmarks"""
        from ..performance.performance_integration import (
            cached_agent_call,
            optimized_rag_query
        )
        
        # Benchmark cached agent call
        async def agent_call():
            await cached_agent_call(
                "scout",
                "analyze",
                {"content": f"test code {random.randint(0, 100)}"}
            )
        
        await self.benchmark.run_benchmark(
            "cached_agent_call",
            agent_call,
            iterations=100
        )
        
        # Benchmark RAG query
        async def rag_query():
            question = f"What is test topic {random.randint(0, 50)}?"
            await optimized_rag_query(question, k=5)
        
        await self.benchmark.run_benchmark(
            "optimized_rag_query",
            rag_query,
            iterations=100
        )
        
        # Generate report
        report = self.benchmark.generate_report()
        print(report)
        
        # Export results
        self.benchmark.export_results("end_to_end_benchmark_results.json")

async def run_full_benchmark_suite():
    """Run complete benchmark suite"""
    logger.info("Starting full benchmark suite")
    
    # Run cache benchmarks
    cache_bench = CacheBenchmark()
    await cache_bench.run_all_benchmarks()
    
    # Run vector search benchmarks
    vector_bench = VectorSearchBenchmark()
    await vector_bench.run_all_benchmarks()
    
    # Run end-to-end benchmarks
    e2e_bench = EndToEndBenchmark()
    await e2e_bench.run_all_benchmarks()
    
    logger.info("Benchmark suite completed")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run benchmarks
    asyncio.run(run_full_benchmark_suite())