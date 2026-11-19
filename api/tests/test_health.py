"""F0.2 — a API responde GET /health."""

import os

import pytest
from fastapi.testclient import TestClient

from arc4_api.config import Config
from arc4_api.main import criar_app

SEM_BANCO = "postgresql://ninguem:segredo@127.0.0.1:1/x"  # porta 1: conexão recusada de imediato


def test_health_sem_banco_responde_503_sem_vazar_detalhes():
    app = criar_app(Config(database_url=SEM_BANCO, timeout_banco_s=1, migrar_automaticamente=False))
    r = TestClient(app).get("/health")
    assert r.status_code == 503
    assert r.json() == {
        "status": "degradado",
        "versao": "0.1.0",
        "banco": "indisponivel",
        "migracao": None,
        "migracao_erro": None,
    }
    assert "segredo" not in r.text


def test_health_banco_nao_configurado():
    app = criar_app(Config(database_url=None))
    r = TestClient(app).get("/api/health")
    assert r.status_code == 503
    assert r.json()["banco"] == "nao_configurado"


def test_migracao_que_falha_aparece_so_pelo_tipo_do_erro():
    app = criar_app(Config(database_url=SEM_BANCO, timeout_banco_s=1))
    r = TestClient(app).get("/api/health")
    assert r.status_code == 503
    assert r.json()["migracao_erro"] == "OperationalError"
    assert "segredo" not in r.text and "127.0.0.1" not in r.text


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL não definido")
def test_health_com_banco():
    app = criar_app(Config(database_url=os.environ["TEST_DATABASE_URL"], migrar_automaticamente=False))
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["banco"] == "ok"
