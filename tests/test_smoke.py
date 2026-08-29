"""Smoke tests so CI has something green from day one. Add real tests per project
(schema of fetched data, transformation helpers, etc.)."""


def test_import_ingest():
    import importlib

    mod = importlib.import_module("scripts.ingest")
    assert hasattr(mod, "put_raw")
    assert hasattr(mod, "put_bronze")


def test_run_date_format():
    from datetime import date

    assert len(date.today().isoformat()) == 10
