"""
Chiamate a Claude per due compiti, entrambi lato "scraper-worker" (batch,
non interattivo, per tenere sotto controllo costi e latenza):

1. normalizza_alias: dato un testo grezzo trovato su un sito/volantino,
   restituisce nome canonico, marca, categoria, formato in JSON.
2. sono_stesso_prodotto: dati due testi, stabilisce se descrivono lo stesso
   prodotto (usato per decidere se un alias va agganciato a un prodotto
   esistente o ne crea uno nuovo).

Questo file NON viene chiamato di default: lo scraper-worker (vedi
scraper/README.md) lo usa solo se ANTHROPIC_API_KEY è impostata. Senza
chiave, il sistema funziona comunque con il fuzzy match locale.
"""

import os
import json
from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"  # modello economico, sufficiente per questo compito

_client: Anthropic | None = None


def _get_client() -> Anthropic | None:
    global _client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    if _client is None:
        _client = Anthropic(api_key=api_key)
    return _client


def normalizza_alias(testo_grezzo: str) -> dict | None:
    """Es. input: 'Pasta Barilla 5 - 500 gr offerta'
    output: {"nome_canonico": "Pasta spaghetti n.5", "marca": "Barilla",
             "categoria": "Pasta", "formato": "500g"}
    """
    client = _get_client()
    if client is None:
        return None

    prompt = f"""Ricevi il nome di un prodotto alimentare così come appare su un
volantino o sito di supermercato italiano. Restituisci SOLO un oggetto JSON,
senza testo aggiuntivo né backtick, con questi campi:
- nome_canonico: nome breve e standard del prodotto (senza marca, senza formato)
- marca: la marca se presente, altrimenti null
- categoria: una categoria generale (es. Latticini, Pasta, Bevande, Pane, Frutta, Verdura, Carne, Pesce, Condimenti, Altro)
- formato: il formato/quantità (es. "1L", "500g", "confezione da 6"), altrimenti null

Testo: "{testo_grezzo}"
"""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    testo = resp.content[0].text.strip()
    try:
        return json.loads(testo)
    except json.JSONDecodeError:
        return None


def sono_stesso_prodotto(testo_a: str, testo_b: str) -> bool:
    client = _get_client()
    if client is None:
        return False

    prompt = f"""Questi due testi descrivono lo stesso prodotto alimentare
(stessa marca e formato, anche se scritti in modo diverso)?
Rispondi SOLO con "si" o "no".

Testo 1: "{testo_a}"
Testo 2: "{testo_b}"
"""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=5,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip().lower().startswith("s")
