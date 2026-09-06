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

-- Dati di esempio (mock) per partire subito senza scraping
INSERT INTO supermercati (nome, indirizzo, fonte_prezzi) VALUES
    ('Conad Centro', 'Via Roma 1', 'manuale'),
    ('Esselunga Nord', 'Via Milano 22', 'manuale'),
    ('Coop Stazione', 'Via Torino 5', 'manuale');

INSERT INTO prodotti (nome_canonico, marca, categoria, formato) VALUES
    ('Latte intero', 'Parmalat', 'Latticini', '1L'),
    ('Pasta spaghetti n.5', 'Barilla', 'Pasta', '500g'),
    ('Pane bianco', 'Generico', 'Pane', '500g'),
    ('Olio extravergine oliva', 'Monini', 'Condimenti', '1L'),
    ('Uova fresche', 'Generico', 'Uova', 'confezione da 6');

INSERT INTO prezzi (prodotto_id, supermercato_id, prezzo, in_offerta) VALUES
    (1, 1, 1.35, FALSE),
    (1, 2, 1.29, TRUE),
    (1, 3, 1.40, FALSE),
    (2, 1, 0.89, FALSE),
    (2, 2, 0.95, FALSE),
    (2, 3, 0.79, TRUE),
    (3, 1, 1.10, FALSE),
    (3, 2, 1.05, FALSE),
    (3, 3, 1.15, FALSE),
    (4, 1, 6.90, FALSE),
    (4, 2, 6.50, TRUE),
    (4, 3, 7.20, FALSE),
    (5, 1, 2.10, FALSE),
    (5, 2, 2.05, FALSE),
    (5, 3, 1.95, TRUE);
