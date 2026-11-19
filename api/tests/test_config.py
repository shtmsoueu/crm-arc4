"""Leitura das variáveis criadas pela integração Neon da Vercel."""

import pytest

from arc4_api.config import URL_LOCAL, Config

VARIAVEIS = ("DATABASE_URL", "POSTGRES_URL", "DATABASE_URL_UNPOOLED", "POSTGRES_URL_NON_POOLING", "VERCEL")


@pytest.fixture(autouse=True)
def _limpa(monkeypatch):
    for v in VARIAVEIS:
        monkeypatch.delenv(v, raising=False)


def test_local_sem_variavel_usa_banco_do_compose():
    assert Config.do_ambiente().database_url == URL_LOCAL


def test_vercel_sem_variavel_fica_nao_configurado(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert Config.do_ambiente().database_url is None


def test_aceita_postgres_url_quando_nao_ha_database_url(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://a@pooler/x")
    assert Config.do_ambiente().database_url == "postgresql://a@pooler/x"


def test_migracao_prefere_conexao_direta(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://a@pooler/x")
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", "postgresql://a@direto/x")
    cfg = Config.do_ambiente()
    assert cfg.database_url == "postgresql://a@pooler/x"
    assert cfg.url_migracao == "postgresql://a@direto/x"


def test_auto_migracao_pode_ser_desligada(monkeypatch):
    monkeypatch.setenv("ARC4_AUTO_MIGRATE", "0")
    assert Config.do_ambiente().migrar_automaticamente is False
