"""Configuração por variáveis de ambiente (nenhum segredo versionado)."""

from __future__ import annotations

import os
from dataclasses import dataclass

# Nomes que a integração Neon da Vercel costuma criar, em ordem de preferência.
VARIAVEIS_BANCO = ("DATABASE_URL", "POSTGRES_URL")
# Conexão direta (sem pooler), preferida para migrations: o advisory lock exige sessão.
VARIAVEIS_BANCO_DIRETO = ("DATABASE_URL_UNPOOLED", "POSTGRES_URL_NON_POOLING")
URL_LOCAL = "postgresql://arc4:arc4@localhost:5432/arc4"


def _primeira(nomes: tuple[str, ...]) -> str | None:
    for nome in nomes:
        valor = os.environ.get(nome, "").strip()
        if valor:
            return valor
    return None


@dataclass(frozen=True)
class Config:
    database_url: str | None
    """None = banco não configurado (ex.: Vercel sem a integração Neon)."""
    database_url_direta: str | None = None
    timeout_banco_s: float = 2.0
    migrar_automaticamente: bool = True

    @property
    def url_migracao(self) -> str | None:
        return self.database_url_direta or self.database_url

    @classmethod
    def do_ambiente(cls) -> Config:
        url = _primeira(VARIAVEIS_BANCO)
        if url is None and not os.environ.get("VERCEL"):
            url = URL_LOCAL  # desenvolvimento local / Docker Compose
        return cls(
            database_url=url,
            database_url_direta=_primeira(VARIAVEIS_BANCO_DIRETO),
            timeout_banco_s=float(os.environ.get("HEALTH_DB_TIMEOUT_S", "2")),
            migrar_automaticamente=os.environ.get("ARC4_AUTO_MIGRATE", "1") != "0",
        )
