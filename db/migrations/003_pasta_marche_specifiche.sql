-- Sostituisce il prodotto mock "Pasta spaghetti n.5 Barilla" con 4 marchi
-- specifici richiesti: Rummo, La Molisana, Armando, Garofalo.
--
-- ATTENZIONE: cancella anche i prezzi collegati alla pasta Barilla (cascade)
-- e, se presente, la relativa voce nella lista della spesa attuale.
--
-- Applicala con:
--   cat db/migrations/003_pasta_marche_specifiche.sql | \
--     docker exec -i spesa-db psql -U spesa -d spesa_db

BEGIN;

DELETE FROM prodotti
WHERE nome_canonico = 'Pasta spaghetti n.5' AND marca = 'Barilla';

INSERT INTO prodotti (nome_canonico, marca, categoria, formato) VALUES
    ('Pasta spaghetti n.5', 'Rummo', 'Pasta', '500g'),
    ('Pasta spaghetti n.5', 'La Molisana', 'Pasta', '500g'),
    ('Pasta spaghetti n.5', 'Armando', 'Pasta', '500g'),
    ('Pasta spaghetti n.5', 'Garofalo', 'Pasta', '500g')
ON CONFLICT (nome_canonico, marca, formato) DO NOTHING;

COMMIT;
