#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Production Readiness
Tests all endpoints, authentication, error handling, and validates production readiness.
"""

import requests
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"
TEST_FILE_PATH = "tests/arquivo_teste.txt"
TEST_TXT_CONTENT = "Este é um documento de teste para o sistema RAG. O presidente do CREA Goiás é o Engenheiro Civil Lamartine Moreira. A sede fica na Rua 239, Setor Universitário."

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.auth import create_access_token


@dataclass
class TestResult:
    """Test result data class"""
    name: str
    passed: bool
    message: str
    duration: float
    endpoint: str = ""


class APITester:
    """Comprehensive API Testing Suite"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.test_corpus_id: Optional[str] = None
        self.test_file_id: Optional[str] = None
        self.temp_files: List[str] = []
        
    def log(self, emoji: str, message: str):
        """Pretty logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {message}")
        
    def add_result(self, name: str, passed: bool, message: str, duration: float, endpoint: str = ""):
        """Add test result"""
        result = TestResult(name, passed, message, duration, endpoint)
        self.results.append(result)
        
        status_emoji = "✅" if passed else "❌"
        status_text = "PASS" if passed else "FAIL"
        self.log(status_emoji, f"{status_text}: {name} ({duration:.2f}s)")
        if not passed:
            print(f"         ↳ {message}")
    
    def test_health_check(self) -> bool:
        """Test 1: Health Check Endpoint"""
        self.log("🏥", "Testing Health Check...")
        start = time.time()
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            duration = time.time() - start
            
            if response.status_code != 200:
                self.add_result("Health Check", False, 
                               f"Expected 200, got {response.status_code}", 
                               duration, "GET /health")
                return False
            
            data = response.json()
            required_fields = ["status", "google_auth", "project_id", "mode"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                self.add_result("Health Check", False, 
                               f"Missing fields: {missing_fields}", 
                               duration, "GET /health")
                return False
            
            if data["status"] != "healthy":
                self.add_result("Health Check", False, 
                               f"Status is '{data['status']}', expected 'healthy'", 
                               duration, "GET /health")
                return False
            
            self.add_result("Health Check", True, 
                           "All fields present and valid", 
                           duration, "GET /health")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Health Check", False, str(e), duration, "GET /health")
            return False
    
    def test_authentication(self) -> bool:
        """Test 2: JWT Authentication"""
        self.log("🔑", "Testing Authentication...")
        start = time.time()
        
        try:
            # Generate valid token
            self.token = create_access_token(subject="test_user", purpose="admin", expiration_hours=1)
            self.headers = {"Authorization": f"Bearer {self.token}"}
            
            # Test with valid token
            response = requests.get(f"{API_V1}/management/corpus", headers=self.headers)
            
            if response.status_code in [200, 401, 403]:
                if response.status_code == 200:
                    duration = time.time() - start
                    self.add_result("Authentication - Valid Token", True, 
                                   "Valid token accepted", 
                                   duration, "JWT Auth")
                else:
                    duration = time.time() - start
                    self.add_result("Authentication - Valid Token", False, 
                                   f"Valid token rejected with {response.status_code}", 
                                   duration, "JWT Auth")
                    return False
            
            # Test with invalid token
            start_invalid = time.time()
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(f"{API_V1}/management/corpus", headers=invalid_headers)
            duration_invalid = time.time() - start_invalid
            
            if response.status_code in [401, 403]:
                self.add_result("Authentication - Invalid Token", True, 
                               f"Invalid token rejected with {response.status_code}", 
                               duration_invalid, "JWT Auth")
            else:
                self.add_result("Authentication - Invalid Token", False, 
                               f"Invalid token not rejected, got {response.status_code}", 
                               duration_invalid, "JWT Auth")
                
            # Test without token
            start_no_token = time.time()
            response = requests.get(f"{API_V1}/management/corpus")
            duration_no_token = time.time() - start_no_token
            
            if response.status_code in [401, 403]:
                self.add_result("Authentication - No Token", True, 
                               f"No token rejected with {response.status_code}", 
                               duration_no_token, "JWT Auth")
                return True
            else:
                self.add_result("Authentication - No Token", False, 
                               f"Request without token not rejected, got {response.status_code}", 
                               duration_no_token, "JWT Auth")
                return False
                
        except Exception as e:
            duration = time.time() - start
            self.add_result("Authentication", False, str(e), duration, "JWT Auth")
            return False
    
    def test_create_corpus(self) -> bool:
        """Test 3: Create Corpus"""
        self.log("➕", "Testing Corpus Creation...")
        start = time.time()
        
        try:
            corpus_data = {
                "department_name": "TestAPI",
                "description": "Automated test corpus - can be deleted"
            }
            
            response = requests.post(
                f"{API_V1}/management/corpus", 
                json=corpus_data, 
                headers=self.headers
            )
            duration = time.time() - start
            
            if response.status_code == 409:
                # Corpus already exists, try to get it
                self.log("⚠️", "Corpus already exists, fetching ID...")
                list_response = requests.get(f"{API_V1}/management/corpus", headers=self.headers)
                corpora = list_response.json()
                corpus = next((c for c in corpora if c["display_name"] == "DEP-TestAPI"), None)
                
                if corpus:
                    self.test_corpus_id = corpus["id"]
                    self.add_result("Create Corpus", True, 
                                   f"Found existing corpus (ID: {self.test_corpus_id[:8]}...)", 
                                   duration, "POST /management/corpus")
                    return True
                else:
                    self.add_result("Create Corpus", False, 
                                   "Corpus exists but could not be found in list", 
                                   duration, "POST /management/corpus")
                    return False
            
            if response.status_code != 201:
                self.add_result("Create Corpus", False, 
                               f"Expected 201, got {response.status_code}: {response.text}", 
                               duration, "POST /management/corpus")
                return False
            
            data = response.json()
            if "id" not in data:
                self.add_result("Create Corpus", False, 
                               "Response missing 'id' field", 
                               duration, "POST /management/corpus")
                return False
            
            self.test_corpus_id = data["id"]
            self.add_result("Create Corpus", True, 
                           f"Corpus created (ID: {self.test_corpus_id[:8]}...)", 
                           duration, "POST /management/corpus")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Create Corpus", False, str(e), duration, "POST /management/corpus")
            return False
    
    def test_list_corpora(self) -> bool:
        """Test 4: List Corpora"""
        self.log("📋", "Testing Corpus Listing...")
        start = time.time()
        
        try:
            response = requests.get(f"{API_V1}/management/corpus", headers=self.headers)
            duration = time.time() - start
            
            if response.status_code != 200:
                self.add_result("List Corpora", False, 
                               f"Expected 200, got {response.status_code}", 
                               duration, "GET /management/corpus")
                return False
            
            corpora = response.json()
            if not isinstance(corpora, list):
                self.add_result("List Corpora", False, 
                               "Response is not a list", 
                               duration, "GET /management/corpus")
                return False
            
            # Verify our test corpus is in the list
            if self.test_corpus_id:
                found = any(c.get("id") == self.test_corpus_id for c in corpora)
                if not found:
                    self.add_result("List Corpora", False, 
                                   "Test corpus not found in list", 
                                   duration, "GET /management/corpus")
                    return False
            
            self.add_result("List Corpora", True, 
                           f"Found {len(corpora)} corpora", 
                           duration, "GET /management/corpus")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("List Corpora", False, str(e), duration, "GET /management/corpus")
            return False
    
    def test_upload_document(self) -> bool:
        """Test 5: Upload Document"""
        self.log("📤", "Testing Document Upload...")
        
        if not self.test_corpus_id:
            self.add_result("Upload Document", False, 
                           "No corpus ID available", 0, "POST /documents/upload")
            return False
        
        # Test with PDF file
        start = time.time()
        try:
            if not os.path.exists(TEST_FILE_PATH):
                self.add_result("Upload Document - TXT", False, 
                               f"Test file not found: {TEST_FILE_PATH}", 
                               0, "POST /documents/upload")
                return False
            
            with open(TEST_FILE_PATH, "rb") as f:
                files = {"file": ("arquivo_teste.txt", f, "text/plain")}
                data = {"corpus_id": self.test_corpus_id, "user_id": "test_user"}
                response = requests.post(
                    f"{API_V1}/documents/upload", 
                    files=files, 
                    data=data, 
                    headers=self.headers
                )
            
            duration = time.time() - start
            
            if response.status_code != 201:
                self.add_result("Upload Document - TXT", False, 
                               f"Expected 201, got {response.status_code}: {response.text}", 
                               duration, "POST /documents/upload")
                return False
            
            data = response.json()
            if "rag_file_id" not in data:
                self.add_result("Upload Document - TXT", False, 
                               "Response missing 'rag_file_id'", 
                               duration, "POST /documents/upload")
                return False
            
            self.test_file_id = data["rag_file_id"]
            self.add_result("Upload Document - TXT", True, 
                           f"TXT uploaded (ID: {self.test_file_id[:8]}...)", 
                           duration, "POST /documents/upload")
            
            # Also test with TXT file
            start_txt = time.time()
            temp_txt = "temp_test_upload.txt"
            self.temp_files.append(temp_txt)
            
            with open(temp_txt, "w", encoding="utf-8") as f:
                f.write(TEST_TXT_CONTENT)
            
            with open(temp_txt, "rb") as f:
                files = {"file": ("test_doc.txt", f, "text/plain")}
                data = {"corpus_id": self.test_corpus_id, "user_id": "test_user"}
                response = requests.post(
                    f"{API_V1}/documents/upload", 
                    files=files, 
                    data=data, 
                    headers=self.headers
                )
            
            duration_txt = time.time() - start_txt
            
            if response.status_code == 201:
                self.add_result("Upload Document - TXT", True, 
                               "TXT uploaded successfully", 
                               duration_txt, "POST /documents/upload")
            else:
                self.add_result("Upload Document - TXT", False, 
                               f"Expected 201, got {response.status_code}", 
                               duration_txt, "POST /documents/upload")
            
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Upload Document", False, str(e), duration, "POST /documents/upload")
            return False
    
    def test_list_corpus_files(self) -> bool:
        """Test 6: List Files in Corpus"""
        self.log("📁", "Testing File Listing...")
        
        if not self.test_corpus_id:
            self.add_result("List Corpus Files", False, 
                           "No corpus ID available", 0, "GET /management/corpus/{id}/files")
            return False
        
        start = time.time()
        try:
            response = requests.get(
                f"{API_V1}/management/corpus/{self.test_corpus_id}/files", 
                headers=self.headers
            )
            duration = time.time() - start
            
            if response.status_code != 200:
                self.add_result("List Corpus Files", False, 
                               f"Expected 200, got {response.status_code}", 
                               duration, "GET /management/corpus/{id}/files")
                return False
            
            files = response.json()
            if not isinstance(files, list):
                self.add_result("List Corpus Files", False, 
                               "Response is not a list", 
                               duration, "GET /management/corpus/{id}/files")
                return False
            
            # Verify our test file is in the list
            if self.test_file_id:
                found = any(f.get("id") == self.test_file_id for f in files)
                if not found:
                    self.add_result("List Corpus Files", False, 
                                   "Test file not found in list", 
                                   duration, "GET /management/corpus/{id}/files")
                    return False
            
            self.add_result("List Corpus Files", True, 
                           f"Found {len(files)} files in corpus", 
                           duration, "GET /management/corpus/{id}/files")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("List Corpus Files", False, str(e), 
                           duration, "GET /management/corpus/{id}/files")
            return False
    
    def test_get_file_details(self) -> bool:
        """Test 7: Get File Details (NEW - Previously untested)"""
        self.log("🔍", "Testing Get File Details...")
        
        if not self.test_corpus_id or not self.test_file_id:
            self.add_result("Get File Details", False, 
                           "No corpus/file ID available", 
                           0, "GET /documents/{corpus_id}/files/{file_id}")
            return False
        
        start = time.time()
        try:
            response = requests.get(
                f"{API_V1}/documents/{self.test_corpus_id}/files/{self.test_file_id}", 
                headers=self.headers
            )
            duration = time.time() - start
            
            if response.status_code != 200:
                self.add_result("Get File Details", False, 
                               f"Expected 200, got {response.status_code}: {response.text}", 
                               duration, "GET /documents/{corpus_id}/files/{file_id}")
                return False
            
            file_data = response.json()
            required_fields = ["id", "display_name", "name"]
            missing_fields = [f for f in required_fields if f not in file_data]
            
            if missing_fields:
                self.add_result("Get File Details", False, 
                               f"Missing fields: {missing_fields}", 
                               duration, "GET /documents/{corpus_id}/files/{file_id}")
                return False
            
            if file_data["id"] != self.test_file_id:
                self.add_result("Get File Details", False, 
                               "File ID mismatch", 
                               duration, "GET /documents/{corpus_id}/files/{file_id}")
                return False
            
            self.add_result("Get File Details", True, 
                           f"Retrieved details for '{file_data['display_name']}'", 
                           duration, "GET /documents/{corpus_id}/files/{file_id}")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Get File Details", False, str(e), 
                           duration, "GET /documents/{corpus_id}/files/{file_id}")
            return False
    
    def test_chat(self) -> bool:
        """Test 8: Chat with RAG"""
        self.log("💬", "Testing Chat Functionality...")
        
        if not self.test_corpus_id:
            self.add_result("Chat", False, "No corpus ID available", 0, "POST /chat/")
            return False
        
        # Wait for indexing
        self.log("⏳", "Waiting 20s for document indexing...")
        time.sleep(20)
        
        # Test single-turn chat
        start = time.time()
        try:
            chat_data = {
                "message": "Qual o conteúdo deste documento?",
                "history": [],
                "corpus_id": self.test_corpus_id
            }
            
            response = requests.post(
                f"{API_V1}/chat/", 
                json=chat_data, 
                headers=self.headers,
                timeout=30
            )
            duration = time.time() - start
            
            if response.status_code != 200:
                self.add_result("Chat - Single Turn", False, 
                               f"Expected 200, got {response.status_code}: {response.text}", 
                               duration, "POST /chat/")
                return False
            
            response_data = response.json()
            if "response" not in response_data or "new_history" not in response_data:
                self.add_result("Chat - Single Turn", False, 
                               "Missing 'response' or 'new_history' in response", 
                               duration, "POST /chat/")
                return False
            
            self.add_result("Chat - Single Turn", True, 
                           f"Got response: '{response_data['response'][:50]}...'", 
                           duration, "POST /chat/")
            
            # Test multi-turn chat
            start_multi = time.time()
            chat_data_multi = {
                "message": "Você pode resumir?",
                "history": response_data["new_history"],
                "corpus_id": self.test_corpus_id
            }
            
            response = requests.post(
                f"{API_V1}/chat/", 
                json=chat_data_multi, 
                headers=self.headers,
                timeout=30
            )
            duration_multi = time.time() - start_multi
            
            if response.status_code == 200:
                self.add_result("Chat - Multi Turn", True, 
                               "Multi-turn conversation successful", 
                               duration_multi, "POST /chat/")
            else:
                self.add_result("Chat - Multi Turn", False, 
                               f"Expected 200, got {response.status_code}", 
                               duration_multi, "POST /chat/")
            
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Chat", False, str(e), duration, "POST /chat/")
            return False
    
    def test_error_scenarios(self) -> bool:
        """Test 9: Error Handling"""
        self.log("⚠️", "Testing Error Scenarios...")
        
        passed_count = 0
        total_tests = 0
        
        # Test 1: Upload to non-existent corpus
        total_tests += 1
        start = time.time()
        try:
            temp_file = "temp_error_test.txt"
            self.temp_files.append(temp_file)
            with open(temp_file, "w") as f:
                f.write("test")
            
            with open(temp_file, "rb") as f:
                files = {"file": ("test.txt", f, "text/plain")}
                data = {"corpus_id": "9999999999999999999", "user_id": "test"}
                response = requests.post(
                    f"{API_V1}/documents/upload", 
                    files=files, 
                    data=data, 
                    headers=self.headers
                )
            
            duration = time.time() - start
            if response.status_code == 404:
                self.add_result("Error - Upload to Non-existent Corpus", True, 
                               "Correctly returned 404", duration, "POST /documents/upload")
                passed_count += 1
            else:
                self.add_result("Error - Upload to Non-existent Corpus", False, 
                               f"Expected 404, got {response.status_code}", 
                               duration, "POST /documents/upload")
        except Exception as e:
            self.add_result("Error - Upload to Non-existent Corpus", False, str(e), 
                           time.time() - start, "POST /documents/upload")
        
        # Test 2: Chat with non-existent corpus
        total_tests += 1
        start = time.time()
        try:
            chat_data = {
                "message": "Test",
                "history": [],
                "corpus_id": "9999999999999999999"
            }
            response = requests.post(f"{API_V1}/chat/", json=chat_data, headers=self.headers)
            duration = time.time() - start
            
            if response.status_code == 404:
                self.add_result("Error - Chat with Non-existent Corpus", True, 
                               "Correctly returned 404", duration, "POST /chat/")
                passed_count += 1
            else:
                self.add_result("Error - Chat with Non-existent Corpus", False, 
                               f"Expected 404, got {response.status_code}", 
                               duration, "POST /chat/")
        except Exception as e:
            self.add_result("Error - Chat with Non-existent Corpus", False, str(e), 
                           time.time() - start, "POST /chat/")
        
        # Test 3: Delete corpus without confirmation
        total_tests += 1
        if self.test_corpus_id:
            start = time.time()
            try:
                response = requests.delete(
                    f"{API_V1}/management/corpus/{self.test_corpus_id}", 
                    headers=self.headers
                )
                duration = time.time() - start
                
                if response.status_code == 400:
                    self.add_result("Error - Delete Without Confirmation", True, 
                                   "Correctly returned 400", duration, 
                                   "DELETE /management/corpus/{id}")
                    passed_count += 1
                else:
                    self.add_result("Error - Delete Without Confirmation", False, 
                                   f"Expected 400, got {response.status_code}", 
                                   duration, "DELETE /management/corpus/{id}")
            except Exception as e:
                self.add_result("Error - Delete Without Confirmation", False, str(e), 
                               time.time() - start, "DELETE /management/corpus/{id}")
        
        return passed_count == total_tests
    
    def test_delete_file(self) -> bool:
        """Test 10: Delete File"""
        self.log("🗑️", "Testing File Deletion...")
        
        if not self.test_corpus_id or not self.test_file_id:
            self.add_result("Delete File", False, "No corpus/file ID available", 
                           0, "DELETE /documents/{corpus_id}/files/{file_id}")
            return False
        
        start = time.time()
        try:
            response = requests.delete(
                f"{API_V1}/documents/{self.test_corpus_id}/files/{self.test_file_id}", 
                headers=self.headers
            )
            duration = time.time() - start
            
            if response.status_code != 204:
                self.add_result("Delete File", False, 
                               f"Expected 204, got {response.status_code}", 
                               duration, "DELETE /documents/{corpus_id}/files/{file_id}")
                return False
            
            self.add_result("Delete File", True, "File deleted successfully", 
                           duration, "DELETE /documents/{corpus_id}/files/{file_id}")
            
            # Test idempotency - delete again
            start_idem = time.time()
            response = requests.delete(
                f"{API_V1}/documents/{self.test_corpus_id}/files/{self.test_file_id}", 
                headers=self.headers
            )
            duration_idem = time.time() - start_idem
            
            if response.status_code == 204:
                self.add_result("Delete File - Idempotency", True, 
                               "Idempotent operation verified", 
                               duration_idem, "DELETE /documents/{corpus_id}/files/{file_id}")
            else:
                self.add_result("Delete File - Idempotency", False, 
                               f"Expected 204, got {response.status_code}", 
                               duration_idem, "DELETE /documents/{corpus_id}/files/{file_id}")
            
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Delete File", False, str(e), 
                           duration, "DELETE /documents/{corpus_id}/files/{file_id}")
            return False
    
    def test_delete_corpus(self) -> bool:
        """Test 11: Delete Corpus"""
        self.log("🗑️", "Testing Corpus Deletion...")
        
        if not self.test_corpus_id:
            self.add_result("Delete Corpus", False, "No corpus ID available", 
                           0, "DELETE /management/corpus/{id}")
            return False
        
        start = time.time()
        try:
            response = requests.delete(
                f"{API_V1}/management/corpus/{self.test_corpus_id}?confirm=true", 
                headers=self.headers
            )
            duration = time.time() - start
            
            if response.status_code != 204:
                self.add_result("Delete Corpus", False, 
                               f"Expected 204, got {response.status_code}: {response.text}", 
                               duration, "DELETE /management/corpus/{id}")
                return False
            
            self.add_result("Delete Corpus", True, "Corpus deleted successfully", 
                           duration, "DELETE /management/corpus/{id}")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.add_result("Delete Corpus", False, str(e), 
                           duration, "DELETE /management/corpus/{id}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        self.log("🧹", "Cleaning up temporary files...")
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                self.log("⚠️", f"Failed to delete {temp_file}: {e}")
    
    def print_report(self):
        """Print final test report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE API TEST REPORT")
        print("="*80)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests:    {total}")
        print(f"✅ Passed:      {passed}")
        print(f"❌ Failed:      {failed}")
        print(f"Success Rate:   {success_rate:.1f}%")
        
        total_duration = sum(r.duration for r in self.results)
        print(f"Total Duration: {total_duration:.2f}s")
        
        if failed > 0:
            print("\n" + "-"*80)
            print("❌ FAILED TESTS:")
            print("-"*80)
            for result in self.results:
                if not result.passed:
                    print(f"\n{result.name}")
                    print(f"  Endpoint: {result.endpoint}")
                    print(f"  Error: {result.message}")
        
        print("\n" + "="*80)
        
        if success_rate == 100:
            print("✅ SUCCESS: API is PRODUCTION READY!")
            print("="*80)
            return 0
        elif success_rate >= 80:
            print("⚠️ WARNING: API has some issues but is mostly functional")
            print("="*80)
            return 1
        else:
            print("❌ FAILURE: API has critical issues - NOT PRODUCTION READY")
            print("="*80)
            return 1
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀", "Starting Comprehensive API Test Suite...")
        print("="*80)
        
        # Check if API is running
        try:
            requests.get(BASE_URL, timeout=2)
        except:
            self.log("❌", f"API is not running at {BASE_URL}")
            print("Please start the API with: ./venv/bin/uvicorn app.main:app --reload")
            return 1
        
        try:
            # Run tests in order
            self.test_health_check()
            self.test_authentication()
            self.test_create_corpus()
            self.test_list_corpora()
            self.test_upload_document()
            self.test_list_corpus_files()
            self.test_get_file_details()  # NEW TEST
            self.test_chat()
            self.test_error_scenarios()
            self.test_delete_file()
            self.test_delete_corpus()
            
        except KeyboardInterrupt:
            self.log("⚠️", "Tests interrupted by user")
            return 1
        except Exception as e:
            self.log("❌", f"Unexpected error: {e}")
            return 1
        finally:
            self.cleanup()
        
        return self.print_report()


def main():
    """Main entry point"""
    tester = APITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
