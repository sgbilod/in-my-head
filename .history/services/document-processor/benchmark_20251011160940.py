"""
Performance Benchmarking Script for Document Processing API

Measures actual performance metrics for all API endpoints.

Run with: python benchmark.py
"""

import os
import time
import tempfile
import statistics
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

import requests
from rich.console import Console
from rich.table import Table
from rich.progress import track


# Configuration
API_KEY = os.getenv("API_KEY", "test-api-key-123")
BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": API_KEY}

console = Console()


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.errors: List[str] = []
    
    def add_result(self, duration: float, success: bool, error: str = None):
        """Add a result."""
        self.times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.errors.append(error)
    
    @property
    def mean(self) -> float:
        """Mean response time."""
        return statistics.mean(self.times) if self.times else 0
    
    @property
    def median(self) -> float:
        """Median response time."""
        return statistics.median(self.times) if self.times else 0
    
    @property
    def p95(self) -> float:
        """95th percentile response time."""
        if not self.times:
            return 0
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]
    
    @property
    def p99(self) -> float:
        """99th percentile response time."""
        if not self.times:
            return 0
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx]
    
    @property
    def min(self) -> float:
        """Minimum response time."""
        return min(self.times) if self.times else 0
    
    @property
    def max(self) -> float:
        """Maximum response time."""
        return max(self.times) if self.times else 0
    
    @property
    def success_rate(self) -> float:
        """Success rate."""
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0


