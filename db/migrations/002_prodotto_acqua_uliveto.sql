-- Aggiunge il primo prodotto "reale" al catalogo (senza ancora i prezzi:
-- quelli li aggiungiamo con la prossima migrazione, una volta raccolti).
--
-- Applicala con:
--   cat db/migrations/002_prodotto_acqua_uliveto.sql | \
--     docker exec -i spesa-db psql -U spesa -d spesa_db

INSERT INTO prodotti (nome_canonico, marca, categoria, formato)
VALUES ('Acqua naturale', 'Uliveto', 'Bevande', 'confezione da 6 x 1,5L')
ON CONFLICT (nome_canonico, marca, formato) DO NOTHING;
