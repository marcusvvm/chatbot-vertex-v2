# 🎨 Guia Frontend: Sistema de Configuração de Chat

> **Versão:** 2.0 (Refatorado)  
> **Última Atualização:** 25/12/2024  
> **Audiência:** Desenvolvedores Frontend

---

## 📋 Índice

1. [Arquitetura do Sistema](#arquitetura-do-sistema)
2. [Sistema de Presets](#sistema-de-presets)
3. [Endpoints da API](#endpoints-da-api)
4. [Schemas de Request/Response](#schemas-de-requestresponse)
5. [Fluxos de Trabalho](#fluxos-de-trabalho)
6. [Tratamento de Erros](#tratamento-de-erros)
7. [Recomendações de UX](#recomendações-de-ux)

---

## Arquitetura do Sistema

### Hierarquia de Configuração

```
┌──────────────────────────────────────────────────────────────┐
│                    CONFIGURAÇÃO FINAL                         │
│              (Usada pelo chat em runtime)                     │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ merge
┌──────────────────────────────────────────────────────────────┐
│                  CORPUS CONFIG (Customizável)                 │
│    📁 config/corpus/{corpus_id}.json                         │
│    • Criada: via PUT /corpus/{id} ou apply-preset            │
│    • Contém: Apenas campos customizados                      │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ override
┌──────────────────────────────────────────────────────────────┐
│                  GLOBAL CONFIG (Defaults)                     │
│    📁 config/global.json                                      │
│    • system_instruction padrão                                │
│    • model_name, generation_config padrão                     │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ fixed (imutável)
┌──────────────────────────────────────────────────────────────┐
│                  FIXED CONFIG (Segurança)                     │
│    📁 config/fixed.json                                       │
│    ⚠️ NÃO EXPOSTA via API                                    │
│    • safety_settings                                          │
│    • formatting_rules                                         │
│    • context_management_instructions                          │
└──────────────────────────────────────────────────────────────┘
```

### Princípios de Design

| Princípio | Implementação |
|-----------|---------------|
| **Future-proof** | Passthrough parameters - API aceita qualquer campo válido do Gemini |
| **Simplicidade** | Presets para 90% dos usuários |
| **Flexibilidade** | Customização livre para power users |
| **Segurança** | Fixed configs nunca expostas |

---

## Sistema de Presets

### Presets Core (Read-Only)

| ID | Nome | Modelo | Características |
|----|------|--------|-----------------|
| `balanced` | Equilibrado (Recomendado) | gemini-2.5-pro | temp=0.2, tokens=4096, thinking=1024 |
| `creative` | Criativo | gemini-2.5-pro | temp=0.5, tokens=8192, thinking=2048 |
| `precise` | Preciso | gemini-2.5-flash | temp=0.1, tokens=2048, sem thinking |
| `fast` | Rápido | gemini-2.5-flash | temp=0.2, tokens=1024, sem thinking |

### Presets Customizados

- Armazenados em `config/presets.json`
- CRUD via API
- Campo `is_core: false`

---

## Endpoints da API

### Base URL

```
https://seu-dominio.com/api/v1
```

### Autenticação

Todos os endpoints requerem JWT:

```
Authorization: Bearer {token}
```

---

### 1. GET /config/presets

**Descrição:** Lista todos os presets disponíveis

**Response (200):**
```json
{
  "presets": [
    {
      "id": "balanced",
      "name": "Equilibrado (Recomendado)",
      "description": "Respostas precisas e rápidas. Bom para uso geral.",
      "model_name": "gemini-2.5-pro",
      "is_core": true
    },
    {
      "id": "creative",
      "name": "Criativo",
      "description": "Respostas mais elaboradas. Melhor para explicações complexas.",
      "model_name": "gemini-2.5-pro",
      "is_core": true
    },
    {
      "id": "precise",
      "name": "Preciso",
      "description": "Respostas concisas e factuais. Ideal para consultas rápidas.",
      "model_name": "gemini-2.5-flash",
      "is_core": true
    },
    {
      "id": "fast",
      "name": "Rápido",
      "description": "Otimizado para velocidade. Menor latência.",
      "model_name": "gemini-2.5-flash",
      "is_core": true
    }
  ]
}
```

---

### 2. GET /config/presets/{preset_id}

**Descrição:** Obtém configuração completa de um preset

**Response (200):**
```json
{
  "id": "balanced",
  "name": "Equilibrado (Recomendado)",
  "description": "Respostas precisas e rápidas. Bom para uso geral.",
  "is_core": true,
  "model_name": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 4096,
    "thinking_budget": 1024
  },
  "rag_retrieval_top_k": 10,
  "max_history_length": 20
}
```

**Response (404):**
```json
{
  "detail": "Preset not found: invalid_id"
}
```

---

### 3. POST /config/presets

**Descrição:** Cria um preset customizado

**Request Body:**
```json
{
  "id": "juridico",
  "name": "Departamento Jurídico",
  "description": "Configuração otimizada para consultas jurídicas",
  "model_name": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.1,
    "max_output_tokens": 8192,
    "thinking_budget": 2048
  },
  "rag_retrieval_top_k": 15,
  "max_history_length": 20
}
```

**Response (201):**
```json
{
  "message": "Preset created successfully",
  "preset": { ...preset completo... }
}
```

**Response (400):**
```json
{
  "detail": "Cannot create preset with core ID: balanced"
}
```

---

### 4. PUT /config/presets/{preset_id}

**Descrição:** Atualiza um preset customizado

**Request Body:**
```json
{
  "name": "Jurídico v2",
  "generation_config": {
    "temperature": 0.15
  }
}
```

**Response (200):**
```json
{
  "message": "Preset updated successfully",
  "preset": { ...preset atualizado... }
}
```

**Response (400):**
```json
{
  "detail": "Cannot modify core preset: balanced"
}
```

---

### 5. DELETE /config/presets/{preset_id}

**Descrição:** Deleta um preset customizado

**Response (200):**
```json
{
  "message": "Preset 'juridico' deleted successfully"
}
```

**Response (400):**
```json
{
  "detail": "Cannot delete core preset: balanced"
}
```

---

### 6. POST /config/corpus/{corpus_id}/apply-preset/{preset_id}

**Descrição:** Aplica um preset a um corpus

**Response (200):**
```json
{
  "message": "Preset 'Equilibrado (Recomendado)' applied successfully",
  "corpus_id": "8207810320882728960",
  "preset_id": "balanced"
}
```

**Response (404):**
```json
{
  "detail": "Preset not found: invalid_preset"
}
```

---

### 7. GET /config/corpus/{corpus_id}

**Descrição:** Obtém configuração atual do corpus

**Response (200):**
```json
{
  "corpus_id": "8207810320882728960",
  "config": {
    "model_name": "gemini-2.5-pro",
    "system_instruction": "Você é um assistente...",
    "generation_config": {
      "temperature": 0.2,
      "top_p": 0.8,
      "top_k": 40,
      "max_output_tokens": 4096
    },
    "rag_retrieval_top_k": 10,
    "timeout_seconds": 90.0,
    "max_history_length": 20
  },
  "has_custom_config": true
}
```

---

### 8. PUT /config/corpus/{corpus_id}

**Descrição:** Atualiza configuração customizada (Expert Mode)

**Request Body:**
```json
{
  "system_instruction": "Você é o assistente do Jurídico...",
  "model_name": "gemini-2.5-pro",
  "generation_config": {
    "temperature": 0.1,
    "max_output_tokens": 8192,
    "thinking_budget": 2048,
    "any_future_param": "value"
  },
  "rag_retrieval_top_k": 15,
  "max_history_length": 20
}
```

**⚠️ PASSTHROUGH:** O campo `generation_config` aceita **QUALQUER** parâmetro válido do Gemini API. Validação real acontece ao usar o chat.

**Response (200):**
```json
{
  "message": "Configuration updated successfully",
  "corpus_id": "8207810320882728960"
}
```

---

### 9. DELETE /config/corpus/{corpus_id}

**Descrição:** Remove customização, volta ao global

**Response (200):**
```json
{
  "message": "Configuration deleted successfully",
  "corpus_id": "8207810320882728960"
}
```

**Response (404):**
```json
{
  "detail": "No custom configuration found for corpus 8207810320882728960"
}
```

---

## Schemas de Request/Response

### PresetSummary (usado em list)

```typescript
interface PresetSummary {
  id: string;           // Identificador único
  name: string;         // Nome exibível
  description: string;  // Descrição curta
  model_name: string;   // Modelo Gemini
  is_core: boolean;     // true = read-only, false = customizável
}
```

### Preset (completo)

```typescript
interface Preset {
  id: string;
  name: string;
  description: string;
  is_core: boolean;
  model_name: string;
  generation_config: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    max_output_tokens?: number;
    thinking_budget?: number;      // Gemini 2.5
    thinking_level?: string;       // Gemini 3
    [key: string]: any;            // Passthrough
  };
  rag_retrieval_top_k: number;
  max_history_length: number;
}
```

### PresetCreateRequest

```typescript
interface PresetCreateRequest {
  id: string;                      // OBRIGATÓRIO, único
  name?: string;                   // default: id
  description?: string;            // default: ""
  model_name?: string;             // default: "gemini-2.5-pro"
  generation_config?: object;      // default: {}
  rag_retrieval_top_k?: number;    // default: 10
  max_history_length?: number;     // default: 20
}
```

### CorpusConfigUpdate

```typescript
interface CorpusConfigUpdate {
  system_instruction?: string;     // max 10000 chars
  model_name?: string;
  generation_config?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    max_output_tokens?: number;
    thinking_budget?: number;
    thinking_level?: string;
    [key: string]: any;            // Passthrough
  };
  rag_retrieval_top_k?: number;    // 1-50
  timeout_seconds?: number;        // 10-300
  max_history_length?: number;     // 1-100
}
```

### CorpusConfigResponse

```typescript
interface CorpusConfigResponse {
  corpus_id: string;
  config: {
    model_name: string;
    system_instruction: string;
    generation_config: object;
    rag_retrieval_top_k: number;
    timeout_seconds: number;
    max_history_length: number;
  };
  has_custom_config: boolean;
}
```

---

## Fluxos de Trabalho

### Fluxo 1: Configuração Simples (Presets)

```
1. GET /config/presets
   → Lista presets disponíveis

2. Usuário escolhe "Preciso"

3. POST /config/corpus/{id}/apply-preset/precise
   → Aplica preset ao corpus

4. ✅ Configuração completa
```

### Fluxo 2: Configuração Customizada

```
1. GET /config/corpus/{id}
   → Obtém config atual

2. Usuário edita valores

3. PUT /config/corpus/{id}
   → Salva config customizada

4. ✅ Configuração completa
```

### Fluxo 3: Criar Preset Personalizado

```
1. POST /config/presets
   → Cria preset "juridico"

2. POST /config/corpus/{id}/apply-preset/juridico
   → Aplica aos corpus do jurídico

3. ✅ Todos os corpus do departamento usam o mesmo preset
```

### Fluxo 4: Reset para Padrão

```
1. DELETE /config/corpus/{id}
   → Remove customização

2. GET /config/corpus/{id}
   → Retorna config global (has_custom_config: false)
```

---

## Tratamento de Erros

### Matriz de Erros

| Código | Causa | Ação do Frontend |
|--------|-------|------------------|
| 200 | Sucesso | Feedback positivo |
| 201 | Criado | Feedback positivo |
| 400 | Dados inválidos / Regra de negócio | Mostrar `detail` |
| 401 | Token inválido | Redirecionar para login |
| 403 | Token expirado | Refresh token |
| 404 | Recurso não existe | Mensagem informativa |
| 422 | Tipo incorreto | Validar antes de enviar |
| 500 | Erro servidor | Retry + mensagem genérica |

### Erros de Presets

| Erro | Causa | Solução |
|------|-------|---------|
| "Cannot create preset with core ID" | Tentou criar com ID reservado | Usar ID diferente |
| "Preset already exists" | ID já em uso | Usar ID diferente ou PUT |
| "Cannot modify core preset" | Tentou editar balanced/creative/etc | Core presets são read-only |
| "Cannot delete core preset" | Tentou deletar core | Só customizados deletáveis |
| "Preset not found" | ID não existe | Verificar ID |

### Erros de Passthrough

Como `generation_config` usa passthrough, erros de parâmetros inválidos **só aparecem ao usar o chat**, não ao salvar.

**Recomendação:**
1. Salvar config → mostrar sucesso
2. Adicionar botão "Testar Configuração"
3. Testar com chat simples
4. Se erro → mostrar mensagem do Google

---

## Recomendações de UX

> **Princípio Central:** Progressive Disclosure (simples por padrão, avançado quando necessário)

### Estratégia de 3 Níveis

A interface deve ser construída em 3 níveis de complexidade progressiva:

| Nível | Público | % Usuários | UI |
|-------|---------|------------|-----|
| **1. Presets** | Todos | ~90% | Radio buttons + descrições |
| **2. Customização Guiada** | Intermediários | ~8% | Sliders + dropdowns + tooltips |
| **3. Expert Mode** | Técnicos | ~2% | Editor JSON direto |

---

### Nível 1: Interface de Presets (90% dos usuários)

**Objetivo:** Zero conhecimento técnico necessário

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚙️ Configuração do Chat - Departamento "Engenharia"             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 📝 Instruções do Assistente                                     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Você é um assistente especializado em documentos de         ││
│ │ engenharia do CREA-GO. Responda sempre de forma técnica     ││
│ │ e precisa, citando normas quando aplicável.                 ││
│ └─────────────────────────────────────────────────────────────┘│
│ ℹ️ Defina a personalidade e regras do assistente                │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 🎯 PERFIL DE COMPORTAMENTO                                       │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ⚫ Equilibrado (Recomendado)                          🔒    ││
│ │    Respostas precisas e rápidas. Bom para uso geral.        ││
│ │    Modelo: gemini-2.5-pro                                   ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ ○ Criativo                                            🔒    ││
│ │    Respostas mais elaboradas. Melhor para explicações.      ││
│ │    Modelo: gemini-2.5-pro                                   ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ ○ Preciso                                             🔒    ││
│ │    Respostas concisas e factuais. Consultas rápidas.        ││
│ │    Modelo: gemini-2.5-flash (mais rápido)                   ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ ○ Rápido                                              🔒    ││
│ │    Otimizado para velocidade. Menor latência.               ││
│ │    Modelo: gemini-2.5-flash (mais rápido)                   ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ ○ Jurídico                                            ✏️    ││
│ │    Configuração otimizada para o departamento jurídico.     ││
│ │    Modelo: gemini-2.5-pro                                   ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ⚙️ [Customizar...] → Abre Nível 2                                │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│           [ Cancelar ]              [ Aplicar Preset ▶ ]        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Elementos Visuais:**

| Elemento | Descrição |
|----------|-----------|
| 🔒 | Preset core (não editável) |
| ✏️ | Preset customizado (editável/deletável) |
| ⚫/○ | Radio button selecionado/não selecionado |
| Modelo | Mostrar modelo em texto secundário cinza |
| Descrição | 1-2 linhas explicando o comportamento |

**Fluxo do Usuário:**

1. Usuário abre a tela de configuração
2. Sistema carrega presets via `GET /config/presets`
3. Sistema carrega config atual via `GET /config/corpus/{id}`
4. Se `has_custom_config=true`, mostrar preset correspondente selecionado (ou "Customizado")
5. Usuário clica em preset desejado
6. Ao clicar "Aplicar Preset":
   - Mostrar spinner: "Aplicando..."
   - Chamar `POST /config/corpus/{id}/apply-preset/{preset_id}`
   - Mostrar toast: "✓ Preset aplicado com sucesso!"
   - Fechar modal ou retornar à tela anterior

---

### Nível 2: Customização Guiada (8% dos usuários)

**Objetivo:** Controle sem precisar entender JSON

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚙️ Configuração Customizada                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [◀ Voltar para Presets]                                         │
│                                                                  │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                  │
│ 🤖 MODELO                                                        │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [▼] Gemini 2.5 Pro (Recomendado)                            ││
│ │     ├─ Gemini 2.5 Pro - Mais inteligente                    ││
│ │     └─ Gemini 2.5 Flash - Mais rápido                       ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 🎛️ PARÂMETROS DE GERAÇÃO                                         │
│                                                                  │
│ Criatividade (Temperature)                            ⓘ        │
│ ├───────────●────────────────────────────┤                      │
│ 0.0 (Preciso)            0.2         1.0 (Criativo)             │
│                                                                  │
│ Variedade de Vocabulário (Top K)                      ⓘ        │
│ ├───────────────────●────────────────────┤                      │
│ 1 (Conservador)          40          100 (Variado)              │
│                                                                  │
│ Tamanho Máximo da Resposta                            ⓘ        │
│ ├────────────────────────────●───────────┤                      │
│ 512 tokens              4096        16384 tokens                │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 🧠 RACIOCÍNIO (Thinking)                                         │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [▼] Alto (1024 tokens) - Recomendado                        ││
│ │     ├─ Desativado (0)                                       ││
│ │     ├─ Baixo (512 tokens)                                   ││
│ │     ├─ Médio (1024 tokens)                                  ││
│ │     └─ Alto (2048 tokens)                                   ││
│ └─────────────────────────────────────────────────────────────┘│
│ ℹ️ Tokens extras para o modelo "pensar" antes de responder      │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 📚 BUSCA DE DOCUMENTOS (RAG)                                     │
│                                                                  │
│ Quantidade de documentos a buscar                     ⓘ        │
│ ├─────────────────●──────────────────────┤                      │
│ 1                   10                 50                       │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 💬 HISTÓRICO DE CONVERSA                                         │
│                                                                  │
│ Mensagens anteriores a manter                         ⓘ        │
│ ├─────────────────●──────────────────────┤                      │
│ 0                   20                100                       │
│                                                                  │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                  │
│ 💾 Salvar como Novo Preset                                       │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Nome: [Minha Config Personalizada____]  [ Criar Preset ]    ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 🔧 [Modo Expert (JSON)...]  → Abre Nível 3                       │
│                                                                  │
│ [ Cancelar ]  [ Testar Config ]  [ Salvar Configuração ▶ ]     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tooltips para os ícones ⓘ:**

| Campo | Tooltip |
|-------|---------|
| Temperature | "Controla a criatividade. Valores mais baixos = respostas mais consistentes e previsíveis. Valores mais altos = mais variação e criatividade." |
| Top K | "Quantas opções de palavras o modelo considera. Valores baixos = vocabulário mais restrito e preciso. Valores altos = mais variedade." |
| Max Output Tokens | "Limite máximo de tokens (≈ palavras) na resposta. Respostas mais longas usam mais recursos." |
| Thinking Budget | "Tokens extras para raciocínio interno antes de responder. Melhora respostas complexas, mas aumenta latência." |
| RAG Top K | "Quantos documentos da base de conhecimento buscar para cada pergunta. Mais documentos = respostas mais completas, mas mais lentas." |
| Max History | "Quantas mensagens anteriores da conversa manter no contexto. Mais mensagens = melhor continuidade, mas mais tokens consumidos." |

**Fluxo do Usuário:**

1. Usuário clica em "Customizar..." no Nível 1
2. Sistema carrega config atual via `GET /config/corpus/{id}`
3. Preenche sliders/dropdowns com valores atuais
4. Usuário ajusta valores usando sliders
5. Ao clicar "Salvar Configuração":
   - Chamar `PUT /config/corpus/{id}` com valores
   - Mostrar toast: "✓ Configuração salva!"
6. **Opcional:** "Testar Config" envia mensagem de teste ao chat

---

### Nível 3: Expert Mode (2% dos usuários)

**Objetivo:** Controle total para usuários técnicos

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 Modo Expert - Configuração Avançada (JSON)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [◀ Voltar]   [📋 Copiar Template]   [📖 Ver Documentação]       │
│                                                                  │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                  │
│ 📄 GENERATION CONFIG (JSON)                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │  1 │ {                                                      ││
│ │  2 │   "temperature": 0.2,                                  ││
│ │  3 │   "top_p": 0.8,                                        ││
│ │  4 │   "top_k": 40,                                         ││
│ │  5 │   "max_output_tokens": 4096,                           ││
│ │  6 │   "thinking_budget": 1024                              ││
│ │  7 │ }                                                      ││
│ │    │                                                        ││
│ │    │  ▌ cursor                                              ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ✓ JSON válido                                                    │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ 📚 TEMPLATES RÁPIDOS                                             │
│                                                                  │
│ [Gemini 2.5 Pro Padrão]   [Gemini 2.5 Flash Rápido]             │
│ [Alto Raciocínio]         [Sem Thinking]                        │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ ⚠️ NOTA IMPORTANTE                                               │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ • Configuração será validada pela API do Google             ││
│ │ • Erros só aparecem ao usar o chat, não ao salvar           ││
│ │ • Novos parâmetros do Gemini funcionam automaticamente      ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                  │
│ [ Cancelar ]    [ Validar JSON ]    [ Salvar ▶ ]                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Recursos do Editor:**

| Recurso | Descrição |
|---------|-----------|
| Syntax Highlighting | Cores para chaves, valores, strings, números |
| Line Numbers | Numeração de linhas para referência |
| Auto-indentation | Identação automática ao pressionar Enter |
| Bracket Matching | Destacar abertura/fechamento de chaves |
| JSON Validation | Validar sintaxe em tempo real |
| Autocomplete | Sugerir campos conhecidos (temperature, top_k, etc.) |

**Templates Rápidos (valores sugeridos):**

```json
// Gemini 2.5 Pro Padrão
{"temperature": 0.2, "top_p": 0.8, "top_k": 40, "max_output_tokens": 4096, "thinking_budget": 1024}

// Gemini 2.5 Flash Rápido
{"temperature": 0.2, "max_output_tokens": 1024}

// Alto Raciocínio
{"temperature": 0.3, "max_output_tokens": 8192, "thinking_budget": 2048}

// Sem Thinking
{"temperature": 0.1, "max_output_tokens": 2048}
```

---

### Componentes Visuais Recomendados

#### 1. Card de Preset

```
┌─────────────────────────────────────────────────────────────┐
│ ○ Equilibrado (Recomendado)                           🔒    │
│    Respostas precisas e rápidas. Bom para uso geral.        │
│    ┌──────────────────┐                                     │
│    │ gemini-2.5-pro   │ ← Chip/Badge com modelo             │
│    └──────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

**Estados:**
- **Normal:** Borda cinza clara, fundo branco
- **Hover:** Borda azul clara, fundo azul muito claro
- **Selecionado:** Borda azul, fundo azul claro, radio preenchido

#### 2. Slider com Valor

```
Criatividade (Temperature)                    [0.2] ⓘ
├─────────●───────────────────────────────────────┤
0.0                                            1.0
Preciso ◄─────────────────────────────────► Criativo
```

**Comportamento:**
- Mostrar valor atual em badge editável
- Labels descritivos nos extremos
- Tooltip ao hover no ícone ⓘ

#### 3. Toast de Feedback

```
┌────────────────────────────────────────┐
│ ✓ Preset aplicado com sucesso!         │    ← Verde, 3s
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ⚠ Configuração salva. Teste o chat.    │    ← Amarelo, 5s
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ✗ Erro: Cannot modify core preset      │    ← Vermelho, 5s
└────────────────────────────────────────┘
```

#### 4. Indicador de Estado

```
Configuração Atual:
┌──────────────────────────────────────────────────┐
│ ⚫ Usando: Equilibrado (Recomendado)        🔒  │  ← Se preset
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ ⚫ Usando: Configuração Customizada         ⚙️  │  ← Se custom
│   [ Resetar para Padrão ]                        │
└──────────────────────────────────────────────────┘
```

---

### Fluxos de Interação

#### Fluxo A: Primeira Configuração

```
┌──────────────────┐     ┌───────────────────┐     ┌────────────────┐
│                  │     │                   │     │                │
│  Abre Config     │────▶│  Mostra Presets   │────▶│  Aplica Preset │
│                  │     │  (Nível 1)        │     │                │
└──────────────────┘     └───────────────────┘     └────────────────┘
                                  │
                                  │ clica "Customizar"
                                  ▼
                         ┌───────────────────┐
                         │  Customização     │────▶ Salvar
                         │  Guiada (Nível 2) │
                         └───────────────────┘
```

#### Fluxo B: Usuário Avançado

```
┌──────────────────┐     ┌───────────────────┐     ┌────────────────┐
│                  │     │                   │     │                │
│  Abre Config     │────▶│  Clica Customizar │────▶│  Expert Mode   │
│                  │     │                   │     │  (Nível 3)     │
└──────────────────┘     └───────────────────┘     └────────────────┘
                                                           │
                                                           ▼
                                                   ┌────────────────┐
                                                   │  Salvar como   │
                                                   │  Novo Preset   │
                                                   └────────────────┘
```

#### Fluxo C: Reset para Padrão

```
┌──────────────────┐     ┌───────────────────┐     ┌────────────────┐
│  Config atual:   │     │  Confirmar:       │     │  Sucesso:      │
│  Customizada     │────▶│  "Tem certeza?"   │────▶│  has_custom:   │
│  [Resetar]       │     │  [Sim] [Não]      │     │  false         │
└──────────────────┘     └───────────────────┘     └────────────────┘
```

---

### Estados da Interface

| Estado | Indicador Visual | Ação Disponível |
|--------|------------------|-----------------|
| `has_custom_config: false` | "Usando configuração padrão" | Aplicar preset |
| `has_custom_config: true` + preset | "Usando: [Nome do Preset] 🔒" | Trocar preset, Resetar |
| `has_custom_config: true` + custom | "Usando: Customizada ⚙️" | Editar, Resetar, Salvar como preset |
| Salvando | Spinner + "Salvando..." | Nenhuma (bloqueado) |
| Erro | Mensagem vermelha + ícone ✗ | Tentar novamente |

---

### Boas Práticas

1. **Defaults Sensatos:** Sempre pré-selecionar "Equilibrado" para novos corpus
2. **Confirmação Destrutiva:** Confirmar antes de resetar ou deletar preset
3. **Feedback Imediato:** Spinner durante chamadas API, toast após conclusão
4. **Progressão Natural:** Oferecer "ver mais opções" em vez de mostrar tudo
5. **Ajuda Contextual:** Tooltips em todos os campos técnicos
6. **Persistência:** Lembrar última aba/nível usado pelo usuário
7. **Validação Visual:** Mostrar erros de JSON em tempo real no Nível 3
8. **Mobile-first:** Sliders funcionam bem em touch; JSON editor é secundário

---

## Checklist de Implementação

### MVP (Essencial)

- [ ] GET /config/presets → Listar presets
- [ ] Seletor de preset na UI (Nível 1)
- [ ] POST /apply-preset → Aplicar ao corpus
- [ ] Feedback de sucesso/erro (toasts)

### Completo

- [ ] GET /config/corpus/{id} → Mostrar config atual
- [ ] Indicador has_custom_config
- [ ] Editor customizado (PUT /corpus/{id}) - Nível 2
- [ ] Sliders com valores e tooltips
- [ ] CRUD de presets customizados
- [ ] DELETE /config/corpus/{id} → Reset

### Power User

- [ ] Editor JSON para generation_config (Nível 3)
- [ ] Syntax highlighting
- [ ] Templates rápidos
- [ ] Botão "Testar Configuração"
- [ ] Criar preset a partir de config atual

