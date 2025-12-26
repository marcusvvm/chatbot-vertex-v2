# Refatoração do Sistema de Chat

**Data:** 25/12/2024  
**Versão:** 2.0  
**Status:** ✅ Implementado

---

## Resumo Executivo

Esta refatoração simplificou a arquitetura do sistema de chat, removendo complexidade desnecessária e implementando um sistema de presets para facilitar a configuração pelo frontend.

### Mudanças Principais

| Antes | Depois |
|-------|--------|
| HistoryFilter com embeddings | Filtro simples (últimas N mensagens) + inteligência no prompt |
| Validação rígida de generation_config | Passthrough para Google API (future-proof) |
| Configuração manual por corpus | Sistema de presets (4 core + custom) |
| Sem instruções de contexto | Context management no system prompt |

### Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `app/domain/chat/service.py` | Removido HistoryFilter, simplificado |
| `app/domain/chat/history_filter.py` | **DELETADO** |
| `app/schemas/config.py` | Passthrough (extra="allow") |
| `app/config/models.py` | Passthrough + context_management_instructions |
| `app/config/adapters.py` | Passthrough em build_generate_content_config |
| `app/config/presets.py` | **NOVO** - Sistema de presets |
| `app/api/endpoints/config.py` | Novos endpoints de presets |
| `config/fixed.json` | Adicionado context_management_instructions |
| `config/presets.json` | **NOVO** - Storage de presets customizados |

---

## Novos Endpoints

### 1. GET /api/v1/config/presets

**Descrição:** Lista todos os presets disponíveis (core + customizados)

**Request:**
```http
GET /api/v1/config/presets
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "presets": [
    {
      "id": "balanced",
      "name": "Equilibrado (Recomendado)",
      "description": "Respostas precisas e rápidas. Bom para uso geral.",
      "model_name": "gemini-2.5-pro",
      "is_core": true
    },
    {
      "id": "creative",
      "name": "Criativo",
      "description": "Respostas mais elaboradas. Melhor para explicações complexas.",
      "model_name": "gemini-2.5-pro",
      "is_core": true
    },
    {
      "id": "precise",
      "name": "Preciso",
      "description": "Respostas concisas e factuais. Ideal para consultas rápidas.",
      "model_name": "gemini-2.5-flash",
      "is_core": true
    },
    {
      "id": "fast",
      "name": "Rápido",
      "description": "Otimizado para velocidade. Menor latência.",
      "model_name": "gemini-2.5-flash",
      "is_core": true
    }
  ]
}
```

---

### 2. GET /api/v1/config/presets/{preset_id}

**Descrição:** Obtém configuração completa de um preset

**Request:**
```http
GET /api/v1/config/presets/balanced
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": "balanced",
  "name": "Equilibrado (Recomendado)",
  "description": "Respostas precisas e rápidas. Bom para uso geral.",
  "is_core": true,
  "model_name": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 4096,
    "thinking_budget": 1024
  },
  "rag_retrieval_top_k": 10,
  "max_history_length": 20
}
```

**Response (404):**
```json
{
  "detail": "Preset not found: invalid_id"
}
```

---

### 3. POST /api/v1/config/presets

**Descrição:** Cria um novo preset customizado

**Request:**
```http
POST /api/v1/config/presets
Authorization: Bearer {token}
Content-Type: application/json

{
  "id": "juridico",
  "name": "Departamento Jurídico",
  "description": "Configuração otimizada para consultas jurídicas",
  "model_name": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.1,
    "max_output_tokens": 8192,
    "thinking_budget": 2048
  },
  "rag_retrieval_top_k": 15,
  "max_history_length": 20
}
```

**Response (201):**
```json
{
  "message": "Preset created successfully",
  "preset": {
    "id": "juridico",
    "name": "Departamento Jurídico",
    "description": "Configuração otimizada para consultas jurídicas",
    "is_core": false,
    "model_name": "gemini-2.5-pro",
    "generation_config": {
      "temperature": 0.1,
      "max_output_tokens": 8192,
      "thinking_budget": 2048
    },
    "rag_retrieval_top_k": 15,
    "max_history_length": 20
  }
}
```

**Response (400) - ID reservado:**
```json
{
  "detail": "Cannot create preset with core ID: balanced"
}
```

**Response (400) - Já existe:**
```json
{
  "detail": "Preset already exists: juridico"
}
```

---

### 4. PUT /api/v1/config/presets/{preset_id}

**Descrição:** Atualiza um preset customizado existente

**Request:**
```http
PUT /api/v1/config/presets/juridico
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Jurídico v2",
  "generation_config": {
    "temperature": 0.15
  }
}
```

**Response (200):**
```json
{
  "message": "Preset updated successfully",
  "preset": {
    "id": "juridico",
    "name": "Jurídico v2",
    "description": "Configuração otimizada para consultas jurídicas",
    "is_core": false,
    "model_name": "gemini-2.5-pro",
    "generation_config": {
      "temperature": 0.15
    },
    "rag_retrieval_top_k": 15,
    "max_history_length": 20
  }
}
```

**Response (400) - Core preset:**
```json
{
  "detail": "Cannot modify core preset: balanced"
}
```

---

### 5. DELETE /api/v1/config/presets/{preset_id}

**Descrição:** Deleta um preset customizado

**Request:**
```http
DELETE /api/v1/config/presets/juridico
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "message": "Preset 'juridico' deleted successfully"
}
```

**Response (400) - Core preset:**
```json
{
  "detail": "Cannot delete core preset: balanced"
}
```

---

