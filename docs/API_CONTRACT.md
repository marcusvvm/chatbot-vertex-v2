# API Contract

Contrato da RAG API - endpoints, schemas e códigos HTTP.

---

## Base URL

```
http://localhost:8000/api/v1
```

---

## Autenticação

Todos os endpoints (exceto `/health`) requerem JWT:

```
Authorization: Bearer {token}
```

---

## Endpoints

### Health Check

#### `GET /health`

Verifica saúde da API.

**Response 200:**
```json
{
  "status": "healthy",
  "google_auth": "configured",
  "project_id": "rag-projetos-crea",
  "mode": "rag_engine_direct"
}
```

---

### Management (Corpus)

#### `POST /api/v1/management/corpus`

Cria um corpus (departamento).

**Request:**
```json
{
  "department_name": "Juridico",
  "description": "Departamento Jurídico"
}
```

**Response 201:**
```json
{
  "id": "1234567890123456789",
  "display_name": "DEP-Juridico",
  "name": "projects/.../ragCorpora/1234567890123456789"
}
```

---

#### `GET /api/v1/management/corpus`

Lista todos os corpora.

**Response 200:** Array de corpus (filtra apenas `DEP-*`)

---

#### `GET /api/v1/management/corpus/{corpus_id}/files`

Lista arquivos de um corpus.

---

#### `DELETE /api/v1/management/corpus/{corpus_id}?confirm=true`

Deleta um corpus. Requer `?confirm=true`.

**Response 204:** No content

---

### Documents

#### `POST /api/v1/documents/upload`

Upload de documento para um corpus.

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file` (file): Arquivo (.pdf, .txt, .docx, .md)
- `corpus_id` (string): ID do corpus
- `user_id` (string): ID do usuário

**Limites:**
- Máximo: 25 MB
- Formatos: PDF, TXT, DOCX, MD

**Response 201:**
```json
{
  "rag_file_id": "9999999999999999999",
  "display_name": "documento.pdf",
  "corpus_id": "1234567890123456789",
  "status": "uploaded"
}
```

---

#### `GET /api/v1/documents/{corpus_id}/files/{file_id}`

Detalhes de um arquivo.

---

#### `DELETE /api/v1/documents/{corpus_id}/files/{file_id}`

Deleta um arquivo. Operação idempotente.

**Response 204:** No content

---

### Chat

#### `POST /api/v1/chat/`

Chat com RAG grounding.

**Request:**
```json
{
  "message": "Qual o endereço da sede?",
  "history": [],
  "corpus_id": "1234567890123456789"
}
```

**Response 200:**
```json
{
  "response": "Segundo o documento...",
  "new_history": [
    {"role": "user", "content": "Qual o endereço da sede?"},
    {"role": "model", "content": "Segundo o documento..."}
  ]
}
```

**Configuração padrão:**
- Modelo: `gemini-2.5-pro`
- Temperature: 0.2
- Timeout: 90s
- RAG top_k: 10
- Histórico: últimas 20 mensagens

---

### Configuration

#### `GET /api/v1/config/global`

Configuração global (defaults).

---

#### `GET /api/v1/config/corpus/{corpus_id}`

Configuração de um corpus (merge global + custom).

**Response 200:**
```json
{
  "corpus_id": "1234567890123456789",
  "config": {
    "model_name": "gemini-2.5-pro",
    "system_instruction": "...",
    "generation_config": {...},
    "rag_retrieval_top_k": 10
  },
  "has_custom_config": false
}
```

---

#### `PUT /api/v1/config/corpus/{corpus_id}`

Atualiza configuração de um corpus.

**Request (todos campos opcionais):**
```json
{
  "system_instruction": "Você é o assistente jurídico...",
  "generation_config": {
    "temperature": 0.1,
    "max_output_tokens": 8192
  },
  "rag_retrieval_top_k": 15
}
```

---

#### `DELETE /api/v1/config/corpus/{corpus_id}`

Remove configuração customizada (reseta para global).

---

### Presets

#### `GET /api/v1/config/presets`

Lista todos os presets.

**Response 200:**
```json
{
  "presets": [
    {"id": "balanced", "name": "Equilibrado", "model_name": "gemini-2.5-pro"},
    {"id": "creative", "name": "Criativo", "model_name": "gemini-2.5-pro"},
    {"id": "precise", "name": "Preciso", "model_name": "gemini-2.5-flash"},
    {"id": "fast", "name": "Rápido", "model_name": "gemini-2.5-flash"}
  ]
}
```

**Presets Default:**

| ID         | Modelo           | Temperature | Uso                   |
| ---------- | ---------------- | ----------- | --------------------- |
| `balanced` | gemini-2.5-pro   | 0.2         | Uso geral             |
| `creative` | gemini-2.5-pro   | 0.5         | Explicações complexas |
| `precise`  | gemini-2.5-flash | 0.1         | Consultas rápidas     |
| `fast`     | gemini-2.5-flash | 0.2         | Baixa latência        |

> **Nota:** Todos os presets são editáveis via PUT e exclusíveis via DELETE.

---

#### `GET /api/v1/config/presets/{preset_id}`

Detalhes de um preset.

---

#### `POST /api/v1/config/presets`

Cria novo preset.

**Request:**

> **Nota:** `id` deve ter no máximo 64 caracteres.

```json
{
  "id": "juridico",
  "name": "Departamento Jurídico",
  "description": "Configuração para consultas jurídicas",
  "model_name": "gemini-2.5-pro",
  "generation_config": {"temperature": 0.1},
  "rag_retrieval_top_k": 15
}
```

---

#### `PUT /api/v1/config/presets/{preset_id}`

Atualiza preset existente.

---

#### `DELETE /api/v1/config/presets/{preset_id}`

Deleta preset customizado.

---

#### `POST /api/v1/config/corpus/{corpus_id}/apply-preset/{preset_id}`

Aplica um preset a um corpus.

**Response 200:**
```json
{
  "message": "Preset 'balanced' applied successfully",
  "corpus_id": "1234567890123456789",
  "preset_id": "balanced"
}
```

---

## Códigos HTTP

### Sucesso

| Código | Uso                      |
| ------ | ------------------------ |
| 200    | GET, PUT, POST (algumas) |
| 201    | POST (criação)           |
| 204    | DELETE                   |

### Erro Cliente

| Código | Causa                  |
| ------ | ---------------------- |
| 400    | Validação falhou       |
| 401    | Token ausente/inválido |
| 404    | Recurso não encontrado |
| 413    | Arquivo > 25MB         |
| 415    | Formato não suportado  |

### Erro Servidor

| Código | Causa                           |
| ------ | ------------------------------- |
| 500    | Erro interno / Validação Google |
| 502    | Erro Vertex AI                  |
| 504    | Timeout                         |

---

## Schemas

### Message
```json
{"role": "user|model", "content": "string"}
```

### GenerationConfig
```json
{
  "temperature": 0.2,
  "top_p": 0.8,
  "top_k": 40,
  "max_output_tokens": 16384,
  "thinking_budget": 1024
}
```

> **Passthrough:** `generation_config` aceita campos adicionais (`extra="allow"`). Campos desconhecidos são passados diretamente para a API do Google.

---

**Última Atualização:** Dezembro 2025