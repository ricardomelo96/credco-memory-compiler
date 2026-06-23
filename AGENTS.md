# AGENTS.md - Esquema da Base de Conhecimento Pessoal

> Adaptado da arquitetura de [Base de Conhecimento com LLM do Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
> Em vez de ingerir artigos externos, este sistema compila conhecimento a partir das suas próprias conversas com IA.

## A Analogia do Compilador

```
daily/          = código-fonte   (suas conversas — o material bruto)
LLM             = compilador     (extrai e organiza o conhecimento)
knowledge/      = executável     (base de conhecimento estruturada e consultável)
lint            = suite de testes(verificações de saúde e consistência)
queries         = runtime        (uso do conhecimento)
```

Você não organiza o conhecimento manualmente. Você tem conversas, e o LLM cuida da síntese, das referências cruzadas e da manutenção.

---

## Arquitetura

### Camada 1: `daily/` - Registros de Conversa (Fonte Imutável)

Os registros diários capturam o que aconteceu nas suas sessões de programação com IA. São as "fontes brutas" — append-only, nunca editadas depois do fato.

```
daily/
├── 2026-04-01.md
├── 2026-04-02.md
├── ...
```

Cada arquivo segue este formato:

```markdown
# Daily Log: YYYY-MM-DD

## Sessions

### Session (HH:MM) - Título Breve

**Context:** O que o usuário estava trabalhando.

**Key Exchanges:**
- Usuário perguntou sobre X, assistente explicou Y
- Decidiu usar abordagem Z porque...
- Descobriu que W não funciona quando...

**Decisions Made:**
- Escolheu biblioteca X em vez de Y porque...
- Arquitetura: adotou o padrão Z

**Lessons Learned:**
- Sempre faça X antes de Y para evitar...
- O problema com Z é que...

**Action Items:**
- [ ] Acompanhar X
- [ ] Refatorar Y quando houver tempo
```

### Camada 2: `knowledge/` - Conhecimento Compilado (Propriedade do LLM)

O LLM é o dono deste diretório. Humanos leem, mas raramente editam diretamente.

```
knowledge/
├── index.md              # Catálogo mestre — cada artigo com resumo de uma linha
├── log.md                # Log cronológico append-only de compilações
├── concepts/             # Artigos atômicos de conhecimento
├── connections/          # Insights transversais ligando 2+ conceitos
└── qa/                   # Respostas arquivadas a consultas (conhecimento composto)
```

### Camada 3: Este Arquivo (AGENTS.md)

O esquema que diz ao LLM como compilar e manter a base de conhecimento. Esta é a "especificação do compilador."

---

## Arquivos Estruturais

### `knowledge/index.md` - Catálogo Mestre

Uma tabela listando todos os artigos de conhecimento. É o mecanismo primário de recuperação — o LLM lê isso PRIMEIRO ao responder qualquer consulta, depois seleciona os artigos relevantes para ler na íntegra.

Formato:

```markdown
# Knowledge Base Index

| Artigo | Resumo | dominio | Compilado de | Atualizado |
|--------|--------|---------|--------------|------------|
| [[concepts/migration-035-magali]] | Split de patrimônio na migration 035 | misto | daily/2026-06-23.md | 2026-06-23 |
| [[connections/auth-and-webhooks]] | Padrões de verificação de token compartilhados entre Supabase auth e webhooks Stripe | daily/2026-04-02.md, daily/2026-04-04.md | 2026-04-04 |
```

### `knowledge/log.md` - Log de Compilação

Registro cronológico append-only de cada operação de compilação, consulta e lint.

Formato:

```markdown
# Build Log

## [2026-04-01T14:30:00] compile | Daily Log 2026-04-01
- Source: daily/2026-04-01.md
- Articles created: [[concepts/nextjs-project-structure]], [[concepts/tailwind-setup]]
- Articles updated: (none)

## [2026-04-02T09:00:00] query | "How do I handle auth redirects?"
- Consulted: [[concepts/supabase-auth]], [[concepts/nextjs-middleware]]
- Filed to: [[qa/auth-redirect-handling]]
```

---

## Formatos de Artigo

### Artigos de Conceito (`knowledge/concepts/`)

Um artigo por unidade atômica de conhecimento. São fatos, padrões, decisões, preferências e lições extraídas das suas conversas.

```markdown
---
title: Nome do Conceito
dominio: tecnico   # tecnico | operacional | misto
created: 2026-06-23
updated: 2026-06-23
sources:
  - daily/2026-06-23.md
---

# Nome do Conceito

[Explicação central em 2-4 frases]

## Key Points

- [Pontos objetivos, cada um independente]

## Details

[Explicação aprofundada, parágrafos estilo enciclopédia]

## Related Concepts

- [[concepts/conceito-relacionado]] - Como se conecta

## Sources

- [[daily/2026-06-23.md]] - Descoberta inicial durante a configuração do projeto
```

**Campo `dominio`:**
- `tecnico` — arquitetura, migrations, RLS, bugs, padrões de código.
- `operacional` — decisões de produto/negócio, processos, escolhas estratégicas, regras de atendimento.
- `misto` — quando os dois mundos se cruzam. Prefira materializar a relação como artigo em `connections/`.

### Artigos de Conexão (`knowledge/connections/`)

Síntese transversal ligando 2+ conceitos. Criados quando uma conversa revela uma relação não óbvia.

```markdown
---
title: "Connection: X and Y"
dominio: misto   # tecnico | operacional | misto
connects:
  - "concepts/concept-x"
  - "concepts/concept-y"
sources:
  - "daily/2026-04-04.md"
created: 2026-04-04
updated: 2026-04-04
---

# Connection: X and Y

## The Connection

[O que liga esses conceitos]

## Key Insight

[A relação não óbvia descoberta]

## Evidence

[Exemplos específicos das conversas]

## Related Concepts

- [[concepts/concept-x]]
- [[concepts/concept-y]]
```

### Artigos de Q&A (`knowledge/qa/`)

Respostas arquivadas a consultas. Toda pergunta complexa respondida pelo sistema pode ser armazenada permanentemente, tornando futuras consultas mais precisas.

```markdown
---
title: "Q: Pergunta Original"
question: "A pergunta exata feita"
consulted:
  - "concepts/article-1"
  - "concepts/article-2"
filed: 2026-04-05
---

# Q: Pergunta Original

## Answer

[A resposta sintetizada com citações [[wikilinks]]]

## Sources Consulted

- [[concepts/article-1]] - Relevante porque...
- [[concepts/article-2]] - Forneceu contexto sobre...

## Follow-Up Questions

- E o caso extremo X?
- Como isso muda se Y?
```

---

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

---

## Operações Principais

### 1. Compilar (daily/ -> knowledge/)

Ao processar um registro diário:

1. Ler o arquivo de log diário
2. Ler `knowledge/index.md` para entender o estado atual do conhecimento
3. Ler os artigos existentes que podem precisar de atualização
4. Para cada piece de conhecimento encontrado no log:
   - Se um artigo de conceito existente cobre este tópico: ATUALIZAR com novas informações, adicionar o log diário como fonte
   - Se é um tópico novo: CRIAR um novo artigo em `concepts/`
5. Se o log revela uma conexão não óbvia entre 2+ conceitos existentes: CRIAR um artigo em `connections/`
6. ATUALIZAR `knowledge/index.md` com entradas novas/modificadas
7. ADICIONAR ao `knowledge/log.md`

**Diretrizes importantes:**
- Um único log diário pode tocar 3-10 artigos de conhecimento
- Prefira atualizar artigos existentes a criar quase-duplicatas
- Use `[[wikilinks]]` estilo Obsidian com caminhos relativos completos a partir de `knowledge/`
- Escreva em estilo enciclopédia — factual, conciso, autocontido
- Todo artigo deve ter frontmatter YAML
- Todo artigo deve referenciar os logs diários de origem

### 2. Consultar (Ask the Knowledge Base)

1. Ler `knowledge/index.md` (o catálogo mestre)
2. Com base na pergunta, identificar 3-10 artigos relevantes no índice
3. Ler esses artigos na íntegra
4. Sintetizar uma resposta com citações `[[wikilink]]`
5. Se `--file-back` for especificado: criar um artigo em `knowledge/qa/` e atualizar index.md e log.md

**Por que funciona sem RAG:** Na escala de uma base de conhecimento pessoal (50-500 artigos), o LLM lendo um índice estruturado supera a similaridade por cosseno. O LLM entende o que a pergunta realmente quer e seleciona as páginas adequadamente. Embeddings encontram palavras similares; o LLM encontra conceitos relevantes.

### 3. Lint (Verificações de Saúde)

Sete verificações, executadas periodicamente:

1. **Links quebrados** — `[[wikilinks]]` apontando para artigos inexistentes
2. **Páginas órfãs** — artigos com zero links de entrada de outros artigos
3. **Fontes órfãs** — logs diários que ainda não foram compilados
4. **Artigos desatualizados** — log diário de origem mudou desde a última compilação
5. **Contradições** — afirmações conflitantes entre artigos (requer julgamento do LLM)
6. **Backlinks ausentes** — A linka para B mas B não linka de volta para A
7. **Artigos esparsos** — abaixo de 200 palavras, provavelmente incompletos

Saída: um relatório markdown com níveis de severidade (error, warning, suggestion).

---

## Convenções

- **Wikilinks:** Use o estilo Obsidian `[[caminho/para/artigo]]` sem extensão `.md`
- **Estilo de escrita:** Estilo enciclopédia, factual, terceira pessoa quando apropriado
- **Datas:** ISO 8601 (YYYY-MM-DD para datas, ISO completo para timestamps em log.md)
- **Nomenclatura de arquivos:** minúsculas, hífens para espaços (ex.: `supabase-row-level-security.md`)
- **Frontmatter:** Todo artigo deve ter frontmatter YAML com no mínimo: title, dominio, sources, created, updated
- **Fontes:** Sempre referencie os log(s) diário(s) que contribuíram para um artigo

---

## Estrutura Completa do Projeto

```
credco-memory-compiler/
|-- .claude/
|   |-- settings.json                # Configuração de hooks (ativa automaticamente no Claude Code)
|-- .gitignore                       # Exclui estado de runtime, arquivos temporários, caches
|-- AGENTS.md                        # Este arquivo — esquema + referência técnica completa
|-- README.md                        # Visão geral concisa + início rápido
|-- pyproject.toml                   # Dependências (na raiz para que hooks possam encontrar)
|-- daily/                           # "Código-fonte" — logs de conversa (imutáveis)
|-- knowledge/                       # "Executável" — conhecimento compilado (propriedade do LLM)
|   |-- index.md                     #   Catálogo mestre — o mecanismo de recuperação
|   |-- log.md                       #   Log de compilação append-only
|   |-- concepts/                    #   Artigos atômicos de conhecimento
|   |-- connections/                 #   Insights transversais ligando 2+ conceitos
|   |-- qa/                          #   Respostas arquivadas (conhecimento composto)
|-- scripts/                         # Ferramentas CLI
|   |-- compile.py                   #   Compila logs diários -> artigos de conhecimento
|   |-- query.py                     #   Faz perguntas (guiado por índice, sem RAG)
|   |-- lint.py                      #   7 verificações de saúde
|   |-- flush.py                     #   Extrai memórias de conversas (segundo plano)
|   |-- config.py                    #   Constantes de caminho
|   |-- utils.py                     #   Utilitários compartilhados
|-- hooks/                           # Hooks do Claude Code
|   |-- session-start.py             #   Injeta conhecimento em cada sessão
|   |-- session-end.py               #   Extrai conversa -> log diário
|   |-- pre-compact.py               #   Rede de segurança: captura contexto antes da compactação
|-- reports/                         # Relatórios de lint (gitignored)
```

---

## Sistema de Hooks (Captura Automática)

Os hooks são configurados em `.claude/settings.json` e disparam automaticamente quando você usa o Claude Code neste projeto.

### Formato de `.claude/settings.json`

Há dois modos de instalação. Escolha com base em onde deseja que os hooks disparem.

**Modo 1: Apenas local (hooks disparam somente quando `cwd` é este repositório)**

Este é o modo padrão do repositório. Caminhos relativos só resolvem corretamente quando o `cwd` do Claude Code é o próprio clone do credco-memory-compiler:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run python hooks/session-start.py", "timeout": 15 }] }],
    "PreCompact": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run python hooks/pre-compact.py", "timeout": 10 }] }],
    "SessionEnd": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run python hooks/session-end.py", "timeout": 10 }] }]
  }
}
```

**Modo 2: Cross-project (hooks disparam de qualquer projeto — recomendado para uso diário)**

Coloque este `.claude/settings.json` em outro projeto (escopo de projeto) ou em `~/.claude/settings.json` (global, dispara em toda sessão do Claude Code). Substitua `<ROOT>` pelo caminho absoluto do clone do credco-memory-compiler:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run --directory <ROOT> python <ROOT>/hooks/session-start.py", "timeout": 15 }] }],
    "PreCompact": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run --directory <ROOT> python <ROOT>/hooks/pre-compact.py", "timeout": 10 }] }],
    "SessionEnd": [{ "matcher": "", "hooks": [{ "type": "command", "command": "uv run --directory <ROOT> python <ROOT>/hooks/session-end.py", "timeout": 10 }] }]
  }
}
```

