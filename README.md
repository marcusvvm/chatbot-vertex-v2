# 🧠 RAG API - Vertex AI

> **API padrão Facade para Gestão de Documentos e Chat com Google Vertex AI RAG Engine.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Vertex_AI-4285F4.svg)](https://cloud.google.com/vertex-ai)

---

## 📖 Visão Geral

A **RAG API** é uma camada de abstração construída sobre o Google Vertex AI. Ela permite criar assistentes virtuais baseados em documentos (RAG - Retrieval Augmented Generation).

### Principais Funcionalidades
- **Gestão de Corpus**: Criação e isolamento de bases de conhecimento por departamento
- **Upload de Documentos**: Ingestão de PDFs, TXTs e outros formatos diretamente para o Vertex AI RAG Engine
- **Chat Contextual**: Interface de chat que utiliza os documentos indexados
- **Autenticação JWT**: Segurança para todos os endpoints

---

## 🏗️ Arquitetura

O sistema adota uma arquitetura de **Região Híbrida**:

| Componente             | Região GCP     | Função                                                                |
| ---------------------- | -------------- | --------------------------------------------------------------------- |
| **RAG Engine & Dados** | `europe-west3` | Armazenamento de documentos e índices vetoriais (Residência de Dados) |
| **LLM (Gemini)**       | `us-central1`  | Geração de respostas (`gemini-2.5-pro`)                               |

📚 **Documentação Completa:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 📂 Estrutura do Projeto

```bash
api-vertex/
├── app/
│   ├── api/            # Endpoints (Router, Controllers)
│   ├── core/           # Configurações, Auth, Exceptions
│   ├── schemas/        # Modelos Pydantic (Request/Response)
│   ├── services/       # Lógica de Negócio (Vertex AI Integration)
│   └── main.py         # Entrypoint da Aplicação
├── docs/               # Documentação Técnica
├── scripts/            # Scripts Utilitários (Token Gen, Tests)
├── tests/              # Testes Automatizados (Pytest)
├── .env.example        # Modelo de Variáveis de Ambiente
└── requirements.txt    # Dependências do Projeto
```

---

## 🚀 Quick Start

### Pré-requisitos
- Python 3.10+
- Conta Google Cloud com Vertex AI habilitado
- Credenciais de Service Account

### 1. Instalação

```bash
# Clone o repositório
git clone https://github.com/marcusvvm/api-vertex.git
cd api-vertex

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2. Configuração

Copie o arquivo de exemplo e configure:
```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:
```env
GOOGLE_APPLICATION_CREDENTIALS=credentials/credentials-rag.json
GCP_PROJECT_ID=seu-projeto-gcp
GCP_LOCATION=europe-west3
GCP_LOCATION_CHAT=us-central1
JWT_SECRET_KEY=sua-chave-secreta-aqui
```

### 3. Subir o Servidor

```bash
# Desenvolvimento (com hot-reload)
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produção (com gunicorn + multi-worker)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

Acesse: http://localhost:8000/docs

---

## ⚙️ Configuração Dinâmica por Corpus

A API suporta **configuração personalizada por departamento/corpus**, permitindo que cada área tenha sua própria persona e parâmetros de IA.

### 🎯 Principais Recursos

- **Persona customizável** - Cada departamento pode ter seu próprio assistente especializado
- **Parâmetros ajustáveis** - Temperature, RAG top-k, timeout, etc.
- **Future-proof** - Campo `configuracao_extra` aceita novos parâmetros do Google
- **Lazy loading** - Configs só criadas quando necessário
- **Zero órfãos** - Configs deletadas automaticamente com o corpus

### 📘 Exemplos de Uso

#### Departamento Jurídico (Conservador)
```bash
curl -X PUT http://localhost:8000/api/v1/config/corpus/{corpus_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "system_instruction": "Você é o assistente jurídico. Seja preciso e técnico.",
    "generation_config": {
      "temperature": 0.1,
      "max_output_tokens": 8192
    },
    "rag_retrieval_top_k": 15
  }'
```

#### Departamento RH (Equilibrado)
```bash
curl -X PUT http://localhost:8000/api/v1/config/corpus/{corpus_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "system_instruction": "Você é o assistente de RH. Seja empático e prestativo.",
    "generation_config": {
      "temperature": 0.4
    }
  }'
