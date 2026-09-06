-- Migrazione: sostituisce i supermercati "finti" (Conad Centro, Esselunga
-- Nord, Coop Stazione) con 7 supermercati reali in zona CAP 00139 Roma
-- (Bufalotta / Porta di Roma), entro 4km, di catene diverse.
--
-- ATTENZIONE: cancella anche i prezzi collegati ai vecchi supermercati
-- (cascade), non la lista_spesa dell'utente né il catalogo prodotti.
-- I nuovi prezzi inseriti sono ANCORA DI ESEMPIO — vanno sostituiti con
-- dati reali (inserimento manuale o scraper) prima di fidarsi del confronto.
--
-- Applicala con:
--   cat db/migrations/001_supermercati_reali_00139.sql | \
--     docker exec -i spesa-db psql -U spesa -d spesa_db

BEGIN;

-- RESTART IDENTITY riporta il contatore degli id a 1 (altrimenti i nuovi
-- supermercati partirebbero da id 4 in poi, rompendo il join sui prezzi qui
-- sotto). CASCADE ripulisce anche i vecchi prezzi collegati (verranno
-- reinseriti subito dopo) — non tocca lista_spesa né prodotti.
TRUNCATE TABLE supermercati RESTART IDENTITY CASCADE;

INSERT INTO supermercati (nome, indirizzo, lat, lng, fonte_prezzi) VALUES
    ('INCOOP (Coop)', 'Via Franco Enriquez 40, 00139 Roma', 41.9655199, 12.5291034, 'manuale'),
    ('Pewex', 'Via Umberto Barbaro 24, 00139 Roma', 41.9587000, 12.5383105, 'manuale'),
    ('SPAZIO CONAD (Porta di Roma)', 'Via Alberto Lionello 201, 00139 Roma', 41.9732906, 12.5407517, 'manuale'),
    ('Carrefour Iper', 'Via della Bufalotta 548, 00139 Roma', 41.9584203, 12.5488061, 'manuale'),
    ('Pam Bufalotta', 'Via di Passo Falzarego 19, 00139 Roma', 41.9520280, 12.5412944, 'manuale'),
    ('Eurospin', 'Viale Lina Cavalieri 58, 00139 Roma', 41.9635722, 12.5133040, 'manuale'),
    ('Todis', 'Via Emilio Teza 90/86, 00139 Roma', 41.9822756, 12.5632019, 'manuale');

-- Prezzi di esempio per i 5 prodotti già presenti nel catalogo, per ognuno
-- dei 7 nuovi supermercati (id assegnati nell'ordine di inserimento sopra:
-- 1=INCOOP, 2=Pewex, 3=SPAZIO CONAD, 4=Carrefour Iper, 5=Pam, 6=Eurospin, 7=Todis)
INSERT INTO prezzi (prodotto_id, supermercato_id, prezzo, in_offerta)
SELECT p.id, s.id, v.prezzo, v.in_offerta
FROM (VALUES
    ('Latte intero',              1, 1.38, FALSE),
    ('Latte intero',              2, 1.32, FALSE),
    ('Latte intero',              3, 1.35, FALSE),
    ('Latte intero',              4, 1.29, TRUE),
    ('Latte intero',              5, 1.40, FALSE),
    ('Latte intero',              6, 1.19, FALSE),
    ('Latte intero',              7, 1.22, TRUE),

    ('Pasta spaghetti n.5',       1, 0.92, FALSE),
    ('Pasta spaghetti n.5',       2, 0.89, FALSE),
    ('Pasta spaghetti n.5',       3, 0.95, FALSE),
    ('Pasta spaghetti n.5',       4, 0.85, FALSE),
    ('Pasta spaghetti n.5',       5, 0.99, FALSE),
    ('Pasta spaghetti n.5',       6, 0.75, TRUE),
    ('Pasta spaghetti n.5',       7, 0.79, FALSE),

    ('Pane bianco',               1, 1.15, FALSE),
    ('Pane bianco',               2, 1.05, FALSE),
    ('Pane bianco',               3, 1.20, FALSE),
    ('Pane bianco',               4, 1.10, FALSE),
    ('Pane bianco',               5, 1.18, FALSE),
    ('Pane bianco',               6, 0.95, FALSE),
    ('Pane bianco',               7, 0.98, TRUE),

    ('Olio extravergine oliva',   1, 7.10, FALSE),
    ('Olio extravergine oliva',   2, 6.80, FALSE),
    ('Olio extravergine oliva',   3, 6.95, FALSE),
    ('Olio extravergine oliva',   4, 6.50, TRUE),
    ('Olio extravergine oliva',   5, 7.20, FALSE),
    ('Olio extravergine oliva',   6, 5.99, FALSE),
    ('Olio extravergine oliva',   7, 6.10, FALSE),

    ('Uova fresche',              1, 2.15, FALSE),
    ('Uova fresche',              2, 2.05, FALSE),
    ('Uova fresche',              3, 2.20, FALSE),
    ('Uova fresche',              4, 1.99, FALSE),
    ('Uova fresche',              5, 2.25, FALSE),
    ('Uova fresche',              6, 1.79, TRUE),
    ('Uova fresche',              7, 1.85, FALSE)
) AS v(nome_prodotto, ordine_supermercato, prezzo, in_offerta)
JOIN prodotti p ON p.nome_canonico = v.nome_prodotto
JOIN supermercati s ON s.id = v.ordine_supermercato;

COMMIT;
