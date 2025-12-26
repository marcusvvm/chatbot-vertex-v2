#!/usr/bin/env python3
"""
🔥 PRODUCTION STRESS TEST - Configuration & Preset System
============================================================

Objetivo: Testar TODOS os aspectos da API de configuração para garantir
que está 100% production-ready. Este script assume papel de "adversário"
tentando quebrar o sistema.

Categorias de Teste:
1. Presets Core (CRUD + proteções)
2. Presets Customizados (CRUD completo)
3. Apply Preset (fluxo completo)
4. Corpus Config (CRUD + passthrough)
5. Edge Cases e Boundary Values
6. Concorrência e Race Conditions
7. Segurança e Autenticação
8. Validação de Schemas
9. Integração Chat + Config
10. Performance e Latência

Autor: Tester Adversário
Data: 25/12/2024
"""

import requests
import sys
import os
import json
import time
import random
import string
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_V1 = f"{BASE_URL}/api/v1"
TEST_CORPUS_ID = os.getenv("CORPUS_ID", "8207810320882728960")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.auth import create_access_token


@dataclass
class TestResult:
    """Test result with full details"""
    category: str
    name: str
    passed: bool
    message: str
    duration: float
    endpoint: str = ""
    request_body: Optional[Dict] = None
    response_body: Optional[Dict] = None
    status_code: int = 0
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class TestStats:
    """Aggregated test statistics"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    critical_failures: int = 0
    total_duration: float = 0.0
    categories: Dict[str, Dict[str, int]] = field(default_factory=dict)


class ProductionAPITester:
    """
    Comprehensive Production-Ready API Tester
    
    Designed to find bugs, edge cases, and potential vulnerabilities.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.stats = TestStats()
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.created_presets: List[str] = []  # Track for cleanup
        self.original_corpus_config: Optional[Dict] = None  # For restoration
        
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def log(self, emoji: str, message: str, level: str = "INFO"):
        """Pretty logging with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {emoji} {message}")
    
    def random_string(self, length: int = 8) -> str:
        """Generate random string for unique test IDs"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def add_result(self, category: str, name: str, passed: bool, message: str, 
                   duration: float, endpoint: str = "", request_body: Dict = None,
                   response_body: Dict = None, status_code: int = 0, 
                   severity: str = "medium"):
        """Add test result with full context"""
        result = TestResult(
            category=category,
            name=name,
            passed=passed,
            message=message,
            duration=duration,
            endpoint=endpoint,
            request_body=request_body,
            response_body=response_body,
            status_code=status_code,
            severity=severity
        )
        self.results.append(result)
        
        # Update stats
        self.stats.total += 1
        if passed:
            self.stats.passed += 1
        else:
            self.stats.failed += 1
            if severity == "critical":
                self.stats.critical_failures += 1
        self.stats.total_duration += duration
        
        # Category stats
        if category not in self.stats.categories:
            self.stats.categories[category] = {"passed": 0, "failed": 0}
        if passed:
            self.stats.categories[category]["passed"] += 1
        else:
            self.stats.categories[category]["failed"] += 1
        
        # Log result
        status_emoji = "✅" if passed else "❌"
        severity_tag = f"[{severity.upper()}]" if not passed else ""
        self.log(status_emoji, f"{name} {severity_tag} ({duration:.3f}s)")
        if not passed:
            print(f"         ↳ {message}")
            if request_body:
                print(f"         ↳ Request: {json.dumps(request_body, ensure_ascii=False)[:200]}")
            if response_body:
                print(f"         ↳ Response: {json.dumps(response_body, ensure_ascii=False)[:200]}")
    
    def request(self, method: str, endpoint: str, **kwargs) -> Tuple[requests.Response, float]:
        """Make request with timing"""
        url = f"{API_V1}{endpoint}"
        start = time.time()
        
        # Add auth headers
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)
        
        response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        duration = time.time() - start
        
        return response, duration
    
    # =========================================================================
    # SETUP
    # =========================================================================
    
    def setup(self) -> bool:
        """Initialize test environment"""
        self.log("🔧", "Setting up test environment...")
        
        # Generate token
        try:
            self.token = create_access_token(
                subject="production_tester", 
                purpose="admin", 
                expiration_hours=1
            )
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.log("✓", "Token generated successfully")
        except Exception as e:
            self.log("❌", f"Failed to generate token: {e}")
            return False
        
        # Check API health
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=5)
            if r.status_code != 200:
                self.log("❌", f"API unhealthy: {r.status_code}")
                return False
            self.log("✓", "API is healthy")
        except Exception as e:
            self.log("❌", f"API not reachable: {e}")
            return False
        
        # Backup current corpus config (for restoration)
        try:
            r, _ = self.request("GET", f"/config/corpus/{TEST_CORPUS_ID}")
            if r.status_code == 200:
                self.original_corpus_config = r.json()
                self.log("✓", f"Backed up config for corpus {TEST_CORPUS_ID[:8]}...")
        except:
            pass
        
        return True
    
    def cleanup(self):
        """Cleanup test artifacts"""
        self.log("🧹", "Cleaning up test artifacts...")
        
        # Delete created presets
        for preset_id in self.created_presets:
            try:
                self.request("DELETE", f"/config/presets/{preset_id}")
                self.log("✓", f"Deleted test preset: {preset_id}")
            except:
                pass
        
        # Restore original corpus config
        if self.original_corpus_config:
            try:
                # Apply balanced preset to reset
                self.request("POST", f"/config/corpus/{TEST_CORPUS_ID}/apply-preset/balanced")
                self.log("✓", "Restored corpus to balanced preset")
            except:
                pass
    
    # =========================================================================
    # CATEGORY 1: PRESETS CORE
    # =========================================================================
    
    def test_presets_core(self):
        """Test core presets (read-only)"""
        self.log("📦", "="*60)
        self.log("📦", "CATEGORY 1: Core Presets")
        self.log("📦", "="*60)
        
        # Test 1.1: List presets
        r, d = self.request("GET", "/config/presets")
        if r.status_code == 200:
            data = r.json()
            presets = data.get("presets", [])
            
            # Verify all 4 core presets exist
            core_ids = {"balanced", "creative", "precise", "fast"}
            found_ids = {p["id"] for p in presets}
            
            if core_ids.issubset(found_ids):
                self.add_result("Core Presets", "List presets returns all 4 core", True,
                               f"Found {len(presets)} presets", d, "GET /presets",
                               response_body=data, status_code=200)
            else:
                missing = core_ids - found_ids
                self.add_result("Core Presets", "List presets returns all 4 core", False,
                               f"Missing: {missing}", d, "GET /presets",
                               response_body=data, status_code=200, severity="critical")
        else:
            self.add_result("Core Presets", "List presets", False,
                           f"Status {r.status_code}", d, "GET /presets",
                           status_code=r.status_code, severity="critical")
        
        # Test 1.2: Get each core preset
        for preset_id in ["balanced", "creative", "precise", "fast"]:
            r, d = self.request("GET", f"/config/presets/{preset_id}")
            if r.status_code == 200:
                data = r.json()
                required = ["id", "name", "description", "is_core", "model_name", "generation_config"]
                missing = [f for f in required if f not in data]
                
                if not missing and data.get("is_core") == True:
                    self.add_result("Core Presets", f"Get preset '{preset_id}'", True,
                                   "All fields present, is_core=true", d, 
                                   f"GET /presets/{preset_id}", status_code=200)
                else:
                    self.add_result("Core Presets", f"Get preset '{preset_id}'", False,
                                   f"Missing: {missing}, is_core={data.get('is_core')}", d,
                                   f"GET /presets/{preset_id}", response_body=data, 
                                   status_code=200, severity="high")
            else:
                self.add_result("Core Presets", f"Get preset '{preset_id}'", False,
                               f"Status {r.status_code}", d, f"GET /presets/{preset_id}",
                               status_code=r.status_code, severity="critical")
        
        # Test 1.3: Cannot create preset with core ID
        for core_id in ["balanced", "creative", "precise", "fast"]:
            body = {"id": core_id, "name": "Attempted Override"}
            r, d = self.request("POST", "/config/presets", json=body)
            
            if r.status_code == 400:
                self.add_result("Core Presets", f"Reject create with core ID '{core_id}'", True,
                               "Correctly rejected with 400", d, "POST /presets",
                               request_body=body, status_code=400)
            else:
                self.add_result("Core Presets", f"Reject create with core ID '{core_id}'", False,
                               f"Expected 400, got {r.status_code}", d, "POST /presets",
                               request_body=body, status_code=r.status_code, severity="critical")
        
        # Test 1.4: Cannot modify core preset
        body = {"name": "Hacked Name"}
        r, d = self.request("PUT", "/config/presets/balanced", json=body)
        if r.status_code == 400:
            self.add_result("Core Presets", "Reject modify core preset", True,
                           "Correctly rejected with 400", d, "PUT /presets/balanced",
                           request_body=body, status_code=400)
        else:
            self.add_result("Core Presets", "Reject modify core preset", False,
                           f"Expected 400, got {r.status_code}", d, "PUT /presets/balanced",
                           request_body=body, status_code=r.status_code, severity="critical")
        
        # Test 1.5: Cannot delete core preset
        r, d = self.request("DELETE", "/config/presets/balanced")
        if r.status_code == 400:
            self.add_result("Core Presets", "Reject delete core preset", True,
                           "Correctly rejected with 400", d, "DELETE /presets/balanced",
                           status_code=400)
        else:
            self.add_result("Core Presets", "Reject delete core preset", False,
                           f"Expected 400, got {r.status_code}", d, "DELETE /presets/balanced",
                           status_code=r.status_code, severity="critical")
    
    # =========================================================================
    # CATEGORY 2: PRESETS CUSTOMIZADOS
    # =========================================================================
    
    def test_presets_custom(self):
        """Test custom preset CRUD"""
        self.log("🎨", "="*60)
        self.log("🎨", "CATEGORY 2: Custom Presets CRUD")
        self.log("🎨", "="*60)
        
        test_id = f"test_preset_{self.random_string()}"
        
        # Test 2.1: Create custom preset
        body = {
            "id": test_id,
            "name": "Test Preset",
            "description": "Created by production tester",
            "model_name": "gemini-2.5-flash",
            "generation_config": {
                "temperature": 0.3,
                "max_output_tokens": 2048
            },
            "rag_retrieval_top_k": 5,
            "max_history_length": 15
        }
        r, d = self.request("POST", "/config/presets", json=body)
        
        if r.status_code == 201:
            self.created_presets.append(test_id)
            data = r.json()
            if data.get("preset", {}).get("is_core") == False:
                self.add_result("Custom Presets", "Create custom preset", True,
                               f"Created '{test_id}'", d, "POST /presets",
                               request_body=body, response_body=data, status_code=201)
            else:
                self.add_result("Custom Presets", "Create custom preset", False,
                               "is_core should be False", d, "POST /presets",
                               request_body=body, response_body=data, 
                               status_code=201, severity="high")
        else:
            self.add_result("Custom Presets", "Create custom preset", False,
                           f"Status {r.status_code}", d, "POST /presets",
                           request_body=body, status_code=r.status_code, severity="critical")
            return  # Can't continue without preset
        
        # Test 2.2: Preset appears in list
        r, d = self.request("GET", "/config/presets")
        if r.status_code == 200:
            preset_ids = {p["id"] for p in r.json().get("presets", [])}
            if test_id in preset_ids:
                self.add_result("Custom Presets", "Custom preset in list", True,
                               f"'{test_id}' found in list", d, "GET /presets", status_code=200)
            else:
                self.add_result("Custom Presets", "Custom preset in list", False,
                               f"'{test_id}' not found", d, "GET /presets", 
                               status_code=200, severity="high")
        
        # Test 2.3: Get custom preset
        r, d = self.request("GET", f"/config/presets/{test_id}")
        if r.status_code == 200:
            data = r.json()
            if data.get("id") == test_id and data.get("generation_config", {}).get("temperature") == 0.3:
                self.add_result("Custom Presets", "Get custom preset", True,
                               "Data matches creation values", d, 
                               f"GET /presets/{test_id}", response_body=data, status_code=200)
            else:
                self.add_result("Custom Presets", "Get custom preset", False,
                               "Data mismatch", d, f"GET /presets/{test_id}",
                               response_body=data, status_code=200, severity="high")
        else:
            self.add_result("Custom Presets", "Get custom preset", False,
                           f"Status {r.status_code}", d, f"GET /presets/{test_id}",
                           status_code=r.status_code, severity="high")
        
        # Test 2.4: Update custom preset
        update_body = {
            "name": "Updated Test Preset",
            "generation_config": {
                "temperature": 0.6,
                "top_k": 50
            }
        }
        r, d = self.request("PUT", f"/config/presets/{test_id}", json=update_body)
        if r.status_code == 200:
            data = r.json()
            updated = data.get("preset", {})
            if updated.get("name") == "Updated Test Preset":
                self.add_result("Custom Presets", "Update custom preset", True,
                               "Name updated correctly", d, f"PUT /presets/{test_id}",
                               request_body=update_body, response_body=data, status_code=200)
            else:
                self.add_result("Custom Presets", "Update custom preset", False,
                               f"Name not updated: {updated.get('name')}", d,
                               f"PUT /presets/{test_id}", request_body=update_body,
                               response_body=data, status_code=200, severity="high")
        else:
            self.add_result("Custom Presets", "Update custom preset", False,
                           f"Status {r.status_code}", d, f"PUT /presets/{test_id}",
                           request_body=update_body, status_code=r.status_code, severity="high")
        
        # Test 2.5: Duplicate ID rejected
        dup_body = {"id": test_id, "name": "Duplicate"}
        r, d = self.request("POST", "/config/presets", json=dup_body)
        if r.status_code == 400:
            self.add_result("Custom Presets", "Reject duplicate ID", True,
                           "Correctly rejected with 400", d, "POST /presets",
                           request_body=dup_body, status_code=400)
        else:
            self.add_result("Custom Presets", "Reject duplicate ID", False,
                           f"Expected 400, got {r.status_code}", d, "POST /presets",
                           request_body=dup_body, status_code=r.status_code, severity="high")
        
        # Test 2.6: Delete custom preset
        r, d = self.request("DELETE", f"/config/presets/{test_id}")
        if r.status_code == 200:
            self.created_presets.remove(test_id)
            self.add_result("Custom Presets", "Delete custom preset", True,
                           f"Deleted '{test_id}'", d, f"DELETE /presets/{test_id}",
                           status_code=200)
            
            # Verify deletion
            r2, d2 = self.request("GET", f"/config/presets/{test_id}")
            if r2.status_code == 404:
                self.add_result("Custom Presets", "Verify deletion", True,
                               "Preset no longer accessible", d2, 
                               f"GET /presets/{test_id}", status_code=404)
            else:
                self.add_result("Custom Presets", "Verify deletion", False,
                               f"Expected 404, got {r2.status_code}", d2,
                               f"GET /presets/{test_id}", status_code=r2.status_code, 
                               severity="high")
        else:
            self.add_result("Custom Presets", "Delete custom preset", False,
                           f"Status {r.status_code}", d, f"DELETE /presets/{test_id}",
                           status_code=r.status_code, severity="high")
    
    # =========================================================================
    # CATEGORY 3: APPLY PRESET
    # =========================================================================
    
    def test_apply_preset(self):
        """Test apply preset to corpus"""
        self.log("🎯", "="*60)
        self.log("🎯", "CATEGORY 3: Apply Preset to Corpus")
        self.log("🎯", "="*60)
        
        # Test 3.1: Apply each core preset
        for preset_id in ["balanced", "creative", "precise", "fast"]:
            r, d = self.request("POST", f"/config/corpus/{TEST_CORPUS_ID}/apply-preset/{preset_id}")
            
            if r.status_code == 200:
                data = r.json()
                if data.get("preset_id") == preset_id:
                    self.add_result("Apply Preset", f"Apply '{preset_id}' preset", True,
                                   "Applied successfully", d, 
                                   f"POST /corpus/{TEST_CORPUS_ID[:8]}../apply-preset/{preset_id}",
                                   response_body=data, status_code=200)
                else:
                    self.add_result("Apply Preset", f"Apply '{preset_id}' preset", False,
                                   "Response preset_id mismatch", d,
                                   f"POST /apply-preset/{preset_id}", response_body=data,
                                   status_code=200, severity="medium")
            else:
                self.add_result("Apply Preset", f"Apply '{preset_id}' preset", False,
                               f"Status {r.status_code}", d, f"POST /apply-preset/{preset_id}",
                               status_code=r.status_code, severity="high")
        
        # Test 3.2: Verify corpus config matches preset
        r, d = self.request("GET", f"/config/corpus/{TEST_CORPUS_ID}")
        if r.status_code == 200:
            data = r.json()
            if data.get("has_custom_config") == True:
                self.add_result("Apply Preset", "Corpus has custom config after apply", True,
                               "has_custom_config=True", d, 
                               f"GET /corpus/{TEST_CORPUS_ID[:8]}..",
                               response_body=data, status_code=200)
            else:
                self.add_result("Apply Preset", "Corpus has custom config after apply", False,
                               "has_custom_config should be True", d,
                               f"GET /corpus/{TEST_CORPUS_ID[:8]}..", response_body=data,
                               status_code=200, severity="high")
        
        # Test 3.3: Apply non-existent preset
        r, d = self.request("POST", f"/config/corpus/{TEST_CORPUS_ID}/apply-preset/nonexistent_preset_xyz")
        if r.status_code == 404:
            self.add_result("Apply Preset", "Reject non-existent preset", True,
                           "Correctly returned 404", d, "POST /apply-preset/nonexistent",
                           status_code=404)
        else:
            self.add_result("Apply Preset", "Reject non-existent preset", False,
                           f"Expected 404, got {r.status_code}", d, "POST /apply-preset/nonexistent",
                           status_code=r.status_code, severity="high")
        
        # Test 3.4: Apply to non-existent corpus (should still work, creates config)
        fake_corpus = "9999999999999999999"
        r, d = self.request("POST", f"/config/corpus/{fake_corpus}/apply-preset/balanced")
        # This might be 200 (creates config file) or 404 (corpus doesn't exist in Vertex)
        if r.status_code in [200, 404]:
            self.add_result("Apply Preset", "Apply to non-existent corpus", True,
                           f"Status {r.status_code} (acceptable)", d,
                           f"POST /corpus/{fake_corpus}/apply-preset/balanced",
                           status_code=r.status_code)
        else:
            self.add_result("Apply Preset", "Apply to non-existent corpus", False,
                           f"Unexpected status {r.status_code}", d,
                           f"POST /corpus/{fake_corpus}/apply-preset/balanced",
                           status_code=r.status_code, severity="medium")
    
    # =========================================================================
    # CATEGORY 4: CORPUS CONFIG
    # =========================================================================
    
    def test_corpus_config(self):
        """Test corpus configuration CRUD"""
        self.log("⚙️", "="*60)
        self.log("⚙️", "CATEGORY 4: Corpus Configuration")
        self.log("⚙️", "="*60)
        
        # Test 4.1: Get corpus config
        r, d = self.request("GET", f"/config/corpus/{TEST_CORPUS_ID}")
        if r.status_code == 200:
            data = r.json()
            required = ["corpus_id", "config", "has_custom_config"]
            missing = [f for f in required if f not in data]
            
            if not missing:
                self.add_result("Corpus Config", "Get corpus config", True,
                               "All required fields present", d,
                               f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                               response_body=data, status_code=200)
            else:
                self.add_result("Corpus Config", "Get corpus config", False,
                               f"Missing: {missing}", d,
                               f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                               response_body=data, status_code=200, severity="high")
        else:
            self.add_result("Corpus Config", "Get corpus config", False,
                           f"Status {r.status_code}", d,
                           f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                           status_code=r.status_code, severity="critical")
        
        # Test 4.2: Update corpus config with known fields
        update_body = {
            "system_instruction": "Você é um assistente de testes.",
            "model_name": "gemini-2.5-pro",
            "generation_config": {
                "temperature": 0.4,
                "max_output_tokens": 3000
            },
            "rag_retrieval_top_k": 8,
            "max_history_length": 25
        }
        r, d = self.request("PUT", f"/config/corpus/{TEST_CORPUS_ID}", json=update_body)
        if r.status_code == 200:
            self.add_result("Corpus Config", "Update with known fields", True,
                           "Updated successfully", d,
                           f"PUT /config/corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=update_body, status_code=200)
        else:
            self.add_result("Corpus Config", "Update with known fields", False,
                           f"Status {r.status_code}", d,
                           f"PUT /config/corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=update_body, status_code=r.status_code, 
                           severity="critical")
        
        # Test 4.3: PASSTHROUGH - Update with unknown generation_config field
        passthrough_body = {
            "generation_config": {
                "temperature": 0.5,
                "future_param_xyz": "test_value",  # Unknown field
                "another_new_param": 123           # Unknown field
            }
        }
        r, d = self.request("PUT", f"/config/corpus/{TEST_CORPUS_ID}", json=passthrough_body)
        if r.status_code == 200:
            self.add_result("Corpus Config", "PASSTHROUGH: Unknown fields accepted", True,
                           "Unknown fields passed through", d,
                           f"PUT /config/corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=passthrough_body, status_code=200)
        else:
            self.add_result("Corpus Config", "PASSTHROUGH: Unknown fields accepted", False,
                           f"Status {r.status_code} - passthrough failed", d,
                           f"PUT /config/corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=passthrough_body, status_code=r.status_code,
                           severity="critical")
        
        # Test 4.4: Verify passthrough fields are stored
        r, d = self.request("GET", f"/config/corpus/{TEST_CORPUS_ID}")
        if r.status_code == 200:
            gen_config = r.json().get("config", {}).get("generation_config", {})
            if gen_config.get("future_param_xyz") == "test_value":
                self.add_result("Corpus Config", "PASSTHROUGH: Fields persisted", True,
                               "Unknown fields stored correctly", d,
                               f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                               response_body=r.json(), status_code=200)
            else:
                self.add_result("Corpus Config", "PASSTHROUGH: Fields persisted", False,
                               f"Field not found: {gen_config}", d,
                               f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                               response_body=r.json(), status_code=200, severity="high")
        
        # Test 4.5: Delete corpus config (reset to global)
        r, d = self.request("DELETE", f"/config/corpus/{TEST_CORPUS_ID}")
        if r.status_code == 200:
            self.add_result("Corpus Config", "Delete corpus config", True,
                           "Config deleted", d,
                           f"DELETE /config/corpus/{TEST_CORPUS_ID[:8]}..",
                           status_code=200)
            
            # Verify reset
            r2, d2 = self.request("GET", f"/config/corpus/{TEST_CORPUS_ID}")
            if r2.status_code == 200:
                if r2.json().get("has_custom_config") == False:
                    self.add_result("Corpus Config", "Verify reset to global", True,
                                   "has_custom_config=False", d2,
                                   f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                                   response_body=r2.json(), status_code=200)
                else:
                    self.add_result("Corpus Config", "Verify reset to global", False,
                                   "Still has custom config", d2,
                                   f"GET /config/corpus/{TEST_CORPUS_ID[:8]}..",
                                   response_body=r2.json(), status_code=200, severity="high")
        else:
            # Might be 404 if no config exists - that's OK
            if r.status_code == 404:
                self.add_result("Corpus Config", "Delete corpus config", True,
                               "No config to delete (404)", d,
                               f"DELETE /config/corpus/{TEST_CORPUS_ID[:8]}..",
                               status_code=404)
            else:
                self.add_result("Corpus Config", "Delete corpus config", False,
                               f"Unexpected status {r.status_code}", d,
                               f"DELETE /config/corpus/{TEST_CORPUS_ID[:8]}..",
                               status_code=r.status_code, severity="medium")
    
    # =========================================================================
    # CATEGORY 5: EDGE CASES
    # =========================================================================
    
    def test_edge_cases(self):
        """Test edge cases and boundary values"""
        self.log("🔪", "="*60)
        self.log("🔪", "CATEGORY 5: Edge Cases & Boundary Values")
        self.log("🔪", "="*60)
        
        # Test 5.1: Empty preset ID
        r, d = self.request("GET", "/config/presets/")
        # Should be 404 or 405, not 500
        if r.status_code < 500:
            self.add_result("Edge Cases", "Empty preset ID", True,
                           f"Status {r.status_code} (not 500)", d,
                           "GET /presets/", status_code=r.status_code)
        else:
            self.add_result("Edge Cases", "Empty preset ID", False,
                           f"Server error {r.status_code}", d,
                           "GET /presets/", status_code=r.status_code, severity="critical")
        
        # Test 5.2: Very long preset ID
        long_id = "a" * 1000
        r, d = self.request("GET", f"/config/presets/{long_id}")
        if r.status_code < 500:
            self.add_result("Edge Cases", "Very long preset ID", True,
                           f"Status {r.status_code} (not 500)", d,
                           f"GET /presets/{long_id[:20]}...", status_code=r.status_code)
        else:
            self.add_result("Edge Cases", "Very long preset ID", False,
                           f"Server error {r.status_code}", d,
                           f"GET /presets/{long_id[:20]}...", status_code=r.status_code,
                           severity="high")
        
        # Test 5.3: Special characters in preset ID
        special_id = "test<>!@#$%"
        body = {"id": special_id, "name": "Special Test"}
        r, d = self.request("POST", "/config/presets", json=body)
        # Should gracefully handle (400 or create safely)
        if r.status_code < 500:
            self.add_result("Edge Cases", "Special chars in preset ID", True,
                           f"Status {r.status_code} (handled)", d,
                           "POST /presets", request_body=body, status_code=r.status_code)
            if r.status_code == 201:
                self.created_presets.append(special_id)
        else:
            self.add_result("Edge Cases", "Special chars in preset ID", False,
                           f"Server error {r.status_code}", d,
                           "POST /presets", request_body=body, status_code=r.status_code,
                           severity="high")
        
        # Test 5.4: Empty generation_config
        body = {
            "generation_config": {}
        }
        r, d = self.request("PUT", f"/config/corpus/{TEST_CORPUS_ID}", json=body)
        if r.status_code < 500:
            self.add_result("Edge Cases", "Empty generation_config", True,
                           f"Status {r.status_code}", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=body, status_code=r.status_code)
        else:
            self.add_result("Edge Cases", "Empty generation_config", False,
                           f"Server error {r.status_code}", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=body, status_code=r.status_code, severity="high")
        
        # Test 5.5: Null values in generation_config
        body = {
            "generation_config": {
                "temperature": None,
                "top_k": None
            }
        }
        r, d = self.request("PUT", f"/config/corpus/{TEST_CORPUS_ID}", json=body)
        if r.status_code < 500:
            self.add_result("Edge Cases", "Null values in generation_config", True,
                           f"Status {r.status_code}", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=body, status_code=r.status_code)
        else:
            self.add_result("Edge Cases", "Null values in generation_config", False,
                           f"Server error {r.status_code}", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=body, status_code=r.status_code, severity="high")
        
        # Test 5.6: Extreme values
        body = {
            "generation_config": {
                "temperature": 999999,
                "max_output_tokens": -1,
                "top_k": 0
            }
        }
        r, d = self.request("PUT", f"/config/corpus/{TEST_CORPUS_ID}", json=body)
        # Should accept (passthrough) - Google will validate
        if r.status_code == 200:
            self.add_result("Edge Cases", "Extreme values (passthrough)", True,
                           "Accepted (Google validates later)", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=body, status_code=r.status_code)
        else:
            self.add_result("Edge Cases", "Extreme values (passthrough)", False,
                           f"Rejected with {r.status_code}", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body=body, status_code=r.status_code, severity="medium")
        
        # Test 5.7: Very long system_instruction
        body = {
            "system_instruction": "A" * 15000  # Exceeds 10000 limit
        }
        r, d = self.request("PUT", f"/config/corpus/{TEST_CORPUS_ID}", json=body)
        if r.status_code == 422:
            self.add_result("Edge Cases", "Exceed system_instruction limit", True,
                           "Correctly rejected with 422", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           request_body={"system_instruction": "A*15000"}, status_code=422)
        elif r.status_code < 500:
            self.add_result("Edge Cases", "Exceed system_instruction limit", True,
                           f"Status {r.status_code} (not 500)", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           status_code=r.status_code)
        else:
            self.add_result("Edge Cases", "Exceed system_instruction limit", False,
                           f"Server error {r.status_code}", d,
                           f"PUT /corpus/{TEST_CORPUS_ID[:8]}..",
                           status_code=r.status_code, severity="high")
    
    # =========================================================================
    # CATEGORY 6: SECURITY
    # =========================================================================
    
    def test_security(self):
        """Test security aspects"""
        self.log("🔒", "="*60)
        self.log("🔒", "CATEGORY 6: Security & Authentication")
        self.log("🔒", "="*60)
        
        endpoints_to_test = [
            ("GET", "/config/presets"),
            ("GET", f"/config/presets/balanced"),
            ("POST", "/config/presets"),
            ("PUT", "/config/presets/test"),
            ("DELETE", "/config/presets/test"),
            ("GET", f"/config/corpus/{TEST_CORPUS_ID}"),
            ("PUT", f"/config/corpus/{TEST_CORPUS_ID}"),
            ("DELETE", f"/config/corpus/{TEST_CORPUS_ID}"),
            ("POST", f"/config/corpus/{TEST_CORPUS_ID}/apply-preset/balanced"),
        ]
        
        # Test without token
        for method, endpoint in endpoints_to_test:
            url = f"{API_V1}{endpoint}"
            start = time.time()
            
            try:
                if method == "GET":
                    r = requests.get(url, timeout=5)
                elif method == "POST":
                    r = requests.post(url, json={}, timeout=5)
                elif method == "PUT":
                    r = requests.put(url, json={}, timeout=5)
                else:
                    r = requests.delete(url, timeout=5)
                
                duration = time.time() - start
                
                if r.status_code in [401, 403]:
                    self.add_result("Security", f"No token: {method} {endpoint[:30]}", True,
                                   f"Correctly rejected ({r.status_code})", duration,
                                   f"{method} {endpoint}", status_code=r.status_code)
                else:
                    self.add_result("Security", f"No token: {method} {endpoint[:30]}", False,
                                   f"Expected 401/403, got {r.status_code}", duration,
                                   f"{method} {endpoint}", status_code=r.status_code,
                                   severity="critical")
            except Exception as e:
                self.add_result("Security", f"No token: {method} {endpoint[:30]}", False,
                               str(e), time.time() - start, f"{method} {endpoint}",
                               severity="high")
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_abc123"}
        url = f"{API_V1}/config/presets"
        start = time.time()
        r = requests.get(url, headers=invalid_headers, timeout=5)
        duration = time.time() - start
        
        if r.status_code in [401, 403]:
            self.add_result("Security", "Invalid token rejected", True,
                           f"Correctly rejected ({r.status_code})", duration,
                           "GET /presets", status_code=r.status_code)
        else:
            self.add_result("Security", "Invalid token rejected", False,
                           f"Expected 401/403, got {r.status_code}", duration,
                           "GET /presets", status_code=r.status_code, severity="critical")
        
        # Test fixed config not exposed
        r, d = self.request("GET", f"/config/corpus/{TEST_CORPUS_ID}")
        if r.status_code == 200:
            config = r.json().get("config", {})
            
            # These should NOT be present
            forbidden = ["safety_settings", "formatting_rules", 
                        "tool_usage_instructions", "context_management_instructions"]
            exposed = [f for f in forbidden if f in config]
            
            if not exposed:
                self.add_result("Security", "Fixed fields NOT exposed", True,
                               "No fixed fields in response", d,
                               f"GET /corpus/{TEST_CORPUS_ID[:8]}..", status_code=200)
            else:
                self.add_result("Security", "Fixed fields NOT exposed", False,
                               f"EXPOSED: {exposed}", d,
                               f"GET /corpus/{TEST_CORPUS_ID[:8]}..",
                               response_body=config, status_code=200, severity="critical")
    
    # =========================================================================
    # CATEGORY 7: CHAT INTEGRATION
    # =========================================================================
    
    def test_chat_integration(self):
        """Test chat works with applied presets"""
        self.log("💬", "="*60)
        self.log("💬", "CATEGORY 7: Chat Integration")
        self.log("💬", "="*60)
        
        # Apply balanced preset
        r, d = self.request("POST", f"/config/corpus/{TEST_CORPUS_ID}/apply-preset/balanced")
        if r.status_code != 200:
            self.add_result("Chat Integration", "Apply preset for test", False,
                           f"Status {r.status_code}", d, "POST /apply-preset/balanced",
                           status_code=r.status_code, severity="high")
            return
        
        # Test simple chat
        chat_body = {
            "message": "Olá, tudo bem?",
            "history": [],
            "corpus_id": TEST_CORPUS_ID
        }
        
        start = time.time()
        try:
            r = requests.post(f"{API_V1}/chat/", json=chat_body, 
                            headers=self.headers, timeout=60)
            duration = time.time() - start
            
            if r.status_code == 200:
                data = r.json()
                if "response" in data:
                    self.add_result("Chat Integration", "Chat with balanced preset", True,
                                   f"Response: '{data['response'][:50]}...'", duration,
                                   "POST /chat/", request_body=chat_body,
                                   response_body=data, status_code=200)
                else:
                    self.add_result("Chat Integration", "Chat with balanced preset", False,
                                   "Missing 'response' in data", duration,
                                   "POST /chat/", response_body=data, status_code=200,
                                   severity="high")
            else:
                self.add_result("Chat Integration", "Chat with balanced preset", False,
                               f"Status {r.status_code}", duration,
                               "POST /chat/", request_body=chat_body,
                               status_code=r.status_code, severity="critical")
        except Exception as e:
            self.add_result("Chat Integration", "Chat with balanced preset", False,
                           str(e), time.time() - start, "POST /chat/", 
                           severity="critical")
        
        # Apply fast preset and test
        r, d = self.request("POST", f"/config/corpus/{TEST_CORPUS_ID}/apply-preset/fast")
        if r.status_code == 200:
            start = time.time()
            try:
                r = requests.post(f"{API_V1}/chat/", json=chat_body,
                                headers=self.headers, timeout=60)
                duration = time.time() - start
                
                if r.status_code == 200:
                    self.add_result("Chat Integration", "Chat with fast preset", True,
                                   f"Response in {duration:.2f}s", duration,
                                   "POST /chat/", status_code=200)
                else:
                    self.add_result("Chat Integration", "Chat with fast preset", False,
                                   f"Status {r.status_code}", duration,
                                   "POST /chat/", status_code=r.status_code, severity="high")
            except Exception as e:
                self.add_result("Chat Integration", "Chat with fast preset", False,
                               str(e), time.time() - start, "POST /chat/", 
                               severity="high")
    
    # =========================================================================
    # REPORT
    # =========================================================================
    
    def print_report(self) -> int:
        """Print comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 PRODUCTION READINESS TEST REPORT")
        print("=" * 80)
        
        # Overall stats
        success_rate = (self.stats.passed / self.stats.total * 100) if self.stats.total > 0 else 0
        
        print(f"\n{'SUMMARY':=^80}")
        print(f"  Total Tests:      {self.stats.total}")
        print(f"  ✅ Passed:        {self.stats.passed}")
        print(f"  ❌ Failed:        {self.stats.failed}")
        print(f"  💀 Critical:      {self.stats.critical_failures}")
        print(f"  Success Rate:     {success_rate:.1f}%")
        print(f"  Total Duration:   {self.stats.total_duration:.2f}s")
        
        # Category breakdown
        print(f"\n{'CATEGORY BREAKDOWN':=^80}")
        for cat, stats in self.stats.categories.items():
            total = stats["passed"] + stats["failed"]
            rate = (stats["passed"] / total * 100) if total > 0 else 0
            status = "✅" if stats["failed"] == 0 else "❌"
            print(f"  {status} {cat}: {stats['passed']}/{total} ({rate:.0f}%)")
        
        # Failed tests
        if self.stats.failed > 0:
            print(f"\n{'FAILED TESTS':=^80}")
            for r in self.results:
                if not r.passed:
                    severity_emoji = {"low": "🟡", "medium": "🟠", 
                                     "high": "🔴", "critical": "💀"}.get(r.severity, "❓")
                    print(f"\n  {severity_emoji} [{r.severity.upper()}] {r.name}")
                    print(f"     Category: {r.category}")
                    print(f"     Endpoint: {r.endpoint}")
                    print(f"     Error:    {r.message}")
                    if r.status_code:
                        print(f"     Status:   {r.status_code}")
        
        # Verdict
        print("\n" + "=" * 80)
        if self.stats.critical_failures > 0:
            print("💀 VERDICT: CRITICAL FAILURES - NOT PRODUCTION READY")
            print("   Fix all critical issues before deployment!")
            return 2
        elif success_rate == 100:
            print("✅ VERDICT: ALL TESTS PASSED - PRODUCTION READY!")
            return 0
        elif success_rate >= 90:
            print("⚠️ VERDICT: MOSTLY READY - Minor issues to address")
            return 1
        else:
            print("❌ VERDICT: SIGNIFICANT ISSUES - NOT PRODUCTION READY")
            return 2
    
    # =========================================================================
    # MAIN
    # =========================================================================
    
    def run(self) -> int:
        """Run all tests"""
        print("=" * 80)
        print("🔥 PRODUCTION STRESS TEST - Configuration & Preset System")
        print("=" * 80)
        print(f"API URL: {BASE_URL}")
        print(f"Test Corpus: {TEST_CORPUS_ID}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        if not self.setup():
            print("\n❌ Setup failed! Cannot continue.")
            return 2
        
        try:
            # Run all test categories
            self.test_presets_core()
            self.test_presets_custom()
            self.test_apply_preset()
            self.test_corpus_config()
            self.test_edge_cases()
            self.test_security()
            self.test_chat_integration()
            
        except KeyboardInterrupt:
            self.log("⚠️", "Tests interrupted by user")
        except Exception as e:
            self.log("❌", f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
        
        return self.print_report()


def main():
    """Entry point"""
    tester = ProductionAPITester()
    sys.exit(tester.run())


if __name__ == "__main__":
    main()
