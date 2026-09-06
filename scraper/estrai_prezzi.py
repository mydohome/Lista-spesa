"""
Usa la Batch API di Claude (50% più economica, elaborazione asincrona) per
estrarre i prezzi dei prodotti target dai volantini di TuttiPrezzi.it.

USO (due passi separati, perché il batch non è istantaneo):

    1) Scarica i volantini, costruisce le richieste e le invia:
       python estrai_prezzi.py invia
       python estrai_prezzi.py invia --supermercato Pewex   # solo uno, utile per test

    2) Più tardi (minuti/ore dopo), controlla se è pronto e salva i risultati:
       python estrai_prezzi.py controlla
       python estrai_prezzi.py controlla --dry-run          # stampa senza scrivere nel database

Lo stato del batch in corso (id + a quale supermercato appartiene ogni
richiesta) viene salvato in stato_batch.json dentro questa cartella, così
"controlla" può essere lanciato in un container/momento diverso da "invia".
"""

import os
import sys
import json
import argparse
import psycopg2
import psycopg2.extras

from config import SUPERMERCATI_TUTTIPREZZI, MAX_PAGINE_PER_VOLANTINO
from volantino_fetcher import scarica_html, estrai_immagini_volantino_attivo, scarica_immagine
from estrazione import costruisci_richieste_batch, interpreta_testo_risultato
from batch_manager import get_client, invia_batch, stato_batch, batch_pronto, recupera_risultati

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://spesa:spesa_pass@spesa-db:5432/spesa_db"
)
FILE_STATO = os.path.join(os.path.dirname(__file__), "stato_batch.json")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def trova_id_supermercato(cur, nome: str):
    cur.execute("SELECT id FROM supermercati WHERE nome = %s", (nome,))
    riga = cur.fetchone()
    return riga["id"] if riga else None


def trova_id_prodotto(cur, nome_canonico: str, marca: str, formato: str):
    cur.execute(
        "SELECT id FROM prodotti WHERE nome_canonico = %s AND marca = %s AND formato = %s",
        (nome_canonico, marca, formato),
    )
    riga = cur.fetchone()
    return riga["id"] if riga else None


def salva_prezzo(cur, prodotto_id: int, supermercato_id: int, prezzo: float, in_offerta: bool):
    cur.execute(
        "INSERT INTO prezzi (prodotto_id, supermercato_id, prezzo, in_offerta) VALUES (%s, %s, %s, %s)",
        (prodotto_id, supermercato_id, prezzo, in_offerta),
    )


# ---------------------------------------------------------------- INVIA ----

def comando_invia(nome_singolo_supermercato: str | None):
    supermercati = SUPERMERCATI_TUTTIPREZZI
    if nome_singolo_supermercato:
        if nome_singolo_supermercato not in supermercati:
            print(f"Supermercato non configurato: {nome_singolo_supermercato}")
            print(f"Disponibili: {', '.join(supermercati.keys())}")
            sys.exit(1)
        supermercati = {nome_singolo_supermercato: supermercati[nome_singolo_supermercato]}

    tutte_le_richieste = []
    mappa_custom_id_supermercato = {}

    for nome_supermercato, config in supermercati.items():
        print(f"\n=== {nome_supermercato} ===")
        print(f"Scarico {config['url']} ...")
        try:
            html = scarica_html(config["url"])
        except Exception as e:
            print(f"  [errore] impossibile scaricare la pagina: {e}")
            continue

        immagini_url = estrai_immagini_volantino_attivo(html, MAX_PAGINE_PER_VOLANTINO)
        if not immagini_url:
            print("  [avviso] nessuna immagine di volantino trovata (struttura pagina cambiata?)")
            continue
        print(f"  Trovate {len(immagini_url)} pagine di volantino attivo. Scarico le immagini...")

        immagini_bytes = []
        for url in immagini_url:
            try:
                immagini_bytes.append(scarica_immagine(url))
            except Exception as e:
                print(f"  [avviso] immagine non scaricata ({url}): {e}")

        if not immagini_bytes:
            print("  [errore] nessuna immagine scaricata con successo.")
            continue

        richieste = costruisci_richieste_batch(nome_supermercato, immagini_bytes)
        print(f"  Preparate {len(richieste)} richieste batch.")
        for r in richieste:
            mappa_custom_id_supermercato[r["custom_id"]] = nome_supermercato
        tutte_le_richieste.extend(richieste)

    if not tutte_le_richieste:
        print("\nNessuna richiesta da inviare (tutti i download falliti?). Interrompo.")
        sys.exit(1)

    print(f"\nInvio {len(tutte_le_richieste)} richieste alla Batch API...")
    client = get_client()
    batch_id = invia_batch(client, tutte_le_richieste)

    with open(FILE_STATO, "w") as f:
        json.dump({"batch_id": batch_id, "mappa_custom_id_supermercato": mappa_custom_id_supermercato}, f)

    print(f"Batch inviato: {batch_id}")
    print(f"Stato salvato in {FILE_STATO}")
    print("\nTra qualche minuto, esegui:  python estrai_prezzi.py controlla")


