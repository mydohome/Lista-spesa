// Percorso relativo: nginx (in questo stesso container) fa da reverse proxy
// verso il backend interno, così il browser non deve mai raggiungere il
// backend direttamente né conoscerne l'host/porta.
const API = "/api";

const inputRicerca = document.getElementById("ricerca");
const suggerimentiEl = document.getElementById("suggerimenti");
const vociListaEl = document.getElementById("voci-lista");
const listaVuotaEl = document.getElementById("lista-vuota");
const azioniEl = document.getElementById("azioni");
const risultatoEl = document.getElementById("risultato");
const btnOttimizza = document.getElementById("btn-ottimizza");

let debounceTimer = null;

inputRicerca.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const q = inputRicerca.value.trim();
  if (q.length < 2) {
    suggerimentiEl.innerHTML = "";
    return;
  }
  debounceTimer = setTimeout(() => cercaProdotti(q), 250);
});

async function cercaProdotti(q) {
  try {
    const res = await fetch(`${API}/prodotti/cerca?q=${encodeURIComponent(q)}`);
    const risultati = await res.json();
    suggerimentiEl.innerHTML = "";
    risultati.forEach((p) => {
      const li = document.createElement("li");
      li.textContent = `${p.nome_canonico}${p.marca ? " — " + p.marca : ""} (${p.formato || ""})`;
      li.addEventListener("click", () => aggiungiProdotto(p.id));
      suggerimentiEl.appendChild(li);
    });
  } catch (err) {
    console.error("Errore ricerca prodotti:", err);
  }
}

async function aggiungiProdotto(prodottoId) {
  try {
    await fetch(`${API}/lista`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prodotto_id: prodottoId, quantita: 1 }),
    });
    inputRicerca.value = "";
    suggerimentiEl.innerHTML = "";
    risultatoEl.hidden = true;
    caricaLista();
  } catch (err) {
    console.error("Errore aggiunta prodotto:", err);
  }
}

async function rimuoviVoce(voceId) {
  try {
    await fetch(`${API}/lista/${voceId}`, { method: "DELETE" });
    caricaLista();
  } catch (err) {
    console.error("Errore rimozione voce:", err);
  }
}

async function caricaLista() {
  try {
    const res = await fetch(`${API}/lista`);
    const voci = await res.json();
    vociListaEl.innerHTML = "";

    if (voci.length === 0) {
      listaVuotaEl.hidden = false;
      azioniEl.hidden = true;
      return;
    }
    listaVuotaEl.hidden = true;
    azioniEl.hidden = false;

    voci.forEach((v) => {
      const li = document.createElement("li");
      const nomeDiv = document.createElement("div");
      nomeDiv.className = "voce-nome";
      nomeDiv.innerHTML = `${v.nome_canonico} × ${v.quantita}
        <span class="dettaglio">${v.marca || ""} ${v.formato || ""}</span>`;

      const btnRimuovi = document.createElement("button");
      btnRimuovi.className = "rimuovi";
      btnRimuovi.textContent = "✕";
      btnRimuovi.addEventListener("click", () => rimuoviVoce(v.lista_id));

      li.appendChild(nomeDiv);
      li.appendChild(btnRimuovi);
      vociListaEl.appendChild(li);
    });
  } catch (err) {
    console.error("Errore caricamento lista:", err);
  }
}

btnOttimizza.addEventListener("click", async () => {
  const strategia = document.querySelector('input[name="strategia"]:checked').value;
  btnOttimizza.disabled = true;
  btnOttimizza.textContent = "Calcolo in corso…";
  try {
    const res = await fetch(`${API}/lista/ottimizza`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ strategia }),
    });
    const dati = await res.json();
    mostraRisultato(dati);
  } catch (err) {
    console.error("Errore ottimizzazione:", err);
  } finally {
    btnOttimizza.disabled = false;
    btnOttimizza.textContent = "Genera liste per supermercato";
  }
});

function mostraRisultato(dati) {
  risultatoEl.innerHTML = "";
  risultatoEl.hidden = false;

  const riepilogo = document.createElement("div");
  riepilogo.className = "riepilogo";
  riepilogo.innerHTML = `
    <span>Totale: <strong>€ ${dati.spesa_totale.toFixed(2)}</strong></span>
    <span>Risparmio stimato: <strong>€ ${dati.risparmio_stimato.toFixed(2)}</strong></span>
  `;
  risultatoEl.appendChild(riepilogo);

  const nomiNegozi = Object.keys(dati.liste_per_supermercato);
  if (nomiNegozi.length === 0) {
    const p = document.createElement("p");
    p.className = "avviso";
    p.textContent = "Nessun prezzo disponibile per i prodotti in lista.";
    risultatoEl.appendChild(p);
    return;
  }

  nomiNegozi.forEach((nome) => {
    const gruppo = document.createElement("div");
    gruppo.className = "gruppo-negozio";
    const voci = dati.liste_per_supermercato[nome];
    const subtotaleNegozio = voci.reduce((s, v) => s + v.subtotale, 0);

    const h3 = document.createElement("h3");
    h3.textContent = `${nome} — € ${subtotaleNegozio.toFixed(2)}`;
    gruppo.appendChild(h3);

    const ul = document.createElement("ul");
    voci.forEach((v) => {
      const li = document.createElement("li");
      const prezzoClass = v.in_offerta ? "prezzo-offerta" : "";
      li.innerHTML = `<span>${v.prodotto} × ${v.quantita}</span>
        <span class="${prezzoClass}">€ ${v.subtotale.toFixed(2)}${v.in_offerta ? " (offerta)" : ""}</span>`;
      ul.appendChild(li);
    });
    gruppo.appendChild(ul);
    risultatoEl.appendChild(gruppo);
  });

  if (dati.prodotti_senza_prezzo.length > 0) {
    const p = document.createElement("p");
    p.className = "avviso";
    p.textContent = `Nessun prezzo trovato per: ${dati.prodotti_senza_prezzo.join(", ")}`;
    risultatoEl.appendChild(p);
  }
}

caricaLista();
