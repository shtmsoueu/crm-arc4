"""A entrada usada pela Vercel (api/app.py) expõe a mesma aplicação, sem depender do pacote instalado."""

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


def test_requirements_espelha_pyproject():
    import tomllib

    deps = tomllib.loads((API / "pyproject.toml").read_text())["project"]["dependencies"]
    reqs = [
        linha.strip()
        for linha in (API / "requirements.txt").read_text().splitlines()
        if linha.strip() and not linha.startswith("#")
    ]
    assert sorted(deps) == sorted(reqs)
