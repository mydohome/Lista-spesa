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
import io
from PIL import Image
from anthropic import Anthropic
from config import PRODOTTI_TARGET, DIMENSIONE_BATCH_IMMAGINI, LATO_MASSIMO_IMMAGINE_PX

MODEL = "claude-haiku-4-5-20251001"


def _ridimensiona_immagine(img_bytes: bytes, lato_massimo: int) -> bytes:
    """Ridimensiona l'immagine così che il lato più lungo sia al massimo
    'lato_massimo' pixel, mantenendo le proporzioni. Claude fattura le
    immagini in base ai pixel: questo passaggio è il modo più efficace per
    tenere bassi i costi senza perdere la leggibilità dei prezzi stampati.
    """
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = img.convert("RGB")  # normalizza eventuali PNG con canale alpha
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