class APIBenchmark:
    """API performance benchmark suite."""
    
    def __init__(self):
        self.results: Dict[str, BenchmarkResult] = {}
        self.temp_dir = tempfile.mkdtemp()
        self.job_ids: List[str] = []
    
    def benchmark(self, name: str, iterations: int = 100):
        """Decorator for benchmark tests."""
        def decorator(func):
            def wrapper():
                result = BenchmarkResult(name)
                self.results[name] = result
                
                console.print(f"\n[cyan]Benchmarking: {name}[/cyan]")
                
                for _ in track(range(iterations), description=f"Running {name}..."):
                    start = time.perf_counter()
                    try:
                        func()
                        duration = (time.perf_counter() - start) * 1000  # ms
                        result.add_result(duration, True)
                    except Exception as e:
                        duration = (time.perf_counter() - start) * 1000
                        result.add_result(duration, False, str(e))
                    
                    # Small delay to avoid overwhelming the API
                    time.sleep(0.01)
                
                return result
            
            return wrapper
        return decorator
    
    def run_all(self):
        """Run all benchmarks."""
        console.print("\n[bold green]Starting API Performance Benchmarks[/bold green]")
        console.print(f"Base URL: {BASE_URL}")
        console.print(f"Timestamp: {datetime.now().isoformat()}\n")
        
        # Run benchmarks
        self.benchmark_health_check()
        self.benchmark_statistics()
        self.benchmark_upload_small()
        self.benchmark_job_status()
        self.benchmark_search_simple()
        self.benchmark_search_with_filters()
        
        # Print results
        self.print_results()
        
        # Save results
        self.save_results()
    
    @benchmark("Health Check", iterations=200)
    def benchmark_health_check(self):
        """Benchmark health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            raise Exception(f"Status code: {response.status_code}")
    
    @benchmark("Statistics", iterations=200)
    def benchmark_statistics(self):
        """Benchmark statistics endpoint."""
        response = requests.get(f"{BASE_URL}/api/v1/statistics", headers=HEADERS)
        if response.status_code not in [200, 429]:  # Allow rate limiting
            raise Exception(f"Status code: {response.status_code}")
    
    @benchmark("Upload Small Document", iterations=50)
    def benchmark_upload_small(self):
        """Benchmark uploading small documents."""
        # Create small temp file
        content = "This is a test document for benchmarking."
        filename = f"bench_{int(time.time() * 1000000)}.txt"
        filepath = Path(self.temp_dir) / filename
        filepath.write_text(content)
        
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f, "text/plain")}
                response = requests.post(
                    f"{BASE_URL}/api/v1/documents",
                    files=files,
                    headers=HEADERS
                )
            
            if response.status_code == 200:
                data = response.json()
                self.job_ids.append(data["job_id"])
            elif response.status_code != 429:  # Allow rate limiting
                raise Exception(f"Status code: {response.status_code}")
        finally:
            filepath.unlink(missing_ok=True)
    
    @benchmark("Job Status Check", iterations=100)
    def benchmark_job_status(self):
        """Benchmark job status endpoint."""
        if not self.job_ids:
            # Create a dummy job first
            self.benchmark_upload_small()
        
        if not self.job_ids:
            raise Exception("No jobs available for status check")
        
        # Use a random job_id
        import random
        job_id = random.choice(self.job_ids)
        
        response = requests.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers=HEADERS
        )
        
        if response.status_code not in [200, 404, 429]:
            raise Exception(f"Status code: {response.status_code}")
    
    @benchmark("Search Simple", iterations=50)
    def benchmark_search_simple(self):
        """Benchmark simple search."""
        search_data = {
            "query": "test document",
            "limit": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search",
            json=search_data,
            headers=HEADERS
        )
        
        if response.status_code not in [200, 429]:
            raise Exception(f"Status code: {response.status_code}")
    
    @benchmark("Search With Filters", iterations=50)
    def benchmark_search_with_filters(self):
        """Benchmark search with filters."""
        search_data = {
            "query": "machine learning",
            "topics": ["AI", "technology"],
            "limit": 20
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search",
            json=search_data,
            headers=HEADERS
        )
        
        if response.status_code not in [200, 429]:
            raise Exception(f"Status code: {response.status_code}")
    
    def print_results(self):
        """Print benchmark results as a table."""
        console.print("\n[bold green]Benchmark Results[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Iterations", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Mean (ms)", justify="right")
        table.add_column("Median (ms)", justify="right")
        table.add_column("P95 (ms)", justify="right")
        table.add_column("P99 (ms)", justify="right")
        table.add_column("Min (ms)", justify="right")
        table.add_column("Max (ms)", justify="right")
        
        for name, result in self.results.items():
            total = result.success_count + result.failure_count
            
            # Color code based on success rate
            success_style = "green" if result.success_rate >= 95 else "yellow" if result.success_rate >= 80 else "red"
            
            table.add_row(
                name,
                str(total),
                f"[{success_style}]{result.success_rate:.1f}%[/{success_style}]",
                f"{result.mean:.2f}",
                f"{result.median:.2f}",
                f"{result.p95:.2f}",
                f"{result.p99:.2f}",
                f"{result.min:.2f}",
                f"{result.max:.2f}",
            )
        
        console.print(table)
        
        # Print any errors
        for name, result in self.results.items():
            if result.errors:
                console.print(f"\n[red]Errors in {name}:[/red]")
                for error in result.errors[:5]:  # Show first 5
                    console.print(f"  - {error}")
    
    def save_results(self):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.txt"
        
        with open(filename, "w") as f:
            f.write("API Performance Benchmark Results\n")
            f.write("=" * 80 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Base URL: {BASE_URL}\n")
            f.write("\n")
            
            for name, result in self.results.items():
                total = result.success_count + result.failure_count
                f.write(f"\n{name}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Iterations: {total}\n")
                f.write(f"Success Rate: {result.success_rate:.2f}%\n")
                f.write(f"Mean: {result.mean:.2f}ms\n")
                f.write(f"Median: {result.median:.2f}ms\n")
                f.write(f"P95: {result.p95:.2f}ms\n")
                f.write(f"P99: {result.p99:.2f}ms\n")
                f.write(f"Min: {result.min:.2f}ms\n")
                f.write(f"Max: {result.max:.2f}ms\n")
                
                if result.errors:
                    f.write(f"\nErrors ({len(result.errors)}):\n")
                    for error in result.errors[:10]:
                        f.write(f"  - {error}\n")
        
        console.print(f"\n[green]Results saved to: {filename}[/green]")


def main():
    """Main entry point."""
    try:
        # Check if API is available
        console.print("[cyan]Checking API availability...[/cyan]")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            console.print("[red]API is not healthy. Please start the API server.[/red]")
            return
        
        console.print("[green]API is available![/green]")
        
        # Run benchmarks
        benchmark = APIBenchmark()
        benchmark.run_all()
        
    except requests.exceptions.ConnectionError:
        console.print(f"[red]Cannot connect to {BASE_URL}[/red]")
        console.print("[yellow]Please start the API server first.[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
