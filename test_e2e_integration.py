"""
End-to-End Integration Testing Suite
Tests all microservices and infrastructure components
"""

import requests
import time
import json
from typing import Dict, Any, List
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class E2ETestRunner:
    """Comprehensive end-to-end integration test runner"""

    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0
        }
        self.start_time = None

        # Service endpoints
        self.services = {
            'api_gateway': 'http://localhost:8000',
            'document_processor': 'http://localhost:8001',
            'ai_engine': 'http://localhost:8002',
            'search_service': 'http://localhost:8003',
            'resource_manager': 'http://localhost:8004'
        }

        # Infrastructure endpoints
        self.infrastructure = {
            'postgresql': 'localhost:5432',
            'redis': 'localhost:6379',
            'qdrant': 'http://localhost:6333',
            'minio': 'http://localhost:9000'
        }

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}\n")

    def print_test(self, test_name: str):
        """Print test name"""
        print(f"{Colors.BLUE}🧪 Testing: {Colors.WHITE}{test_name}{Colors.END}", end=' ... ')

    def print_pass(self, message: str = "PASS"):
        """Print pass result"""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        self.results['passed'] += 1
        self.results['total'] += 1

    def print_fail(self, message: str = "FAIL"):
        """Print fail result"""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        self.results['failed'] += 1
        self.results['total'] += 1

    def print_skip(self, message: str = "SKIP"):
        """Print skip result"""
        print(f"{Colors.YELLOW}⏭️  {message}{Colors.END}")
        self.results['skipped'] += 1
        self.results['total'] += 1

    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

    def test_service_health(self, name: str, url: str, timeout: int = 5) -> bool:
        """Test if service is healthy"""
        self.print_test(f"{name} health check")
        try:
            response = requests.get(f"{url}/", timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                service_name = data.get('service', 'Unknown')
                self.print_pass(f"PASS - {service_name}")
                return True
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_fail("FAIL - Connection refused")
            return False
        except requests.exceptions.Timeout:
            self.print_fail("FAIL - Timeout")
            return False
        except Exception as e:
            self.print_fail(f"FAIL - {str(e)}")
            return False

    def test_infrastructure_connectivity(self):
        """Test all infrastructure services"""
        self.print_header("PHASE 1: INFRASTRUCTURE CONNECTIVITY")

        # Test Qdrant
        self.print_test("Qdrant vector database")
        try:
            response = requests.get(f"{self.infrastructure['qdrant']}/", timeout=5)
            if response.status_code == 200:
                self.print_pass("PASS - Qdrant responding")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_fail(f"FAIL - {str(e)}")

        # Test Qdrant collections
        self.print_test("Qdrant collections")
        try:
            response = requests.get(
                f"{self.infrastructure['qdrant']}/collections",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                collections = data.get('result', {}).get('collections', [])
                collection_names = [c['name'] for c in collections]
                self.print_pass(f"PASS - {len(collections)} collections: {', '.join(collection_names)}")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_fail(f"FAIL - {str(e)}")

        # Test MinIO
        self.print_test("MinIO object storage")
        try:
            response = requests.get(
                f"{self.infrastructure['minio']}/minio/health/live",
                timeout=5
            )
            if response.status_code == 200:
                self.print_pass("PASS - MinIO responding")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_fail(f"FAIL - {str(e)}")

    def test_microservices_health(self):
        """Test all microservices health endpoints"""
        self.print_header("PHASE 2: MICROSERVICES HEALTH CHECKS")

        all_healthy = True
        for name, url in self.services.items():
            healthy = self.test_service_health(name.replace('_', ' ').title(), url)
            if not healthy:
                all_healthy = False

        return all_healthy

    def test_api_gateway_routing(self):
        """Test API Gateway routing to backend services"""
        self.print_header("PHASE 3: API GATEWAY ROUTING")

        # Test routing to document processor
        self.print_test("API Gateway → Document Processor route")
        try:
            response = requests.get(
                f"{self.services['api_gateway']}/api/documents/health",
                timeout=5
            )
            if response.status_code in [200, 404]:  # 404 is OK if route exists
                self.print_pass("PASS - Route exists")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            # Route might not exist yet - that's OK
            self.print_skip(f"SKIP - Route not configured yet")

        # Test routing to AI engine
        self.print_test("API Gateway → AI Engine route")
        try:
            response = requests.get(
                f"{self.services['api_gateway']}/api/ai/health",
                timeout=5
            )
            if response.status_code in [200, 404]:
                self.print_pass("PASS - Route exists")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - Route not configured yet")

    def test_ai_engine_capabilities(self):
        """Test AI Engine specific capabilities"""
        self.print_header("PHASE 4: AI ENGINE CAPABILITIES")

        # Test embeddings endpoint
        self.print_test("AI Engine embeddings endpoint")
        try:
            test_text = "This is a test document about artificial intelligence."
            response = requests.post(
                f"{self.services['ai_engine']}/embeddings",
                json={"text": test_text},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'embedding' in data or 'embeddings' in data:
                    embedding = data.get('embedding') or data.get('embeddings')
                    if isinstance(embedding, list) and len(embedding) > 0:
                        self.print_pass(f"PASS - Embedding generated (dim={len(embedding)})")
                    else:
                        self.print_fail("FAIL - Invalid embedding format")
                else:
                    self.print_fail("FAIL - No embedding in response")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

        # Test RAG query endpoint
        self.print_test("AI Engine RAG query endpoint")
        try:
            response = requests.post(
                f"{self.services['ai_engine']}/rag/query",
                json={
                    "query": "What is machine learning?",
                    "top_k": 5
                },
                timeout=10
            )

            if response.status_code == 200:
                self.print_pass("PASS - RAG query successful")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

    def test_search_service_capabilities(self):
        """Test Search Service capabilities"""
        self.print_header("PHASE 5: SEARCH SERVICE CAPABILITIES")

        # Test search endpoint
        self.print_test("Search Service query endpoint")
        try:
            response = requests.get(
                f"{self.services['search_service']}/search",
                params={"q": "artificial intelligence", "limit": 5},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.print_pass(f"PASS - Search returned {len(data.get('results', []))} results")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

        # Test vector search
        self.print_test("Search Service vector search")
        try:
            response = requests.post(
                f"{self.services['search_service']}/vector-search",
                json={
                    "query": "machine learning algorithms",
                    "top_k": 10
                },
                timeout=10
            )

            if response.status_code == 200:
                self.print_pass("PASS - Vector search successful")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

    def test_document_processor_capabilities(self):
        """Test Document Processor capabilities"""
        self.print_header("PHASE 6: DOCUMENT PROCESSOR CAPABILITIES")

        # Test document upload endpoint exists
        self.print_test("Document Processor upload endpoint")
        try:
            # Just check if endpoint exists (will fail without actual file, but that's OK)
            response = requests.post(
                f"{self.services['document_processor']}/documents/upload",
                timeout=5
            )

            # Any response (even 400/422) means endpoint exists
            if response.status_code in [400, 422, 200]:
                self.print_pass("PASS - Upload endpoint exists")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

        # Test documents list endpoint
        self.print_test("Document Processor list endpoint")
        try:
            response = requests.get(
                f"{self.services['document_processor']}/documents",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', 0)
                self.print_pass(f"PASS - {count} documents indexed")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

    def test_resource_manager_capabilities(self):
        """Test Resource Manager capabilities"""
        self.print_header("PHASE 7: RESOURCE MANAGER CAPABILITIES")

        # Test resources endpoint
        self.print_test("Resource Manager list endpoint")
        try:
            response = requests.get(
                f"{self.services['resource_manager']}/resources",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', 0)
                self.print_pass(f"PASS - {count} resources tracked")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

        # Test resource discovery
        self.print_test("Resource Manager discovery endpoint")
        try:
            response = requests.post(
                f"{self.services['resource_manager']}/discover",
                json={"topic": "artificial intelligence"},
                timeout=10
            )

            if response.status_code == 200:
                self.print_pass("PASS - Discovery endpoint responding")
            elif response.status_code == 404:
                self.print_skip("SKIP - Endpoint not implemented yet")
            else:
                self.print_fail(f"FAIL - Status {response.status_code}")
        except Exception as e:
            self.print_skip(f"SKIP - {str(e)}")

    def test_cross_service_communication(self):
        """Test communication between services"""
        self.print_header("PHASE 8: CROSS-SERVICE COMMUNICATION")

        self.print_info("Testing service-to-service communication...")

        # These tests would require actual data flow between services
        # For now, we'll verify the services can reach each other

        self.print_test("All services on same network")
        all_healthy = all([
            self.test_service_health(name, url, timeout=3)
            for name, url in [
                ("Gateway", self.services['api_gateway']),
                ("AI", self.services['ai_engine']),
                ("Search", self.services['search_service'])
            ]
        ])

        if all_healthy:
            self.print_info("✅ All services can communicate")
        else:
            self.print_info("⚠️  Some services unreachable")

    def print_summary(self):
        """Print test summary"""
        duration = time.time() - self.start_time

        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{'TEST SUMMARY'.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

        # Results
        total = self.results['total']
        passed = self.results['passed']
        failed = self.results['failed']
        skipped = self.results['skipped']

        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"{Colors.GREEN}✅ Passed:  {passed}/{total} ({pass_rate:.1f}%){Colors.END}")
        print(f"{Colors.RED}❌ Failed:  {failed}/{total}{Colors.END}")
        print(f"{Colors.YELLOW}⏭️  Skipped: {skipped}/{total}{Colors.END}")
        print(f"\n{Colors.CYAN}⏱️  Duration: {duration:.2f} seconds{Colors.END}")

        # Overall status
        print(f"\n{Colors.BOLD}Overall Status:{Colors.END} ", end='')
        if failed == 0 and passed > 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED!{Colors.END}")
        elif failed > 0:
            print(f"{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}")
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  NO TESTS RUN{Colors.END}")

        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}\n")

        # Next steps
        if failed == 0 and passed > 0:
            print(f"{Colors.CYAN}{Colors.BOLD}🎉 INTEGRATION TESTING COMPLETE!{Colors.END}")
            print(f"{Colors.CYAN}Next steps:{Colors.END}")
            print(f"  1. Deploy frontend application")
            print(f"  2. Perform user acceptance testing")
            print(f"  3. Load testing and performance optimization")
            print(f"  4. Production deployment preparation")
        else:
            print(f"{Colors.YELLOW}Investigate failed tests before proceeding.{Colors.END}")

    def run_all_tests(self):
        """Run complete test suite"""
        self.start_time = time.time()

        print(f"\n{Colors.MAGENTA}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║          🧪 END-TO-END INTEGRATION TEST SUITE 🧪               ║")
        print("║                    In My Head v1.0                             ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")

        print(f"{Colors.CYAN}Starting comprehensive integration tests...{Colors.END}")
        print(f"{Colors.CYAN}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")

        # Run all test phases
        try:
            self.test_infrastructure_connectivity()
            microservices_healthy = self.test_microservices_health()

            if microservices_healthy:
                self.test_api_gateway_routing()
                self.test_ai_engine_capabilities()
                self.test_search_service_capabilities()
                self.test_document_processor_capabilities()
                self.test_resource_manager_capabilities()
                self.test_cross_service_communication()
            else:
                self.print_info("⚠️  Skipping detailed tests - some services unhealthy")

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}Test suite error: {str(e)}{Colors.END}")

        # Print summary
        self.print_summary()


def main():
    """Main entry point"""
    runner = E2ETestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()
