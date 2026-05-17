# Base de Conhecimento Pessoal LLM

**Suas conversas com IA se compilam automaticamente em uma base de conhecimento pesquisável.**

Adaptado da [arquitetura de KB do Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), mas em vez de coletar artigos da web, o material bruto são suas próprias conversas com o Claude Code. Quando uma sessão termina (ou auto-compacta no meio), hooks do Claude Code capturam o transcript da conversa e disparam um processo em segundo plano que usa o [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) para extrair o que importa — decisões, lições aprendidas, padrões, pegadinhas — e anexa em um log diário. Você então compila esses logs diários em artigos de conhecimento estruturados e cross-referenciados, organizados por conceito. A recuperação usa um arquivo de índice simples no lugar de RAG — sem banco vetorial, sem embeddings, só markdown.

A Anthropic esclareceu que o uso pessoal do Claude Agent SDK está coberto pela sua assinatura do Claude (Max, Team, ou Enterprise) — sem necessidade de créditos de API à parte. Diferente do OpenClaw, que requer cobrança via API para seu memory flush, este roda direto na sua assinatura.

## Instalação

### Pré-requisitos

Confira se você tem os 3 itens abaixo antes de começar:

- **[Claude Code](https://docs.claude.com/claude-code)** instalado e logado na sua conta
- **[uv](https://docs.astral.sh/uv/)** (gerenciador de Python): no macOS, `brew install uv` — no Linux, `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Python 3.12+** — o `uv` baixa automaticamente se não tiver

Verifique:

```bash
uv --version       # deve mostrar 0.5+ ou maior
claude --version   # deve mostrar a versão do Claude Code
```

### Passo 1 — Clonar e instalar dependências

```bash
cd ~/projetos    # ou qualquer pasta onde você guarda projetos
git clone https://github.com/ricardomelo96/credco-memory-compiler
cd credco-memory-compiler
uv sync
```

**Anote o caminho absoluto** do repo — você vai usar adiante:

```bash
pwd
# exemplo: /Users/seu-usuario/projetos/credco-memory-compiler
```

### Passo 2 — Teste se a base funciona

```bash
uv run python hooks/session-start.py              # deve imprimir um JSON
uv run python scripts/lint.py --structural-only   # deve rodar sem erro
```

Se os dois rodarem sem exception, instalação base está OK.

### Passo 3 — Ativar a captura automática (escolha 1 dos 3 modos)

#### Modo A — Manual (sem hooks, mais conservador)

Não configure hook nenhum. Você roda os comandos da seção [Comandos](#comandos-principais) à mão quando quiser. **Útil para:** experimentar antes de se comprometer.

#### Modo B — Captura em UM projeto específico (recomendado para começar)

Vá no projeto **onde você quer capturar as conversas** (não no repo do credco-memory-compiler — em outro projeto seu). Crie o arquivo `.claude/settings.json` lá com o conteúdo abaixo, **trocando `/CAMINHO/ABSOLUTO/credco-memory-compiler` pelo path que você anotou no Passo 1**:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run --directory /CAMINHO/ABSOLUTO/credco-memory-compiler python /CAMINHO/ABSOLUTO/credco-memory-compiler/hooks/session-start.py",
        "timeout": 15
      }]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run --directory /CAMINHO/ABSOLUTO/credco-memory-compiler python /CAMINHO/ABSOLUTO/credco-memory-compiler/hooks/pre-compact.py",
        "timeout": 10
      }]
    }],
    "SessionEnd": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run --directory /CAMINHO/ABSOLUTO/credco-memory-compiler python /CAMINHO/ABSOLUTO/credco-memory-compiler/hooks/session-end.py",
        "timeout": 10
      }]
    }]
  }
}
```

A captura roda apenas quando você abrir o Claude Code nesse projeto. **Outros projetos não são afetados.**

#### Modo C — Captura GLOBAL (em todas as suas sessões Claude Code)

Mesmo JSON do Modo B, mas no arquivo `~/.claude/settings.json` (settings globais do Claude Code).

**Atenção:**
- Se você **já tem hooks** configurados nesse arquivo, faça **merge dos blocos `SessionStart`, `PreCompact`, `SessionEnd`** — não sobrescreva o arquivo inteiro
- Se você **já usa outro sistema** de captura de memória, vai duplicar custo. Desative o outro antes

### Passo 4 — Verificar end-to-end

Após ativar hooks (Modo B ou C):

1. Abra Claude Code em um projeto onde os hooks estão ativos
2. Tenha uma conversa **com 3+ trocas** (conversas curtas são ignoradas pra economizar API)
3. Encerre a sessão com `/exit` ou `Ctrl+D`
4. Aguarde **~30 segundos** (flush.py roda em background depois da sessão)
5. Confira:

```bash
ls /CAMINHO/ABSOLUTO/credco-memory-compiler/daily/
# deve ter um arquivo YYYY-MM-DD.md

