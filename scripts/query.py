"""
Query the knowledge base using index-guided retrieval (no RAG).

The LLM reads the index, picks relevant articles, and synthesizes an answer.
No vector database, no embeddings, no chunking - just structured markdown
and an index the LLM can reason over.

Usage:
    uv run python query.py "How should I handle auth redirects?"
    uv run python query.py "What patterns do I use for API design?" --file-back
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from config import KNOWLEDGE_DIR, QA_DIR, now_iso
from utils import load_state, read_all_wiki_content, save_state

ROOT_DIR = Path(__file__).resolve().parent.parent


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


async def run_query(question: str, file_back: bool = False, dominio: str | None = None) -> str:
    """Query the knowledge base and optionally file the answer back."""
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    wiki_content = read_all_wiki_content(dominio=dominio)

    tools = ["Read", "Glob", "Grep"]
    if file_back:
        tools.extend(["Write", "Edit"])

    file_back_instructions = ""
    if file_back:
        timestamp = now_iso()
        file_back_instructions = f"""

## Instruções de Arquivamento (File Back)

Após responder, faça o seguinte:
1. Crie um artigo Q&A em {QA_DIR}/ com o nome do arquivo sendo uma versão
   slugificada da pergunta (ex.: knowledge/qa/como-aplicar-migration-035.md)
2. Use o formato de artigo Q&A do schema (frontmatter com title, question,
   consulted, filed)
3. Atualize {KNOWLEDGE_DIR / 'index.md'} com uma nova linha para este artigo Q&A
   (incluindo a coluna dominio)
4. Anexe ao {KNOWLEDGE_DIR / 'log.md'}:
   ## [{timestamp}] query (filed) | resumo da pergunta
   - Pergunta: {question}
   - Consultados: [[lista de artigos lidos]]
   - Arquivado em: [[qa/nome-do-artigo]]
"""

    prompt = f"""Você é um motor de consulta da base de conhecimento. Responda à pergunta do
usuário consultando a base abaixo. Responda em português.

## Como Responder

1. Leia a seção ÍNDICE primeiro - ela lista cada artigo com um resumo de uma linha
2. Identifique de 3 a 10 artigos relevantes para a pergunta
3. Leia esses artigos com atenção (eles estão incluídos abaixo)
4. Sintetize uma resposta clara e completa
5. Cite as fontes usando [[wikilinks]] (ex.: [[concepts/migration-035-write-functions]])
6. Se a base não contiver informação relevante, diga isso honestamente

## Base de Conhecimento

{wiki_content}

## Pergunta

{question}
{file_back_instructions}"""

    answer = ""
    cost = 0.0

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=str(ROOT_DIR),
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=tools,
                permission_mode="acceptEdits",
                max_turns=15,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        answer += block.text
            elif isinstance(message, ResultMessage):
                cost = message.total_cost_usd or 0.0
    except Exception as e:
        answer = f"Error querying knowledge base: {e}"

    # Update state
    state = load_state()
    state["query_count"] = state.get("query_count", 0) + 1
    state["total_cost"] = state.get("total_cost", 0.0) + cost
    save_state(state)

    return answer


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


if __name__ == "__main__":
    main()
