# Lista spesa — confronto prezzi multi-supermercato

Web app per gestire la lista della spesa: ogni prodotto viene confrontato
tra i supermercati di zona configurati, e la lista finale viene divisa in
sotto-liste ottimizzate per supermercato.

MVP con dati mock: il database parte popolato con 3 supermercati finti e 5
prodotti, per testare subito il flusso senza collegare fonti reali.

## Struttura

```
.
├── backend/        FastAPI: catalogo prodotti, matching, ottimizzazione liste
├── frontend/        HTML/CSS/JS puro + nginx (funge anche da reverse proxy verso il backend)
├── db/init.sql      Schema Postgres + dati mock
├── docker-compose.yml   Sviluppo locale (porte esposte)
└── deploy/          Produzione dietro Nginx Proxy Manager (nessuna porta esposta)
```

## Sviluppo locale

```bash
docker compose up --build
```

- Frontend: http://localhost:8080
- API + docs interattive: http://localhost:8000/docs
- Postgres: localhost:5432 (utente `spesa`, password `spesa_pass`)

## Deploy in produzione

Due opzioni, a seconda di dove vuoi raggiungere l'app:

- [`deploy/`](deploy/README-deploy.md) — dietro Nginx Proxy Manager, con
  dominio pubblico e HTTPS, nessuna porta esposta sull'host.
- [`deploy-lan/`](deploy-lan/README-lan.md) — solo rete locale (casa/ufficio),
  senza NPM né HTTPS: il frontend espone direttamente una porta sull'host.

## Normalizzazione prodotti via AI (opzionale)

`backend/app/ai_normalize.py` usa Claude Haiku per normalizzare nomi
prodotto grezzi (utile quando si collegheranno fonti reali tramite uno
scraper). Disattivo di default: si attiva impostando `ANTHROPIC_API_KEY`.
Senza, il sistema usa un fuzzy match locale gratuito (`backend/app/matching.py`).

## Come funziona l'ottimizzazione

Due strategie selezionabili dall'utente:
- **Risparmio massimo**: ogni prodotto va nel supermercato dove costa meno,
  anche su più negozi.
- **Un solo supermercato**: sceglie il singolo supermercato che copre più
  prodotti al costo totale minore.

## Prossimi passi

1. Scraper-worker reale per importare prezzi da fonti esterne (volantini,
   e-commerce dei supermercati) — verificando i Termini di Servizio di ogni
   fonte prima di automatizzare.
2. Selezione supermercati "di zona" via geolocalizzazione da UI.
3. Storico prezzi (lo schema `prezzi` è già pensato per non sovrascrivere,
   solo aggiungere righe con timestamp).
4. Autenticazione multi-utente, se serve condividere l'app.
