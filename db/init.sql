-- Schema iniziale per la gestione lista spesa multi-supermercato

CREATE TABLE supermercati (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    indirizzo TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    fonte_prezzi TEXT,          -- URL volantino/e-commerce, o 'manuale'
    attivo BOOLEAN DEFAULT TRUE
);

-- Catalogo prodotti "normalizzato": un prodotto reale (es. "Latte intero 1L")
CREATE TABLE prodotti (
    id SERIAL PRIMARY KEY,
    nome_canonico TEXT NOT NULL,      -- es. "Latte intero 1L"
    marca TEXT,                       -- es. "Parmalat"
    categoria TEXT,                   -- es. "Latticini"
    formato TEXT,                     -- es. "1L", "500g"
    UNIQUE(nome_canonico, marca, formato)
);

-- Alias/varianti di nome per lo stesso prodotto, trovati su fonti diverse
CREATE TABLE prodotti_alias (
    id SERIAL PRIMARY KEY,
    prodotto_id INTEGER REFERENCES prodotti(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    fonte TEXT                        -- da quale supermercato/sito arriva l'alias
);

-- Prezzo di un prodotto in un supermercato in un dato momento
CREATE TABLE prezzi (
    id SERIAL PRIMARY KEY,
    prodotto_id INTEGER REFERENCES prodotti(id) ON DELETE CASCADE,
    supermercato_id INTEGER REFERENCES supermercati(id) ON DELETE CASCADE,
    prezzo NUMERIC(10,2) NOT NULL,
    in_offerta BOOLEAN DEFAULT FALSE,
    rilevato_il TIMESTAMP DEFAULT NOW(),
    UNIQUE(prodotto_id, supermercato_id, rilevato_il)
);

-- Lista della spesa dell'utente (MVP: singolo utente, no auth)
CREATE TABLE lista_spesa (
    id SERIAL PRIMARY KEY,
    prodotto_id INTEGER REFERENCES prodotti(id) ON DELETE CASCADE,
    quantita INTEGER DEFAULT 1,
    aggiunto_il TIMESTAMP DEFAULT NOW(),
    comprato BOOLEAN DEFAULT FALSE
);

-- Indici utili per le query di confronto prezzo più recente
CREATE INDEX idx_prezzi_prodotto ON prezzi(prodotto_id);
CREATE INDEX idx_prezzi_supermercato ON prezzi(supermercato_id);

-- Dati iniziali: supermercati reali in zona CAP 00139 Roma (Bufalotta / Porta
-- di Roma), entro 4km, catene diverse per un confronto prezzo significativo.
-- I prezzi sono ancora di esempio: vanno sostituiti con dati reali (scraper
-- o inserimento manuale) prima di fidarsi del confronto.
INSERT INTO supermercati (nome, indirizzo, lat, lng, fonte_prezzi) VALUES
    ('INCOOP (Coop)', 'Via Franco Enriquez 40, 00139 Roma', 41.9655199, 12.5291034, 'manuale'),
    ('Pewex', 'Via Umberto Barbaro 24, 00139 Roma', 41.9587000, 12.5383105, 'manuale'),
    ('SPAZIO CONAD (Porta di Roma)', 'Via Alberto Lionello 201, 00139 Roma', 41.9732906, 12.5407517, 'manuale'),
    ('Carrefour Iper', 'Via della Bufalotta 548, 00139 Roma', 41.9584203, 12.5488061, 'manuale'),
    ('Pam Bufalotta', 'Via di Passo Falzarego 19, 00139 Roma', 41.9520280, 12.5412944, 'manuale'),
    ('Eurospin', 'Viale Lina Cavalieri 58, 00139 Roma', 41.9635722, 12.5133040, 'manuale'),
    ('Todis', 'Via Emilio Teza 90/86, 00139 Roma', 41.9822756, 12.5632019, 'manuale');

INSERT INTO prodotti (nome_canonico, marca, categoria, formato) VALUES
    ('Latte intero', 'Parmalat', 'Latticini', '1L'),
    ('Pasta spaghetti n.5', 'Rummo', 'Pasta', '500g'),
    ('Pasta spaghetti n.5', 'La Molisana', 'Pasta', '500g'),
    ('Pasta spaghetti n.5', 'Armando', 'Pasta', '500g'),
    ('Pasta spaghetti n.5', 'Garofalo', 'Pasta', '500g'),
    ('Pane bianco', 'Generico', 'Pane', '500g'),
    ('Olio extravergine oliva', 'Monini', 'Condimenti', '1L'),
    ('Uova fresche', 'Generico', 'Uova', 'confezione da 6'),
    ('Acqua naturale', 'Uliveto', 'Bevande', 'confezione da 6 x 1,5L');

-- Prezzi di esempio SOLO per i prodotti di cui abbiamo già dati mock
-- (Latte, Pane, Olio, Uova). Pasta (4 marche) e Acqua Uliveto restano senza
-- prezzo finché non vengono inseriti quelli reali: meglio "nessun prezzo
-- trovato" in app che un numero inventato.
INSERT INTO prezzi (prodotto_id, supermercato_id, prezzo, in_offerta)
SELECT p.id, s.id, v.prezzo, v.in_offerta
FROM (VALUES
    ('Latte intero',              'INCOOP (Coop)',                  1.38, FALSE),
    ('Latte intero',              'Pewex',                           1.32, FALSE),
    ('Latte intero',              'SPAZIO CONAD (Porta di Roma)',   1.35, FALSE),
    ('Latte intero',              'Carrefour Iper',                  1.29, TRUE),
    ('Latte intero',              'Pam Bufalotta',                   1.40, FALSE),
    ('Latte intero',              'Eurospin',                        1.19, FALSE),
    ('Latte intero',              'Todis',                           1.22, TRUE),

    ('Pane bianco',               'INCOOP (Coop)',                  1.15, FALSE),
    ('Pane bianco',               'Pewex',                           1.05, FALSE),
    ('Pane bianco',               'SPAZIO CONAD (Porta di Roma)',   1.20, FALSE),
    ('Pane bianco',               'Carrefour Iper',                  1.10, FALSE),
    ('Pane bianco',               'Pam Bufalotta',                   1.18, FALSE),
    ('Pane bianco',               'Eurospin',                        0.95, FALSE),
    ('Pane bianco',               'Todis',                           0.98, TRUE),

    ('Olio extravergine oliva',   'INCOOP (Coop)',                  7.10, FALSE),
    ('Olio extravergine oliva',   'Pewex',                           6.80, FALSE),
    ('Olio extravergine oliva',   'SPAZIO CONAD (Porta di Roma)',   6.95, FALSE),
    ('Olio extravergine oliva',   'Carrefour Iper',                  6.50, TRUE),
    ('Olio extravergine oliva',   'Pam Bufalotta',                   7.20, FALSE),
    ('Olio extravergine oliva',   'Eurospin',                        5.99, FALSE),
    ('Olio extravergine oliva',   'Todis',                           6.10, FALSE),

    ('Uova fresche',              'INCOOP (Coop)',                  2.15, FALSE),
    ('Uova fresche',              'Pewex',                           2.05, FALSE),
    ('Uova fresche',              'SPAZIO CONAD (Porta di Roma)',   2.20, FALSE),
    ('Uova fresche',              'Carrefour Iper',                  1.99, FALSE),
    ('Uova fresche',              'Pam Bufalotta',                   2.25, FALSE),
    ('Uova fresche',              'Eurospin',                        1.79, TRUE),
    ('Uova fresche',              'Todis',                           1.85, FALSE)
) AS v(nome_prodotto, nome_supermercato, prezzo, in_offerta)
JOIN prodotti p ON p.nome_canonico = v.nome_prodotto AND p.marca IN ('Parmalat', 'Generico', 'Monini')
JOIN supermercati s ON s.nome = v.nome_supermercato;

