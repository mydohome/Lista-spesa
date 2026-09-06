# Deploy dietro Nginx Proxy Manager

Stesso codice di `backend/` e `frontend/` nella root del repo — cambia solo
il compose. Nessuna porta pubblicata sull'host: unico ingresso è NPM
tramite `proxy-net`.

```
Internet → NPM → spesa-frontend:80 (proxy-net)
                        │
                        └──/api/*──→ spesa-backend:8000 (rete "backend", interna)
                                            │
                                            └──→ spesa-db:5432 (rete "backend", interna)
```

Il container `frontend` monta un nginx che serve i file statici e inoltra
tutte le chiamate `/api/*` al backend, raggiungibile per nome sulla rete
Docker interna `backend`. Solo `frontend` sta su `proxy-net`: è l'unico
container che NPM deve conoscere. `backend` e `db` sono su una rete
`internal: true`, irraggiungibili dall'esterno.

## Passi

1. Clona il repo sulla macchina, es. `/home/ubuntu/docker/lista-spesa`
2. `cd lista-spesa/deploy`
3. `cp .env.example .env` e valorizza `POSTGRES_PASSWORD` (e opzionalmente
   `ANTHROPIC_API_KEY`)
4. `docker compose up -d --build`
5. Verifica che il frontend sia su `proxy-net`:
   `docker network inspect proxy-net | grep spesa-frontend`
6. In NPM (via tunnel SSH su `127.0.0.1:81`), crea un Proxy Host:
   - Domain: es. `spesa.tuodominio.it`
   - Forward Hostname/IP: `spesa-frontend`
   - Forward Port: `80`
   - SSL: Let's Encrypt come per gli altri servizi

## Note

- `./db-data` (dentro `deploy/`) persiste i dati Postgres sull'host: fai
  backup di quella cartella per non perdere lista/prezzi tra un redeploy e
  l'altro.
- `../db/init.sql` viene eseguito SOLO al primo avvio (volume dati vuoto).
  Se modifichi lo schema con dati già presenti, serve una migrazione
  manuale.
- Un futuro scraper-worker va messo sulla rete `backend` (mai su
  `proxy-net`): deve solo scrivere sul db, non essere raggiungibile da fuori.