O flag `--directory <ROOT>` diz ao `uv` onde encontrar o `pyproject.toml` independentemente do diretório de trabalho atual. Sem ele, os hooks falham silenciosamente em qualquer projeto que não seja o credco-memory-compiler — o `uv` encerra procurando um `pyproject.toml` que não consegue encontrar, sem mensagem visível ao usuário.

`matcher` vazio captura todos os eventos.

### Detalhes dos Hooks

**`session-start.py`** (SessionStart)
- I/O local puro, sem chamadas de API, executa em menos de 1 segundo
- Lê `knowledge/index.md` e o log diário mais recente
- Emite JSON para stdout: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`
- O Claude vê o índice da base de conhecimento no início de cada sessão
- Contexto máximo: 20.000 caracteres

**`session-end.py`** (SessionEnd)
- Lê input do hook do stdin (JSON com `session_id`, `transcript_path`, `cwd`)
- Copia o transcript JSONL bruto para um arquivo temporário (sem parsing no hook — mantém rápido)
- Spawna `flush.py` como processo de segundo plano totalmente desanexado
- Guarda contra recursão: sai imediatamente se a variável de ambiente `CLAUDE_INVOKED_BY` estiver definida

**`pre-compact.py`** (PreCompact)
- Mesma arquitetura que session-end.py
- Dispara antes que o Claude Code compacte automaticamente a janela de contexto
- Protege contra `transcript_path` vazio (bug conhecido do Claude Code #13668)
- Crítico para sessões longas: captura o contexto antes que a sumarização o descarte

**Por que tanto PreCompact quanto SessionEnd?** Sessões longas podem disparar múltiplas compactações automáticas antes de você fechar a sessão. Sem PreCompact, o contexto intermediário se perde na sumarização antes que o SessionEnd sequer dispare.

### Processo de Flush em Segundo Plano (`flush.py`)

Spawnado por ambos os hooks como processo de segundo plano totalmente desanexado:
- **Windows:** flags `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS`
- **Mac/Linux:** `start_new_session=True`

Isso garante que flush.py sobreviva após a saída do processo de hook do Claude Code.

**O que flush.py faz:**
1. Define a variável de ambiente `CLAUDE_INVOKED_BY=memory_flush` (evita disparo recursivo de hooks)
2. Lê o contexto de conversa pré-extraído do arquivo `.md` temporário
3. Pula se o contexto estiver vazio ou se a mesma sessão foi processada dentro de 60 segundos (deduplicação)
4. Chama o Claude Agent SDK (`query()` com `allowed_tools=[]`, `max_turns=2`)
5. O Claude decide o que vale salvar — retorna pontos estruturados ou `FLUSH_OK`
6. Adiciona o resultado em `daily/YYYY-MM-DD.md`
7. Remove o arquivo de contexto temporário
8. **Compilação automática no final do dia:** Se for após as 18h no horário local (`COMPILE_AFTER_HOUR = 18`) e o log diário de hoje mudou desde sua última compilação (comparação de hash contra `state.json`), spawna `compile.py` como outro processo de segundo plano desanexado. Isso significa que a compilação acontece automaticamente uma vez por dia sem precisar de cron job ou trigger manual.

### Formato de Transcript JSONL

O Claude Code armazena conversas como arquivos `.jsonl`. As mensagens ficam aninhadas sob a chave `message`:

```python
entry = json.loads(line)
msg = entry.get("message", {})
role = msg.get("role", "")     # "user" ou "assistant"
content = msg.get("content", "")  # string ou lista de blocos de conteúdo
```

O conteúdo pode ser uma string ou uma lista de blocos (`{"type": "text", "text": "..."}` dicts).

---

## Detalhes dos Scripts

### compile.py - O Compilador

Usa o `query()` assíncrono com streaming do Claude Agent SDK:

```python
async for message in query(
    prompt=compile_prompt,
    options=ClaudeAgentOptions(
        cwd=str(ROOT_DIR),
        system_prompt={"type": "preset", "preset": "claude_code"},
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],
        permission_mode="acceptEdits",
        max_turns=30,
    ),
):
```

- Constrói um prompt com: esquema AGENTS.md, índice atual, todos os artigos existentes e o log diário
- O Claude lê o log diário, decide quais conceitos extrair e escreve os arquivos diretamente
- `permission_mode="acceptEdits"` aprova automaticamente todas as operações de arquivo
- Incremental: rastreia hashes SHA-256 dos logs diários em `state.json`, pula arquivos não modificados
- Custo: ~US$0,45-0,65 por log diário (aumenta conforme a KB cresce)

**CLI:**
```bash
uv run python scripts/compile.py              # compila apenas novos/modificados
uv run python scripts/compile.py --all        # força recompilação de tudo
uv run python scripts/compile.py --file daily/2026-04-01.md
uv run python scripts/compile.py --dry-run
```

### query.py - Recuperação Guiada por Índice

Carrega toda a base de conhecimento no contexto (índice + todos os artigos). Sem RAG.

Na escala de KB pessoal (50-500 artigos), o LLM lendo um índice estruturado supera a similaridade vetorial. O LLM entende o que você realmente está perguntando; a similaridade por cosseno apenas encontra palavras similares.

**CLI:**
```bash
uv run python scripts/query.py "Quais padrões de auth uso?"
uv run python scripts/query.py "Qual é minha estratégia de tratamento de erros?" --file-back
```

Com `--file-back`, cria um artigo de Q&A em `knowledge/qa/` e atualiza o índice e o log. Este é o loop composto — cada pergunta torna a KB mais inteligente.

### lint.py - Verificações de Saúde

Sete verificações:

| Verificação | Tipo | Detecta |
|-------------|------|---------|
| Links quebrados | Estrutural | `[[wikilinks]]` para artigos inexistentes |
| Páginas órfãs | Estrutural | Artigos com zero links de entrada |
| Fontes órfãs | Estrutural | Logs diários ainda não compilados |
| Artigos desatualizados | Estrutural | Logs de origem modificados desde a compilação |
| Backlinks ausentes | Estrutural | A linka para B mas B não linka de volta |
| Artigos esparsos | Estrutural | Abaixo de 200 palavras |
| Contradições | LLM | Afirmações conflitantes entre artigos |

**CLI:**
```bash
uv run python scripts/lint.py                    # todas as verificações
uv run python scripts/lint.py --structural-only  # pula verificação LLM (gratuito)
```

Relatórios salvos em `reports/lint-YYYY-MM-DD.md`.

---

## Rastreamento de Estado

`scripts/state.json` rastreia:
- `ingested` — mapa de nomes de arquivos de log diário para hashes SHA-256, timestamps de compilação e custos
- `query_count` — total de consultas executadas
- `last_lint` — timestamp do lint mais recente
- `total_cost` — custo acumulado de API

`scripts/last-flush.json` rastreia deduplicação de flush (session_id + timestamp).

Ambos são gitignored e regenerados automaticamente.

---

## Dependências

`pyproject.toml` (na raiz do projeto):
- `claude-agent-sdk>=0.1.29` - Claude Agent SDK para chamadas LLM com uso de ferramentas
- `python-dotenv>=1.0.0` - Gerenciamento de variáveis de ambiente
- `tzdata>=2024.1` - Dados de fuso horário
- Python 3.12+, gerenciado por [uv](https://docs.astral.sh/uv/)

Nenhuma chave de API necessária — usa as credenciais integradas do Claude Code em `~/.claude/.credentials.json`.

---

## Custos

| Operação | Custo |
|----------|-------|
| Compilar um log diário | US$0,45-0,65 |
| Consulta (sem file-back) | ~US$0,15-0,25 |
| Consulta (com file-back) | ~US$0,25-0,40 |
| Lint completo (com contradições) | ~US$0,15-0,25 |
| Lint estrutural apenas | US$0,00 |
| Memory flush (por sessão) | ~US$0,02-0,05 |

---

## Solução de Problemas

O diagnóstico mais útil é `scripts/flush.log`. Tanto os hooks quanto o `flush.py` adicionam entradas com timestamps, então quando algo parece "não funcionar", comece por aqui:

```bash
tail -50 scripts/flush.log
```

### Modos de falha comuns

| Sintoma | Causa provável | Correção |
|---------|----------------|---------|
| Nenhum `daily/YYYY-MM-DD.md` aparece | Caminho do comando do hook resolve incorretamente | Use caminhos absolutos com `uv run --directory <ROOT>` (veja Modo 2 na seção Hook System) |
| `flush.log` mostra `uv: command not found` | Shell do hook não tem `uv` no PATH | Adicione `~/.local/bin` ao PATH no rc do shell; reinicie o terminal |
| `flush.log` mostra `No \`pyproject.toml\` found` | Mesma causa — problema de caminho relativo | Mesma correção |
| `flush.log` mostra `SKIP: only N turns (min 3)` | Conversa muito curta | Tenha uma conversa de 3+ turnos antes de sair |
| `flush.log` mostra `SKIP: no transcript path` | Bug conhecido do Claude Code #13668 | Inofensivo. A próxima sessão funciona |
| Log diário recebe entradas duplicadas | Corrida entre PreCompact + SessionEnd | Já mitigado pelo dedup em `last-flush.json` (janela de 120s) |
| `flush.log` cresce muito ao longo dos meses | Sem rotação de log embutida | Remova manualmente `scripts/flush.log` periodicamente, ou adicione `RotatingFileHandler` |
| `compile.py` nunca executa automaticamente | Verificação pós-horário falhou para seu fuso | Defina `COMPILE_AFTER_HOUR` em `flush.py` e `TIMEZONE` em `config.py` para seu fuso; ou execute `uv run python scripts/compile.py` manualmente |

