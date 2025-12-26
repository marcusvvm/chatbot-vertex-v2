# Sistema de Configuração

Configuração dinâmica por corpus e sistema de presets.

---

## Hierarquia de Configuração

```
fixed.json      → Imutável (safety settings, grounding rules)
     ↓
global.json     → Defaults globais
     ↓
corpus/{id}.json → Customização por corpus (opcional)
     ↓
Config Final    → Merge aplicado no chat
```

---

## Presets

Presets são templates de configuração armazenados em `config/presets.json`.

**Todos os presets são editáveis via API.** Presets default (balanced, creative, precise, fast) são criados automaticamente se o arquivo estiver vazio.

### Presets Default

| ID         | Nome        | Modelo           | Temperature | Uso                   |
| ---------- | ----------- | ---------------- | ----------- | --------------------- |
| `balanced` | Equilibrado | gemini-2.5-pro   | 0.2         | Uso geral             |
| `creative` | Criativo    | gemini-2.5-pro   | 0.5         | Explicações complexas |
| `precise`  | Preciso     | gemini-2.5-flash | 0.1         | Consultas rápidas     |
| `fast`     | Rápido      | gemini-2.5-flash | 0.2         | Baixa latência        |

### Características detalhadas

```
balanced:
  temperature: 0.2
  max_output_tokens: 4096
  thinking_budget: 1024
  rag_top_k: 10
  history: 20

creative:
  temperature: 0.5
  max_output_tokens: 8192
  thinking_budget: 2048
  rag_top_k: 15
  history: 20

precise:
  temperature: 0.1
  max_output_tokens: 2048
  thinking_budget: none
  rag_top_k: 5
  history: 20

fast:
  temperature: 0.2
  max_output_tokens: 1024
  thinking_budget: none
  rag_top_k: 3
  history: 10
```

---

## Parâmetros de Configuração

### Customizáveis

| Parâmetro             | Tipo   | Range         | Default        | Descrição                             |
| --------------------- | ------ | ------------- | -------------- | ------------------------------------- |
| `system_instruction`  | string | max 10k chars | persona padrão | Persona do assistente                 |
| `model_name`          | string | -             | gemini-2.5-pro | Modelo LLM                            |
| `temperature`         | float  | 0.0-2.0       | 0.2            | Aleatoriedade (0=determinístico)      |
| `top_p`               | float  | 0.0-1.0       | 0.8            | Nucleus sampling                      |
| `top_k`               | int    | 1-100         | 40             | Top-K sampling                        |
| `max_output_tokens`   | int    | 128-32768     | 16384          | Limite de tokens na resposta          |
| `thinking_budget`     | int    | 128-4096      | 1024           | Tokens de raciocínio (gemini-2.5-pro) |
| `rag_retrieval_top_k` | int    | 1-50          | 10             | Chunks recuperados do RAG             |
| `timeout_seconds`     | float  | 10-300        | 90             | Timeout da requisição                 |
| `max_history_length`  | int    | 1-100         | 20             | Mensagens no histórico                |

### Fixos (imutáveis)

- `formatting_rules` - Regras de formatação Markdown
- `grounding_rules` - Regras de uso do RAG
- `safety_settings` - Configurações de segurança

---

## Thinking Budget

O `gemini-2.5-pro` usa tokens internos para "pensar" antes de responder.

| Valor | Comportamento   | Caso de Uso       |
| ----- | --------------- | ----------------- |
| 128   | Mínimo, rápido  | Perguntas simples |
| 1024  | Balanceado      | Uso geral         |
| 2048  | Mais raciocínio | Tarefas complexas |

**Atenção:** Thinking tokens consomem parte do `max_output_tokens`. Se respostas estiverem truncadas, aumente `max_output_tokens` ou reduza `thinking_budget`.

---

## Passthrough

O schema de `generation_config` aceita campos adicionais:

```python
class GenerationConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")
```

Campos desconhecidos são passados diretamente para a API do Google. Validação real acontece no Google API.

**Vantagem:** Novos parâmetros do Gemini funcionam automaticamente sem atualizar o backend.

---

## Arquivos de Configuração

### config/fixed.json

Configurações imutáveis aplicadas a todos os chats:
- System prompt base
- Regras de grounding
- Safety settings

### config/global.json

Defaults aplicados quando corpus não tem config customizada:
- Modelo padrão
- Parâmetros de geração
- Limites de histórico

### config/presets.json

Todos os presets (default + customizados). Preset IDs têm limite de 64 caracteres. Presets default são criados automaticamente se o arquivo estiver vazio.

### config/corpus/{corpus_id}.json

Configuração específica de um corpus. Criado automaticamente na primeira customização (lazy loading).

---

## Fluxo de Aplicação

1. **Chat recebe request** com `corpus_id`
2. **ConfigService.get_merged_config()** executa:
   - Carrega `fixed.json`
   - Carrega `global.json`
   - Carrega `corpus/{corpus_id}.json` se existir
   - Merge: fixed + global + corpus
3. **Config final** passada para `ChatService.chat_rag()`

---

## Recomendações por Departamento

| Departamento | Preset Sugerido | Customização                    |
| ------------ | --------------- | ------------------------------- |
| Jurídico     | `balanced`      | temperature: 0.1, rag_top_k: 15 |
| RH           | `creative`      | temperature: 0.4                |
| Técnico      | `balanced`      | rag_top_k: 20                   |
| Atendimento  | `fast`          | (default)                       |

---

**Última Atualização:** Dezembro 2025
