/* Emergency Route Finder -- click-a-point web map (Phase E6).
 * Data is precomputed offline (WHO AccessMod in Docker) -- this page only reads static GeoJSON
 * files under data/. See docs/capabilities.md and RESULTS.md in the repository for the method
 * and the labeled assumptions behind every number shown here. */

const EMERGENCY_LABELS = {
  childbirth_complication: "Childbirth complication",
  snakebite: "Snakebite",
  injury_drowning: "Injury or drowning",
  minor_illness: "Minor illness",
};
const SEASON_LABELS = { dry: "dry season", flood0708: "flood (2026-07-08)" };

const state = {
  emergency: "childbirth_complication",
  season: "dry",
  points: [],                 // [{grid_id, lon, lat}]
  routesByEmergency: {},       // emergency -> { grid_id -> { dry: feature, flood0708: feature } }
  selectedGridId: null,
};

const map = L.map("map", { zoomControl: true }).setView([24.7, 91.2], 9);
L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
  { attribution: "Tiles &copy; Esri", maxZoom: 17 }
).addTo(map);

const pointsLayer = L.layerGroup().addTo(map);
let routeLayer = null;
let facilityMarker = null;
let selectedMarker = null;

function distanceSq(a, b) {
  const dx = a.lon - b.lon;
  const dy = a.lat - b.lat;
  return dx * dx + dy * dy;
}

function nearestPoint(lon, lat) {
  const target = { lon, lat };
  let best = null;
  let bestD = Infinity;
  for (const p of state.points) {
    const d = distanceSq(p, target);
    if (d < bestD) {
      bestD = d;
      best = p;
    }
  }
  return best;
}

async function loadPoints() {
  const res = await fetch("data/e6_points.geojson");
  const data = await res.json();
  state.points = data.features.map((f) => ({
    grid_id: f.properties.grid_id,
    lon: f.geometry.coordinates[0],
    lat: f.geometry.coordinates[1],
  }));
  for (const p of state.points) {
    L.circleMarker([p.lat, p.lon], {
      radius: 3, weight: 1, color: "#0f766e", fillColor: "#5eead4", fillOpacity: 0.7,
    }).addTo(pointsLayer);
  }
}

async function loadRoutes(emergency) {
  if (state.routesByEmergency[emergency]) return state.routesByEmergency[emergency];
  const res = await fetch(`data/e6_routes_${emergency}.geojson`);
  const data = await res.json();
  const byGrid = {};
  for (const f of data.features) {
    const gid = f.properties.grid_id;
    byGrid[gid] = byGrid[gid] || {};
    byGrid[gid][f.properties.season] = f;
  }
  state.routesByEmergency[emergency] = byGrid;
  return byGrid;
}

function clearRoute() {
  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
  }
  if (facilityMarker) {
    map.removeLayer(facilityMarker);
    facilityMarker = null;
  }
}

function renderResult(feature, gridId) {
  const box = document.getElementById("result");
  if (!feature) {
    box.innerHTML = `<div class="no-route-box">No route to a qualifying facility within
      reach for ${EMERGENCY_LABELS[state.emergency]} at this point, in the ${SEASON_LABELS[state.season]}.</div>`;
    clearRoute();
    return;
  }
  const p = feature.properties;
  const badge = p.within_target
    ? `<span class="badge ok">within ${p.target_minutes} min target</span>`
    : `<span class="badge late">outside ${p.target_minutes} min target</span>`;
  let warnings = "";
  const items = [];
  if (p.flood_adds_minutes != null && p.flood_adds_minutes >= 15) {
    items.push(`The flood adds about ${Math.round(p.flood_adds_minutes)} minutes here.`);
  }
  if (p.crosses_flood) {
    items.push("This route crosses flooded ground (a boat or wading leg).");
  }
  if (items.length) {
    warnings = `<div class="warning-box">${items.join(" ")}</div>`;
  }
  box.innerHTML = `
    <div class="facility">${p.facility_name}</div>
    <div class="row"><span>Travel time</span><span>${Math.round(p.minutes)} min</span></div>
    <div class="row"><span>Travel mode</span><span>${p.mode}</span></div>
    <div class="row"><span>Target</span><span>${badge}</span></div>
    <div class="row"><span>Season</span><span>${SEASON_LABELS[state.season]}</span></div>
    ${warnings}
    <p class="hint">Point ${gridId} of the precomputed grid. Backup facility and a full
    dry-vs-flood record for this exact point: run
    <code>make route LON=${p.lon.toFixed(4)} LAT=${p.lat.toFixed(4)} EMERGENCY=${state.emergency}</code>
    locally (see the repository README).</p>
  `;

  clearRoute();
  const latlngs = feature.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  const color = p.within_target ? "#0f766e" : "#b45309";
  routeLayer = L.polyline(latlngs, { color, weight: 4, opacity: 0.85 }).addTo(map);
  facilityMarker = L.marker(latlngs[latlngs.length - 1]).addTo(map).bindPopup(p.facility_name);
  map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] });
}

async function showPoint(gridId) {
  const byGrid = await loadRoutes(state.emergency);
  const seasons = byGrid[gridId] || {};
  renderResult(seasons[state.season] || null, gridId);
}

map.on("click", (e) => {
  const nearest = nearestPoint(e.latlng.lng, e.latlng.lat);
  if (!nearest) return;
  state.selectedGridId = nearest.grid_id;
  if (selectedMarker) map.removeLayer(selectedMarker);
  selectedMarker = L.circleMarker([nearest.lat, nearest.lon], {
    radius: 6, weight: 2, color: "#111827", fillColor: "#fbbf24", fillOpacity: 0.9,
  }).addTo(map);
  showPoint(nearest.grid_id);
});

document.getElementById("emergency-select").addEventListener("change", (e) => {
  state.emergency = e.target.value;
  if (state.selectedGridId != null) showPoint(state.selectedGridId);
});

for (const btn of document.querySelectorAll(".season-toggle button")) {
  btn.addEventListener("click", () => {
    for (const b of document.querySelectorAll(".season-toggle button")) b.classList.remove("active");
    btn.classList.add("active");
    state.season = btn.dataset.season;
    if (state.selectedGridId != null) showPoint(state.selectedGridId);
  });
}

document.getElementById("about-link").addEventListener("click", (e) => {
  e.preventDefault();
  const section = document.getElementById("about-section");
  section.style.display = section.style.display === "none" ? "block" : "none";
});

loadPoints();
