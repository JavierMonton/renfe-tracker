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

/** Human-readable check interval, e.g. "Every 60 min" or "Every 1 h". */
function formatCheckInterval(minutes) {
  if (minutes == null || minutes <= 0) return "—";
  if (minutes < 60) return "Every " + minutes + " min";
  const hours = minutes / 60;
  return "Every " + (hours === 1 ? "1 h" : hours + " h");
}

/** Current price = latest price_event if provided, else initial_price. For list API we only have initial_price. */
function getCurrentPriceForTrip(trip, events) {
  if (events && events.length > 0) {
    const latest = events.reduce((a, e) => (e.detected_at > (a?.detected_at || "") ? e : a), null);
    return latest?.price_detected != null ? latest.price_detected : trip.initial_price;
  }
  return trip.initial_price != null ? trip.initial_price : null;
}

function compareIsoDate(a, b) {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

function compareTimeHHMM(a, b) {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

function compareTripsByDeparture(a, b) {
  const aHasTime = Boolean(a.departure_time);
  const bHasTime = Boolean(b.departure_time);

  // User preference: trips without a time always go after trips with a time (even if date is earlier).
  if (aHasTime !== bHasTime) return aHasTime ? -1 : 1;

  const d = compareIsoDate(a.date || "", b.date || "");
  if (d !== 0) return d;

  if (aHasTime && bHasTime) {
    return compareTimeHHMM(a.departure_time, b.departure_time);
  }

  // Stable fallback (no time): keep deterministic ordering
  return (a.id || 0) - (b.id || 0);
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
    "<thead><tr><th>Route</th><th>Date</th><th>Train</th><th>Check interval</th><th>Price / status</th><th></th></tr></thead><tbody></tbody>";
  const tbody = table.querySelector("tbody");

  const groups = new Map();
  trips.forEach((t) => {
    const origin = t.origin || "";
    const destination = t.destination || "";
    const key = origin + " → " + destination;
    if (!groups.has(key)) groups.set(key, { origin, destination, trips: [] });
    groups.get(key).trips.push(t);
  });

  const groupList = Array.from(groups.values());
  groupList.forEach((g) => {
    g.trips.sort(compareTripsByDeparture);
    g.earliestTrip = g.trips[0] || null;
  });
  groupList.sort((a, b) => compareTripsByDeparture(a.earliestTrip || {}, b.earliestTrip || {}));

  function renderTripRow(t) {
    const tr = document.createElement("tr");
    const notYetPublished = t.initial_price == null;
    const currentPrice = getCurrentPriceForTrip(t, t.price_events);
    const dateParts = [t.date];
    if (t.departure_time) {
      dateParts.push(t.departure_time);
    }
    const dateLabel = escapeHtml(dateParts.join(" · "));
    let priceHtml;
    if (notYetPublished) {
      priceHtml = '<span class="trip-status trip-status--unpublished">Trip not yet published</span>';
    } else {
      priceHtml =
        '<span class="trip-price">€' +
        (currentPrice != null ? Number(currentPrice).toFixed(2) : "—") +
        "</span>";
    }
    const listEstMin = t.estimated_price_min != null && t.estimated_price_min !== "" ? Number(t.estimated_price_min) : NaN;
    const listEstMax = t.estimated_price_max != null && t.estimated_price_max !== "" ? Number(t.estimated_price_max) : NaN;
    const hasEstMin = !Number.isNaN(listEstMin);
    const hasEstMax = !Number.isNaN(listEstMax);
    if (hasEstMin || hasEstMax) {
      const fmtPrice = (n) => Number(n).toFixed(2).replace(".", ",");
      if (hasEstMin && hasEstMax) {
        priceHtml +=
          '<div class="price-range">Precio habitual: ' +
          fmtPrice(listEstMin) +
          ' € – ' +
          fmtPrice(listEstMax) +
          " €</div>";
      } else if (hasEstMin) {
        priceHtml += '<div class="price-range">Precio habitual: desde ' + fmtPrice(listEstMin) + ' €</div>';
      } else {
        priceHtml += '<div class="price-range">Precio habitual: hasta ' + fmtPrice(listEstMax) + ' €</div>';
      }
    }
    priceHtml +=
      '<div class="trip-last-checked">Last checked at: ' +
      (t.last_checked_at ? escapeHtml(formatLastCheckedAt(t.last_checked_at)) : "Not checked yet") +
      "</div>";
    tr.innerHTML =
      "<td>" +
      escapeHtml(t.origin + " → " + t.destination) +
      '</td><td class="trips-table__cell--date">' +
      dateLabel +
      "</td><td>" +
      escapeHtml(t.train_identifier) +
      "</td><td>" +
      escapeHtml(formatCheckInterval(t.check_interval_minutes)) +
      "</td><td>" +
      priceHtml +
      '</td><td class="trips-table__actions"><a href="#/trip/' +
      t.id +
      '">View details</a> <button type="button" class="btn btn-secondary btn--small trip-remove-btn" data-trip-id="' +
      t.id +
      '" aria-label="Remove tracked trip">Remove</button></td>';
    return tr;
  }

  groupList.forEach((g) => {
    const headerTr = document.createElement("tr");
    headerTr.className = "trips-group-row";
    headerTr.innerHTML = '<td colspan="6">' + escapeHtml(g.origin + " → " + g.destination) + "</td>";
    tbody.appendChild(headerTr);

    g.trips.forEach((t) => {
      tbody.appendChild(renderTripRow(t));
    });
  });

  container.innerHTML = "";
  container.appendChild(table);
}

// ----- Search -----
async function loadSearch() {
  showView("view-search");

  // Reset loading state so it never shows before the user clicks Search
  const submitBtn = $("search-submit-btn");
  const loadingEl = $("search-loading");
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.textContent = "Search";
  }
  if (loadingEl) {
    loadingEl.hidden = true;
  }

  const originInput = $("search-origin-input");
  const destInput = $("search-destination-input");
  const originSug = $("search-origin-suggestions");
  const destSug = $("search-destination-suggestions");
  const swapBtn = $("swap-route-btn");

  if (swapBtn && originInput && destInput) {
    swapBtn.addEventListener("click", () => {
      const originValue = originInput.value;
      originInput.value = destInput.value;
      destInput.value = originValue;
      originInput.focus();
    });
  }

  // Default date to tomorrow
  const dateInput = $("search-date");
  if (!dateInput.value) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.value = tomorrow.toISOString().slice(0, 10);
  }

  let stationOptions = null;
  try {
    const res = await fetch(API + "/search/options");
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    stationOptions = Array.from(new Set([...(data.origins || []), ...(data.destinations || [])])).sort();
  } catch (e) {
    stationOptions = [];
  }

  function attachTypeahead(inputEl, sugEl) {
    if (!inputEl || !sugEl || !stationOptions) return;

    function renderSuggestions() {
      const q = inputEl.value.trim().toLowerCase();
      if (!q) {
        sugEl.innerHTML = "";
        sugEl.hidden = true;
        return;
      }
      const matches = stationOptions.filter((name) => name.toLowerCase().includes(q)).slice(0, 10);
      if (matches.length === 0) {
        sugEl.innerHTML = "";
        sugEl.hidden = true;
        return;
      }
      sugEl.innerHTML = matches
        .map(
          (name) =>
            '<button type="button" class="typeahead-option">' + escapeHtml(name) + "</button>"
        )
        .join("");
      sugEl.hidden = false;
    }

    inputEl.addEventListener("input", renderSuggestions);
    inputEl.addEventListener("focus", renderSuggestions);
    inputEl.addEventListener("blur", () => {
      // Slight delay so click can register
      setTimeout(() => {
        sugEl.hidden = true;
      }, 150);
    });
    sugEl.addEventListener("click", (e) => {
      const btn = e.target.closest(".typeahead-option");
      if (!btn) return;
      inputEl.value = btn.textContent || "";
      sugEl.hidden = true;
      inputEl.focus();
    });
  }

  attachTypeahead(originInput, originSug);
  attachTypeahead(destInput, destSug);

  const form = $("search-form");
  form.onsubmit = async (ev) => {
    ev.preventDefault();
    const date = $("search-date").value;
    const o = originInput.value.trim();
    const d = destInput.value.trim();
    if (!date || !o || !d) return;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Buscando…";
    }
    if (loadingEl) {
      loadingEl.hidden = false;
    }

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
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Search";
      }
      if (loadingEl) {
        loadingEl.hidden = true;
      }
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
    li.className = "result-card" + (train.is_possible ? " result-card--possible" : "");

    const duration = train.duration_minutes != null ? formatDuration(train.duration_minutes) : "";
    const depTime = train.departure_time ? escapeHtml(train.departure_time) : "";
    let meta = depTime ? (depTime + (duration ? " · " + duration : "")) : duration;
    // Show possible price range when backend provides estimated min/max; show partial (desde/hasta) when only one bound exists.
    const fmtPrice = (n) => Number(n).toFixed(2).replace(".", ",");
    const hasMin = train.estimated_price_min != null;
    const hasMax = train.estimated_price_max != null;
    if (hasMin && hasMax) {
      meta += (meta ? ' · ' : '') + '<span class="price-range">Precio habitual: ' + fmtPrice(train.estimated_price_min) + ' € – ' + fmtPrice(train.estimated_price_max) + ' €</span>';
    } else if (hasMin) {
      meta += (meta ? ' · ' : '') + '<span class="price-range">Precio habitual: desde ' + fmtPrice(train.estimated_price_min) + ' €</span>';
    } else if (hasMax) {
      meta += (meta ? ' · ' : '') + '<span class="price-range">Precio habitual: hasta ' + fmtPrice(train.estimated_price_max) + ' €</span>';
    }

    let possibleBadge = "";
    if (train.is_possible) {
      possibleBadge =
        '<div class="result-card__possible-badge-wrap">' +
        '<span class="result-card__possible-badge">Tren posible – aún no publicado para esta fecha</span>' +
        (train.inferred_from_date
          ? '<span class="result-card__inferred-date">Inferido desde ' + escapeHtml(formatInferredDate(train.inferred_from_date)) + "</span>"
          : "") +
        "</div>";
    }

    li.innerHTML =
      '<div class="train-info">' +
      '<div class="train-name">' +
      escapeHtml(train.name || "Train") +
      "</div>" +
      '<div class="train-meta">' +
      meta +
      "</div>" +
      possibleBadge +
      "</div>" +
      '<div class="price">€' +
      (train.price != null ? Number(train.price).toFixed(2) : "—") +
      "</div>" +
      '<div class="actions"><button type="button" class="btn btn-primary" data-track="' +
      escapeHtml(train.name || "") +
      '">Track this trip</button></div>';

    li.querySelector("[data-track]").addEventListener("click", () => {
      openTrackModal(origin, destination, date, train);
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

function formatInferredDate(yyyyMmDd) {
  if (!yyyyMmDd) return "";
  try {
    const [y, m, d] = yyyyMmDd.split("-");
    if (y && m && d) return d + "/" + m + "/" + y;
  } catch {}
  return yyyyMmDd;
}

// Single source of truth for track-interval options (minutes → label)
const TRACK_INTERVAL_OPTIONS = [
  { value: 1, label: "Every 1 minute" },
  { value: 5, label: "Every 5 minutes" },
  { value: 10, label: "Every 10 minutes" },
  { value: 30, label: "Every 30 minutes" },
  { value: 60, label: "Every 1 hour" },
  { value: 120, label: "Every 2 hours" },
  { value: 360, label: "Every 6 hours" },
  { value: 720, label: "Every 12 hours" },
];

function renderTrackIntervalSelect(selectEl) {
  if (!selectEl) return;
  const defaultMinutes = 60;
  selectEl.innerHTML = TRACK_INTERVAL_OPTIONS.map(
    (o) =>
      '<option value="' +
      o.value +
      '"' +
      (o.value === defaultMinutes ? " selected" : "") +
      ">" +
      escapeHtml(o.label) +
      "</option>"
  ).join("");
}

// Pending track params (set when opening modal, used on submit)
let pendingTrack = null;

function openTrackModal(origin, destination, date, train) {
  pendingTrack = { origin, destination, date, train };
  const modal = $("track-interval-modal");
  const intervalSelect = $("track-interval");
  const errorEl = $("track-interval-error");
  if (intervalSelect) intervalSelect.value = "60";
  if (errorEl) {
    errorEl.textContent = "";
    errorEl.hidden = true;
  }
  if (modal) {
    modal.hidden = false;
    intervalSelect?.focus();
  }
}

function closeTrackModal() {
  pendingTrack = null;
  const modal = $("track-interval-modal");
  if (modal) modal.hidden = true;
}

// ----- Remove trip modal -----
let pendingRemoveTripId = null;

function openRemoveTripModal(tripId) {
  pendingRemoveTripId = tripId;
  const modal = $("remove-trip-modal");
  if (modal) {
    modal.hidden = false;
    modal.querySelector("#remove-trip-confirm")?.focus();
  }
}

function closeRemoveTripModal() {
  pendingRemoveTripId = null;
  const modal = $("remove-trip-modal");
  if (modal) modal.hidden = true;
}

function initRemoveTripModal() {
  const modal = $("remove-trip-modal");
  const confirmBtn = $("remove-trip-confirm");

  // Delegation: any .trip-remove-btn (list or detail) opens the modal
  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest(".trip-remove-btn");
    if (!btn) return;
    e.preventDefault();
    const tripId = parseInt(btn.getAttribute("data-trip-id"), 10);
    if (!Number.isNaN(tripId)) openRemoveTripModal(tripId);
  });

  modal?.querySelectorAll("[data-remove-modal-close], [data-remove-modal-cancel]").forEach((el) => {
    el.addEventListener("click", () => closeRemoveTripModal());
  });

  modal?.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeRemoveTripModal();
  });

  confirmBtn?.addEventListener("click", async () => {
    if (pendingRemoveTripId == null) return;
    const tripId = pendingRemoveTripId;
    closeRemoveTripModal();
    pendingRemoveTripId = null;
    try {
      const res = await fetch(API + "/trips/" + tripId, { method: "DELETE" });
      if (!res.ok) throw new Error(res.status === 404 ? "Trip not found" : res.statusText);
      await loadHome();
      location.hash = "#/";
    } catch (e) {
      alert("Could not remove trip: " + (e.message || "Unknown error"));
    }
  });
}

