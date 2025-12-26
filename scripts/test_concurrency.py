#!/usr/bin/env python3
"""
Concurrency Test Suite - Tests API scalability with 20 simultaneous users
Validates thread pool improvements and production readiness (Gunicorn + 4 workers)
"""

import requests
import sys
import time
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, stdev, median

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"
NUM_CONCURRENT_USERS = 20
TEST_TXT_CONTENT = "Este é um documento de teste para o sistema RAG. O presidente do CREA Goiás é o Engenheiro Civil Lamartine Moreira."

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.auth import create_access_token


@dataclass
class ConcurrencyTestResult:
    """Result of a single concurrent request"""
    user_id: int
    operation: str
    success: bool
    duration: float
    error: str = ""


class ConcurrencyTester:
    """Tests API concurrency with multiple simultaneous users"""
    
    def __init__(self, num_users: int = NUM_CONCURRENT_USERS):
        self.num_users = num_users
        self.base_url = BASE_URL
        self.api_v1 = API_V1
        self.results: List[ConcurrencyTestResult] = []
        self.test_corpus_id: str = ""
        
    def log(self, emoji: str, message: str):
        """Pretty logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {message}")
        
    def print_section(self, title: str):
        """Print section separator"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
        
    def setup_corpus(self) -> bool:
        """Setup: Create a test corpus for all users to use"""
        self.log("🔧", "Setting up test corpus...")
        
        token = create_access_token(subject="setup_user", purpose="admin")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to create corpus
        corpus_data = {
            "department_name": "ConcurrencyTest",
            "description": "Corpus for concurrency testing"
        }
        
        response = requests.post(
            f"{self.api_v1}/management/corpus",
            json=corpus_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            self.test_corpus_id = response.json()["id"]
            self.log("✅", f"Corpus created: {self.test_corpus_id[:8]}...")
            return True
        elif response.status_code == 409:
            # Already exists, get it
            list_response = requests.get(f"{self.api_v1}/management/corpus", headers=headers)
            corpora = list_response.json()
            corpus = next((c for c in corpora if c["display_name"] == "DEP-ConcurrencyTest"), None)
            if corpus:
                self.test_corpus_id = corpus["id"]
                self.log("✅", f"Using existing corpus: {self.test_corpus_id[:8]}...")
                return True
        
        self.log("❌", "Failed to setup corpus")
        return False
        
    def cleanup_corpus(self):
        """Cleanup: Delete test corpus"""
        if not self.test_corpus_id:
            return
            
        self.log("🧹", "Cleaning up test corpus...")
        token = create_access_token(subject="cleanup_user", purpose="admin")
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            requests.delete(
                f"{self.api_v1}/management/corpus/{self.test_corpus_id}?confirm=true",
                headers=headers,
                timeout=30
            )
            self.log("✅", "Cleanup complete")
        except:
            pass
    
    def single_user_chat(self, user_id: int) -> ConcurrencyTestResult:
        """Simulate a single user sending a chat message"""
        operation = f"User {user_id:02d} Chat"
        
        try:
            # Generate unique token for this user
            token = create_access_token(subject=f"user_{user_id}", purpose="admin")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Send chat request
            chat_data = {
                "message": f"Usuário {user_id}: Quem é o presidente do CREA-GO?",
                "history": [],
                "corpus_id": self.test_corpus_id
            }
            
            start = time.time()
            response = requests.post(
                f"{self.api_v1}/chat/",
                json=chat_data,
                headers=headers,
                timeout=120
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                return ConcurrencyTestResult(
                    user_id=user_id,
                    operation=operation,
                    success=True,
                    duration=duration
                )
            else:
                return ConcurrencyTestResult(
                    user_id=user_id,
                    operation=operation,
                    success=False,
                    duration=duration,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start if 'start' in locals() else 0
            return ConcurrencyTestResult(
                user_id=user_id,
                operation=operation,
                success=False,
                duration=duration,
                error=str(e)
            )
    
    def test_sequential_chat(self) -> Tuple[List[float], float]:
        """Test: 20 users sending messages SEQUENTIALLY (baseline)"""
        self.print_section("TEST 1: Sequential Chat (Baseline)")
        self.log("👤", f"Testing {self.num_users} users SEQUENTIALLY...")
        
        latencies = []
        start_total = time.time()
        
        for i in range(self.num_users):
            result = self.single_user_chat(i + 1)
            latencies.append(result.duration)
            
            status = "✅" if result.success else "❌"
            print(f"  {status} User {result.user_id:02d}: {result.duration:.2f}s", end="")
            if not result.success:
                print(f" ({result.error})")
            else:
                print()
        
        total_time = time.time() - start_total
        
        # Statistics
        print(f"\n📊 Sequential Results:")
        print(f"  Total Time:    {total_time:.2f}s")
        print(f"  Avg Latency:   {mean(latencies):.2f}s")
        print(f"  Min Latency:   {min(latencies):.2f}s")
        print(f"  Max Latency:   {max(latencies):.2f}s")
        print(f"  Median:        {median(latencies):.2f}s")
        if len(latencies) > 1:
            print(f"  Std Dev:       {stdev(latencies):.2f}s")
        
        return latencies, total_time
    
    def test_concurrent_chat(self) -> Tuple[List[float], float]:
        """Test: 20 users sending messages CONCURRENTLY"""
        self.print_section("TEST 2: Concurrent Chat (20 Simultaneous Users)")
        self.log("👥", f"Testing {self.num_users} users CONCURRENTLY...")
        
        latencies = []
        start_total = time.time()
        
        # Use ThreadPoolExecutor to simulate concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_users) as executor:
            # Submit all requests at once
            futures = [
                executor.submit(self.single_user_chat, i + 1)
                for i in range(self.num_users)
            ]
            
            # Wait for all to complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                latencies.append(result.duration)
                
                status = "✅" if result.success else "❌"
                print(f"  {status} User {result.user_id:02d}: {result.duration:.2f}s", end="")
                if not result.success:
                    print(f" ({result.error})")
                else:
                    print()
        
        total_time = time.time() - start_total
        
        # Statistics
        print(f"\n📊 Concurrent Results:")
        print(f"  Total Time:    {total_time:.2f}s")
        print(f"  Avg Latency:   {mean(latencies):.2f}s")
        print(f"  Min Latency:   {min(latencies):.2f}s")
        print(f"  Max Latency:   {max(latencies):.2f}s")
        print(f"  Median:        {median(latencies):.2f}s")
        if len(latencies) > 1:
            print(f"  Std Dev:       {stdev(latencies):.2f}s")
        print(f"  Throughput:    {self.num_users / total_time:.2f} req/s")
        
        return latencies, total_time
    
    def compare_results(self, seq_latencies: List[float], seq_time: float,
                       con_latencies: List[float], con_time: float):
        """Compare sequential vs concurrent results"""
        self.print_section("COMPARISON: Sequential vs Concurrent")
        
        print(f"\n{'Metric':<25} {'Sequential':<15} {'Concurrent':<15} {'Improvement'}")
        print("-" * 80)
        
        # Total Time
        speedup = seq_time / con_time
        print(f"{'Total Time':<25} {seq_time:>10.2f}s     {con_time:>10.2f}s     {speedup:>6.2f}x faster")
        
        # Average Latency
        seq_avg = mean(seq_latencies)
        con_avg = mean(con_latencies)
        latency_diff = ((con_avg - seq_avg) / seq_avg) * 100
        print(f"{'Avg Latency':<25} {seq_avg:>10.2f}s     {con_avg:>10.2f}s     {latency_diff:>+6.1f}%")
        
        # Max Latency
        seq_max = max(seq_latencies)
        con_max = max(con_latencies)
        max_diff = ((con_max - seq_max) / seq_max) * 100
        print(f"{'Max Latency (P100)':<25} {seq_max:>10.2f}s     {con_max:>10.2f}s     {max_diff:>+6.1f}%")
        
        # P95 Latency
        seq_p95 = sorted(seq_latencies)[int(len(seq_latencies) * 0.95)]
        con_p95 = sorted(con_latencies)[int(len(con_latencies) * 0.95)]
        p95_diff = ((con_p95 - seq_p95) / seq_p95) * 100
        print(f"{'P95 Latency':<25} {seq_p95:>10.2f}s     {con_p95:>10.2f}s     {p95_diff:>+6.1f}%")
        
        # Throughput
        seq_throughput = self.num_users / seq_time
        con_throughput = self.num_users / con_time
        throughput_gain = (con_throughput - seq_throughput) / seq_throughput * 100
        print(f"{'Throughput (req/s)':<25} {seq_throughput:>10.2f}      {con_throughput:>10.2f}      {throughput_gain:>+6.1f}%")
        
        print("\n" + "=" * 80)
        
        # Verdict
        if speedup >= 15:  # Close to 20x (ideal for 20 users)
            print("✅ EXCELLENT: Near-ideal parallelism achieved!")
        elif speedup >= 10:
            print("✅ GOOD: Strong parallelism with some overhead")
        elif speedup >= 5:
            print("⚠️  ACCEPTABLE: Moderate parallelism, some queuing")
        else:
            print("❌ POOR: Significant queuing, needs optimization")
        
        print(f"\n🎯 Key Insight:")
        if speedup >= 15:
            print(f"   With {speedup:.1f}x speedup, the API can handle {self.num_users} concurrent users")
            print(f"   with minimal queuing. Thread pool improvements are working!")
        elif speedup >= 5:
            print(f"   With {speedup:.1f}x speedup, some concurrent requests are queuing.")
            print(f"   Consider increasing thread pool size or workers.")
        else:
            print(f"   With only {speedup:.1f}x speedup, severe queuing detected.")
            print(f"   Multi-worker setup or thread pool needs adjustment.")
        
        print("=" * 80)
    
    def run_all_tests(self):
        """Run complete concurrency test suite"""
        print("\n" + "=" * 80)
        print("  CONCURRENCY TEST SUITE - API Scalability Validation")
        print("  Testing with Gunicorn + 4 Workers + 50-thread Pool")
        print("=" * 80)
        
        # Check health
        self.log("🏥", "Checking API health...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                self.log("❌", "API is not healthy! Aborting tests.")
                return False
            self.log("✅", "API is healthy")
        except Exception as e:
            self.log("❌", f"Cannot reach API: {e}")
            return False
        
        # Setup
        if not self.setup_corpus():
            self.log("❌", "Failed to setup test environment")
            return False
        
        # Warm-up request (to avoid cold start affecting results)
        self.log("🔥", "Warming up (1 request)...")
        self.single_user_chat(0)
        time.sleep(2)
        
        try:
            # Test 1: Sequential
            seq_latencies, seq_time = self.test_sequential_chat()
            time.sleep(3)  # Cooldown
            
            # Test 2: Concurrent
            con_latencies, con_time = self.test_concurrent_chat()
            
            # Compare
            self.compare_results(seq_latencies, seq_time, con_latencies, con_time)
            
        finally:
            # Cleanup
            self.cleanup_corpus()
        
        print("\n✅ Concurrency test suite completed!\n")
        return True


def main():
    """Main entry point"""
    tester = ConcurrencyTester(num_users=20)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