cat /CAMINHO/ABSOLUTO/credco-memory-compiler/daily/$(date +%Y-%m-%d).md
```

Se aparecer um log com seções `**Context:**`, `**Key Exchanges:**`, etc — **funcionou**.

### Quando algo não funciona

O arquivo `scripts/flush.log` é o lugar pra olhar primeiro:

```bash
tail -50 /CAMINHO/ABSOLUTO/credco-memory-compiler/scripts/flush.log
```

Erros comuns:

| Mensagem no log | Causa | Solução |
|---|---|---|
| `uv: command not found` | Hook não acha `uv` no PATH | Adicione `~/.local/bin` ao PATH no seu `~/.zshrc` |
| `No \`pyproject.toml\` found` | Você usou path relativo em vez de absoluto | Revise Modo B — todos os paths devem ser absolutos |
| `SKIP: only 2 turns (min 3)` | Conversa muito curta pra valer flush | Tenha conversa com 3+ trocas pra testar |
| `SKIP: no transcript path` | Bug conhecido do Claude Code | Inofensivo. Próxima sessão funciona |
| Nada aparece no `flush.log` | Hook nem disparou | Confira que o `.claude/settings.json` está no projeto certo e tem JSON válido |

### Timezone

O sistema dispara a compilação diária automaticamente após **18h locais**. O default está em `America/Sao_Paulo` (`scripts/config.py`). Se você está em outro fuso, edite essa constante.

## Como Funciona

```
Conversa -> hooks SessionEnd/PreCompact -> flush.py extrai conhecimento
    -> daily/YYYY-MM-DD.md -> compile.py -> knowledge/concepts/, connections/, qa/
        -> hook SessionStart injeta o índice na sessão seguinte -> ciclo se repete
```

- **Hooks** capturam conversas automaticamente (fim de sessão + safety-net pré-compactação)
- **flush.py** chama o Claude Agent SDK para decidir o que vale salvar, e após as 18h dispara a compilação automaticamente
- **compile.py** transforma logs diários em artigos de conceito organizados com referências cruzadas (automático ou manual)
- **query.py** responde perguntas usando recuperação guiada por índice (sem RAG na escala pessoal)
- **lint.py** roda 7 checks de saúde (links quebrados, órfãos, contradições, desatualização)

## Comandos Principais

```bash
uv run python scripts/compile.py                      # compila novos daily logs
uv run python scripts/query.py "pergunta"             # consulta a base de conhecimento
uv run python scripts/query.py "pergunta" --file-back # consulta + salva resposta de volta
uv run python scripts/lint.py                         # roda health checks
uv run python scripts/lint.py --structural-only       # só checks estruturais (gratuitos)
```

## Por Que Sem RAG?

O insight do Karpathy: em escala pessoal (50-500 artigos), o LLM lendo um `index.md` estruturado supera similaridade vetorial. O LLM entende o que você realmente está perguntando; similaridade de cosseno só acha palavras parecidas. RAG passa a ser necessário em ~2.000+ artigos, quando o índice excede a janela de contexto.

## Referência Técnica

Veja **[AGENTS.md](AGENTS.md)** para a referência técnica completa: formatos de artigos, arquitetura dos hooks, internals dos scripts, detalhes cross-platform, custos, e opções de customização. O AGENTS.md foi projetado para dar a um agente de IA tudo que ele precisa para entender, modificar, ou reconstruir o sistema.