### Testes de fumaça (execute após instalação)

```bash
# 1. O hook SessionStart deve imprimir JSON
uv run python hooks/session-start.py

# 2. Lint estrutural deve passar (sem chamada LLM, gratuito)
uv run python scripts/lint.py --structural-only

# 3. Compilação dry-run (não executa se não houver logs diários)
uv run python scripts/compile.py --dry-run
```

Se os três passarem sem exceção, a instalação base está OK. A partir daí, os únicos pontos de falha restantes são a configuração do caminho do hook (Modo 1 vs Modo 2) e o `uv` estar no PATH dentro do subshell do hook.

### Verificando end-to-end após ativação do hook

```bash
# Abra o Claude Code em um projeto onde os hooks estão ativos
# Tenha uma conversa de 3+ turnos, depois /exit
# Aguarde ~30s (flush.py executa assincronamente)

# Verifique se um log diário foi gerado
ls -lh <ROOT>/daily/

# Verifique o flush.log para confirmar que flush.py executou até o fim
tail -30 <ROOT>/scripts/flush.log

# Inspecione manualmente o que foi capturado
cat <ROOT>/daily/$(date +%Y-%m-%d).md
```

---

## Personalização

### Tipos Adicionais de Artigo

Adicione diretórios como `people/`, `projects/`, `tools/` em `knowledge/`. Defina o formato do artigo neste arquivo (AGENTS.md) e atualize `list_wiki_articles()` em `utils.py` para incluí-los.

### Integração com Obsidian

A base de conhecimento é puro markdown com `[[wikilinks]]` — funciona nativamente no Obsidian. Aponte um vault para `knowledge/` para visualização em grafo, backlinks e busca.

### Escalando Além da Recuperação Guiada por Índice

Com ~2.000+ artigos / ~2M+ tokens, o índice se torna grande demais para a janela de contexto. Nesse ponto, adicione RAG híbrido (busca por palavras-chave + semântica) como camada de recuperação antes do LLM. Veja a recomendação de Karpathy de usar `qmd` de Tobi Lutke para busca em escala.
