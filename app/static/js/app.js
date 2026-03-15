/**
 * Renfe Tracker – vanilla JS SPA.
 * Hash routes: #/, #/search, #/results, #/trip/:id
 * API base: /api (same origin).
 */

const API = "/api";

function $(id) {
  return document.getElementById(id);
}

function showView(viewId) {
  document.querySelectorAll(".view").forEach((el) => (el.hidden = true));
  const view = $(viewId);
  if (view) view.hidden = false;
}

// ----- Home -----
async function loadHome() {
  showView("view-home");
  const container = $("home-content");
  container.innerHTML = '<p class="loading">Loading trips…</p>';

  try {
    const res = await fetch(API + "/trips");
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    renderTripsTable(container, data.trips || []);
  } catch (e) {
    container.innerHTML = '<p class="error-message">Error loading trips. ' + escapeHtml(String(e.message)) + "</p>";
  }
}

function renderTripsTable(container, trips) {
  if (trips.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><p>No tracked trips yet.</p><p><a href="#/search" class="btn btn-primary">Track new trip</a></p></div>';
    return;
  }

  const table = document.createElement("table");
  table.className = "trips-table";
  table.setAttribute("role", "table");
  table.innerHTML =
    "<thead><tr><th>Route</th><th>Date</th><th>Train</th><th></th></tr></thead><tbody></tbody>";
  const tbody = table.querySelector("tbody");

  trips.forEach((t) => {
    const tr = document.createElement("tr");
    tr.innerHTML =
      "<td>" +
      escapeHtml(t.origin + " → " + t.destination) +
      "</td><td>" +
      escapeHtml(t.date) +
      "</td><td>" +
      escapeHtml(t.train_identifier) +
      '</td><td><a href="#/trip/' +
      t.id +
      '">View details</a></td>';
    tbody.appendChild(tr);
  });

  container.innerHTML = "";
  container.appendChild(table);
}

// ----- Search -----
async function loadSearch() {
  showView("view-search");
  const origin = $("search-origin");
  const dest = $("search-destination");

  // Default date to tomorrow
  const dateInput = $("search-date");
  if (!dateInput.value) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.value = tomorrow.toISOString().slice(0, 10);
  }

  if (origin.options.length <= 1) {
    try {
      const res = await fetch(API + "/search/options");
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      (data.origins || []).forEach((o) => {
        const opt = document.createElement("option");
        opt.value = o;
        opt.textContent = o;
        origin.appendChild(opt);
      });
      (data.destinations || []).forEach((d) => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        dest.appendChild(opt);
      });
    } catch (e) {
      origin.innerHTML = '<option value="">Error loading options</option>';
    }
  }

  const form = $("search-form");
  form.onsubmit = async (ev) => {
    ev.preventDefault();
    const date = $("search-date").value;
    const o = $("search-origin").value;
    const d = $("search-destination").value;
    if (!date || !o || !d) return;

    try {
      const res = await fetch(API + "/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date, origin: o, destination: d }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || data.message || res.statusText);
      sessionStorage.setItem(
        "renfe_search",
        JSON.stringify({ date, origin: o, destination: d, trains: data.trains || [] })
      );
      location.hash = "#/results";
    } catch (e) {
      alert("Búsqueda fallida: " + e.message);
    }
  };
}

