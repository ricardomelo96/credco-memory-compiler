# Adaptação do credco-memory-compiler — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o compilador de memória pessoal numa base de conhecimento interna da credco, com saída em PT-BR e separação técnico/operacional por tag de domínio.

**Architecture:** Pipeline `daily/ → compile → knowledge/ → index → query` permanece intacto. As mudanças vivem em 3 lugares: o schema (`AGENTS.md`, lido pelo `compile.py` como especificação), os blocos de instrução dos prompts (`flush.py`, `compile.py`) e um filtro de domínio na consulta (`utils.py` + `query.py`). Cada artigo ganha `dominio: tecnico | operacional | misto` no frontmatter e o `index.md` ganha uma coluna correspondente.

**Tech Stack:** Python 3.12+, `uv`, `claude-agent-sdk`, `pytest` (novo, dev-only).

## Global Constraints

- **Idioma de saída:** PT-BR. Termos técnicos/nomes próprios preservados em inglês (`migration`, `tenant`, `RLS`, `write-loop`) — sem tradução forçada.
- **Sem dependências de runtime novas** no `pyproject.toml`. Só `pytest` como dev dependency.
- **Single-user, local em filesystem.** Sem centralização, sem fontes de ingestão novas.
- **Valores de domínio:** exatamente `tecnico`, `operacional`, `misto` (sem acento, minúsculo) no frontmatter `dominio:`. A flag de CLI aceita só `tecnico` e `operacional` (artigos `misto` sempre aparecem nos dois).
- **Sentinela preservada:** a saída exata `FLUSH_OK` do prompt de extração deve continuar existindo (consumida em `flush.py` no ramo de "nada a salvar").
- **Sem chamadas à LLM nos testes.** Os testes exercitam parsing, filtragem, CLI e conteúdo de prompt — nunca o `claude-agent-sdk`.

---

### Task 1: Harness de testes + filtro de domínio em `utils.py`

Estabelece o pytest e adiciona as funções puras que sustentam o filtro `--dominio`.

**Files:**
- Modify: `pyproject.toml` (adicionar dev dep + config do pytest)
- Modify: `scripts/utils.py` (adicionar `parse_frontmatter_field`, `article_matches_domain`; estender `read_all_wiki_content`)
- Create: `tests/test_domain_filter.py`

**Interfaces:**
- Produces:
  - `parse_frontmatter_field(content: str, field: str) -> str | None` — lê um campo escalar de topo do frontmatter YAML.
  - `article_matches_domain(content: str, dominio: str | None) -> bool` — `True` se `dominio is None`, ou se o campo `dominio` do artigo é igual a `dominio` ou a `"misto"`.
  - `read_all_wiki_content(dominio: str | None = None) -> str` — assinatura estendida; filtra apenas artigos de `concepts/` por domínio, mantém `connections/` e `qa/` sempre.

- [ ] **Step 1: Adicionar pytest e config ao `pyproject.toml`**

Acrescentar ao final do arquivo:

```toml
[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["scripts"]
testpaths = ["tests"]
```

Depois rodar:

```bash
uv add --dev pytest
```

- [ ] **Step 2: Escrever os testes (falhando)**

Create `tests/test_domain_filter.py`:

```python
from utils import parse_frontmatter_field, article_matches_domain

CONCEPT_TECNICO = """---
title: Migration 035 da Magali
dominio: tecnico
---

# Migration 035
Conteúdo.
"""

CONCEPT_OPERACIONAL = """---
title: Escolha do Split
dominio: "operacional"
---

# Split
Conteúdo.
"""

CONCEPT_MISTO = """---
title: Magali write-loop
dominio: misto
---

# Write-loop
Conteúdo.
"""

NO_FRONTMATTER = "# Sem frontmatter\n\nConteúdo."


def test_parse_reads_unquoted_field():
    assert parse_frontmatter_field(CONCEPT_TECNICO, "dominio") == "tecnico"


def test_parse_strips_quotes():
    assert parse_frontmatter_field(CONCEPT_OPERACIONAL, "dominio") == "operacional"


def test_parse_missing_field_returns_none():
    assert parse_frontmatter_field(CONCEPT_TECNICO, "inexistente") is None


def test_parse_no_frontmatter_returns_none():
    assert parse_frontmatter_field(NO_FRONTMATTER, "dominio") is None


def test_match_none_domain_includes_everything():
    assert article_matches_domain(CONCEPT_OPERACIONAL, None) is True


def test_match_exact_domain():
    assert article_matches_domain(CONCEPT_TECNICO, "tecnico") is True
    assert article_matches_domain(CONCEPT_OPERACIONAL, "tecnico") is False


def test_match_misto_always_included():
    assert article_matches_domain(CONCEPT_MISTO, "tecnico") is True
    assert article_matches_domain(CONCEPT_MISTO, "operacional") is True
```

