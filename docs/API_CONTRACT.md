# RAG API - Contrato

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Autenticação e Segurança](#autenticação-e-segurança)
3. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Management (Corpus)](#management-corpus)
   - [Documents](#documents)
   - [Chat](#chat)
4. [Modelos de Dados](#modelos-de-dados)
5. [Códigos HTTP](#códigos-http)
6. [Limitações e Restrições](#limitações-e-restrições)
7. [Erros Comuns](#erros-comuns)
8. [Análise Crítica da API](#análise-crítica-da-api)

---

## 📖 Visão Geral

A **RAG API** é uma camada de abstração sobre o Google Vertex AI RAG Engine, projetada para facilitar a gestão de documentos departamentais e chat com grounding (RAG - Retrieval Augmented Generation).

### Conceitos Principais

- **Corpus (Departamento)**: Container lógico que armazena documentos relacionados a um departamento específico. No Vertex AI, é chamado de RAG Corpus.
- **Documento**: Arquivo (PDF, TXT, DOCX, MD) indexado dentro de um corpus para retrieval.
- **RAG (Retrieval Augmented Generation)**: Técnica que permite à IA responder perguntas baseada apenas nos documentos fornecidos (grounding).
- **Chat**: Conversa multi-turn com a IA, usando documentos de um corpus específico como base de conhecimento.

### Stack Tecnológico

- **Framework**: FastAPI
- **Cloud Provider**: Google Cloud Platform

**Permissões IAM Necessárias:**
- `aiplatform.ragCorpora.*` (criar, listar, deletar corpora)
- `aiplatform.ragFiles.*` (upload, listar, deletar files)

---

---

## 🔐 Autenticação e Segurança

### Autenticação da API (JWT)
> [!IMPORTANT]
> **Autenticação Obrigatória**: Todos os endpoints (exceto `/health` e `/docs`) requerem autenticação via **JWT Bearer Token**.

- **Tipo**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Algoritmo**: HS256
- **Expiração**: Configurável (padrão 30 dias)

**Gerar Token (CLI):**
```bash
python scripts/generate_token.py --user admin --purpose admin
```

### Autenticação Google Cloud
A API autentica-se no GCP via **Service Account**:
- **Arquivo:** `credentials/credentials-rag.json`
- **Projeto:** Configurado em `GCP_PROJECT_ID` no `.env`
- **Escopos:** `https://www.googleapis.com/auth/cloud-platform`

### CORS (Cross-Origin Resource Sharing)
Restrito via Regex para:
- Localhost e 127.0.0.1
- Rede Local (192.168.x.x e 10.x.x.x)
- Domínio `*.crea-go.org.br`

---

## 🌐 Endpoints

### Base URL Configuration

```
Produção: http://<seu-servidor>:8000/api/v1
Desenvolvimento: http://localhost:8000/api/v1
```

---

### Health Check

#### `GET /health`

Verifica a saúde da API e conectividade com GCP.

**Tags**: `[Health]`

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response 200 OK**:
```json
{
  "status": "healthy",
  "google_auth": "connected",
  "project_id": "rag-projetos-crea",
  "mode": "rag_engine_direct"
}
```

**Response 503 Service Unavailable**:
```json
{
  "detail": "Google Cloud Authentication Failed: [error message]"
}
```

**Uso**:
- Monitoramento de uptime
- Verificação de conectividade GCP
- Health check de Kubernetes/Docker

---

## Management (Corpus)

Endpoints para gerenciar departamentos (RAG Corpora).

---

### Criar Corpus

#### `POST /api/v1/management/corpus`

Cria um novo departamento (RAG Corpus) no Vertex AI.

**Tags**: `[management]`

**Request Body**:
```json
{
  "department_name": "Juridico",
  "description": "Departamento Jurídico - Contratos e pareceres"
}
```

**Schemas**:
- `department_name` (string, obrigatório): Nome do departamento
- `description` (string, opcional): Descrição do corpus

**Comportamento Especial**:
- ✅ Auto-adiciona prefixo `DEP-` se ausente
- ⏱️ Operação síncrona (aguarda confirmação do GCP)
- ⚠️ Pode levar 5-15 segundos

**Response 201 Created**:
```json
{
  "id": "1234567890123456789",
  "display_name": "DEP-Juridico",
  "name": "projects/projeto/locations/us-east4/ragCorpora/1234567890123456789",
  "create_time": null
}
```

**Códigos HTTP**:
- `201 Created`: Corpus criado com sucesso
- `400 Bad Request`: Validação falhou
- `409 Conflict`: Corpus com mesmo nome já existe
- `502 Bad Gateway`: Erro do Vertex AI

**Limitações**:
- ⚠️ `create_time` sempre `null` (limitação do SDK)
- ⚠️ Não valida duplicatas por `display_name` antes da criação

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/management/corpus" \
  -H "Content-Type: application/json" \
  -d '{
    "department_name": "RH",
    "description": "Recursos Humanos"
  }'
```

---

### Listar Corpora

#### `GET /api/v1/management/corpus`

Lista todos os departamentos do sistema.

**Tags**: `[management]`

**Filtro Automático**:
- ✅ Retorna apenas corpora com prefixo `DEP-`
- ❌ Corpora de outros sistemas são ocultados

**Response 200 OK**:
```json
[
  {
    "id": "1234567890123456789",
    "display_name": "DEP-Juridico",
    "name": "projects/projeto/locations/us-east4/ragCorpora/1234567890123456789",
    "create_time": null
  },
  {
    "id": "9876543210987654321",
    "display_name": "DEP-RH",
    "name": "projects/projeto/locations/us-east4/ragCorpora/9876543210987654321",
    "create_time": null
  }
]
```

**Códigos HTTP**:
- `200 OK`: Sucesso (pode retornar lista vazia)
- `502 Bad Gateway`: Erro do Vertex AI

**Paginação**: ❌ Não implementada (retorna todos)

---

### Listar Arquivos de um Corpus

#### `GET /api/v1/management/corpus/{corpus_id}/files`

Lista os arquivos dentro de um departamento específico.

**Tags**: `[management]`

**Path Parameters**:
- `corpus_id` (string, obrigatório): ID do corpus

**Request**:
```http
GET /api/v1/management/corpus/1234567890123456789/files HTTP/1.1
```

**Response 200 OK**:
```json
[
  {
    "id": "1111111111111111111",
    "display_name": "contrato_prestacao_servicos.pdf",
    "name": "projects/.../ragCorpora/.../ragFiles/1111111111111111111",
    "create_time": null
  }
]
```

**Códigos HTTP**:
- `200 OK`: Sucesso (pode retornar lista vazia)
- `404 Not Found`: Corpus não existe
- `502 Bad Gateway`: Erro do Vertex AI

**Limitações**:
- ⚠️ `create_time` sempre `null`
- ⚠️ Não retorna status de indexação do arquivo

---

### Deletar Corpus

#### `DELETE /api/v1/management/corpus/{corpus_id}`

Deleta um corpus inteiro e todos os seus arquivos.

**Tags**: `[management]`

**⚠️ OPERAÇÃO DESTRUTIVA - Sem Undo**

**Path Parameters**:
- `corpus_id` (string, obrigatório): ID do corpus

**Query Parameters**:
- `confirm` (boolean, obrigatório): Deve ser `true` para confirmar

**Request**:
```http
DELETE /api/v1/management/corpus/1234567890123456789?confirm=true HTTP/1.1
```

**Response 204 No Content**:
```
(corpo vazio)
```

**Códigos HTTP**:
- `204 No Content`: Corpus deletado com sucesso
- `400 Bad Request`: Confirmação ausente ou inválida
- `502 Bad Gateway`: Erro do Vertex AI

**Segurança**:
- ✅ Requer `?confirm=true` explícito
- ✅ Autenticação JWT obrigatória
- ❌ Sem auditoria de quem deletou

**Exemplo cURL**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/management/corpus/123456?confirm=true"
```

---

## Documents

Endpoints para gerenciar documentos dentro de corpora.

---

### Upload de Documento

#### `POST /api/v1/documents/upload`

Upload de documento para indexação em um corpus.

**Tags**: `[documents]`

**Content-Type**: `multipart/form-data`

**Form Fields**:
- `file` (file, obrigatório): Arquivo para upload
- `corpus_id` (string, obrigatório): ID do corpus de destino
- `user_id` (string, obrigatório): ID do usuário (mantido por compatibilidade)

**Validações**:

| Validação           | Limite                         | Código de Erro               |
| ------------------- | ------------------------------ | ---------------------------- |
| Extensão do arquivo | `.pdf`, `.txt`, `.docx`, `.md` | 415 Unsupported Media Type   |
| Tamanho máximo      | 25 MB                          | 413 Request Entity Too Large |
| Tamanho mínimo      | > 0 bytes                      | 400 Bad Request              |
| Corpus existe       | N/A                            | 404 Not Found                |

**Request**:
```http
POST /api/v1/documents/upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="manual.pdf"
Content-Type: application/pdf

<binary data>
------WebKitFormBoundary
Content-Disposition: form-data; name="corpus_id"

1234567890123456789
------WebKitFormBoundary
Content-Disposition: form-data; name="user_id"

user123
------WebKitFormBoundary--
```

**Response 201 Created**:
```json
{
  "rag_file_id": "9999999999999999999",
  "gcs_uri": "projects/.../ragCorpora/.../ragFiles/9999999999999999999",
  "display_name": "manual.pdf",
  "corpus_id": "1234567890123456789",
  "status": "uploaded"
}
```

**Códigos HTTP**:
- `201 Created`: Upload bem-sucedido
- `400 Bad Request`: Arquivo vazio
- `404 Not Found`: Corpus não existe
- `413 Request Entity Too Large`: Arquivo > 25MB
- `415 Unsupported Media Type`: Extensão não permitida
- `502 Bad Gateway`: Erro do Vertex AI

**Processamento Assíncrono**:
- ⏱️ Upload é **síncrono** (aguarda confirmação)
- ⏱️ Indexação é **assíncrona** (pode levar 10-60 segundos)
- ⚠️ API não retorna status de indexação
- ⚠️ Cliente deve aguardar antes de usar no chat

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@/path/to/document.pdf" \
  -F "corpus_id=1234567890123456789" \
  -F "user_id=user123"
```

**Cleanup Automático**:
- ✅ Arquivo temporário deletado após upload
- ✅ Cleanup executado mesmo em caso de erro

---

### Deletar Documento

#### `DELETE /api/v1/documents/{corpus_id}/files/{file_id}`

Deleta um arquivo específico de um corpus.

**Tags**: `[documents]`

**Path Parameters**:
- `corpus_id` (string, obrigatório): ID do corpus
- `file_id` (string, obrigatório): ID do arquivo

**Request**:
```http
DELETE /api/v1/documents/1234567890123456789/files/9999999999999999999 HTTP/1.1
```

**Response 204 No Content**:
```
(corpo vazio)
```

**Códigos HTTP**:
- `204 No Content`: Sempre retornado (operação idempotente)
- `502 Bad Gateway`: Erro do Vertex AI (não relacionado a "not found")

**Idempotência**:
- ✅ Deletar arquivo inexistente retorna `204` (sem erro)
- ✅ Seguro re-executar múltiplas vezes

**Exemplo cURL**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/123456/files/999999"
```

---

### Obter Detalhes de Documento

#### `GET /api/v1/documents/{corpus_id}/files/{file_id}`

Retorna detalhes de um arquivo específico.

**Tags**: `[documents]`

**Path Parameters**:
- `corpus_id` (string, obrigatório): ID do corpus
- `file_id` (string, obrigatório): ID do arquivo

**Request**:
```http
GET /api/v1/documents/1234567890123456789/files/9999999999999999999 HTTP/1.1
```

**Response 200 OK**:
```json
{
  "id": "9999999999999999999",
  "display_name": "manual.pdf",
  "name": "projects/.../ragCorpora/.../ragFiles/9999999999999999999",
  "create_time": "2025-11-21T10:30:00Z",
  "update_time": "2025-11-21T10:30:00Z"
}
```

**Códigos HTTP**:
- `200 OK`: Arquivo encontrado
- `404 Not Found`: Arquivo ou corpus não existe
- `502 Bad Gateway`: Erro do Vertex AI

**Limitações**:
- ⚠️ `create_time`/`update_time` podem ser `null` dependendo do SDK
- ❌ Não retorna status de indexação

---

## Chat

Endpoint para interação com RAG chat.

---

### Chat com RAG

#### `POST /api/v1/chat/`

Envia uma mensagem para a IA com grounding em documentos de um corpus.

**Tags**: `[chat]`

**Modelo de IA**: Gemini 2.5 Pro

**Request Body**:
```json
{
  "message": "Quem é o presidente do CREA Goiás?",
  "history": [
    {
      "role": "user",
      "content": "Olá"
    },
    {
      "role": "model",
      "content": "Olá! Como posso ajudar?"
    }
  ],
  "corpus_id": "1234567890123456789"
}
```

**Schemas**:
```typescript
interface Message {
  role: "user" | "model";
  content: string;
}

interface ChatRequest {
  message: string;          // Mensagem atual (obrigatório)
  history: Message[];       // Histórico da conversa (opcional, padrão: [])
  corpus_id: string;        // ID do corpus para grounding (obrigatório)
}
```

**Response 200 OK**:
```json
{
  "response": "Segundo o documento info_crea.txt, o presidente do CREA Goiás é o Engenheiro Civil Lamartine Moreira. Seu mandato é de 2024 a 2026.",
  "new_history": [
    {
      "role": "user",
      "content": "Olá"
    },
    {
      "role": "model",
      "content": "Olá! Como posso ajudar?"
    },
    {
      "role": "user",
      "content": "Quem é o presidente do CREA Goiás?"
    },
    {
      "role": "model",
      "content": "Segundo o documento info_crea.txt, o presidente do CREA Goiás é o Engenheiro Civil Lamartine Moreira. Seu mandato é de 2024 a 2026."
    }
  ]
}
```

**Códigos HTTP**:
- `200 OK`: Resposta gerada com sucesso
- `404 Not Found`: Corpus não existe
- `500 Internal Server Error`: Erro genérico

**Configuração do Modelo**:

```python
# Parâmetros de Geração
temperature: 0.2          # Respostas mais determinísticas
top_p: 0.8               # Nucleus sampling
top_k: 40                # Limite de tokens considerados
max_output_tokens: 2048  # Máximo de tokens na resposta

# Safety Settings
HARASSMENT: BLOCK_MEDIUM_AND_ABOVE
HATE_SPEECH: BLOCK_MEDIUM_AND_ABOVE
SEXUALLY_EXPLICIT: BLOCK_MEDIUM_AND_ABOVE
DANGEROUS_CONTENT: BLOCK_MEDIUM_AND_ABOVE
```

**System Instruction (Persona)**:
- Assistente Virtual do CREA Goiás
- Uso estritamente interno (funcionários)
- Tom profissional, direto e prestativo
- Responde **APENAS** com base nos documentos (grounding estrito)
- Cita fontes quando possível

**Comportamento de Grounding**:
- ✅ Usa apenas informações dos documentos do corpus
- ✅ Cita o nome do documento na resposta
- ✅ Retorna mensagem padrão se resposta não estiver nos docs
- ❌ Não usa conhecimento prévio do modelo

**RAG Configuration**:
- `similarity_top_k`: 3 (retorna top 3 chunks mais similares)
- Retrieval automático baseado na query

**Contexto Multi-Turn**:
- ✅ Suporta histórico de conversas
- ✅ Mantém contexto entre mensagens
- ⚠️ Cliente deve gerenciar histórico (stateless)
- ⚠️ **Limite Automático**: Histórico truncado automaticamente para as últimas **20 mensagens** (silencioso).

**Exemplo cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Qual o endereço da sede?",
    "history": [],
    "corpus_id": "1234567890123456789"
  }'
```

**Configuração do Modelo (gemini-2.5-pro)**:
| Parâmetro       | Valor        | Descrição                        |
| --------------- | ------------ | -------------------------------- |
| Thinking Budget | 1024 tokens  | Raciocínio interno do modelo     |
| Max Output      | 16384 tokens | Limite máximo de resposta        |
| Timeout         | 90 segundos  | Tempo máximo de processamento    |
| RAG Top K       | 10 chunks    | Chunks recuperados para contexto |
| Temperature     | 0.2          | Respostas mais determinísticas   |

**Limitações**:
- ⏱️ Timeout de 90s (pode ser insuficiente para consultas muito complexas)
- 💾 Sem cache de respostas
- 📊 Sem rate limiting
- 📜 Histórico limitado a 20 mensagens

---

## 📊 Modelos de Dados

### CorpusCreate
```json
{
  "department_name": "string (obrigatório)",
  "description": "string (opcional)"
}
```

### CorpusResponse
```json
{
  "id": "string",
  "display_name": "string",
  "name": "string",
  "create_time": "datetime | null"
}
```

### DocumentUploadResponse
```json
{
  "rag_file_id": "string",
  "gcs_uri": "string",
  "display_name": "string",
  "corpus_id": "string",
  "status": "string (default: 'imported')"
}
```

### Message
```json
{
  "role": "user | model",
  "content": "string"
}
```

### ChatRequest
```json
{
  "message": "string",
  "history": "Message[]",
  "corpus_id": "string"
}
```

### ChatResponse
```json
{
  "response": "string",
  "new_history": "Message[]"
}
```

---

## 🚦 Códigos HTTP

### Sucesso (2xx)

| Código         | Significado       | Uso                      |
| -------------- | ----------------- | ------------------------ |
| 200 OK         | Sucesso           | GET requests             |
| 201 Created    | Recurso criado    | POST corpus, POST upload |
| 204 No Content | Sucesso sem corpo | DELETE requests          |

### Erro do Cliente (4xx)

| Código                       | Significado              | Exemplo                            |
| ---------------------------- | ------------------------ | ---------------------------------- |
| 400 Bad Request              | Validação falhou         | Arquivo vazio, confirmação ausente |
| 404 Not Found                | Recurso não existe       | Corpus/arquivo inexistente         |
| 409 Conflict                 | Conflito de estado       | Corpus duplicado                   |
| 413 Request Entity Too Large | Arquivo muito grande     | Upload > 25MB                      |
| 415 Unsupported Media Type   | Tipo de arquivo inválido | Upload de .exe                     |

### Erro do Servidor (5xx)

| Código                    | Significado              | Uso                 |
| ------------------------- | ------------------------ | ------------------- |
| 500 Internal Server Error | Erro genérico            | Exceção não tratada |
| 502 Bad Gateway           | Erro do serviço upstream | Vertex AI falhou    |
| 503 Service Unavailable   | Serviço indisponível     | GCP auth falhou     |

---

## ⚠️ Limitações e Restrições

### Limites de Upload
- **Tamanho máximo**: 25 MB por arquivo
- **Formatos aceitos**: PDF, TXT, DOCX, MD
- **Upload concorrente**: Não testado/garantido

### Limites de Corpus
- **Máximo de corpora**: Limitado pelo projeto GCP
- **Naming**: Prefixo `DEP-` obrigatório (auto-adicionado)
- **Duplicatas**: Não validadas antes da criação

### Limites de Chat
- **Tamanho do histórico**: Sem limite (risco de timeout)
- **Timeout**: Não configurado
### 1. "Google Cloud Authentication Failed"
**Causa**: Service account inválida ou sem permissões  
**Solução**: Verificar `GOOGLE_APPLICATION_CREDENTIALS` e permissões IAM

### 2. "Corpus not found"
**Causa**: ID do corpus inválido ou deletado  
**Solução**: Verificar ID com `GET /api/v1/management/corpus`

### 3. "Arquivo muito grande. Máximo: 25MB"
**Causa**: Upload excede limite do Vertex AI  
**Solução**: Comprimir arquivo ou dividir em partes

### 4. "Upstream Error from Google Cloud Platform"
**Causa**: Vertex AI retornou erro  
**Solução**: Verificar logs do GCP, quotas e status do serviço

### 5. Chat retorna informação incorreta
**Causa**: Documento não indexado ou grounding falhou  
**Solução**: Aguardar indexação (60s) após upload, verificar relevância dos docs

### 6. "Tipo de arquivo não suportado"
**Causa**: Extensão não permitida  
**Solução**: Converter para PDF, TXT, DOCX ou MD


---

## 📞 Contato
- Autor: Marcus Vinicius Vieira de Meneses
- Contato: (marcuscreago@gmail.com)

---