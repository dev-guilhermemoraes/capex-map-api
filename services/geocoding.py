"""Cliente do serviço externo de geocoding (Nominatim / OpenStreetMap).

Documentação: https://nominatim.org/release-docs/latest/api/Search/
Política de uso: máx. 1 requisição e User-Agent identificando a aplicação.
"""
import logging
import os
import time
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "capex-map-mvp/1.0 (projeto academico)")
_ultima_chamada = 0.0


def geocodificar(cidade: str, uf: str) -> Optional[Tuple[float, float]]:
    """Retorna (latitude, longitude) da cidade/UF ou None se não encontrar."""
    global _ultima_chamada
    espera = 1.0 - (time.time() - _ultima_chamada)
    if espera > 0:
        time.sleep(espera)

    params = {
        "city": cidade,
        "state": uf,
        "country": "Brasil",
        "format": "json",
        "limit": 1,
    }
    try:
        resp = requests.get(NOMINATIM_URL, params=params,
                            headers={"User-Agent": USER_AGENT}, timeout=8)
        _ultima_chamada = time.time()
        resp.raise_for_status()
        dados = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Falha no geocoding de %s/%s: %s", cidade, uf, exc)
        return None

    if not dados:
        logger.info("Geocoding sem resultado para %s/%s", cidade, uf)
        return None
    return float(dados[0]["lat"]), float(dados[0]["lon"])