- [ ] **Step 3: Rodar os testes para confirmar que falham**

Run: `uv run pytest tests/test_domain_filter.py -v`
Expected: FAIL com `ImportError: cannot import name 'parse_frontmatter_field'`

- [ ] **Step 4: Implementar as funções em `utils.py`**

Adicionar na seção "Wikilink helpers" / "Wiki content helpers" do `scripts/utils.py`:

```python
def parse_frontmatter_field(content: str, field: str) -> str | None:
    """Return the value of a top-level scalar field in the YAML frontmatter, or None."""
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    block = content[3:end]
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            value = stripped[len(field) + 1:].strip()
            return value.strip("\"'") or None
    return None


def article_matches_domain(content: str, dominio: str | None) -> bool:
    """True if no domain filter, or the article's dominio is the target or 'misto'."""
    if dominio is None:
        return True
    art_dom = parse_frontmatter_field(content, "dominio")
    return art_dom in (dominio, "misto")
```

- [ ] **Step 5: Estender `read_all_wiki_content` para aceitar o filtro**

Substituir a função existente em `scripts/utils.py` por:

```python
def read_all_wiki_content(dominio: str | None = None) -> str:
    """Read index + all wiki articles into a single string for context.

    When `dominio` is given, concept articles are filtered to that domain
    (plus 'misto'); connections/ and qa/ are always included.
    """
    parts = [f"## INDEX\n\n{read_wiki_index()}"]

    for subdir in [CONCEPTS_DIR, CONNECTIONS_DIR, QA_DIR]:
        if not subdir.exists():
            continue
        for md_file in sorted(subdir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            if subdir == CONCEPTS_DIR and not article_matches_domain(content, dominio):
                continue
            rel = md_file.relative_to(KNOWLEDGE_DIR)
            parts.append(f"## {rel}\n\n{content}")

    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 6: Rodar os testes para confirmar que passam**

Run: `uv run pytest tests/test_domain_filter.py -v`
Expected: PASS (7 passed)

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock scripts/utils.py tests/test_domain_filter.py
git commit -m "feat: filtro de dominio e harness de testes em utils"
```

---

### Task 2: Flag `--dominio` na CLI de consulta

Liga o filtro da Task 1 ao `query.py`.

**Files:**
- Modify: `scripts/query.py` (adicionar `build_parser`, param `dominio` em `run_query`, repasse ao `read_all_wiki_content`)
- Create: `tests/test_query_cli.py`

**Interfaces:**
- Consumes: `read_all_wiki_content(dominio=...)` da Task 1.
- Produces:
  - `build_parser() -> argparse.ArgumentParser` — parser com `question`, `--file-back`, `--dominio` (choices `["tecnico", "operacional"]`, default `None`).
  - `run_query(question: str, file_back: bool = False, dominio: str | None = None) -> str`.

- [ ] **Step 1: Escrever os testes (falhando)**

Create `tests/test_query_cli.py`:

```python
import pytest
from query import build_parser


def test_dominio_defaults_to_none():
    args = build_parser().parse_args(["minha pergunta"])
    assert args.dominio is None


def test_dominio_accepts_tecnico():
    args = build_parser().parse_args(["minha pergunta", "--dominio", "tecnico"])
    assert args.dominio == "tecnico"


def test_dominio_accepts_operacional():
    args = build_parser().parse_args(["q", "--dominio", "operacional"])
    assert args.dominio == "operacional"


def test_dominio_rejects_invalid_choice():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["q", "--dominio", "misto"])
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

Run: `uv run pytest tests/test_query_cli.py -v`
Expected: FAIL com `ImportError: cannot import name 'build_parser'`

- [ ] **Step 3: Extrair `build_parser` e adicionar a flag em `query.py`**

Substituir o corpo de `main()` em `scripts/query.py`. Primeiro adicionar a função `build_parser` (acima de `main`):

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consulta a base de conhecimento da credco")
    parser.add_argument("question", help="A pergunta a fazer")
    parser.add_argument(
        "--file-back",
        action="store_true",
        help="Arquiva a resposta de volta na base como artigo Q&A",
    )
    parser.add_argument(
        "--dominio",
        choices=["tecnico", "operacional"],
        default=None,
        help="Filtra os conceitos por domínio (artigos 'misto' sempre incluídos)",
    )
    return parser
```

