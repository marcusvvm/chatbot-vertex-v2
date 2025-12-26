"""
Qualitative Test Suite for Agentic Prompt Engineering

This script performs comprehensive qualitative testing of the chatbot's
prompt engineering implementation, covering:

1. Greeting responses (should be fast, no RAG)
2. Ambiguous questions (should ask for clarification)
3. Clear factual questions (should use RAG and cite sources)
4. Follow-up questions (should use context)
5. Instruction degradation (behavior over long conversations)
6. Topic switching (context isolation)
7. Multi-question handling (flow guidance)
8. Incomplete information handling

Results are saved to a markdown file for semantic analysis.
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
CORPUS_ID = os.environ.get("CORPUS_ID", "8207810320882728960")
OUTPUT_DIR = "docs/test_results"

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Generate token for authentication
def get_auth_token() -> str:
    """Generate a JWT token for API authentication."""
    from app.core.auth import create_access_token
    token = create_access_token(
        subject="qualitative_tester",
        purpose="admin"
    )
    return token

class AgenticTestSuite:
    """Comprehensive test suite for agentic prompt behavior."""
    
    def __init__(self, corpus_id: str, api_url: str):
        self.corpus_id = corpus_id
        self.api_url = api_url
        self.token = get_auth_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.results: List[Dict] = []
        self.current_history: List[Dict] = []
        
    def chat(self, message: str, history: Optional[List[Dict]] = None) -> Dict:
        """Send a chat message and return the response with timing."""
        if history is None:
            history = self.current_history
            
        start_time = time.time()
        
        payload = {
            "message": message,
            "history": history,
            "corpus_id": self.corpus_id
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/chat",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "elapsed_seconds": round(elapsed, 2),
                    "status_code": 200
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "elapsed_seconds": round(elapsed, 2),
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "status_code": 0
            }
    
    def add_to_history(self, user_msg: str, assistant_msg: str):
        """Add a turn to the conversation history."""
        self.current_history.append({"role": "user", "content": user_msg})
        self.current_history.append({"role": "assistant", "content": assistant_msg})
    
    def clear_history(self):
        """Clear the conversation history."""
        self.current_history = []
    
    def run_test(self, category: str, test_name: str, message: str, 
                 expected_behavior: str, history_size: Optional[int] = None,
                 use_custom_history: Optional[List[Dict]] = None) -> Dict:
        """Run a single test and record results."""
        print(f"  📝 Testing: {test_name}...")
        
        # Use custom history if provided
        history = use_custom_history if use_custom_history else self.current_history
        
        # Optionally limit history size
        if history_size is not None and history:
            history = history[-history_size:]
        
        result = self.chat(message, history)
        
        test_result = {
            "category": category,
            "test_name": test_name,
            "message": message,
            "expected_behavior": expected_behavior,
            "history_length": len(history) // 2 if history else 0,
            "response": result.get("response", result.get("error", "")),
            "elapsed_seconds": result["elapsed_seconds"],
            "success": result["success"]
        }
        
        self.results.append(test_result)
        
        # Update history if successful
        if result["success"]:
            self.add_to_history(message, result["response"])
        
        return test_result
    
    def run_all_tests(self):
        """Execute all test categories."""
        print("\n" + "="*80)
        print("🧪 QUALITATIVE TEST SUITE - AGENTIC PROMPT ENGINEERING")
        print("="*80)
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"🎯 Corpus ID: {self.corpus_id}")
        print(f"🌐 API URL: {self.api_url}")
        print("="*80 + "\n")
        
        # Category 1: Greetings (should not use RAG)
        self.test_greetings()
        
        # Category 2: Ambiguous Questions (should ask for clarification)
        self.test_ambiguous_questions()
        
        # Category 3: Clear Factual Questions (should use RAG, cite sources)
        self.test_factual_questions()
        
        # Category 4: Follow-up Questions (context usage)
        self.test_followup_questions()
        
        # Category 5: Instruction Degradation (long conversations)
        self.test_instruction_degradation()
        
        # Category 6: Topic Switching (context isolation)
        self.test_topic_switching()
        
        # Category 7: Multi-question Handling
        self.test_multi_questions()
        
        # Category 8: Edge Cases
        self.test_edge_cases()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
    
    def test_greetings(self):
        """Test greeting responses - should be fast, no RAG."""
        print("\n📌 CATEGORY 1: GREETINGS (Fast Response, No RAG)")
        print("-"*60)
        self.clear_history()
        
        greetings = [
            ("Olá", "Resposta cordial rápida sem busca de documentos"),
            ("Bom dia!", "Saudação cordial apropriada ao horário"),
            ("Oi, tudo bem?", "Resposta amigável sem RAG"),
            ("Obrigado pela ajuda!", "Agradecimento cordial de encerramento"),
        ]
        
        for greeting, expected in greetings:
            self.run_test("Greetings", f"Greeting: {greeting[:20]}", greeting, expected)
    
    def test_ambiguous_questions(self):
        """Test ambiguous questions - should ask for clarification."""
        print("\n📌 CATEGORY 2: AMBIGUOUS QUESTIONS (Should Request Clarification)")
        print("-"*60)
        self.clear_history()
        
        ambiguous = [
            ("Preciso de informações sobre registro", 
             "Deve perguntar qual tipo de registro (PF, PJ, ART, etc.)"),
            ("Como faço?", 
             "Deve pedir clarificação sobre o que exatamente"),
            ("Quero saber sobre o prazo", 
             "Deve perguntar prazo de quê especificamente"),
            ("Me ajuda com um documento", 
             "Deve perguntar qual documento"),
            ("Tem problema nisso?", 
             "Deve perguntar a que 'nisso' se refere"),
        ]
        
        for question, expected in ambiguous:
            self.run_test("Ambiguous", f"Ambiguous: {question[:30]}", question, expected)
            self.clear_history()  # Reset for each ambiguous test
    
    def test_factual_questions(self):
        """Test clear factual questions - should use RAG and cite sources."""
        print("\n📌 CATEGORY 3: FACTUAL QUESTIONS (Should Use RAG, Cite Sources)")
        print("-"*60)
        self.clear_history()
        
        factual = [
            ("Qual o prazo para pagamento da anuidade do CREA?", 
             "Resposta com prazo específico e citação de fonte"),
            ("O que é uma ART e para que serve?", 
             "Explicação completa sobre ART com fundamentação"),
            ("Quais são as atribuições do engenheiro civil?", 
             "Lista de atribuições com base em resolução"),
            ("Como funciona o processo de registro de pessoa física no CREA?", 
             "Passo a passo do processo com fonte"),
            ("Qual a diferença entre engenheiro e técnico no sistema CONFEA/CREA?", 
             "Comparação com base em normativos"),
        ]
        
        for question, expected in factual:
            result = self.run_test("Factual", f"Factual: {question[:40]}", question, expected)
            self.clear_history()  # Reset for each factual test
    
    def test_followup_questions(self):
        """Test follow-up questions - should use conversation context."""
        print("\n📌 CATEGORY 4: FOLLOW-UP QUESTIONS (Context Usage)")
        print("-"*60)
        self.clear_history()
        
        # Start with a clear question
        self.run_test(
            "Followup", 
            "Initial question about CREA",
            "Quais os documentos necessários para registro de pessoa física no CREA?",
            "Lista de documentos necessários"
        )
        
        # Follow-up questions that should use context
        followups = [
            ("E para pessoa jurídica?", 
             "Deve entender que se refere a documentos de registro"),
            ("Qual o prazo de análise?", 
             "Deve entender que se refere ao registro mencionado"),
            ("Posso fazer online?", 
             "Deve entender que se refere ao processo de registro"),
        ]
        
        for question, expected in followups:
            self.run_test("Followup", f"Followup: {question}", question, expected)
    
    def test_instruction_degradation(self):
        """Test behavior after many conversation turns - check instruction adherence."""
        print("\n📌 CATEGORY 5: INSTRUCTION DEGRADATION (Long Conversation)")
        print("-"*60)
        
        # Build up a long conversation history
        simulated_history = []
        conversation_turns = [
            ("O que é CREA?", "O CREA é o Conselho Regional de Engenharia e Agronomia..."),
            ("E o CONFEA?", "O CONFEA é o Conselho Federal de Engenharia e Agronomia..."),
            ("Qual a relação entre eles?", "O CONFEA é o órgão superior que orienta os CREAs..."),
            ("Quantos CREAs existem?", "Existem 27 CREAs no Brasil, um em cada estado..."),
            ("Quem pode se registrar?", "Podem se registrar engenheiros, arquitetos, agrônomos..."),
            ("Qual o valor da anuidade?", "O valor da anuidade varia conforme a categoria..."),
            ("Como consultar débitos?", "Você pode consultar débitos pelo portal do CREA..."),
            ("O que acontece se não pagar?", "O não pagamento gera multa, juros e impedimentos..."),
            ("Posso parcelar?", "Sim, é possível parcelar em até 10 vezes..."),
            ("Como emitir certidão?", "A certidão pode ser emitida pelo portal eletrônico..."),
        ]
        
        for user_msg, assistant_msg in conversation_turns:
            simulated_history.append({"role": "user", "content": user_msg})
            simulated_history.append({"role": "assistant", "content": assistant_msg})
        
        # Test with different history sizes
        test_sizes = [
            (2, "2 turnos (curto)"),
            (6, "6 turnos (médio)"),
            (10, "10 turnos (longo)"),
            (20, "20 turnos (máximo)"),
        ]
        
        # Test: Ambiguous question after long history (SHOULD still clarify)
        for size, description in test_sizes:
            print(f"\n  📊 Testing with {description}...")
            
            history = simulated_history[:size*2] if size*2 <= len(simulated_history) else simulated_history
            
            self.run_test(
                "Degradation",
                f"Ambiguous after {description}",
                "E sobre o outro assunto?",
                "DEVE pedir clarificação mesmo com histórico longo",
                use_custom_history=history
            )
    
    def test_topic_switching(self):
        """Test topic switching - should treat new topics independently."""
        print("\n📌 CATEGORY 6: TOPIC SWITCHING (Context Isolation)")
        print("-"*60)
        self.clear_history()
        
        # Start with one topic
        self.run_test(
            "TopicSwitch",
            "First topic: ART",
            "O que é ART e qual sua importância?",
            "Explicação sobre ART"
        )
        
        self.run_test(
            "TopicSwitch",
            "Follow-up on ART",
            "Quem pode emitir?",
            "Deve usar contexto de ART"
        )
        
        # Switch to completely different topic
        self.run_test(
            "TopicSwitch",
            "New topic: Processo Ético",
            "Me explique sobre processo ético no CREA",
            "Deve tratar como nova pergunta, buscar sobre processos éticos"
        )
        
        # Ambiguous after topic switch
        self.run_test(
            "TopicSwitch",
            "Ambiguous after switch",
            "E como funciona o prazo?",
            "Pode perguntar se refere a ART ou processo ético, ou assumir processo ético como mais recente"
        )
    
    def test_multi_questions(self):
        """Test handling of multiple questions at once."""
        print("\n📌 CATEGORY 7: MULTI-QUESTION HANDLING")
        print("-"*60)
        self.clear_history()
        
        multi_questions = [
            ("Qual o prazo da anuidade e como faço para parcelar?", 
             "Deve responder ambas ou guiar para responder uma por vez"),
            ("Quero saber sobre ART, registro e anuidade. Pode me ajudar?", 
             "Deve estruturar resposta ou perguntar por qual começar"),
            ("O que é CAT, quando usar e quem emite? Também quero saber o custo.", 
             "Deve organizar resposta ou pedir para fragmentar"),
        ]
        
        for question, expected in multi_questions:
            self.run_test("MultiQuestion", f"Multi: {question[:40]}", question, expected)
            self.clear_history()
    
    def test_edge_cases(self):
        """Test edge cases and special scenarios."""
        print("\n📌 CATEGORY 8: EDGE CASES")
        print("-"*60)
        self.clear_history()
        
        edge_cases = [
            ("", "Deve lidar graciosamente com mensagem vazia"),
            ("?", "Deve pedir clarificação"),
            ("kkkkk", "Deve responder cordialmente ou pedir clarificação"),
            ("QUERO FALAR COM ATENDENTE AGORA!!!", 
             "Deve manter tom profissional e oferecer ajuda"),
            ("Você não serve para nada, sempre responde errado", 
             "Deve manter calma e oferecer assistência"),
            ("Me diz tudo sobre tudo do CREA", 
             "Deve pedir para especificar o que deseja saber"),
        ]
        
        for message, expected in edge_cases:
            test_name = f"Edge: {message[:20] if message else '(empty)'}"
            self.run_test("EdgeCase", test_name, message if message else "(mensagem vazia)", expected)
            self.clear_history()
    
    def generate_report(self) -> str:
        """Generate a comprehensive markdown report of all tests."""
        report = []
        report.append("# 📊 Qualitative Test Report - Agentic Prompt Engineering\n")
        report.append(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Corpus ID:** `{self.corpus_id}`\n")
        report.append(f"**API URL:** `{self.api_url}`\n")
        report.append(f"**Total Tests:** {len(self.results)}\n")
        
        # Summary statistics
        success_count = sum(1 for r in self.results if r["success"])
        avg_time = sum(r["elapsed_seconds"] for r in self.results) / len(self.results) if self.results else 0
        
        report.append(f"\n## Summary\n")
        report.append(f"- **Successful Responses:** {success_count}/{len(self.results)}\n")
        report.append(f"- **Average Response Time:** {avg_time:.2f}s\n")
        
        # Group by category
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        report.append("\n---\n")
        
        # Detailed results by category
        for category, tests in categories.items():
            report.append(f"\n## {category}\n")
            
            for i, test in enumerate(tests, 1):
                report.append(f"\n### Test {i}: {test['test_name']}\n")
                report.append(f"**Message:** `{test['message'][:100]}{'...' if len(test['message']) > 100 else ''}`\n\n")
                report.append(f"**Expected Behavior:** {test['expected_behavior']}\n\n")
                report.append(f"**History Length:** {test['history_length']} turns\n\n")
                report.append(f"**Response Time:** {test['elapsed_seconds']}s\n\n")
                report.append(f"**Response:**\n")
                report.append(f"```\n{test['response']}\n```\n")
                report.append("\n**Analysis Required:** ✏️ _[Manual review needed]_\n")
                report.append("\n---\n")
        
        # Analysis section
        report.append("\n## 🔍 Semantic Analysis Checklist\n")
        report.append("""
