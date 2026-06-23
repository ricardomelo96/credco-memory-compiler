# Design — Adaptação do credco-memory-compiler para a credco

**Data:** 2026-06-23
**Autor:** Ricardo (via brainstorming)
**Status:** Aprovado, aguardando plano de implementação

## Objetivo

Adaptar o `credco-memory-compiler` (hoje um compilador de memória pessoal a
partir de conversas com o Claude Code) para servir como **base de conhecimento
interna da credco**, alimentada por duas fontes que passam pelo mesmo cérebro:

1. **Conhecimento técnico** — sessões de Claude Code (arquitetura, migrations,
   RLS, bugs, padrões de código).
2. **Conhecimento operacional** — decisões de produto/negócio, processos e
   escolhas estratégicas que já acontecem dentro das conversas com o Claude Code.

## Restrições e premissas (o que NÃO muda)

- **Single-user (Ricardo), local em filesystem.** Sem centralização, sem
  Supabase, sem multi-dev por enquanto. Pode evoluir depois se o time crescer.
- **Alimentação 100% via Claude Code.** Nenhuma fonte de ingestão nova
  (sem WhatsApp/IG/planilhas). Os hooks existentes já capturam tudo.
- **Pipeline intacto:** `daily/ → compile → knowledge/ → index → query`. Os
  hooks (`session-start/end`, `pre-compact`), a dedup de flush, o auto-compile
  após as 18h e o `lint.py` permanecem como estão.
- **Sem dependências novas** no `pyproject.toml`. Sem reescrita estrutural de
  Python.

## Decisão de arquitetura: pool único com tag de domínio (abordagem A)

Todos os artigos continuam juntos em `knowledge/concepts/`. A separação entre
técnico e operacional é feita por **metadado**, não por estrutura de pastas.

**Por quê A e não subpastas/KBs separadas:** o diferencial deste sistema sobre
um Notion qualquer são as `connections/` — insights não-óbvios que cruzam os dois
mundos (ex.: a decisão técnica da migration 035 da Magali ligada à razão de
negócio "Ricardo escolheu Split"). Separar fisicamente técnico/operacional
destruiria exatamente esse ativo e forçaria classificações binárias sobre
conhecimento que é, por natureza, misto.

### O campo `dominio`

Cada artigo em `knowledge/concepts/` ganha no frontmatter:

```yaml
dominio: tecnico | operacional | misto
```

- **tecnico** — arquitetura, migrations, RLS, bugs, padrões de código
  (Magali write-loop, n8n, Supabase, patrim).
- **operacional** — decisões de produto/negócio, processos, escolhas
  estratégicas, regras de atendimento.
- **misto** — quando os dois se cruzam. É o caso mais valioso e vira candidato
  natural a um artigo em `connections/`.

O `index.md` ganha uma **coluna `dominio`**. As `connections/` continuam livres
para cruzar técnico↔operacional.

## Idioma

Português (PT-BR), preservando termos técnicos e nomes próprios em inglês de
forma natural (`migration`, `tenant`, `RLS`, `write-loop`). Tradução não-forçada.

## Mudanças concretas

A adaptação vive em 3 arquivos de especificação/prompt + 1 ajuste menor. O insight
central: **o `AGENTS.md` É o compilador** — `compile.py:49` lê o arquivo inteiro
como `schema` e injeta no prompt. Logo, a taxonomia é editável em markdown, não
hardcoded em Python.

### 1. `AGENTS.md` (maior alavanca)

- Traduzir o schema para PT-BR.
- Adicionar o campo `dominio` ao formato de artigo (frontmatter).
- Adicionar a coluna `dominio` ao exemplo de `index.md`.
- Adicionar uma seção **"Domínio credco"** com o vocabulário do negócio para o
  compilador reconhecer e nomear conceitos de forma consistente: tenants /
  `p_tenant_id`, Magali, transactions, reminders, n8n, Evolution WhatsApp API,
  IG auto-responder, patrim, Supabase/RLS, pg_cron/SDR.
- Definir a regra: conceito que cruza técnico e operacional → `dominio: misto`
  e preferir materializar a relação como artigo em `connections/`.

### 2. `flush.py` — prompt de extração (linha 85)

- Traduzir o prompt para PT-BR.
- Manter as seções existentes, traduzidas: **Contexto, Trocas-chave, Decisões,
  Lições Aprendidas, Ações**.
- Instruir a marcar cada item/seção como técnico ou operacional, para dar ao
  compilador o sinal de `dominio`.
- Preservar a saída sentinela `FLUSH_OK` (usada pelo `flush.py:236`).

### 3. `compile.py` — prompt de compilação (linha 67)

- Traduzir as instruções para PT-BR.
- Instruir a preencher o campo `dominio` em cada artigo.
- Instruir a preencher a coluna `dominio` ao adicionar linhas no `index.md`.
- Reforçar: conceitos `misto` → preferir `connections/`.

### 4. `query.py`

- Adicionar flag opcional `--dominio tecnico|operacional` que filtra o índice
  antes de responder. Sem flag, comportamento atual (busca tudo).

### Config

- `scripts/config.py`: timezone já é `America/Sao_Paulo`. Nenhuma mudança
  necessária.

## Verificação

1. `uv run python scripts/lint.py --structural-only` — deve passar sem erro.
2. Compilar um daily log de teste com conteúdo técnico + operacional misturado.
3. Confirmar que:
   - (a) os artigos saem em PT-BR com `dominio` correto;
   - (b) o `index.md` tem a coluna `dominio` preenchida;
   - (c) ao menos uma `connection` cross-domínio é criada quando o log cruza os
     dois mundos.

## Fora de escopo (YAGNI)

- Centralização / multi-dev / Supabase.
- Ingestão de fontes externas (WhatsApp da Magali, IG, planilhas).
- UI / interface não-CLI.
- Migração de artigos existentes (a base começa praticamente vazia).