Depois reescrever `main()`:

```python
def main():
    args = build_parser().parse_args()

    print(f"Pergunta: {args.question}")
    print(f"File back: {'sim' if args.file_back else 'não'}")
    print(f"Domínio: {args.dominio or 'todos'}")
    print("-" * 60)

    answer = asyncio.run(run_query(args.question, file_back=args.file_back, dominio=args.dominio))
    print(answer)

    if args.file_back:
        print("\n" + "-" * 60)
        qa_count = len(list(QA_DIR.glob("*.md"))) if QA_DIR.exists() else 0
        print(f"Resposta arquivada em knowledge/qa/ ({qa_count} artigos Q&A no total)")
```

- [ ] **Step 4: Repassar `dominio` em `run_query`**

Em `scripts/query.py`, alterar a assinatura e a leitura do conteúdo:

```python
async def run_query(question: str, file_back: bool = False, dominio: str | None = None) -> str:
```

e a linha que lê o conteúdo (era `wiki_content = read_all_wiki_content()`):

```python
    wiki_content = read_all_wiki_content(dominio=dominio)
```

- [ ] **Step 5: Rodar os testes para confirmar que passam**

Run: `uv run pytest tests/test_query_cli.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Commit**

```bash
git add scripts/query.py tests/test_query_cli.py
git commit -m "feat: flag --dominio na consulta"
```

---

### Task 3: Reescrever `AGENTS.md` (schema PT-BR + domínio credco)

O `AGENTS.md` é lido inteiro pelo `compile.py:49` como especificação. Esta task transforma a taxonomia.

**Files:**
- Modify: `AGENTS.md`
- Create: `tests/test_agents_schema.py`

**Interfaces:**
- Produces: um `AGENTS.md` que (a) descreve o campo `dominio` no formato de artigo, (b) tem uma seção "Domínio credco" com o vocabulário do negócio, (c) mostra a coluna `dominio` no exemplo de `index.md`.

- [ ] **Step 1: Escrever o teste estrutural (falhando)**

Create `tests/test_agents_schema.py`:

```python
from pathlib import Path

AGENTS = (Path(__file__).resolve().parent.parent / "AGENTS.md").read_text(encoding="utf-8")


def test_documents_dominio_field():
    assert "dominio:" in AGENTS


def test_documents_three_domain_values():
    for value in ("tecnico", "operacional", "misto"):
        assert value in AGENTS


def test_has_credco_domain_section():
    assert "Domínio credco" in AGENTS


def test_mentions_core_credco_vocabulary():
    for term in ("Magali", "tenant", "n8n", "Supabase"):
        assert term in AGENTS


def test_index_example_has_dominio_column():
    # Procura uma linha de cabeçalho de tabela que contenha a coluna de domínio
    assert any(
        "dominio" in line.lower() and "|" in line
        for line in AGENTS.splitlines()
    )
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `uv run pytest tests/test_agents_schema.py -v`
Expected: FAIL (`test_has_credco_domain_section`, `test_index_example_has_dominio_column`, etc.)

- [ ] **Step 3: Adicionar o campo `dominio` ao formato de artigo**

No `AGENTS.md`, localizar o bloco de frontmatter de exemplo dos artigos de conceito (a seção que mostra o YAML com `title:`, `sources:`, etc.) e acrescentar a linha `dominio:` logo após o `title:`. Exemplo do bloco resultante:

```yaml
---
title: Nome do Conceito
dominio: tecnico   # tecnico | operacional | misto
created: 2026-06-23
updated: 2026-06-23
sources:
  - daily/2026-06-23.md
---
```

