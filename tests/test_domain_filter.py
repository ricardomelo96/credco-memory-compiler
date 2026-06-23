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
