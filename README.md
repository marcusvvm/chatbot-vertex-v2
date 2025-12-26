# RAG API - Vertex AI

API Facade para gestão de documentos e chat com Google Vertex AI RAG Engine.

---

## Requisitos

- Python 3.10+
- Credenciais GCP (service account com permissões Vertex AI)

---

## Quick Start

### 1. Clone o repositório

```bash
git clone https://github.com/marcusvvm/chatbot-vertex-v2.git
cd chatbot-vertex-v2
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure a chave JWT:

```env
JWT_SECRET_KEY=sua-chave-secreta-com-minimo-32-caracteres
```

### 5. Obtenha as credenciais GCP

Solicite o arquivo `credentials-rag.json` ao administrador do projeto GCP e coloque em:

```
credentials/credentials-rag.json
```

### 6. Gere um token JWT

```bash
./venv/bin/python scripts/generate_token.py --user admin --purpose admin
```

Copie o token gerado para usar nos endpoints autenticados.

### 7. Inicie o servidor

**Desenvolvimento:**
```bash
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Produção:**
```bash
./venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### 8. Verifique o funcionamento

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status":"healthy","google_auth":"configured","project_id":"rag-projetos-crea","mode":"rag_engine_direct"}
```

Acesse a documentação interativa: http://localhost:8000/docs

---

## Estrutura do Projeto

```
bia-back/
├── app/
│   ├── api/endpoints/          # Controllers (chat, config, corpus, documents)
│   ├── config/                 # Sistema de configuração dinâmica
│   │   ├── adapters.py         # Adaptadores para Google SDK
│   │   ├── models.py           # Modelos internos
│   │   ├── presets.py          # Sistema de presets
│   │   └── service.py          # ConfigService
│   ├── core/                   # Infraestrutura transversal
│   │   ├── auth.py             # Validação JWT
│   │   ├── config.py           # Settings
│   │   ├── dependencies.py     # Dependency injection
│   │   └── exceptions.py       # Exceptions customizadas
│   ├── domain/                 # Domínios de negócio
│   │   ├── chat/service.py     # Lógica de chat com Gemini
│   │   ├── corpus/service.py   # CRUD de corpus
│   │   └── documents/service.py # Upload de documentos
│   ├── infrastructure/gcp/     # Cliente GCP singleton
│   ├── schemas/                # Schemas Pydantic
│   └── main.py                 # Entrypoint FastAPI
├── config/                     # Arquivos de configuração
│   ├── fixed.json              # Config imutável (system prompts)
│   ├── global.json             # Defaults globais
│   ├── presets.json            # Presets customizados
│   └── corpus/                 # Configs específicas por corpus
├── credentials/                # Credenciais GCP (não versionado)
├── docs/                       # Documentação técnica
├── scripts/                    # Utilitários e testes
└── tests/                      # Testes Pytest
```

---

## Autenticação JWT

### Gerar Token

```bash
# Token padrão (30 dias)
./venv/bin/python scripts/generate_token.py --user admin --purpose admin

# Token de longa duração (1 ano)
./venv/bin/python scripts/generate_token.py --user sistema --purpose admin --hours 8760
```

### Usar Token

Adicione o header `Authorization` em todas as requisições:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" http://localhost:8000/api/v1/management/corpus
```

No Swagger UI:
1. Acesse http://localhost:8000/docs
2. Clique em **Authorize** 🔒
3. Cole o token
4. Clique em **Authorize**

### Endpoints públicos

- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

Todos os demais endpoints requerem autenticação.

---

## Testes

```bash
# Teste completo da API
./venv/bin/python scripts/test_complete_api.py

# Teste de configuração e presets
./venv/bin/python scripts/test_production_config.py

# Teste de concorrência
./venv/bin/python scripts/test_concurrency.py
```

---

## Documentação Adicional

| Documento                                 | Descrição                                          |
| ----------------------------------------- | -------------------------------------------------- |
| [API_CONTRACT.md](docs/API_CONTRACT.md)   | Contrato da API (endpoints, schemas, códigos HTTP) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)   | Arquitetura técnica (GCP, regiões, autenticação)   |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Sistema de configuração (presets, parâmetros)      |

---

## Operações

### Parar o servidor

```bash
# Terminal interativo
Ctrl + C

# Processo em background
fuser -k 8000/tcp
```

---

## Contato

**Mantenedor:** Marcus Vinicius  
**Email:** marcuscreago@gmail.com