Acrescentar, imediatamente abaixo do bloco, a regra (em PT-BR):

```markdown
**Campo `dominio`:**
- `tecnico` — arquitetura, migrations, RLS, bugs, padrões de código.
- `operacional` — decisões de produto/negócio, processos, escolhas estratégicas, regras de atendimento.
- `misto` — quando os dois mundos se cruzam. Prefira materializar a relação como artigo em `connections/`.
```

- [ ] **Step 4: Adicionar a seção "Domínio credco"**

Inserir uma nova seção de nível 2 no `AGENTS.md` (antes da seção de regras de compilação):

```markdown
## Domínio credco

Vocabulário do negócio que o compilador deve reconhecer e nomear de forma
consistente ao criar conceitos:

- **Tenants / `p_tenant_id`** — modelo multi-tenant; isolamento por tenant.
- **Magali** — assistente/agente da credco; tem write-loop (`create_transaction`, `create_reminder`).
- **transactions / reminders** — entidades centrais escritas pela Magali.
- **n8n** — orquestração de automações (anon vs service_role).
- **Evolution WhatsApp API / IG auto-responder** — canais de atendimento.
- **patrim** — linha de projetos (ex.: patrim-nio-em-foco).
- **Supabase / RLS** — banco e segurança a nível de linha.
- **pg_cron / SDR** — jobs agendados de prospecção.

Use estes nomes próprios em inglês sem traduzir.
```

- [ ] **Step 5: Atualizar o exemplo de `index.md` com a coluna `dominio`**

Localizar no `AGENTS.md` o exemplo da tabela do `index.md` e adicionar a coluna `dominio`. O cabeçalho passa a ser:

```markdown
| Artigo | Resumo | dominio | Compilado de | Atualizado |
|--------|--------|---------|--------------|------------|
| [[concepts/migration-035-magali]] | Split de patrimônio na migration 035 | misto | daily/2026-06-23.md | 2026-06-23 |
```

- [ ] **Step 6: Traduzir os títulos/descrições de seção para PT-BR**

Passar pelo `AGENTS.md` e traduzir os cabeçalhos e textos explicativos para PT-BR (mantendo nomes de diretórios `daily/`, `knowledge/`, `concepts/`, `connections/`, `qa/` e termos técnicos em inglês). Não alterar a estrutura de pastas nem os nomes de arquivos.

- [ ] **Step 7: Rodar os testes para confirmar que passam**

Run: `uv run pytest tests/test_agents_schema.py -v`
Expected: PASS (5 passed)

- [ ] **Step 8: Rodar o lint estrutural para garantir que nada quebrou**

Run: `uv run python scripts/lint.py --structural-only`
Expected: roda sem exception (avisos sobre base vazia são aceitáveis)

- [ ] **Step 9: Commit**

```bash
git add AGENTS.md tests/test_agents_schema.py
git commit -m "feat: schema PT-BR com dominio e vocabulario credco"
```

---

### Task 4: Prompt de extração do `flush.py` em PT-BR com tag de domínio

Isola o bloco de instrução numa constante testável e o traduz.

**Files:**
- Modify: `scripts/flush.py` (extrair `FLUSH_INSTRUCTIONS`, usar no `run_flush`)
- Create: `tests/test_flush_prompt.py`

**Interfaces:**
- Produces: constante de módulo `FLUSH_INSTRUCTIONS: str` em `scripts/flush.py`.

- [ ] **Step 1: Escrever o teste (falhando)**

Create `tests/test_flush_prompt.py`:

