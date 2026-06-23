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
