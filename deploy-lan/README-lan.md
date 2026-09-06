# Deploy semplice in LAN (senza NPM)

Per quando la macchina è già isolata nella rete locale (casa/ufficio) e non
serve un dominio pubblico, HTTPS, o passare da un reverse proxy: il
frontend espone direttamente una porta sull'host.

```
LAN → http://<ip-macchina>:8080 → spesa-frontend (nginx)
                                        │
                                        └──/api/*──→ spesa-backend:8000 (rete interna)
                                                            │
                                                            └──→ spesa-db:5432 (rete interna)
```

Backend e db restano su una rete Docker dedicata, non raggiungibili
direttamente da altri dispositivi in LAN — solo il frontend è esposto.

## Passi

1. Clona il repo sulla macchina
2. `cd Lista-spesa/deploy-lan`
3. `cp .env.example .env` e imposta `POSTGRES_PASSWORD`
4. `docker compose up -d --build`
5. Da un altro dispositivo in LAN: `http://<ip-della-macchina>:8080`

Per trovare l'IP della macchina: `ip addr show` (Linux) o `hostname -I`.

## Quando NON usare questo compose

- Se vuoi raggiungere l'app anche da fuori casa/ufficio → usa `deploy/`
  (dietro Nginx Proxy Manager, con dominio e HTTPS).
- Se sulla stessa macchina giri già altri servizi con NPM sulla porta 80/443
  → va bene comunque, questo compose non tocca quelle porte (usa 8080).

## Note

- Nessun HTTPS: va bene in LAN fidata, non esporre questa porta su internet
  (es. non aprirla sul router).
- `./db-data` persiste i dati Postgres sull'host.
- Se la porta 8080 è già occupata, cambia il primo numero in
  `docker-compose.yml` (es. `"8090:80"`), non il secondo.