function formatLastCheckedAt(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString("es-ES", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function initTrackModal() {
  const modal = $("track-interval-modal");
  const form = $("track-interval-form");
  const errorEl = $("track-interval-error");
  const submitBtn = $("track-interval-submit");

  // Populate interval dropdown from single source of truth
  renderTrackIntervalSelect($("track-interval"));

  function showError(msg) {
    const fullMsg = "Could not track trip: " + (msg || "Unknown error");
    if (errorEl) {
      errorEl.textContent = fullMsg;
      errorEl.hidden = false;
    } else {
      alert(fullMsg);
    }
  }

  function hideError() {
    if (errorEl) {
      errorEl.textContent = "";
      errorEl.hidden = true;
    }
  }

  modal?.querySelectorAll("[data-modal-close], [data-modal-cancel]").forEach((el) => {
    el.addEventListener("click", () => {
      closeTrackModal();
    });
  });

  modal?.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeTrackModal();
    }
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!pendingTrack) return;
    const { origin, destination, date, train } = pendingTrack;
    const intervalSelect = $("track-interval");
    const check_interval_minutes = intervalSelect ? parseInt(intervalSelect.value, 10) : 60;
    const train_identifier = train?.name ?? "";
    const initial_price = train?.price != null ? Number(train.price) : null;
    const departure_time = train?.departure_time || undefined;
    let estimated_prices = Array.isArray(train?.estimated_prices) ? train.estimated_prices : [];
    if (estimated_prices.length === 0 && train?.estimated_price_min != null && train?.estimated_price_max != null) {
      const mn = Number(train.estimated_price_min);
      const mx = Number(train.estimated_price_max);
      if (!Number.isNaN(mn) && !Number.isNaN(mx)) estimated_prices = [mn, mx];
    }

    hideError();
    if (submitBtn) {
      submitBtn.disabled = true;
    }

    try {
      const res = await fetch(API + "/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin,
          destination,
          date,
          train_identifier,
          check_interval_minutes,
          initial_price,
          estimated_prices,
          ...(departure_time ? { departure_time } : {}),
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const d = data.detail;
        const msg =
          typeof d === "string"
            ? d
            : Array.isArray(d) && d[0]?.msg
              ? d[0].msg
              : d?.message ?? res.statusText;
        showError(msg);
        return;
      }
      closeTrackModal();
      location.hash = "#/";
    } catch (e) {
      const msg = e.message && /fetch|network/i.test(String(e.message)) ? "Failed to fetch" : (e.message || "Network error");
      showError(msg);
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
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
  const notYetPublished = trip.initial_price == null && !(events && events.length > 0);
  const currentPrice = getCurrentPriceForTrip(trip, events);
  const metaParts = [trip.date];
  if (trip.departure_time) {
    metaParts.push(trip.departure_time);
  }
  metaParts.push(
    trip.train_identifier,
    "Price checked " + formatCheckInterval(trip.check_interval_minutes).replace(/^Every /, "").toLowerCase()
  );
  const metaText = metaParts.join(" · ");

  const card = document.createElement("div");
  card.className = "trip-detail-card";
  let statusHtml = "";
  if (notYetPublished) {
    statusHtml = '<p class="trip-detail-status trip-status--unpublished">Trip not yet published</p>';
  } else {
    statusHtml =
      '<p class="trip-detail-price">Current price: €' +
      (currentPrice != null ? Number(currentPrice).toFixed(2) : "—") +
      "</p>";
  }
  const estMin = trip.estimated_price_min != null && trip.estimated_price_min !== "" ? Number(trip.estimated_price_min) : NaN;
  const estMax = trip.estimated_price_max != null && trip.estimated_price_max !== "" ? Number(trip.estimated_price_max) : NaN;
  const hasEstMin = !Number.isNaN(estMin);
  const hasEstMax = !Number.isNaN(estMax);
  if (hasEstMin || hasEstMax) {
    const fmtPrice = (n) => Number(n).toFixed(2).replace(".", ",");
    if (hasEstMin && hasEstMax) {
      statusHtml += '<p class="trip-detail-estimated-range price-range">Precio habitual: ' + fmtPrice(estMin) + ' € – ' + fmtPrice(estMax) + ' €</p>';
    } else if (hasEstMin) {
      statusHtml += '<p class="trip-detail-estimated-range price-range">Precio habitual: desde ' + fmtPrice(estMin) + ' €</p>';
    } else {
      statusHtml += '<p class="trip-detail-estimated-range price-range">Precio habitual: hasta ' + fmtPrice(estMax) + ' €</p>';
    }
  }
  statusHtml +=
    '<p class="trip-detail-last-checked">Last checked at: ' +
    (trip.last_checked_at
      ? escapeHtml(formatLastCheckedAt(trip.last_checked_at))
      : "Not checked yet") +
    "</p>";

  card.innerHTML =
    "<h2>" +
    escapeHtml(trip.origin + " → " + trip.destination) +
    "</h2>" +
    '<div class="trip-meta">' +
    escapeHtml(metaText) +
    "</div>" +
    '<div class="trip-detail-status-wrap">' +
    statusHtml +
    "</div>" +
    '<div class="trip-detail-actions">' +
    '<button type="button" class="btn btn-secondary trip-remove-btn" data-trip-id="' +
    trip.id +
    '" aria-label="Remove tracked trip">Remove trip</button>' +
    "</div>";

  const eventsEl = document.createElement("div");
  if (events.length === 0) {
    eventsEl.innerHTML =
      '<p class="events-empty">' +
      (notYetPublished ? "No price changes yet. Trip not yet published." : "No price changes yet.") +
      "</p>";
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

initTrackModal();
initRemoveTripModal();
window.addEventListener("hashchange", route);
window.addEventListener("load", route);
