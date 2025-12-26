# Chat Configuration Guide

> Documentação técnica sobre as configurações do chat e tuning do modelo Gemini.

---

## 📋 Visão Geral

Este documento descreve as configurações disponíveis para o sistema de chat RAG, incluindo parâmetros do modelo, estratégias de diagnóstico e recomendações de tuning.

**Arquivo de Configuração:** `app/core/chat_config.py`

---

## 🔧 Parâmetros Configuráveis

### Modelo

```python
MODEL_NAME = "gemini-2.5-pro"  # Atual (com THINKING_BUDGET controlado)
# MODEL_NAME = "gemini-1.5-pro"  # Alternativo (sem thinking tokens)
```

| Modelo           | Thinking Tokens | THINKING_BUDGET | Recomendação                            |
| ---------------- | --------------- | --------------- | --------------------------------------- |
| `gemini-2.5-pro` | ✅ Usa           | Configurável    | ✅ Recomendado (com budget limitado)     |
| `gemini-1.5-pro` | ❌ Não usa       | N/A             | Alternativa para respostas muito longas |

---

### Thinking Budget (Controle de Raciocínio)

O `gemini-2.5-pro` usa tokens internos para "pensar" antes de responder. Sem controle, ele pode consumir a maioria do `max_output_tokens` em raciocínio, deixando pouco espaço para a resposta.

```python
# Thinking Budget Configuration (for gemini-2.5-pro)
THINKING_BUDGET = 1024  # Tokens reservados para raciocínio interno
```

| Valor  | Comportamento             | Caso de Uso                                |
| ------ | ------------------------- | ------------------------------------------ |
| `128`  | Mínimo, respostas rápidas | Perguntas simples, baixa latência          |
| `1024` | **Balanceado (atual)**    | Uso geral, equilíbrio qualidade/velocidade |
| `2048` | Mais reasoning            | Tarefas complexas, multi-step              |
| `-1`   | Dinâmico                  | Modelo decide automaticamente              |

**Implementação em `vertex_service.py`:**
```python
thinking_config=types.ThinkingConfig(
    thinking_budget=ChatConfig.THINKING_BUDGET
)
```

---

### Geração de Conteúdo

```python
GENERATION_CONFIG = {
    "temperature": 0.2,        # Respostas mais determinísticas
    "top_p": 0.8,              # Nucleus sampling
    "top_k": 40,               # Limite de tokens considerados
    "max_output_tokens": 16384 # Limite de tokens na resposta
}
```

| Parâmetro           | Valor | Descrição                                  |
| ------------------- | ----- | ------------------------------------------ |
| `temperature`       | 0.2   | Baixa = respostas mais consistentes        |
| `top_p`             | 0.8   | Probabilidade acumulada para sampling      |
| `top_k`             | 40    | Top K tokens a considerar                  |
| `max_output_tokens` | 16384 | Máximo de tokens gerados (inclui thinking) |

---

### RAG e Timeout

```python
RAG_RETRIEVAL_TOP_K = 5    # Chunks retornados na busca
TIMEOUT_SECONDS = 90.0     # Timeout da requisição
MAX_HISTORY_LENGTH = 20    # Mensagens no histórico
```

---

## 🔍 Diagnóstico de Truncamento

### Problema Identificado

Respostas estavam sendo cortadas no meio, sem completar a informação solicitada.

### Estratégia de Logging

Adicionado logging temporário em `app/services/vertex_service.py` para capturar metadados da resposta do Vertex AI:

```python
# === DIAGNOSTIC LOGGING (TEMPORARY) ===
import logging
logger = logging.getLogger(__name__)

if hasattr(response, 'candidates') and response.candidates:
    candidate = response.candidates[0]
    finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
    logger.warning(f"[DIAG] finish_reason: {finish_reason}")
    
    if hasattr(candidate, 'safety_ratings'):
        logger.warning(f"[DIAG] safety_ratings: {candidate.safety_ratings}")
    
    if hasattr(response, 'usage_metadata'):
        logger.warning(f"[DIAG] usage_metadata: {response.usage_metadata}")

response_text = response.text
logger.warning(f"[DIAG] response_length: {len(response_text)} chars")
# === END DIAGNOSTIC LOGGING ===
```

### Resultados Obtidos

#### Teste 1: `max_output_tokens = 2048` com `gemini-2.5-pro`

```
finish_reason: FinishReason.MAX_TOKENS
thoughts_token_count: 1457
candidates_token_count: 589
total_token_count: 3139
response_length: 1776 chars
```

**Análise:** Modelo usou 1457 tokens para "pensar" + 589 para resposta = 2046 (limite atingido).

#### Teste 2: `max_output_tokens = 8192` com `gemini-2.5-pro`

```
finish_reason: FinishReason.MAX_TOKENS
thoughts_token_count: 7863
candidates_token_count: 327
total_token_count: 9283
response_length: 737 chars
```

**Análise:** Modelo usou 7863 tokens para "pensar" (96%!), deixando apenas 327 para resposta.

---

## 🎯 Conclusões e Recomendações

### Por que as respostas eram truncadas?

O modelo `gemini-2.5-pro` possui um recurso de "thinking tokens" que consome a maior parte do `max_output_tokens` para raciocínio interno, deixando pouco espaço para a resposta visível.

### Configuração Atual (Recomendada)

| Parâmetro             | Valor            | Justificativa                                |
| --------------------- | ---------------- | -------------------------------------------- |
| `MODEL_NAME`          | `gemini-2.5-pro` | Modelo mais avançado com thinking controlado |
| `THINKING_BUDGET`     | 1024             | Balanceado: qualidade + velocidade           |
| `max_output_tokens`   | 16384            | Margem ampla para respostas longas           |
| `RAG_RETRIEVAL_TOP_K` | 5                | Contexto suficiente sem overhead             |
| `TIMEOUT_SECONDS`     | 90.0             | Acomodar respostas complexas                 |

### Quando Ajustar THINKING_BUDGET

| Cenário                  | Ação                                                            |
| ------------------------ | --------------------------------------------------------------- |
| Respostas truncadas      | Verificar se `THINKING_BUDGET` + resposta > `max_output_tokens` |
| Respostas superficiais   | Aumentar para 2048                                              |
| Latência alta            | Reduzir para 128                                                |
| Perguntas simples lentas | Reduzir para 128                                                |

---

## 🛠️ Manutenção

### Logging de Diagnóstico (Removido)

O logging temporário foi removido após diagnóstico. Para reativar, adicione em `vertex_service.py` após `response = ...`:

```python
import logging
logger = logging.getLogger(__name__)
logger.warning(f"[DIAG] finish_reason: {response.candidates[0].finish_reason}")
logger.warning(f"[DIAG] usage_metadata: {response.usage_metadata}")
```

### Monitorar Finish Reason

Se problemas de truncamento retornarem, verifique:
1. `finish_reason` nos logs.
2. Se `finish_reason: MAX_TOKENS`, aumente `max_output_tokens`.
3. Se `finish_reason: SAFETY`, revise `safety_settings`.

---

**Última Atualização:** Dezembro 2025
