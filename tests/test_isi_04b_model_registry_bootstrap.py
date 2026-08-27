from __future__ import annotations

import subprocess
import sys
import textwrap


def test_clean_process_knowledge_seed_registers_organization_fk_dependency():
    """Regression for the real CLI path: no prior aggregate-model import may be assumed."""
    code = textwrap.dedent(
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from src.core.database import Base
        from src.knowledge.seed import seed_knowledge_registry

        assert 'core_organizations' in Base.metadata.tables, sorted(Base.metadata.tables)
        assert 'knowledge_sources' in Base.metadata.tables, sorted(Base.metadata.tables)

        engine = create_engine('sqlite+pysqlite:///:memory:')
        Base.metadata.create_all(engine)
        domains = {
            'domains': [
                {
                    'code': 'simpa.test',
                    'product_scope': 'SIMPA',
                    'title_sr': 'Test',
                    'title_en': 'Test',
                }
            ]
        }
        sources = {
            'sources': [
                {
                    'source_key': 'public.simpa.test.v1',
                    'knowledge_scope': 'PUBLIC',
                    'product_scope': 'SIMPA',
                    'locale': 'sr-Latn',
                    'source_type': 'document',
                    'title': 'Test source',
                    'source_uri': '',
                    'origin_name': '',
                    'authority_level': 'institutional',
                    'review_status': 'reviewed',
                    'sensitivity': 'public',
                    'rag_eligible': True,
                    'content_sha256': '',
                    'provenance': 'regression',
                    'domain_codes': ['simpa.test'],
                }
            ]
        }
        with Session(engine) as session:
            result = seed_knowledge_registry(session, domains, sources)
            assert result['domains'] == 1
            assert result['sources'] == 1
            assert result['source_domains'] == 1
        """
    )
    result = subprocess.run([sys.executable, '-c', code], text=True, capture_output=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_cli_explicitly_bootstraps_platform_model_registry():
    from pathlib import Path

    text = Path('tools/seed_domain_knowledge_content.py').read_text()
    assert 'import src.platform.models' in text