// ----- Results -----
function loadResults() {
  showView("view-results");
  const container = $("results-content");
  const raw = sessionStorage.getItem("renfe_search");
  if (!raw) {
    container.innerHTML = '<p class="error-message">No search results. <a href="#/search">Search again</a>.</p>';
    return;
  }

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    container.innerHTML = '<p class="error-message">Invalid data. <a href="#/search">Search again</a>.</p>';
    return;
  }

  const trains = data.trains || [];
  const date = data.date;
  const origin = data.origin;
  const destination = data.destination;

  if (trains.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No trains found for this search.</p></div>';
    return;
  }

  const ul = document.createElement("ul");
  ul.className = "results-list";

  trains.forEach((train) => {
    const li = document.createElement("li");
    li.className = "result-card";

    const duration = train.duration_minutes != null ? formatDuration(train.duration_minutes) : "";
    let meta = duration;
    if (train.estimated_price_min != null && train.estimated_price_max != null) {
      meta += '<span class="price-range">(est. €' + train.estimated_price_min + "–€" + train.estimated_price_max + ")</span>";
    }

    li.innerHTML =
      '<div class="train-info">' +
      '<div class="train-name">' +
      escapeHtml(train.name || "Train") +
      "</div>" +
      '<div class="train-meta">' +
      meta +
      "</div>" +
      "</div>" +
      '<div class="price">€' +
      (train.price != null ? Number(train.price).toFixed(2) : "—") +
      "</div>" +
      '<div class="actions"><button type="button" class="btn btn-primary" data-track="' +
      escapeHtml(train.name || "") +
      '">Track this trip</button></div>';

    li.querySelector("[data-track]").addEventListener("click", () => {
      trackTrip(origin, destination, date, train.name || "");
    });
    ul.appendChild(li);
  });

  container.innerHTML = "";
  container.appendChild(ul);
}

function formatDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? h + " h " + m + " min" : h + " h";
}

async function trackTrip(origin, destination, date, train_identifier) {
  try {
    const res = await fetch(API + "/trips", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        origin,
        destination,
        date,
        train_identifier,
        check_interval_minutes: 60,
      }),
    });
    if (!res.ok) throw new Error(res.statusText);
    location.hash = "#/";
  } catch (e) {
    alert("Could not track trip: " + e.message);
  }
}

// ----- Trip detail -----
async function loadTripDetail(id) {
  showView("view-trip");
  const container = $("trip-content");
  container.innerHTML = '<p class="loading">Loading trip…</p>';

  try {
    const res = await fetch(API + "/trips/" + id);
    if (!res.ok) throw new Error(res.status === 404 ? "Trip not found" : res.statusText);
    const data = await res.json();
    renderTripDetail(container, data.trip, data.price_events || []);
  } catch (e) {
    container.innerHTML = '<p class="error-message">' + escapeHtml(String(e.message)) + "</p>";
  }
}

function renderTripDetail(container, trip, events) {
  const card = document.createElement("div");
  card.className = "trip-detail-card";
  card.innerHTML =
    "<h2>" +
    escapeHtml(trip.origin + " → " + trip.destination) +
    "</h2>" +
    '<div class="trip-meta">' +
    escapeHtml(trip.date) +
    " · " +
    escapeHtml(trip.train_identifier) +
    "</div>";

  const eventsEl = document.createElement("div");
  if (events.length === 0) {
    eventsEl.innerHTML = '<p class="events-empty">No price changes yet.</p>';
  } else {
    const ul = document.createElement("ul");
    ul.className = "events-list";
    events.forEach((ev) => {
      const li = document.createElement("li");
      li.innerHTML =
        '<span class="price">€' +
        (ev.price_detected != null ? Number(ev.price_detected).toFixed(2) : "—") +
        "</span>" +
        '<span class="date">' +
        escapeHtml(formatDetectedAt(ev.detected_at)) +
        "</span>";
      ul.appendChild(li);
    });
    eventsEl.appendChild(ul);
  }

  card.appendChild(eventsEl);
  container.innerHTML = "";
  container.appendChild(card);
}

function formatDetectedAt(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString("es-ES", {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

// ----- Router -----
function route() {
  const hash = location.hash.slice(1) || "/";
  const parts = hash.split("/").filter(Boolean);

  if (parts[0] === "trip" && parts[1]) {
    loadTripDetail(parts[1]);
    return;
  }
  if (parts[0] === "results") {
    loadResults();
    return;
  }
  if (parts[0] === "search") {
    loadSearch();
    return;
  }
  loadHome();
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

window.addEventListener("hashchange", route);
window.addEventListener("load", route);
