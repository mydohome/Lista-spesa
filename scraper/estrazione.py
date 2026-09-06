"""
Manda le immagini di volantino a Claude (vision) chiedendo di individuare
SOLO i prodotti che ci interessano (config.PRODOTTI_TARGET), per tenere
sotto controllo sia i costi che le allucinazioni: il modello non deve
"inventare" un catalogo, deve solo dire se vede uno dei prodotti richiesti
e a che prezzo.
"""

import os
import json
import base64
from anthropic import Anthropic
from config import PRODOTTI_TARGET, DIMENSIONE_BATCH_IMMAGINI

MODEL = "claude-haiku-4-5-20251001"


def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY non impostata: impossibile usare Claude per "
            "l'estrazione. Impostala nel file .env di deploy/."
        )
    return Anthropic(api_key=api_key)


def _prompt_prodotti_target() -> str:
    righe = [
        f"- {p['nome_canonico']} ({p['marca']}, {p['formato']})"
        for p in PRODOTTI_TARGET
    ]
    return "\n".join(righe)


def _batch(lista: list, dimensione: int):
    for i in range(0, len(lista), dimensione):
        yield lista[i : i + dimensione]


def estrai_prezzi_da_immagini(immagini_bytes: list[bytes]) -> list[dict]:
    """Ritorna una lista di dict: {nome_canonico, marca, formato, prezzo,
    in_offerta}, solo per i prodotti EFFETTIVAMENTE trovati nelle immagini.
    """
    client = _client()
    trovati = []

    prompt_prodotti = _prompt_prodotti_target()

    for gruppo in _batch(immagini_bytes, DIMENSIONE_BATCH_IMMAGINI):
        content = [
            {
                "type": "text",
                "text": f"""Queste immagini sono pagine di un volantino di
supermercato italiano. Cerca SOLO questi prodotti specifici (per nome e
marca esatti, non prodotti simili o di altre marche):

{prompt_prodotti}

Se trovi uno di questi prodotti nelle immagini, con relativo prezzo,
rispondi con un array JSON (e SOLO quello, nessun testo aggiuntivo, niente
backtick) con oggetti in questo formato:
[{{"nome_canonico": "...", "marca": "...", "formato": "...", "prezzo": 1.23, "in_offerta": true}}]

Se non trovi NESSUNO di questi prodotti specifici in queste immagini,
rispondi con un array vuoto: []

Usa ESATTAMENTE nome_canonico, marca e formato come scritti sopra (non
riformulare). "prezzo" è il prezzo finale in euro (se c'è uno sconto,
usa il prezzo scontato). "in_offerta" è true se il prodotto è in
promozione/sconto, false altrimenti.""",
            }
        ]
        for img_bytes in gruppo:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.b64encode(img_bytes).decode("utf-8"),
                    },
                }
            )

        risposta = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )
        testo = risposta.content[0].text.strip()
        try:
            risultati = json.loads(testo)
            if isinstance(risultati, list):
                trovati.extend(risultati)
        except json.JSONDecodeError:
            print(f"  [avviso] risposta non-JSON ignorata: {testo[:200]}")

    return trovati