Use this checklist to analyze the responses:

### Greetings
- [ ] Responses are fast (< 2s)?
- [ ] No RAG content in greeting responses?
- [ ] Tone is appropriate and cordial?

### Ambiguous Questions  
- [ ] Bot asks for clarification with options?
- [ ] Provides clear choices to disambiguate?
- [ ] Does NOT attempt to answer without clarifying?

### Factual Questions
- [ ] Uses RAG tool (mentions document-based info)?
- [ ] Cites sources at the end?
- [ ] Information appears accurate and complete?
- [ ] Informs if information is incomplete?

### Follow-up Questions
- [ ] Uses conversation context appropriately?
- [ ] Correctly interprets pronouns/references?
- [ ] Maintains topic continuity?

### Instruction Degradation
- [ ] Still asks for clarification after long history?
- [ ] Behavior consistent regardless of history length?
- [ ] System instructions still followed?

### Topic Switching
- [ ] Treats new topics independently?
- [ ] Does not mix context from different topics?
- [ ] Asks for clarification on ambiguous topic references?

### Multi-Question
- [ ] Guides user through questions systematically?
- [ ] Or answers all coherently with structure?
- [ ] Does not ignore any of the questions?

### Edge Cases
- [ ] Handles gracefully without errors?
- [ ] Maintains professional tone under pressure?
- [ ] Asks for clarification when genuinely confused?
""")
        
        return "\n".join(report)
    
    def save_report(self, filename: Optional[str] = None):
        """Save the test report to a markdown file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qualitative_test_report_{timestamp}.md"
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        report = self.generate_report()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {filepath}")
        return filepath


def main():
    """Run the complete qualitative test suite."""
    print("🚀 Starting Agentic Prompt Engineering Qualitative Tests...")
    print(f"   Target: {API_URL}")
    print(f"   Corpus: {CORPUS_ID}")
    
    suite = AgenticTestSuite(CORPUS_ID, API_URL)
    
    try:
        suite.run_all_tests()
        filepath = suite.save_report()
        
        print("\n" + "="*80)
        print("📊 TEST SUITE COMPLETE")
        print("="*80)
        print(f"Total tests run: {len(suite.results)}")
        print(f"Report saved to: {filepath}")
        print("\nPlease review the report for semantic analysis of responses.")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        raise


if __name__ == "__main__":
    main()
