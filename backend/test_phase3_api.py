#!/usr/bin/env python3
"""
Phase 3 API and Infrastructure Test

Tests the API endpoints and infrastructure without requiring workers.
This validates that the Phase 3 components are properly set up.
"""

import requests
import sys

API_BASE_URL = "http://localhost:8000"

class Phase3APITest:
    def __init__(self):
        self.results = {"passed": 0, "failed": 0, "tests": []}

    def test(self, name, passed, message=""):
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if message:
            print(f"       {message}")

        self.results["tests"].append({"name": name, "passed": passed, "message": message})
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1

        return passed

    def test_health(self):
        """Test /health endpoint"""
        print("\n" + "="*60)
        print("Testing API Health")
        print("="*60)

        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            data = response.json()

            self.test(
                "Health Endpoint",
                response.status_code == 200 and data.get("status") == "healthy",
                f"Version: {data.get('version', 'unknown')}"
            )
        except Exception as e:
            self.test("Health Endpoint", False, str(e))

    def test_docs(self):
        """Test Swagger docs are available"""
        print("\n" + "="*60)
        print("Testing API Documentation")
        print("="*60)

        try:
            response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
            self.test(
                "Swagger UI",
                response.status_code == 200,
                "Available at /docs"
            )
        except Exception as e:
            self.test("Swagger UI", False, str(e))

        try:
            response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=5)
            self.test(
                "OpenAPI Schema",
                response.status_code == 200,
                "OpenAPI spec available"
            )
        except Exception as e:
            self.test("OpenAPI Schema", False, str(e))

    def test_elasticsearch_health(self):
        """Test Elasticsearch health endpoint"""
        print("\n" + "="*60)
        print("Testing Elasticsearch")
        print("="*60)

        try:
            response = requests.get(f"{API_BASE_URL}/search/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.test(
                    "Elasticsearch Connection",
                    data.get("status") == "healthy",
                    f"Version: {data.get('elasticsearch_version')}, Cluster: {data.get('cluster_name')}"
                )
                self.test(
                    "Elasticsearch Index",
                    data.get("index_exists") is not None,
                    f"Index exists: {data.get('index_exists')}, Documents: {data.get('document_count', 0)}"
                )
            else:
                self.test("Elasticsearch Connection", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.test("Elasticsearch Connection", False, str(e))

    def test_brands_endpoint(self):
        """Test brands endpoints"""
        print("\n" + "="*60)
        print("Testing Brands Endpoints")
        print("="*60)

        #Test GET /brands
        try:
            response = requests.get(f"{API_BASE_URL}/brands", timeout=5)
            if response.status_code == 200:
                brands = response.json()
                self.test(
                    "GET /brands",
                    True,
                    f"Retrieved {len(brands)} brands"
                )
            else:
                self.test("GET /brands", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.test("GET /brands", False, str(e))

        # Test POST /brands
        try:
            test_brand = {"name": "APITestBrand_Temp"}
            response = requests.post(f"{API_BASE_URL}/brands", json=test_brand, timeout=5)

            if response.status_code == 201:
                brand_data = response.json()
                brand_id = brand_data.get("id")
                self.test(
                    "POST /brands (create)",
                    True,
                    f"Created brand ID: {brand_id}"
                )

                # Test GET /brands/{id}
                response2 = requests.get(f"{API_BASE_URL}/brands/{brand_id}", timeout=5)
                self.test(
                    "GET /brands/{id}",
                    response2.status_code == 200,
                    f"Retrieved brand details"
                )

                # Test GET /brands/{id}/mentions
                response3 = requests.get(f"{API_BASE_URL}/brands/{brand_id}/mentions", timeout=5)
                self.test(
                    "GET /brands/{id}/mentions",
                    response3.status_code == 200,
                    "Mentions endpoint working (0 mentions expected)"
                )

                # Test GET /brands/{id}/sentiment-trend
                response4 = requests.get(f"{API_BASE_URL}/brands/{brand_id}/sentiment-trend", timeout=5)
                self.test(
                    "GET /brands/{id}/sentiment-trend",
                    response4.status_code == 200,
                    "Sentiment trend endpoint working"
                )

            elif response.status_code == 400 and "already exists" in response.text:
                self.test("POST /brands (create)", True, "Brand already exists (expected)")
            else:
                self.test("POST /brands (create)", False, f"HTTP {response.status_code}")

        except Exception as e:
            self.test("POST /brands (create)", False, str(e))

    def test_search_endpoint(self):
        """Test search endpoint"""
        print("\n" + "="*60)
        print("Testing Search Endpoint")
        print("="*60)

        try:
            search_data = {
                "query": "test",
                "limit": 10
            }
            response = requests.post(f"{API_BASE_URL}/search", json=search_data, timeout=5)

            if response.status_code == 200:
                data = response.json()
                self.test(
                    "POST /search",
                    True,
                    f"Search returned {data.get('total', 0)} results in {data.get('took_ms', 0)}ms"
                )
            else:
                self.test("POST /search", False, f"HTTP {response.status_code}")

        except Exception as e:
            self.test("POST /search", False, str(e))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total = self.results["passed"] + self.results["failed"]
        print(f"\nTotal Tests: {total}")
        print(f"✓ Passed: {self.results['passed']}")
        print(f"✗ Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['passed']/total*100) if total > 0 else 0:.1f}%")

        if self.results["failed"] > 0:
            print("\nFailed Tests:")
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  ✗ {test['name']}")
                    if test["message"]:
                        print(f"    {test['message']}")

        print("\n" + "="*60)

        return self.results["failed"] == 0

    def run(self):
        """Run all API tests"""
        print("\n" + "="*60)
        print("PHASE 3 API & INFRASTRUCTURE TEST")
        print("="*60)

        self.test_health()
        self.test_docs()
        self.test_elasticsearch_health()
        self.test_brands_endpoint()
        self.test_search_endpoint()

        return self.print_summary()


if __name__ == "__main__":
    tester = Phase3APITest()
    success = tester.run()
    exit(0 if success else 1)
