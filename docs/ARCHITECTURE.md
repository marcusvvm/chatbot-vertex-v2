# 🏗️ Arquitetura do Sistema

Este documento descreve a arquitetura técnica da API RAG Facade, com foco nas decisões de design relacionadas à infraestrutura Google Cloud, autenticação e conformidade.

---

## 📋 Configuração Atual

### Variáveis de Ambiente (.env)

| Variável                         | Valor Exemplo                      | Função                                        |
| -------------------------------- | ---------------------------------- | --------------------------------------------- |
| `GCP_PROJECT_ID`                 | `rag-projetos-crea`                | Projeto GCP principal                         |
| `GCP_LOCATION`                   | `europe-west3`                     | Região do RAG Engine e armazenamento de dados |
| `GCP_LOCATION_CHAT`              | `us-central1`                      | Região do modelo Gemini (LLM)                 |
| `GOOGLE_APPLICATION_CREDENTIALS` | `credentials/credentials-rag.json` | Caminho para credenciais da Service Account   |

---

## 🌍 Arquitetura de Regiões

### 1. RAG & Dados (`europe-west3`)
* **Componentes**: Vertex AI RAG Engine, Corpora, Documentos, Índices Vetoriais
* **Configuração**: Variável `GCP_LOCATION`

### 2. Chat & LLM (`us-central1`)
* **Componentes**: Modelo Gemini (`gemini-2.5-pro`)
* **Motivo**: **Disponibilidade de Recursos**. Modelos mais recentes e avançados são lançados primeiro ou exclusivamente em regiões dos EUA
* **Configuração**: Variável `GCP_LOCATION_CHAT`

### Fluxo de Dados
1. **Upload**: Documentos são enviados e indexados na região da Europa
2. **Retrieval**: O sistema busca trechos relevantes (contexto) na região da Europa
3. **Geração**: O contexto recuperado é enviado para o modelo nos EUA apenas para a geração da resposta (processamento efêmero)

---

## 🔐 Estratégia de Autenticação Unificada

O projeto utiliza uma **Credencial Única Unificada** para simplificar a gestão e operação.

### Service Account
* **Arquivo**: `credentials/credentials-rag.json`
* **Projeto GCP**: `rag-projetos-crea` (ou conforme configurado no `.env`)
* **Permissões Necessárias**:
  * Vertex AI User
  * Vertex AI Administrator (para gestão de corpora)

### Implementação Técnica

Devido a particularidades dos SDKs do Google (`vertexai` vs `google.genai`), a autenticação é tratada de forma específica:

1. **Variável de Ambiente**: `GOOGLE_APPLICATION_CREDENTIALS` aponta para o JSON da chave
2. **Workaround SDK**: O SDK `vertexai.rag` ignora credenciais passadas explicitamente em alguns métodos, exigindo a variável de ambiente global
3. **Escopos OAuth**: O SDK `google.genai` requer escopos explícitos (`https://www.googleapis.com/auth/cloud-platform`) quando inicializado com credenciais de service account

```python
# Exemplo de Inicialização (VertexService)
self.credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_APPLICATION_CREDENTIALS
).with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
```

---

## 🧩 Componentes Principais

### 1. RAG Facade (FastAPI)
Camada de abstração que expõe endpoints REST para gestão de documentos e chat.
* **Endpoints**: `/management` (Corpus/Files), `/documents` (Upload/Delete), `/chat` (Interação)
* **Segurança**: JWT Authentication

### 2. Google Vertex AI
Plataforma backend para inteligência artificial.
* **RAG Engine**: Gerencia indexação e recuperação vetorial
* **Gemini API**: Provê o modelo de linguagem generativa

---

## 🔄 Ciclo de Vida da Requisição de Chat

1. **Auth**: API valida token JWT
2. **Retrieval (Europa)**: `VertexService` consulta o RAG Corpus em `GCP_LOCATION`
   - Busca os top K chunks mais relevantes (configurável via `RAG_RETRIEVAL_TOP_K`)
3. **Prompting**: Sistema constrói prompt com:
   - System instruction (persona, regras de grounding, formatação)
   - Contexto recuperado do RAG
   - Histórico de conversa
   - Mensagem do usuário
4. **Generation (EUA)**: `VertexService` envia prompt para Gemini em `GCP_LOCATION_CHAT`
   - **THINKING_BUDGET**: 1024 tokens reservados para raciocínio interno
   - **MAX_OUTPUT_TOKENS**: 16384 tokens máximo de resposta
   - **TIMEOUT**: 90 segundos
5. **Response**: Resposta gerada (Markdown formatado) é retornada ao usuário

---

## ⚙️ Configurações de Chat

Ver [CHAT_CONFIGURATION.md](CHAT_CONFIGURATION.md) para detalhes sobre:
- Thinking Budget (controle de raciocínio interno)
- Output tokens (limite de resposta)
- RAG retrieval parameters (quantos chunks buscar)
- Timeout de requisição
- Safety settings

---

**Última Atualização**: Dezembro 2025
