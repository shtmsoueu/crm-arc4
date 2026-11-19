"""Aplica as migrations do Alembic quando a API sobe (D-007, revisado).

Na Vercel não há terminal: a primeira requisição de cada instância garante que o banco
está na última revisão. É seguro com várias instâncias ao mesmo tempo (advisory lock no
PostgreSQL) e idempotente (o Alembic não reaplica o que já está aplicado).
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import psycopg

from .config import Config

log = logging.getLogger("arc4_api.migracao")

# api/src/arc4_api/migracao.py -> raiz do repositório
ALEMBIC_INI = Path(__file__).resolve().parents[3] / "db" / "alembic.ini"
CHAVE_LOCK = 4_140_900  # qualquer inteiro fixo e exclusivo deste projeto
INTERVALO_NOVA_TENTATIVA_S = 60.0


@dataclass
class EstadoMigracao:
    concluida: bool = False
    erro: str | None = None
    """Só o tipo do erro: a mensagem do driver pode conter host e usuário."""
    tentada_em: float = 0.0


def aplicar(url: str) -> None:
    """Leva o banco em ``url`` até a revisão head, segurando um advisory lock."""
    from alembic import command
    from alembic.config import Config as AlembicConfig

    if not ALEMBIC_INI.is_file():
        raise FileNotFoundError("db/alembic.ini fora do pacote implantado")
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as c:
        c.execute("select pg_advisory_lock(%s)", (CHAVE_LOCK,))
        try:
            cfg = AlembicConfig(str(ALEMBIC_INI))
            cfg.attributes["database_url"] = url
            command.upgrade(cfg, "head")
        finally:
            c.execute("select pg_advisory_unlock(%s)", (CHAVE_LOCK,))


class Migrador:
    """Tenta uma vez por instância; em caso de falha, tenta de novo após um intervalo."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.estado = EstadoMigracao()
        self._lock = threading.Lock()

    def garantir(self) -> None:
        if self.estado.concluida or not self.cfg.migrar_automaticamente:
            return
        url = self.cfg.url_migracao
        if url is None:
            return
        with self._lock:
            agora = time.monotonic()
            if self.estado.concluida or (
                self.estado.erro and agora - self.estado.tentada_em < INTERVALO_NOVA_TENTATIVA_S
            ):
                return
            self.estado.tentada_em = agora
            try:
                aplicar(url)
            except Exception as e:  # noqa: BLE001 — a API continua no ar e o /health mostra o erro
                self.estado.erro = type(e).__name__
                log.warning("migração automática falhou: %s", self.estado.erro)
            else:
                self.estado = EstadoMigracao(concluida=True, tentada_em=agora)
