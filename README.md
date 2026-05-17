# Base de Conhecimento Pessoal LLM

**Suas conversas com IA se compilam automaticamente em uma base de conhecimento pesquisável.**

Adaptado da [arquitetura de KB do Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), mas em vez de coletar artigos da web, o material bruto são suas próprias conversas com o Claude Code. Quando uma sessão termina (ou auto-compacta no meio), hooks do Claude Code capturam o transcript da conversa e disparam um processo em segundo plano que usa o [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) para extrair o que importa — decisões, lições aprendidas, padrões, pegadinhas — e anexa em um log diário. Você então compila esses logs diários em artigos de conhecimento estruturados e cross-referenciados, organizados por conceito. A recuperação usa um arquivo de índice simples no lugar de RAG — sem banco vetorial, sem embeddings, só markdown.

A Anthropic esclareceu que o uso pessoal do Claude Agent SDK está coberto pela sua assinatura do Claude (Max, Team, ou Enterprise) — sem necessidade de créditos de API à parte. Diferente do OpenClaw, que requer cobrança via API para seu memory flush, este roda direto na sua assinatura.

## Início Rápido

Diga ao seu agente de IA:

> "Clone https://github.com/ricardomelo96/credco-memory-compiler dentro deste projeto. Configure os hooks do Claude Code para que minhas conversas sejam capturadas automaticamente em logs diários, compiladas em uma base de conhecimento, e injetadas de volta em sessões futuras. Leia o AGENTS.md para a referência técnica completa de como tudo funciona."

O agente vai:
1. Clonar o repo e rodar `uv sync` para instalar as dependências
2. Copiar `.claude/settings.json` no seu projeto (ou mesclar os hooks no seu settings existente)
3. Os hooks são ativados automaticamente na próxima vez que você abrir o Claude Code

A partir daí, suas conversas começam a se acumular. Após as 18h locais, o próximo flush de sessão dispara automaticamente a compilação dos logs daquele dia em artigos de conhecimento. Você também pode rodar `uv run python scripts/compile.py` manualmente a qualquer momento.

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
