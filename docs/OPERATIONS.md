# ⚙️ Guia de Operações e DevOps

Este documento serve como manual para administradores de sistema e desenvolvedores que precisam operar, configurar e implantar a API.

---

## 🚀 Ciclo de Vida da Aplicação

### Pré-requisitos
- **Python**: 3.10 ou superior
- **Virtualenv**: Recomendado para isolamento

### Instalação de Dependências
As dependências do projeto estão listadas no arquivo `requirements.txt`.

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Instalar pacotes
pip install -r requirements.txt
```

### Subir a Aplicação (Desenvolvimento)
Para rodar o servidor localmente com *hot-reload* (reinicia ao salvar arquivos):

```bash
# Padrão (Porta 8000)
./venv/bin/uvicorn app.main:app --reload

# Porta Personalizada (ex: 8080)
./venv/bin/uvicorn app.main:app --reload --port 8080 --host 0.0.0.0
```

### Derrubar a Aplicação
- **Terminal Interativo**: Pressione `Ctrl + C`.
- **Background**: Se rodou em background (ex: com `nohup`), use `fuser` ou `kill` para parar o processo na porta:
  ```bash
  # Matar processo na porta 8000
  fuser -k 8000/tcp
  ```

---

## 🔧 Configuração

### Variáveis de Ambiente (.env)
A aplicação segue a metodologia *12-Factor App* e concentra configurações no arquivo `.env`.

| Variável                         | Descrição                               | Exemplo                            |
| -------------------------------- | --------------------------------------- | ---------------------------------- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho para o JSON da Service Account  | `credentials/credentials-rag.json` |
| `GCP_PROJECT_ID`                 | ID do projeto no Google Cloud           | `rag-projetos-crea`                |
| `GCP_LOCATION`                   | Região do RAG Engine (Dados)            | `europe-west3`                     |
| `GCP_LOCATION_CHAT`              | Região do Modelo Gemini (Processamento) | `us-central1`                      |
| `JWT_SECRET_KEY`                 | Chave secreta para assinar tokens       | (string aleatória longa)           |
| `DEBUG`                          | Ativa logs detalhados e reload          | `True` (Dev) / `False` (Prod)      |

### Configurar Porta
A porta não é configurada no `.env`, mas sim no comando de inicialização do servidor (veja seção "Subir a Aplicação").

---

## 🔑 Gestão de Acesso (Tokens)

A API não possui endpoint público de "Login". Tokens devem ser gerados via CLI por um administrador.

### Gerar Token
Use o script utilitário na pasta `scripts/`:

```bash
# Token padrão (Admin, 30 dias)
python scripts/generate_token.py --user admin

# Token de longa duração (ex: 1 ano para integração entre sistemas)
python scripts/generate_token.py --user sistema_crm --hours 8760

# Token com permissão específica (futuro)
python scripts/generate_token.py --user auditoria --purpose readonly
```

---

## 🏭 Migração para Produção

Para rodar em ambiente produtivo (AWS, GCP Compute Engine, Digital Ocean), **NÃO** use o comando de desenvolvimento (`uvicorn --reload`).

### 1. Servidor de Aplicação (Gunicorn)
Use o `gunicorn` como gerenciador de processos e o `uvicorn` como worker class. Isso garante melhor performance e estabilidade.

**Instalar Gunicorn:**
```bash
pip install gunicorn
```

**Comando de Produção:**
```bash
# Roda 4 workers, bind na porta 8000
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### 2. Proxy Reverso (Nginx)
Nunca exponha o Gunicorn/Uvicorn diretamente à internet. Use o Nginx na frente para:
- Terminar SSL (HTTPS)
- Comprimir respostas (Gzip)
- Proteger contra ataques básicos

**Exemplo de Configuração Nginx:**
```nginx
server {
    listen 80;
    server_name api.crea-go.org.br;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Checklist de Segurança
- [ ] **DEBUG=False**: Garanta que está `False` no `.env` de produção.
- [ ] **HTTPS**: Obrigatório. Use Let's Encrypt (Certbot) no Nginx.
- [ ] **Secret Key**: Gere uma nova `JWT_SECRET_KEY` forte e única para produção.
- [ ] **Service Account**: Use uma Service Account com permissões mínimas necessárias (Princípio do Menor Privilégio).

---

## 📦 Docker (Opcional)

Para facilitar o deploy, você pode containerizar a aplicação.

**Dockerfile Básico:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
```
