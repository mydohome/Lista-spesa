# Scraper prezzi (da TuttiPrezzi.it)

Estrae i prezzi dei prodotti del nostro catalogo dai volantini pubblicati su
[TuttiPrezzi.it](https://www.tuttiprezzi.it), un aggregatore che pubblica i
volantini di molte catene come sequenze di immagini JPG.

**Copertura attuale**: 6 dei 7 supermercati (Carrefour Iper, Spazio Conad,
Pam, INCOOP/Coop, Pewex, Todis). **Eurospin non è coperto** — va gestito a
parte (es. sito ufficiale eurospin.it, o inserimento manuale).

## Come funziona

1. Scarica la pagina della catena su TuttiPrezzi.it
2. Isola le immagini del volantino **attualmente attivo** (si ferma al primo
   commento HTML o link "volantino precedente", per non mischiare prezzi
   vecchi con quelli correnti)
3. Manda le immagini a Claude (vision, modello Haiku) chiedendo di cercare
   SOLO i prodotti già nel nostro catalogo (vedi `config.py`) — non un
   catalogo generico, per tenere bassi i costi e il rischio di errori
4. Salva nel database solo i prezzi dei prodotti che matchano ESATTAMENTE
   nome/marca/formato già presenti in tabella `prodotti`

## Uso

Prima di tutto, un test **senza scrivere nel database** (dry-run), su un
solo supermercato:

```bash
docker compose run --rm scraper python estrai_prezzi.py --supermercato Pewex --dry-run
```

Se l'output ti sembra corretto, rilancialo senza `--dry-run` per salvare
davvero, oppure senza `--supermercato` per farli tutti:

```bash
docker compose run --rm scraper python estrai_prezzi.py
```

Richiede `ANTHROPIC_API_KEY` impostata nel `.env` (stesso file usato dal
backend).

## Limiti conosciuti, onestamente

- **Il parsing HTML è fragile per natura**: si basa sulla struttura attuale
  di TuttiPrezzi.it (osservata il 06/09/2026). Se il sito cambia layout,
  lo script può smettere di trovare immagini — si accorgerà da solo e
  stamperà un avviso invece di inventare dati, ma andrà aggiornato.
- **Il disclaimer del sito stesso** dice che le offerte potrebbero non
  essere valide in tutti i punti vendita elencati: i prezzi sono indicativi
  per la catena/formato di negozio, non garantiti per il singolo indirizzo.
- **Non è automatico**: va lanciato manualmente (o schedulato tu con un
  cron esterno) — non gira in background da solo. Consigliato: una volta
  ogni 1-2 settimane, quando escono i nuovi volantini.
- **Nessuna verifica automatica di sanità dei prezzi**: se Claude legge
  male un prezzo da un'immagine sfocata, quel prezzo entra comunque nel
  database. Controlla ogni tanto i risultati con occhio critico, specie le
  prime volte.

## Costi

Claude fattura le immagini in base ai **pixel**, non al peso del file. Le
pagine di volantino scaricate sono spesso a piena risoluzione (es.
1700×2400px = ~5.400 token per immagine). Lo scraper le ridimensiona
automaticamente (lato massimo 1024px, vedi `LATO_MASSIMO_IMMAGINE_PX` in
`config.py`) prima di inviarle: la stessa pagina scende a ~980 token,
circa **5-6 volte più economica**, senza perdita pratica di leggibilità dei
prezzi stampati.

Con Claude Haiku, immagini ridimensionate e volantini di poche decine di
pagine, un giro completo sui 6 supermercati coperti resta nell'ordine di
**pochi centesimi di dollaro** in totale, non per supermercato.

Se in futuro i costi dovessero comunque preoccupare, altre leve disponibili
(non ancora implementate):
- alzare `DIMENSIONE_BATCH_IMMAGINI` per fare meno chiamate (rischio: il
  modello "perde" prodotti su troppe pagine insieme)
- scaricare solo le pagine centrali del volantino (dove tipicamente stanno
  alimentari e bevande, saltando copertina/retro con info legali) invece
  di tutte le pagine
- abbassare ulteriormente `LATO_MASSIMO_IMMAGINE_PX` (es. 768px): rischio
  di perdere leggibilità su prezzi scritti piccoli
