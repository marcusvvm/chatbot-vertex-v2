# Arquitetura do Sistema

Arquitetura técnica da RAG API Facade com foco em infraestrutura Google Cloud e decisões de design.

---

## Configuração GCP

### Variáveis de Ambiente

| Variável                         | Valor                              | Função                    |
| -------------------------------- | ---------------------------------- | ------------------------- |
| `GCP_PROJECT_ID`                 | `rag-projetos-crea`                | Projeto GCP               |
| `GCP_LOCATION`                   | `europe-west3`                     | Região RAG Engine (dados) |
| `GCP_LOCATION_CHAT`              | `us-central1`                      | Região Gemini (LLM)       |
| `GOOGLE_APPLICATION_CREDENTIALS` | `credentials/credentials-rag.json` | Service account           |

### Arquitetura de Regiões

| Componente | Região         | Responsabilidade                                          |
| ---------- | -------------- | --------------------------------------------------------- |
| RAG Engine | `europe-west3` | Armazenamento de documentos, índices vetoriais, retrieval |
| Gemini LLM | `us-central1`  | Geração de respostas (modelos mais recentes)              |

**Fluxo de dados:**
1. Upload → Documentos indexados na Europa
2. Retrieval → Chunks recuperados da Europa
3. Geração → Contexto enviado para LLM nos EUA
4. Resposta → Retornada ao cliente

---

## Estrutura do Código

```
app/
├── api/
│   ├── endpoints/              # Controllers HTTP
│   │   ├── chat.py             # POST /chat/
│   │   ├── config.py           # /config/* (presets, corpus config)
│   │   ├── corpus.py           # /management/corpus
│   │   └── documents.py        # /documents/*
│   └── router.py               # Agregador de rotas
├── config/                     # Sistema de configuração dinâmica
│   ├── adapters.py             # Tradução config → Google SDK
│   ├── models.py               # Modelos internos (dataclasses)
│   ├── presets.py              # CRUD de presets (balanced, creative, etc.)
│   └── service.py              # ConfigService (merge global + corpus)
├── core/                       # Infraestrutura transversal
│   ├── auth.py                 # Criação/validação JWT
│   ├── config.py               # Settings (pydantic-settings)
│   ├── dependencies.py         # Dependency injection (FastAPI Depends)
│   └── exceptions.py           # Exception handlers
├── domain/                     # Lógica de negócio
│   ├── chat/service.py         # ChatService (RAG + Gemini)
│   ├── corpus/service.py       # CorpusService (CRUD Vertex AI)
│   └── documents/service.py    # DocumentService (upload files)
├── infrastructure/
│   └── gcp/client.py           # GCPClient singleton (credenciais)
├── schemas/                    # Pydantic schemas (request/response)
└── main.py                     # Entrypoint FastAPI
```

---

## Autenticação

### API (JWT)

- Algoritmo: HS256
- Secret: Configurado em `JWT_SECRET_KEY`
- Todos os endpoints (exceto `/health`, `/docs`) requerem token

### Google Cloud (Service Account)

- Arquivo: `credentials/credentials-rag.json`
- Escopos: `https://www.googleapis.com/auth/cloud-platform`
- Permissões IAM: `Vertex AI User`, `Vertex AI Administrator`

```python
# Inicialização (app/infrastructure/gcp/client.py)
credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_APPLICATION_CREDENTIALS
).with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
```

---

## Ciclo de Requisição de Chat

```
1. Request → JWT validation
2. ConfigService → Carrega config (global + corpus)
3. RAG Tool → Monta retrieval (top_k chunks)
4. Gemini API → generate_content() com:
   - System instruction (persona + grounding rules)
   - Histórico de conversa
   - Mensagem do usuário
   - RAG grounding
5. Response → Texto formatado em Markdown
```

### Parâmetros de Geração (defaults)

| Parâmetro             | Valor            | Descrição                    |
| --------------------- | ---------------- | ---------------------------- |
| `model_name`          | `gemini-2.5-pro` | Modelo LLM                   |
| `temperature`         | 0.2              | Respostas determinísticas    |
| `max_output_tokens`   | 16384            | Limite de resposta           |
| `thinking_budget`     | 1024             | Tokens de raciocínio interno |
| `rag_retrieval_top_k` | 10               | Chunks recuperados           |
| `timeout_seconds`     | 90               | Timeout de requisição        |

---

## Concorrência

### Arquitetura

```
[Gunicorn] → 4 workers (processos)
    ↓
[FastAPI async] → event loop
    ↓
[ThreadPoolExecutor] → 50 threads para chamadas síncronas ao Gemini
```

### Configuração

```python
# app/main.py
chat_executor = ThreadPoolExecutor(max_workers=50)
```

O SDK `google.genai` é síncrono. O endpoint de chat usa `run_in_executor` para não bloquear o event loop.

---

**Última Atualização:** Dezembro 2025
