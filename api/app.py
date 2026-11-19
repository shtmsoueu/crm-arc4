"""Entrada da API na Vercel (projeto com Root Directory = api/).

A Vercel procura uma instância FastAPI chamada ``app`` em ``app.py`` na raiz do projeto.
O código fica em ``src/arc4_api``; o caminho é acrescentado aqui para que a importação
funcione mesmo que a Vercel instale só as dependências, sem instalar o pacote.
Fora da Vercel (Docker, `make dev`), use ``arc4_api.main:app`` normalmente.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from arc4_api.main import app  # noqa: E402

__all__ = ["app"]