```python
from flush import FLUSH_INSTRUCTIONS


def test_instructions_are_portuguese():
    assert "Contexto" in FLUSH_INSTRUCTIONS
    assert "Decisões" in FLUSH_INSTRUCTIONS
    assert "Lições" in FLUSH_INSTRUCTIONS


def test_instructions_ask_for_domain_tag():
    assert "tecnico" in FLUSH_INSTRUCTIONS
    assert "operacional" in FLUSH_INSTRUCTIONS


def test_preserves_flush_ok_sentinel():
    assert "FLUSH_OK" in FLUSH_INSTRUCTIONS
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `uv run pytest tests/test_flush_prompt.py -v`
Expected: FAIL com `ImportError: cannot import name 'FLUSH_INSTRUCTIONS'`

- [ ] **Step 3: Adicionar a constante `FLUSH_INSTRUCTIONS` em `flush.py`**

Adicionar no nível de módulo (perto do topo, após os imports), em `scripts/flush.py`:

```python
FLUSH_INSTRUCTIONS = """Revise o contexto da conversa abaixo e responda com um resumo
conciso dos itens importantes que devem ser preservados no log diário.
NÃO use nenhuma ferramenta — responda apenas texto puro, em português.

Formate a resposta como uma entrada de log diário com estas seções:

**Contexto:** [Uma linha sobre o que o usuário estava fazendo]

**Domínio:** [tecnico, operacional ou misto — classifique o foco da sessão]

**Trocas-chave:**
- [Perguntas/respostas ou discussões importantes]

**Decisões:**
- [Decisões tomadas, com a razão]

**Lições Aprendidas:**
- [Gotchas, padrões ou insights descobertos]

**Ações:**
- [Follow-ups ou TODOs mencionados]

Ignore qualquer coisa que seja:
- Chamadas de ferramenta ou leituras de arquivo rotineiras
- Conteúdo trivial ou óbvio
- Idas e vindas triviais ou pedidos de esclarecimento

Inclua apenas seções com conteúdo real. Se nada valer a pena salvar,
responda exatamente: FLUSH_OK"""
```

- [ ] **Step 4: Usar a constante no `run_flush`**

Em `scripts/flush.py`, substituir a atribuição multilinha de `prompt` dentro de `run_flush` por:

```python
    prompt = f"""{FLUSH_INSTRUCTIONS}

## Contexto da Conversa

{context}"""
```

- [ ] **Step 5: Rodar os testes para confirmar que passam**

Run: `uv run pytest tests/test_flush_prompt.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Verificar que o módulo ainda importa e roda**

Run: `uv run python -c "import sys; sys.path.insert(0, 'scripts'); import flush; print('ok')"`
Expected: imprime `ok` sem exception

- [ ] **Step 7: Commit**

```bash
git add scripts/flush.py tests/test_flush_prompt.py
git commit -m "feat: prompt de extracao em PT-BR com tag de dominio"
```

---

### Task 5: Prompt de compilação do `compile.py` em PT-BR com domínio + coluna no índice

Isola o bloco de regras numa constante testável, traduz e adiciona as instruções de domínio.

**Files:**
- Modify: `scripts/compile.py` (extrair `COMPILE_INSTRUCTIONS`, usar no prompt)
- Create: `tests/test_compile_prompt.py`

**Interfaces:**
- Consumes: o schema em PT-BR da Task 3 (injetado em runtime, não em build-time).
- Produces: constante de módulo `COMPILE_INSTRUCTIONS: str` em `scripts/compile.py`.

- [ ] **Step 1: Escrever o teste (falhando)**

Create `tests/test_compile_prompt.py`:

```python
from compile import COMPILE_INSTRUCTIONS


def test_instructions_are_portuguese():
    assert "conceito" in COMPILE_INSTRUCTIONS.lower()
    assert "artigo" in COMPILE_INSTRUCTIONS.lower()


def test_instructs_to_fill_dominio_field():
    assert "dominio" in COMPILE_INSTRUCTIONS.lower()


def test_instructs_misto_to_connections():
    assert "misto" in COMPILE_INSTRUCTIONS.lower()
    assert "connections" in COMPILE_INSTRUCTIONS.lower()


def test_index_row_includes_dominio_column():
    assert "dominio" in COMPILE_INSTRUCTIONS.lower()
```

- [ ] **Step 2: Rodar para confirmar que falha**

Run: `uv run pytest tests/test_compile_prompt.py -v`
Expected: FAIL com `ImportError: cannot import name 'COMPILE_INSTRUCTIONS'`

- [ ] **Step 3: Adicionar a constante `COMPILE_INSTRUCTIONS` em `compile.py`**

Adicionar no nível de módulo (após os imports) em `scripts/compile.py`:

