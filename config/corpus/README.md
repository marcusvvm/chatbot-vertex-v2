# Exemplos de Configuração por Departamento

Este diretório contém exemplos de configuração customizada para diferentes departamentos.

---

## 📁 Arquivos de Exemplo

### `example-juridico.json`
**Departamento**: Jurídico  
**Característica**: Conservador, preciso, técnico

**Customizações**:
- Temperature: 0.1 (muito baixa para respostas precisas)
- RAG top_k: 15 (mais contexto)
- Thinking budget: 2048 (mais raciocínio)
- Persona: Assistente jurídico técnico

**Caso de uso**: Consultas sobre leis, normas, processos administrativos

---

### `example-rh.json`
**Departamento**: Recursos Humanos  
**Característica**: Empático, equilibrado, prestativo

**Customizações**:
- Temperature: 0.4 (equilibrado)
- Persona: Assistente de RH empático

**Caso de uso**: Políticas internas, benefícios, procedimentos de pessoal

---

### `example-tecnico.json`
**Departamento**: Técnico de Engenharia  
**Característica**: Técnico-científico, preciso

**Customizações**:
- Temperature: 0.2 (padrão)
- RAG top_k: 15 (mais contexto técnico)
- Max tokens: 12288 (respostas mais longas)
- Persona: Assistente técnico de engenharia

**Caso de uso**: Normas técnicas, ARTs, fiscalização

---

## 🚀 Como Usar

### 1. Criar Corpus

```bash
curl -X POST http://localhost:8000/api/v1/management/corpus \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "department_name": "MeuDepartamento",
    "description": "Descrição do departamento"
  }'
```

### 2. Customizar Baseado em Exemplo

Copie um dos exemplos e personalize:

```bash
# Usar config similar ao Jurídico
curl -X PUT http://localhost:8000/api/v1/config/corpus/{corpus_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d @example-juridico.json
```

### 3. Ajustar Conforme Necessidade

Edite os valores para seu caso específico:

```json
{
  "system_instruction": "Sua persona customizada aqui...",
  "generation_config": {
    "temperature": 0.3
  }
}
```

---

## 💡 Dicas de Configuração

### Temperature

- **0.0-0.2**: Muito conservador (jurídico, técnico)
- **0.3-0.5**: Equilibrado (RH, atendimento)
- **0.6-0.9**: Criativo (marketing, comunicação)

### RAG Top K

- **5-10**: Contexto padrão
- **11-20**: Mais contexto (departamentos com muitos docs)
- **>20**: Uso avançado (pode aumentar latência)

### Max Output Tokens

- **1024-4096**: Respostas curtas
- **4096-8192**: Respostas médias
- **8192-16384**: Respostas longas

---

## 🎯 Exemplos por Caso de Uso

### Atendimento ao Cliente
```json
{
  "system_instruction": "Você é o assistente de atendimento. Seja cordial e resolva problemas rapidamente.",
  "generation_config": {
    "temperature": 0.5,
    "max_output_tokens": 2048
  },
  "timeout_seconds": 60.0
}
```

### Análise Técnica Complexa
```json
{
  "system_instruction": "Você é especialista em análise técnica. Seja detalhado e preciso.",
  "generation_config": {
    "temperature": 0.2,
    "max_output_tokens": 16384
  },
  "rag_retrieval_top_k": 20,
  "thinking_budget": 2048,
  "timeout_seconds": 150.0
}
```

### Consultas Rápidas (FAQ)
```json
{
  "system_instruction": "Você responde perguntas frequentes de forma direta e concisa.",
  "generation_config": {
    "temperature": 0.3,
    "max_output_tokens": 512
  },
  "timeout_seconds": 30.0
}
```

---

## 📚 Mais Informações

Consulte [CONFIGURATION.md](../../docs/CONFIGURATION.md) para documentação completa do sistema de configuração.
