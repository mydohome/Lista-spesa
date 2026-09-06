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
    ('Pasta spaghetti n.5', 'Barilla', 'Pasta', '500g'),
    ('Pane bianco', 'Generico', 'Pane', '500g'),
    ('Olio extravergine oliva', 'Monini', 'Condimenti', '1L'),
    ('Uova fresche', 'Generico', 'Uova', 'confezione da 6');

-- Prezzi di esempio per ciascun prodotto in ciascuno dei 7 supermercati
-- (supermercato_id segue l'ordine di inserimento sopra, 1=INCOOP ... 7=Todis)
INSERT INTO prezzi (prodotto_id, supermercato_id, prezzo, in_offerta) VALUES
    (1, 1, 1.38, FALSE), (1, 2, 1.32, FALSE), (1, 3, 1.35, FALSE), (1, 4, 1.29, TRUE),
    (1, 5, 1.40, FALSE), (1, 6, 1.19, FALSE), (1, 7, 1.22, TRUE),

    (2, 1, 0.92, FALSE), (2, 2, 0.89, FALSE), (2, 3, 0.95, FALSE), (2, 4, 0.85, FALSE),
    (2, 5, 0.99, FALSE), (2, 6, 0.75, TRUE),  (2, 7, 0.79, FALSE),

    (3, 1, 1.15, FALSE), (3, 2, 1.05, FALSE), (3, 3, 1.20, FALSE), (3, 4, 1.10, FALSE),
    (3, 5, 1.18, FALSE), (3, 6, 0.95, FALSE), (3, 7, 0.98, TRUE),

    (4, 1, 7.10, FALSE), (4, 2, 6.80, FALSE), (4, 3, 6.95, FALSE), (4, 4, 6.50, TRUE),
    (4, 5, 7.20, FALSE), (4, 6, 5.99, FALSE), (4, 7, 6.10, FALSE),

    (5, 1, 2.15, FALSE), (5, 2, 2.05, FALSE), (5, 3, 2.20, FALSE), (5, 4, 1.99, FALSE),
    (5, 5, 2.25, FALSE), (5, 6, 1.79, TRUE),  (5, 7, 1.85, FALSE);

