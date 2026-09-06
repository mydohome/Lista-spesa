"""
Dato l'elenco di prodotti in lista spesa e i relativi prezzi per
supermercato, produce le sotto-liste ottimizzate.

Due strategie:
- "risparmio_massimo": ogni prodotto va nel supermercato dove costa meno,
  anche se questo significa girare più negozi.
- "minimo_supermercati": si sceglie UN solo supermercato (o il minimo
  indispensabile) minimizzando la spesa totale, preferendo consolidare
  gli acquisti in pochi posti.

In entrambi i casi si calcola anche il risparmio stimato rispetto a fare
tutta la spesa nel supermercato più caro per quella lista, per dare
all'utente un numero concreto.
"""

from .db import get_conn


def _prezzi_lista(prodotto_ids: list[int]) -> dict:
    """Ritorna {prodotto_id: [{supermercato_id, nome, prezzo, in_offerta}, ...]}"""
    if not prodotto_ids:
        return {}
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (p.prodotto_id, p.supermercato_id)
                    p.prodotto_id, p.supermercato_id, s.nome AS supermercato_nome,
                    p.prezzo, p.in_offerta
                FROM prezzi p
                JOIN supermercati s ON s.id = p.supermercato_id
                WHERE p.prodotto_id = ANY(%s) AND s.attivo = TRUE
                ORDER BY p.prodotto_id, p.supermercato_id, p.rilevato_il DESC
                """,
                (prodotto_ids,),
            )
            righe = cur.fetchall()
    finally:
        conn.close()

    risultato: dict = {}
    for r in righe:
        risultato.setdefault(r["prodotto_id"], []).append(
            {
                "supermercato_id": r["supermercato_id"],
                "supermercato_nome": r["supermercato_nome"],
                "prezzo": float(r["prezzo"]),
                "in_offerta": r["in_offerta"],
            }
        )
    return risultato


def ottimizza(lista_items: list[dict], strategia: str = "risparmio_massimo") -> dict:
    """
    lista_items: [{"prodotto_id": int, "nome": str, "quantita": int}, ...]
    Ritorna: {
        "liste_per_supermercato": {supermercato_nome: [{prodotto, quantita, prezzo_unitario, subtotale}]},
        "spesa_totale": float,
        "risparmio_stimato": float,
        "prodotti_senza_prezzo": [nomi]
    }
    """
    prodotto_ids = [item["prodotto_id"] for item in lista_items]
    prezzi = _prezzi_lista(prodotto_ids)

    liste_per_supermercato: dict = {}
    spesa_totale = 0.0
    spesa_peggior_caso = 0.0
    prodotti_senza_prezzo = []

    if strategia == "risparmio_massimo":
        for item in lista_items:
            opzioni = prezzi.get(item["prodotto_id"])
            if not opzioni:
                prodotti_senza_prezzo.append(item["nome"])
                continue
            migliore = min(opzioni, key=lambda o: o["prezzo"])
            peggiore = max(opzioni, key=lambda o: o["prezzo"])
            quantita = item.get("quantita", 1)
            subtotale = round(migliore["prezzo"] * quantita, 2)

            liste_per_supermercato.setdefault(migliore["supermercato_nome"], []).append(
                {
                    "prodotto": item["nome"],
                    "quantita": quantita,
                    "prezzo_unitario": migliore["prezzo"],
                    "in_offerta": migliore["in_offerta"],
                    "subtotale": subtotale,
                }
            )
            spesa_totale += subtotale
            spesa_peggior_caso += round(peggiore["prezzo"] * quantita, 2)

    elif strategia == "minimo_supermercati":
        # Sceglie il singolo supermercato che copre più prodotti al costo totale minore
        supermercati_coinvolti = set()
        for opzioni in prezzi.values():
            for o in opzioni:
                supermercati_coinvolti.add((o["supermercato_id"], o["supermercato_nome"]))

        miglior_supermercato = None
        miglior_costo = None
        for s_id, s_nome in supermercati_coinvolti:
            costo = 0.0
            copertura = 0
            for item in lista_items:
                opzioni = prezzi.get(item["prodotto_id"], [])
                match = next((o for o in opzioni if o["supermercato_id"] == s_id), None)
                if match:
                    costo += match["prezzo"] * item.get("quantita", 1)
                    copertura += 1
            # preferisci il supermercato che copre più prodotti; a parità, il più economico
            if miglior_supermercato is None or (copertura, -costo) > (
                miglior_supermercato[1], -miglior_supermercato[2]
            ):
                miglior_supermercato = (s_nome, copertura, costo, s_id)
                miglior_costo = costo

        if miglior_supermercato:
            s_nome, _, _, s_id = miglior_supermercato
            for item in lista_items:
                opzioni = prezzi.get(item["prodotto_id"], [])
                match = next((o for o in opzioni if o["supermercato_id"] == s_id), None)
                if not match:
                    prodotti_senza_prezzo.append(item["nome"])
                    continue
                quantita = item.get("quantita", 1)
                subtotale = round(match["prezzo"] * quantita, 2)
                liste_per_supermercato.setdefault(s_nome, []).append(
                    {
                        "prodotto": item["nome"],
                        "quantita": quantita,
                        "prezzo_unitario": match["prezzo"],
                        "in_offerta": match["in_offerta"],
                        "subtotale": subtotale,
                    }
                )
                spesa_totale += subtotale

            # peggior caso per stima risparmio: prezzo più alto disponibile per prodotto
            for item in lista_items:
                opzioni = prezzi.get(item["prodotto_id"], [])
                if opzioni:
                    peggiore = max(opzioni, key=lambda o: o["prezzo"])
                    spesa_peggior_caso += round(peggiore["prezzo"] * item.get("quantita", 1), 2)

    risparmio_stimato = round(spesa_peggior_caso - spesa_totale, 2)

    return {
        "strategia": strategia,
        "liste_per_supermercato": liste_per_supermercato,
        "spesa_totale": round(spesa_totale, 2),
        "risparmio_stimato": max(risparmio_stimato, 0.0),
        "prodotti_senza_prezzo": prodotti_senza_prezzo,
    }