```python
COMPILE_INSTRUCTIONS = """## Sua Tarefa

Leia o log diário acima e compile-o em artigos de wiki seguindo o schema à risca.
Escreva todo o conteúdo em português (preservando termos técnicos e nomes próprios
em inglês).

### Regras:

1. **Extrair conceitos-chave** — identifique 3-7 conceitos distintos que merecem artigo próprio.
2. **Criar artigos de conceito** em `knowledge/concepts/` — um .md por conceito.
   - Use o formato exato do AGENTS.md (frontmatter YAML + seções).
   - Preencha `dominio:` com `tecnico`, `operacional` ou `misto`.
   - Inclua `sources:` apontando para o log diário.
   - Use wikilinks `[[concepts/slug]]` para ligar conceitos relacionados.
3. **Criar artigos de conexão** em `knowledge/connections/` quando o log revelar
   relações não-óbvias entre 2+ conceitos. Conceitos `misto` (que cruzam técnico e
   operacional) devem preferencialmente virar uma `connection`.
4. **Atualizar artigos existentes** quando o log adicionar informação a conceitos já no wiki.
5. **Atualizar knowledge/index.md** — adicione novas linhas à tabela, incluindo a
   coluna `dominio`: `| [[path/slug]] | Resumo | dominio | source-file | data |`
6. **Anexar a knowledge/log.md** — entrada com timestamp registrando artigos criados/atualizados.

### Padrões de qualidade:
- Todo artigo precisa de frontmatter YAML completo, incluindo `dominio`.
- Todo artigo deve linkar a pelo menos 2 outros via [[wikilinks]].
- Seção de pontos-chave: 3-5 bullets. Detalhes: 2+ parágrafos. Relacionados: 2+ entradas.
- A seção Fontes deve citar o log diário com as afirmações específicas extraídas."""
```

- [ ] **Step 4: Substituir o bloco de regras inline pelo uso da constante**

Em `scripts/compile.py`, o f-string do `prompt` hoje contém, da linha "## Your Task" até o fim, as regras em inglês. Substituir tudo a partir de `## Your Task` pela interpolação da constante. O `prompt` resultante fica:

```python
    prompt = f"""You are a knowledge compiler. Your job is to read a daily conversation log
and extract knowledge into structured wiki articles.

## Schema (AGENTS.md)

{schema}

## Current Wiki Index

{wiki_index}

## Existing Wiki Articles

{existing_articles_context if existing_articles_context else "(Nenhum artigo existente ainda)"}

## Daily Log to Compile

**File:** {log_path.name}

{log_content}

{COMPILE_INSTRUCTIONS}

### Caminhos de arquivo:
- Artigos de conceito em: {CONCEPTS_DIR}
- Artigos de conexão em: {CONNECTIONS_DIR}
- Índice em: {KNOWLEDGE_DIR / 'index.md'}
- Log em: {KNOWLEDGE_DIR / 'log.md'}
- Timestamp para as entradas: {timestamp}
"""
```

> Nota: o `{schema}` é o `AGENTS.md` já em PT-BR (Task 3), injetado em runtime — por isso a tradução do schema e a do prompt se reforçam.

- [ ] **Step 5: Rodar os testes para confirmar que passam**

Run: `uv run pytest tests/test_compile_prompt.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Verificar que o módulo ainda importa**

Run: `uv run python -c "import sys; sys.path.insert(0, 'scripts'); import compile; print('ok')"`
Expected: imprime `ok` sem exception

- [ ] **Step 7: Rodar a suíte completa**

Run: `uv run pytest -v`
Expected: PASS (todos os testes das Tasks 1-5)

- [ ] **Step 8: Commit**

```bash
git add scripts/compile.py tests/test_compile_prompt.py
git commit -m "feat: prompt de compilacao em PT-BR com dominio e coluna no indice"
```

---

## Verificação final (manual, opcional)

Após as 5 tasks, um teste end-to-end real (consome API):

1. Criar um `daily/AAAA-MM-DD.md` de teste com conteúdo técnico **e** operacional misturado (ex.: uma decisão de migration + a razão de negócio por trás).
2. Run: `uv run python scripts/compile.py`
3. Conferir:
   - (a) artigos em `knowledge/concepts/` saem em PT-BR com `dominio` correto;
   - (b) `knowledge/index.md` tem a coluna `dominio` preenchida;
   - (c) ao menos uma `connection` cross-domínio foi criada.
4. Run: `uv run python scripts/query.py "pergunta técnica" --dominio tecnico` e confirmar que a resposta ignora conceitos puramente operacionais.
