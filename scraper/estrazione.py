"""
Costruisce le richieste per la Batch API di Claude (elaborazione asincrona,
50% più economica sia in input che in output rispetto alle chiamate
dirette — perfetta per questo scraper, che non ha bisogno di risposte
immediate) e interpreta i risultati una volta pronti.
"""

import json
import base64
import io
import re
from PIL import Image
from config import PRODOTTI_TARGET, DIMENSIONE_BATCH_IMMAGINI, LATO_MASSIMO_IMMAGINE_PX

MODEL = "claude-haiku-4-5-20251001"


def _ridimensiona_immagine(img_bytes: bytes, lato_massimo: int) -> bytes:
    """Ridimensiona l'immagine così che il lato più lungo sia al massimo
    'lato_massimo' pixel, mantenendo le proporzioni. Claude fattura le
    immagini in base ai pixel: questo passaggio tiene bassi i costi senza
    perdere la leggibilità dei prezzi stampati.
    """
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = img.convert("RGB")
        larghezza, altezza = img.size
        lato_attuale = max(larghezza, altezza)
        if lato_attuale > lato_massimo:
            scala = lato_massimo / lato_attuale
            nuova_dimensione = (int(larghezza * scala), int(altezza * scala))
            img = img.resize(nuova_dimensione, Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
    except Exception as e:
        print(f"  [avviso] ridimensionamento immagine fallito, uso originale: {e}")
        return img_bytes


def _prompt_prodotti_target() -> str:
    righe = [
        f"- {p['nome_canonico']} ({p['marca']}, {p['formato']})"
        for p in PRODOTTI_TARGET
    ]
    return "\n".join(righe)


def _batch(lista: list, dimensione: int):
    for i in range(0, len(lista), dimensione):
        yield lista[i : i + dimensione]


def sanitizza_custom_id(testo: str) -> str:
    """La Batch API richiede custom_id che matchino [a-zA-Z0-9_-]{1,64}."""
    pulito = re.sub(r"[^a-zA-Z0-9_-]", "_", testo)
    return pulito[:64]


def costruisci_richieste_batch(nome_supermercato: str, immagini_bytes: list[bytes]) -> list[dict]:
    """Ritorna una lista di richieste pronte per client.messages.batches.create(),
    una per ogni gruppo di immagini. Ogni richiesta ha un custom_id univoco
    che include il nome del supermercato e l'indice del gruppo, per poter
    riassociare i risultati in seguito.
    """
    richieste = []
    prompt_prodotti = _prompt_prodotti_target()
    nome_sanitizzato = sanitizza_custom_id(nome_supermercato)

    for indice, gruppo in enumerate(_batch(immagini_bytes, DIMENSIONE_BATCH_IMMAGINI)):
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
            img_ridotta = _ridimensiona_immagine(img_bytes, LATO_MASSIMO_IMMAGINE_PX)
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.b64encode(img_ridotta).decode("utf-8"),
                    },
                }
            )

        richieste.append(
            {
                "custom_id": f"{nome_sanitizzato}__{indice}",
                "params": {
                    "model": MODEL,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": content}],
                },
            }
        )

    return richieste


def interpreta_testo_risultato(testo: str) -> list[dict]:
    """Converte il testo di risposta di un singolo risultato del batch in
    una lista di prodotti trovati (lista vuota se non parsabile o vuota).
    """
    try:
        risultati = json.loads(testo.strip())
        return risultati if isinstance(risultati, list) else []
    except json.JSONDecodeError:
        print(f"  [avviso] risposta non-JSON ignorata: {testo[:200]}")
        return []
