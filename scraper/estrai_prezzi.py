"""
Script principale: per ciascun supermercato configurato, scarica il
volantino corrente da TuttiPrezzi.it, cerca i prodotti target con Claude
vision, e salva i prezzi trovati nel database.

USO:
    python estrai_prezzi.py                        # tutti i supermercati configurati
    python estrai_prezzi.py --supermercato Pewex    # solo uno (utile per test)
    python estrai_prezzi.py --dry-run               # scarica ed estrae, ma NON scrive nel database

Va eseguito con ANTHROPIC_API_KEY e DATABASE_URL nell'ambiente (il
Dockerfile del progetto principale già lo fa se lanciato via docker compose,
vedi README della cartella scraper/).
"""

import os
import sys
import argparse
import psycopg2
import psycopg2.extras

from config import SUPERMERCATI_TUTTIPREZZI, MAX_PAGINE_PER_VOLANTINO
from volantino_fetcher import scarica_html, estrai_immagini_volantino_attivo, scarica_immagine
from estrazione import estrai_prezzi_da_immagini

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://spesa:spesa_pass@spesa-db:5432/spesa_db"
)


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def trova_id_supermercato(cur, nome: str) -> int | None:
    cur.execute("SELECT id FROM supermercati WHERE nome = %s", (nome,))
    riga = cur.fetchone()
    return riga["id"] if riga else None


def trova_id_prodotto(cur, nome_canonico: str, marca: str, formato: str) -> int | None:
    cur.execute(
        "SELECT id FROM prodotti WHERE nome_canonico = %s AND marca = %s AND formato = %s",
        (nome_canonico, marca, formato),
    )
    riga = cur.fetchone()
    return riga["id"] if riga else None


def salva_prezzo(cur, prodotto_id: int, supermercato_id: int, prezzo: float, in_offerta: bool):
    cur.execute(
        """
        INSERT INTO prezzi (prodotto_id, supermercato_id, prezzo, in_offerta)
        VALUES (%s, %s, %s, %s)
        """,
        (prodotto_id, supermercato_id, prezzo, in_offerta),
    )


def elabora_supermercato(nome_supermercato: str, config: dict, dry_run: bool):
    print(f"\n=== {nome_supermercato} ===")
    print(f"Scarico {config['url']} ...")
    try:
        html = scarica_html(config["url"])
    except Exception as e:
        print(f"  [errore] impossibile scaricare la pagina: {e}")
        return

    immagini_url = estrai_immagini_volantino_attivo(html, MAX_PAGINE_PER_VOLANTINO)
    if not immagini_url:
        print("  [avviso] nessuna immagine di volantino trovata (struttura pagina cambiata?)")
        return
    print(f"  Trovate {len(immagini_url)} pagine di volantino attivo.")

    print("  Scarico le immagini...")
    immagini_bytes = []
    for url in immagini_url:
        try:
            immagini_bytes.append(scarica_immagine(url))
        except Exception as e:
            print(f"  [avviso] immagine non scaricata ({url}): {e}")

    if not immagini_bytes:
        print("  [errore] nessuna immagine scaricata con successo.")
        return

    print(f"  Analizzo {len(immagini_bytes)} immagini con Claude...")
    trovati = estrai_prezzi_da_immagini(immagini_bytes)

    if not trovati:
        print("  Nessun prodotto target trovato in questo volantino.")
        return

    print(f"  Trovati {len(trovati)} prodotti target:")
    for t in trovati:
        flag = " (OFFERTA)" if t.get("in_offerta") else ""
        print(f"    - {t.get('nome_canonico')} {t.get('marca')} {t.get('formato')}: € {t.get('prezzo')}{flag}")

    if dry_run:
        print("  [dry-run] non scrivo nel database.")
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            supermercato_id = trova_id_supermercato(cur, nome_supermercato)
            if supermercato_id is None:
                print(f"  [errore] supermercato '{nome_supermercato}' non trovato nel database.")
                return

            salvati = 0
            for t in trovati:
                prodotto_id = trova_id_prodotto(
                    cur, t.get("nome_canonico", ""), t.get("marca", ""), t.get("formato", "")
                )
                if prodotto_id is None:
                    print(f"  [avviso] prodotto non in catalogo, ignorato: {t}")
                    continue
                salva_prezzo(
                    cur, prodotto_id, supermercato_id,
                    float(t["prezzo"]), bool(t.get("in_offerta", False)),
                )
                salvati += 1
            conn.commit()
            print(f"  Salvati {salvati} prezzi nel database.")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Estrae prezzi dai volantini TuttiPrezzi.it")
    parser.add_argument("--supermercato", help="Nome esatto di un solo supermercato da elaborare")
    parser.add_argument("--dry-run", action="store_true", help="Non scrivere nel database")
    args = parser.parse_args()

    if args.supermercato:
        if args.supermercato not in SUPERMERCATI_TUTTIPREZZI:
            print(f"Supermercato non configurato: {args.supermercato}")
            print(f"Disponibili: {', '.join(SUPERMERCATI_TUTTIPREZZI.keys())}")
            sys.exit(1)
        elabora_supermercato(args.supermercato, SUPERMERCATI_TUTTIPREZZI[args.supermercato], args.dry_run)
    else:
        for nome, config in SUPERMERCATI_TUTTIPREZZI.items():
            elabora_supermercato(nome, config, args.dry_run)


if __name__ == "__main__":
    main()
