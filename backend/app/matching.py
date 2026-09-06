"""
Matching tra il testo libero digitato dall'utente (o estratto da un volantino)
e il catalogo prodotti normalizzato.

Livello 1 (sempre attivo, gratis): fuzzy match locale con difflib su
nome_canonico + marca + alias già noti.

Livello 2 (opzionale, richiede ANTHROPIC_API_KEY): se il fuzzy match non
supera una soglia di confidenza, si chiede a Claude di decidere se un nuovo
alias osservato corrisponde a un prodotto esistente o è un prodotto nuovo.
Usato soprattutto dallo scraper-worker quando importa dati da fonti esterne,
non nel percorso interattivo dell'utente (per non introdurre latenza/costi
ad ogni digitazione).
"""

from difflib import SequenceMatcher
from typing import Optional
from .db import get_conn

SOGLIA_FUZZY = 0.55


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def cerca_prodotti(query: str, limit: int = 10) -> list[dict]:
    """Autocomplete: cerca prodotti nel catalogo che assomigliano alla query."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome_canonico, marca, categoria, formato FROM prodotti")
            prodotti = cur.fetchall()
    finally:
        conn.close()

    risultati = []
    for p in prodotti:
        testo_confronto = f"{p['nome_canonico']} {p['marca'] or ''}"
        score = _similarity(query, testo_confronto)
        # match "contiene" alza molto lo score, utile per query brevi tipo "latte"
        if query.lower().strip() in testo_confronto.lower():
            score = max(score, 0.8)
        if score >= SOGLIA_FUZZY:
            risultati.append({**p, "score": round(score, 2)})

    risultati.sort(key=lambda r: r["score"], reverse=True)
    return risultati[:limit]


def trova_prodotto_esatto(prodotto_id: int) -> Optional[dict]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM prodotti WHERE id = %s", (prodotto_id,))
            return cur.fetchone()
    finally:
        conn.close()
