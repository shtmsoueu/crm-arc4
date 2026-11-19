"""D-007 — a API cria as tabelas sozinha na primeira requisição (Vercel não tem terminal)."""

from concurrent.futures import ThreadPoolExecutor

import psycopg
from fastapi.testclient import TestClient

from arc4_api.config import Config
from arc4_api.main import criar_app
from arc4_api.migracao import aplicar


def test_primeira_requisicao_migra_o_banco_vazio(banco_vazio):
    app = criar_app(Config(database_url=banco_vazio))
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200
    assert r.json() == {
        "status": "ok",
        "versao": "0.1.0",
        "banco": "ok",
        "migracao": "0001",
        "migracao_erro": None,
    }
    # Nova instância (outro cold start): não reaplica e não falha.
    assert TestClient(criar_app(Config(database_url=banco_vazio))).get("/health").status_code == 200


def test_varias_instancias_ao_mesmo_tempo(banco_vazio):
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda _: aplicar(banco_vazio), range(4)))
    with psycopg.connect(banco_vazio) as c:
        assert c.execute("select version_num from alembic_version").fetchall() == [("0001",)]
