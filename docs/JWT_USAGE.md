# Guia de Autenticação JWT

## 🔐 Visão Geral

A API requer autenticação JWT para todos os endpoints, exceto `/health` e `/docs`.

---

## 🔑 Gerar Token

### Via Script CLI

```bash
# Desenvolvimento/Teste (30 dias)
python scripts/generate_token.py --user admin --purpose admin

# Produção (20 anos - recomendado)
python scripts/generate_token.py --user sistema_producao --purpose admin --hours 175200
```

### Saída:

```
======================================================================
🔑 TOKEN JWT GERADO COM SUCESSO
======================================================================

Usuário: sistema_producao
Propósito: admin
Expiração: 175200 horas

Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

======================================================================
```

---

## 📡 Usar Token

### Header de Autenticação

Adicione o token no header `Authorization`:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/api/v1/management/corpus
```

### Swagger UI

1. Acesse: http://localhost:8000/docs
2. Clique em **"Authorize"** 🔒
3. Cole o token JWT
4. Clique em **"Authorize"** e depois **"Close"**

---

## 🛠️ Troubleshooting

### Erro: "Token inválido ou expirado"

**Causas:**
- Token expirou
- Token copiado incorretamente (espaços, quebras)
- Secret key mudou no `.env`

**Solução:**
```bash
python scripts/generate_token.py --user seu_usuario --purpose admin
```

### Erro: "Token ausente"

**Causa:** Header não enviado

**Verifique:**
```bash
# ✅ Correto
curl -H "Authorization: Bearer eyJhbGc..." http://localhost:8000/api/v1/...

# ❌ Errado (faltou "Bearer ")
curl -H "Authorization: eyJhbGc..." http://localhost:8000/api/v1/...
```

---

## 📊 Estrutura do Token

### Campos do Payload
```json
{
  "sub": "usuario_ou_sistema",
  "purpose": "admin | readonly | uploader",
  "exp": 1736868000,  // Unix timestamp
  "iat": 1734184000   // Unix timestamp
}
```

---

## 🚀 Endpoints Públicos (Sem Token)

- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc
- `GET /openapi.json` - OpenAPI schema

Todos os outros endpoints **REQUEREM** autenticação.

---
## 📞 Contato

**Mantenedor:** Marcus Vinicius  
**Email:** marcuscreago@gmail.com  
**Última Atualização:** Dezembro 2025