```

### 📚 Documentação Completa

- **[CONFIGURATION.md](docs/CONFIGURATION.md)** - Guia completo de configuração
- **[config/corpus/](config/corpus/)** - Exemplos por departamento
- **[API Contract](docs/API_CONTRACT.md)** - Referência dos endpoints

---

### 4. Derrubar o Servidor

```bash
# Terminal interativo: Ctrl + C

# Se rodando em background:
fuser -k 8000/tcp
```

📚 **Guia Completo de Operações:** [docs/OPERATIONS.md](docs/OPERATIONS.md)

---

## 🔑 Autenticação

### Gerar Token JWT

```bash
# Token admin (30 dias)
python scripts/generate_token.py --user admin --purpose admin

# Token de longa duração (1 ano)
python scripts/generate_token.py --user sistema --purpose admin --hours 8760
```

### Usar o Token

```bash
# Adicione ao header Authorization
curl -H "Authorization: Bearer SEU_TOKEN" http://localhost:8000/api/v1/management/corpus
```

📚 **Guia Completo de Autenticação:** [docs/JWT_USAGE.md](docs/JWT_USAGE.md)

---

## 📡 Operações Essenciais da API

### Usando o Swagger UI (Recomendado)

A maneira mais fácil de testar e usar a API é através da interface Swagger UI:

1. **Acesse:** http://localhost:8000/docs
2. **Autentique:**
   - Clique no botão **"Authorize"** 🔒 (canto superior direito)
   - Cole seu token JWT no campo
   - Clique em **"Authorize"** e depois **"Close"**
3. **Teste os endpoints:**
   - Expanda qualquer endpoint (ex: `POST /api/v1/management/corpus`)
   - Clique em **"Try it out"**
   - Preencha os parâmetros
   - Clique em **"Execute"**

Todos os endpoints estão documentados com exemplos de request/response.

### Exemplos via cURL (Alternativa)

```bash
# Health Check
curl http://localhost:8000/health

# Listar Corpus (requer auth)
curl -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/api/v1/management/corpus

# Chat
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Sua pergunta aqui", "corpus_id": "SEU_CORPUS_ID", "history": []}'
```

📚 **Contrato Completo da API:** [docs/API_CONTRACT.md](docs/API_CONTRACT.md)

---

## 🧪 Testes

### Executar Suite de Testes Completa
```bash
python scripts/test_complete_api.py
```

### Executar Testes Unitários
```bash
pytest tests/test_auth.py -v
```

---

## 🤖 Configuração do Modelo de Chat

O chatbot usa o **Gemini 2.5 Pro**:
- **Thinking Budget:** 1024 tokens (raciocínio interno)
- **Max Output:** 16384 tokens
- **Timeout:** 90 segundos
- **RAG Retrieval:** Top 10 chunks

📚 **Configurações Detalhadas:** [docs/CHAT_CONFIGURATION.md](docs/CHAT_CONFIGURATION.md)

---

## 📚 Documentação Adicional

| Documento                                           | Descrição                                       |
| --------------------------------------------------- | ----------------------------------------------- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)             | Arquitetura técnica, regiões GCP, autenticação  |
| [API_CONTRACT.md](docs/API_CONTRACT.md)             | Contrato completo da API com todos os endpoints |
| [JWT_USAGE.md](docs/JWT_USAGE.md)                   | Guia completo de autenticação JWT               |
| [OPERATIONS.md](docs/OPERATIONS.md)                 | DevOps, deploy, troubleshooting                 |
| [CHAT_CONFIGURATION.md](docs/CHAT_CONFIGURATION.md) | Configuração do modelo Gemini                   |

---

## 🚦 Códigos de Erro Comuns

| Código | Significado      | Causa Comum                       |
| ------ | ---------------- | --------------------------------- |
| 400    | Bad Request      | Parâmetros inválidos              |
| 401    | Unauthorized     | Token JWT ausente/inválido        |
| 404    | Not Found        | Corpus ou arquivo não encontrado  |
| 413    | Entity Too Large | Arquivo > 25MB                    |
| 502    | Bad Gateway      | Erro de comunicação com Vertex AI |

---

## 📞 Contato

**Mantenedor:** Marcus Vinicius  
**Email:** marcuscreago@gmail.com  

---
