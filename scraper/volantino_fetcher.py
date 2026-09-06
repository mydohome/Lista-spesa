"""
Scarica una pagina catena di TuttiPrezzi.it e ne estrae le URL delle
immagini del PRIMO volantino attivo (quello con le date "offerte dal...al...").

Le pagine di TuttiPrezzi.it, per come sono fatte, contengono spesso più
edizioni di volantino nello stesso file HTML: quella corrente in cima, e
altre più vecchie subito sotto, spesso racchiuse in commenti HTML
<!-- ... --> (quindi già "disattivate" visivamente, ma ancora presenti nel
codice sorgente). Per non confondere prezzi vecchi con quelli attuali,
prendiamo SOLO le immagini che compaiono prima del primo commento HTML o
del primo link "TORNA AL VOLANTINO PRECEDENTE" incontrato nel documento.

ATTENZIONE: questo parsing è stato scritto studiando la struttura della
pagina Carrefour e Pewex il 06/09/2026. Se il sito cambia struttura, questa
euristica può smettere di funzionare — in tal caso la funzione restituirà
una lista vuota o incompleta piuttosto che dati sbagliati, e va aggiornata.
"""

import requests
from bs4 import BeautifulSoup, Comment

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def scarica_html(url: str) -> str:
    risposta = requests.get(url, headers=HEADERS, timeout=20)
    risposta.raise_for_status()
    return risposta.text


def estrai_immagini_volantino_attivo(html: str, max_pagine: int) -> list[str]:
    """Ritorna la lista (ordinata) delle URL immagine del volantino corrente,
    fermandosi al primo commento HTML o al primo link 'volantino precedente'.
    """
    soup = BeautifulSoup(html, "lxml")
    body = soup.body or soup

    immagini = []
    for elemento in body.descendants:
        if isinstance(elemento, Comment):
            # Inizia un blocco archiviato/commentato: fermati qui.
            break

        nome_tag = getattr(elemento, "name", None)

        if nome_tag == "a":
            testo = (elemento.get_text() or "").upper()
            if "VOLANTINO PRECEDENTE" in testo or "VOLANTINO SUCCESSIVO" in testo:
                # Fine del primo blocco volantino.
                break

        if nome_tag == "img":
            src = elemento.get("src", "")
            if src.lower().endswith((".jpg", ".jpeg", ".png")):
                immagini.append(src)

        if len(immagini) >= max_pagine:
            break

    return immagini


def scarica_immagine(url: str) -> bytes:
    risposta = requests.get(url, headers=HEADERS, timeout=20)
    risposta.raise_for_status()
    return risposta.content
