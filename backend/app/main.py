from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import get_conn
from .matching import cerca_prodotti
from .ottimizzazione import ottimizza

app = FastAPI(title="Spesa Smart API")

# In sviluppo locale/Docker su rete privata: CORS aperto per semplicità.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NuovaVoceLista(BaseModel):
    prodotto_id: int
    quantita: int = 1


class StrategiaRichiesta(BaseModel):
    strategia: str = "risparmio_massimo"  # oppure "minimo_supermercati"


@app.get("/api/supermercati")
def elenco_supermercati():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM supermercati WHERE attivo = TRUE ORDER BY nome")
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/api/prodotti/cerca")
def cerca(q: str):
    if not q or len(q.strip()) < 2:
        return []
    return cerca_prodotti(q)


@app.get("/api/lista")
def leggi_lista():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT l.id AS lista_id, l.quantita, l.comprato,
                       p.id AS prodotto_id, p.nome_canonico, p.marca, p.formato
                FROM lista_spesa l
                JOIN prodotti p ON p.id = l.prodotto_id
                ORDER BY l.aggiunto_il DESC
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


@app.post("/api/lista", status_code=201)
def aggiungi_a_lista(voce: NuovaVoceLista):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM prodotti WHERE id = %s", (voce.prodotto_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Prodotto non trovato")
            cur.execute(
                "INSERT INTO lista_spesa (prodotto_id, quantita) VALUES (%s, %s) RETURNING id",
                (voce.prodotto_id, voce.quantita),
            )
            nuovo_id = cur.fetchone()["id"]
            conn.commit()
            return {"id": nuovo_id}
    finally:
        conn.close()


@app.delete("/api/lista/{voce_id}", status_code=204)
def rimuovi_da_lista(voce_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM lista_spesa WHERE id = %s", (voce_id,))
            conn.commit()
    finally:
        conn.close()


@app.post("/api/lista/ottimizza")
def ottimizza_lista(richiesta: StrategiaRichiesta):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT l.prodotto_id, l.quantita, p.nome_canonico, p.marca
                FROM lista_spesa l
                JOIN prodotti p ON p.id = l.prodotto_id
                WHERE l.comprato = FALSE
                """
            )
            righe = cur.fetchall()
    finally:
        conn.close()

    if not righe:
        return {
            "strategia": richiesta.strategia,
            "liste_per_supermercato": {},
            "spesa_totale": 0.0,
            "risparmio_stimato": 0.0,
            "prodotti_senza_prezzo": [],
        }

    lista_items = [
        {
            "prodotto_id": r["prodotto_id"],
            "nome": f"{r['nome_canonico']} ({r['marca']})" if r["marca"] else r["nome_canonico"],
            "quantita": r["quantita"],
        }
        for r in righe
    ]
    return ottimizza(lista_items, strategia=richiesta.strategia)


@app.get("/api/health")
def health():
    return {"status": "ok"}
