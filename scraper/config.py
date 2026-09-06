"""
Configurazione dello scraper: quale pagina di TuttiPrezzi.it corrisponde a
ciascun supermercato in database, e quali prodotti cercare nei volantini.

TuttiPrezzi.it (https://www.tuttiprezzi.it) è un aggregatore di volantini che
pubblica le pagine dei volantini come immagini JPG in sequenza, per catena.
Ogni pagina catena elenca in fondo gli indirizzi dei punti vendita a cui le
offerte potrebbero applicarsi (non è garanzia che valgano ovunque: è lo
stesso disclaimer che il sito stesso riporta).

IMPORTANTE: questa configurazione è stata verificata manualmente il
06/09/2026 controllando che i nostri 6 supermercati compaiano davvero nelle
rispettive pagine. Se TuttiPrezzi.it cambia struttura del sito, questa
mappa (e la logica di parsing in estrai_prezzi.py) potrebbe smettere di
funzionare e andrà aggiornata.

Eurospin non risulta coperto da TuttiPrezzi.it: va gestito con un'altra
fonte (es. il sito ufficiale eurospin.it) o a mano.
"""

# nome_supermercato deve corrispondere ESATTAMENTE al campo "nome" nella
# tabella supermercati del database, per poter associare i prezzi trovati.
SUPERMERCATI_TUTTIPREZZI = {
    "Carrefour Iper": {
        "url": "https://www.tuttiprezzi.it/carrefour.html",
        "indirizzo_atteso": "Via della Bufalotta, 548",
    },
    "SPAZIO CONAD (Porta di Roma)": {
        "url": "https://www.tuttiprezzi.it/spazioconad.html",
        "indirizzo_atteso": "Alberto Lionello",
    },
    "Pam Bufalotta": {
        "url": "https://www.tuttiprezzi.it/pam.html",
        "indirizzo_atteso": "Falzarego",
    },
    "INCOOP (Coop)": {
        "url": "https://www.tuttiprezzi.it/coop.html",
        "indirizzo_atteso": "Enriquez",
    },
    "Pewex": {
        "url": "https://www.tuttiprezzi.it/pewex.html",
        "indirizzo_atteso": "Via Umberto Barbaro, 24",
    },
    "Todis": {
        "url": "https://www.tuttiprezzi.it/todis.html",
        "indirizzo_atteso": "Emilio Teza",
    },
    # "Eurospin" non è su TuttiPrezzi.it: da gestire a parte.
}

# Prodotti che cerchiamo nei volantini: nome_canonico e marca DEVONO
# corrispondere a quelli già presenti nella tabella "prodotti" del database,
# altrimenti lo scraper trova il prezzo ma non riesce ad associarlo a nessun
# prodotto (viene segnalato e scartato, mai inventato).
PRODOTTI_TARGET = [
    {"nome_canonico": "Latte intero", "marca": "Parmalat", "formato": "1L"},
    {"nome_canonico": "Pasta spaghetti n.5", "marca": "Rummo", "formato": "500g"},
    {"nome_canonico": "Pasta spaghetti n.5", "marca": "La Molisana", "formato": "500g"},
    {"nome_canonico": "Pasta spaghetti n.5", "marca": "Armando", "formato": "500g"},
    {"nome_canonico": "Pasta spaghetti n.5", "marca": "Garofalo", "formato": "500g"},
    {"nome_canonico": "Pane bianco", "marca": "Generico", "formato": "500g"},
    {"nome_canonico": "Olio extravergine oliva", "marca": "Monini", "formato": "1L"},
    {"nome_canonico": "Uova fresche", "marca": "Generico", "formato": "confezione da 6"},
    {"nome_canonico": "Acqua naturale", "marca": "Uliveto", "formato": "confezione da 6 x 1,5L"},
]

# Quante immagini di volantino inviare a Claude per ogni chiamata (batch).
# Numeri più bassi = più chiamate ma risposte più precise; più alti = meno
# chiamate ma rischio che il modello "perda" prodotti su pagine affollate.
DIMENSIONE_BATCH_IMMAGINI = 4

# Numero massimo di pagine di volantino da scaricare per supermercato
# (i volantini di questi formati raramente superano le 50 pagine; un limite
# evita di scaricare volantini enormi per errore di parsing).
MAX_PAGINE_PER_VOLANTINO = 60
