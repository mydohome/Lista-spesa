"""
Wrapper sottile sulla Batch API di Claude: invia un lotto di richieste,
controlla se è pronto, recupera i risultati quando lo è.

La Batch API elabora le richieste in modo asincrono (di solito entro
qualche minuto/ora, non istantaneo) a metà prezzo rispetto alle chiamate
dirette. Per questo lo script è diviso in due comandi separati (invia /
controlla): non ha senso tenere il container acceso ad aspettare.
"""

import os
from anthropic import Anthropic


def get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY non impostata: impossibile usare la Batch API. "
            "Impostala nel file .env di deploy/."
        )
    return Anthropic(api_key=api_key)


def invia_batch(client: Anthropic, richieste: list[dict]) -> str:
    """Invia il lotto di richieste e ritorna l'id del batch."""
    batch = client.messages.batches.create(requests=richieste)
    return batch.id


def stato_batch(client: Anthropic, batch_id: str):
    """Ritorna l'oggetto batch corrente (contiene processing_status e i
    conteggi di richieste completate/fallite)."""
    return client.messages.batches.retrieve(batch_id)


def batch_pronto(batch) -> bool:
    return batch.processing_status == "ended"


def recupera_risultati(client: Anthropic, batch_id: str):
    """Itera sui risultati del batch. Ogni elemento ha .custom_id e
    .result (con .result.type in {'succeeded', 'errored', 'expired', 'canceled'}).
    """
    return client.messages.batches.results(batch_id)
