"""Entrada da Vercel: api/app.py expõe a aplicação e o vercel.json da raiz encaminha /api para ela."""

import subprocess
import sys
from pathlib import Path

API = Path(__file__).resolve().parents[1]


def test_app_py_expoe_fastapi_sem_instalar_o_pacote():
    # -I: ignora o ambiente do usuário e o diretório atual; só o shim põe src/ no caminho.
    codigo = (
        "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
        "m = runpy.run_path(sys.argv[1] + '/app.py'); "
        "from fastapi import FastAPI; assert isinstance(m['app'], FastAPI); "
        "assert any(r.path == '/api/health' for r in m['app'].routes)"
    )
    subprocess.run([sys.executable, "-I", "-c", codigo, str(API)], check=True)  # noqa: S603 — entrada fixa


def test_vercel_json_aponta_para_a_entrada_da_api():
    import json

    cfg = json.loads((API.parent / "vercel.json").read_text(encoding="utf-8"))
    assert "api/app.py" in cfg["functions"]
    destinos = {r["source"]: r["destination"] for r in cfg["rewrites"]}
    assert destinos["/api/:path*"] == "/api/app"
    assert destinos["/health"] == "/api/app"
    # A SPA é o último recurso: rotas da API vêm antes.
    assert cfg["rewrites"][-1]["destination"] == "/index.html"
    assert cfg["outputDirectory"] == "web/dist"