# -------------------------------------------------------------- CONTROLLA --

def comando_controlla(dry_run: bool):
    if not os.path.exists(FILE_STATO):
        print(f"Nessun batch in corso (file {FILE_STATO} non trovato).")
        print("Lancia prima:  python estrai_prezzi.py invia")
        sys.exit(1)

    with open(FILE_STATO) as f:
        stato = json.load(f)
    batch_id = stato["batch_id"]
    mappa = stato["mappa_custom_id_supermercato"]

    client = get_client()
    batch = stato_batch(client, batch_id)
    print(f"Batch {batch_id}: stato = {batch.processing_status}")
    print(f"  completate: {batch.request_counts.succeeded}, "
          f"in corso: {batch.request_counts.processing}, "
          f"errori: {batch.request_counts.errored}")

    if not batch_pronto(batch):
        print("\nIl batch non è ancora pronto. Riprova tra un po'.")
        return

    print("\nBatch pronto. Recupero i risultati...")
    trovati_per_supermercato: dict[str, list[dict]] = {}

    for risultato in recupera_risultati(client, batch_id):
        nome_supermercato = mappa.get(risultato.custom_id, "?")
        if risultato.result.type != "succeeded":
            print(f"  [avviso] richiesta {risultato.custom_id} ({nome_supermercato}): {risultato.result.type}")
            continue
        testo = risultato.result.message.content[0].text
        prodotti_trovati = interpreta_testo_risultato(testo)
        if prodotti_trovati:
            trovati_per_supermercato.setdefault(nome_supermercato, []).extend(prodotti_trovati)

    if not trovati_per_supermercato:
        print("Nessun prodotto target trovato in nessun volantino.")
        return

    for nome_supermercato, trovati in trovati_per_supermercato.items():
        print(f"\n=== {nome_supermercato}: {len(trovati)} prodotti trovati ===")
        for t in trovati:
            flag = " (OFFERTA)" if t.get("in_offerta") else ""
            print(f"    - {t.get('nome_canonico')} {t.get('marca')} {t.get('formato')}: € {t.get('prezzo')}{flag}")

    if dry_run:
        print("\n[dry-run] non scrivo nel database.")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            totale_salvati = 0
            for nome_supermercato, trovati in trovati_per_supermercato.items():
                supermercato_id = trova_id_supermercato(cur, nome_supermercato)
                if supermercato_id is None:
                    print(f"  [errore] supermercato '{nome_supermercato}' non trovato nel database.")
                    continue
                for t in trovati:
                    prodotto_id = trova_id_prodotto(
                        cur, t.get("nome_canonico", ""), t.get("marca", ""), t.get("formato", "")
                    )
                    if prodotto_id is None:
                        print(f"  [avviso] prodotto non in catalogo, ignorato: {t}")
                        continue
                    salva_prezzo(cur, prodotto_id, supermercato_id, float(t["prezzo"]), bool(t.get("in_offerta", False)))
                    totale_salvati += 1
            conn.commit()
            print(f"\nSalvati {totale_salvati} prezzi nel database.")
    finally:
        conn.close()

    os.remove(FILE_STATO)
    print(f"Rimosso {FILE_STATO} (batch completato).")


def main():
    parser = argparse.ArgumentParser(description="Estrae prezzi dai volantini TuttiPrezzi.it via Batch API")
    sottocomandi = parser.add_subparsers(dest="comando", required=True)

    p_invia = sottocomandi.add_parser("invia", help="Scarica i volantini e invia il batch")
    p_invia.add_argument("--supermercato", help="Nome esatto di un solo supermercato")

    p_controlla = sottocomandi.add_parser("controlla", help="Controlla lo stato e salva i risultati se pronti")
    p_controlla.add_argument("--dry-run", action="store_true", help="Non scrivere nel database")

    args = parser.parse_args()

    if args.comando == "invia":
        comando_invia(args.supermercato)
    elif args.comando == "controlla":
        comando_controlla(args.dry_run)


if __name__ == "__main__":
    main()