### 6. POST /api/v1/config/corpus/{corpus_id}/apply-preset/{preset_id}

**Descrição:** Aplica um preset a um corpus

**Request:**
```http
POST /api/v1/config/corpus/8207810320882728960/apply-preset/balanced
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "message": "Preset 'Equilibrado (Recomendado)' applied successfully",
  "corpus_id": "8207810320882728960",
  "preset_id": "balanced"
}
```

**Response (404):**
```json
{
  "detail": "Preset not found: invalid_preset"
}
```

---

## Schemas Atualizados

### GenerationConfigUpdate (Request)

```json
{
  "temperature": 0.2,           // float, opcional
  "top_p": 0.8,                 // float, opcional
  "top_k": 40,                  // int, opcional
  "max_output_tokens": 4096,    // int, opcional
  "thinking_budget": 1024,      // int, opcional (Gemini 2.5)
  "thinking_level": "high",     // string, opcional (Gemini 3)
  "any_future_param": "value"   // PASSTHROUGH: qualquer campo aceito
}
```

**Nota:** O schema usa `extra="allow"`, permitindo campos desconhecidos. Validação real acontece no Google API.

### CorpusConfigUpdate (Request)

```json
{
  "system_instruction": "Você é um assistente...",  // string, max 10000
  "model_name": "gemini-2.5-pro",                   // string
  "generation_config": { ... },                     // GenerationConfigUpdate
  "rag_retrieval_top_k": 10,                        // int, 1-50
  "timeout_seconds": 90.0,                          // float, 10-300
  "max_history_length": 20                          // int, 1-100
}
```

### PresetSummary (Response de list)

```json
{
  "id": "balanced",
  "name": "Equilibrado (Recomendado)",
  "description": "Respostas precisas e rápidas.",
  "model_name": "gemini-2.5-pro",
  "is_core": true
}
```

### Preset (Response completo)

```json
{
  "id": "balanced",
  "name": "Equilibrado (Recomendado)",
  "description": "Respostas precisas e rápidas.",
  "is_core": true,
  "model_name": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 4096,
    "thinking_budget": 1024
  },
  "rag_retrieval_top_k": 10,
  "max_history_length": 20
}
```

---

## Presets Core (Read-Only)

| ID | Nome | Modelo | Uso Recomendado |
|----|------|--------|-----------------|
| `balanced` | Equilibrado (Recomendado) | gemini-2.5-pro | Uso geral |
| `creative` | Criativo | gemini-2.5-pro | Explicações complexas |
| `precise` | Preciso | gemini-2.5-flash | Consultas rápidas |
| `fast` | Rápido | gemini-2.5-flash | Baixa latência |

**Características por preset:**

```
balanced:
  temperature: 0.2, max_tokens: 4096, thinking: 1024
  rag_top_k: 10, history: 20

creative:
  temperature: 0.5, max_tokens: 8192, thinking: 2048
  rag_top_k: 15, history: 20

precise:
  temperature: 0.1, max_tokens: 2048, thinking: none
  rag_top_k: 5, history: 20

fast:
  temperature: 0.2, max_tokens: 1024, thinking: none
  rag_top_k: 3, history: 10
```

---

## Context Management

O sistema agora inclui instruções de gerenciamento de contexto no system prompt (via `fixed.json`):

### Regras Implementadas

1. **Continuação de conversa:** Se a pergunta é claramente uma continuação, usa o contexto recente
2. **Mudança de tópico:** Se o tópico muda, ignora contexto anterior
3. **Dúvida:** Pergunta ao usuário se está mudando de assunto
4. **Eficiência:** Cumprimentos não usam RAG, perguntas ambíguas pedem clarificação

### Limite de Histórico

- **Padrão:** 20 mensagens
- **Configurável:** Via `max_history_length` no corpus ou preset
- **Comportamento:** Corte automático, transparente ao usuário

---

## Passthrough Parameters

### Como Funciona

1. Frontend envia `generation_config` com qualquer campo
2. Backend aceita (Pydantic com `extra="allow"`)
3. Backend passa direto para Google SDK
4. Google API valida e retorna erro se inválido

### Vantagens

- **Future-proof:** Novos parâmetros do Gemini 3/4 funcionam automaticamente
- **Menos código:** Sem normalização/tradução manual
- **Erros claros:** Mensagem direta do Google

### Exemplo de Erro

Se o frontend enviar parâmetro inválido:

```json
POST /api/v1/config/corpus/123
{
  "generation_config": {
    "temperature": 5.0  // Inválido
  }
}
```

A configuração é salva (backend aceita), mas ao usar o chat:

```json
{
  "error": {
    "code": 400,
    "message": "Invalid value for 'temperature': must be between 0 and 2",
    "status": "INVALID_ARGUMENT"
  }
}
```

---

## Migração

### Para Frontend Existente

1. **Nenhuma mudança obrigatória** - endpoints antigos continuam funcionando
2. **Opcional:** Usar novos endpoints de presets para UX melhorada
3. **Remover:** Campo `thinking_budget` de top-level (agora está em `generation_config`)

### Checklist

- [ ] Atualizar UI para mostrar seletor de presets
- [ ] Implementar fluxo de aplicar preset
- [ ] (Opcional) Implementar CRUD de presets customizados
- [ ] Testar passthrough com campos desconhecidos

---

## Scripts de Validação

```bash
# Validar toda a implementação
python scripts/validate_simplification_e2e.py

# Testar endpoint de presets
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/config/presets

# Aplicar preset
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/config/corpus/{corpus_id}/apply-preset/balanced
```
