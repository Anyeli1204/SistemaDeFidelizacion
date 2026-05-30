const STORAGE_KEY = "lab8_api_urls";

const els = {
  body: document.body,
  headerSub: document.getElementById("headerSub"),
  tabRestaurante: document.getElementById("tabRestaurante"),
  tabCliente: document.getElementById("tabCliente"),
  viewRestaurante: document.getElementById("view-restaurante"),
  viewCliente: document.getElementById("view-cliente"),
  urlRestaurante: document.getElementById("urlRestaurante"),
  urlConsulta: document.getElementById("urlConsulta"),
  statusRestaurante: document.getElementById("statusRestaurante"),
  statusConsulta: document.getElementById("statusConsulta"),
  formConsumo: document.getElementById("formConsumo"),
  formSaldo: document.getElementById("formSaldo"),
  resultConsumo: document.getElementById("resultConsumo"),
  resultSaldo: document.getElementById("resultSaldo"),
  saldoCard: document.getElementById("saldoCard"),
  saldoValor: document.getElementById("saldoValor"),
  saldoTarjeta: document.getElementById("saldoTarjeta"),
};

const SUBTITLES = {
  restaurante: "Registra los consumos de tus clientes",
  cliente: "Consulta tus puntos acumulados",
};

function loadUrls() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    if (saved.restaurante) els.urlRestaurante.value = saved.restaurante;
    if (saved.consulta) els.urlConsulta.value = saved.consulta;
  } catch {
    /* ignore */
  }
}

function saveUrls() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      restaurante: els.urlRestaurante.value.replace(/\/$/, ""),
      consulta: els.urlConsulta.value.replace(/\/$/, ""),
    })
  );
}

function getUrls() {
  return {
    restaurante: els.urlRestaurante.value.replace(/\/$/, ""),
    consulta: els.urlConsulta.value.replace(/\/$/, ""),
  };
}

function showView(name) {
  const isRestaurante = name === "restaurante";
  els.body.dataset.view = name;
  els.headerSub.textContent = SUBTITLES[name];
  els.tabRestaurante.classList.toggle("view-nav__btn--active", isRestaurante);
  els.tabCliente.classList.toggle("view-nav__btn--active", !isRestaurante);
  els.viewRestaurante.classList.toggle("view--active", isRestaurante);
  els.viewRestaurante.hidden = !isRestaurante;
  els.viewCliente.classList.toggle("view--active", !isRestaurante);
  els.viewCliente.hidden = isRestaurante;
}

document.querySelectorAll(".view-nav__btn").forEach((btn) => {
  btn.addEventListener("click", () => showView(btn.dataset.view));
});

function showResult(el, ok, message) {
  el.hidden = false;
  el.className = `result ${ok ? "result--ok" : "result--error"}`;
  el.textContent = message;
}

async function checkHealth(baseUrl, label, pillEl) {
  try {
    const res = await fetch(`${baseUrl}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    pillEl.textContent = "Servicio disponible";
    pillEl.className = "status-pill status-pill--ok";
  } catch {
    pillEl.textContent = "Servicio no disponible";
    pillEl.className = "status-pill status-pill--fail";
  }
}

async function refreshHealth() {
  const { restaurante, consulta } = getUrls();
  await Promise.all([
    checkHealth(restaurante, "", els.statusRestaurante),
    checkHealth(consulta, "", els.statusConsulta),
  ]);
}

function toIsoUtc(datetimeLocal) {
  if (!datetimeLocal) return null;
  const d = new Date(datetimeLocal);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

els.formConsumo.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {
    monto_consumido: Number(fd.get("monto")),
    numero_tarjeta: String(fd.get("tarjeta")).trim(),
    codigo_restaurante: String(fd.get("codigo")).trim(),
  };
  const email = String(fd.get("email") || "").trim();
  if (email) payload.email_cliente = email;
  const fecha = toIsoUtc(fd.get("fecha"));
  if (fecha) payload.fecha_hora = fecha;

  const { restaurante } = getUrls();
  try {
    const res = await fetch(`${restaurante}/api/consumos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showResult(
        els.resultConsumo,
        false,
        "No se pudo registrar el consumo. Revisa los datos e intenta de nuevo."
      );
      return;
    }
    showResult(els.resultConsumo, true, "Consumo registrado correctamente.");
  } catch {
    showResult(
      els.resultConsumo,
      false,
      "No hay conexión con el sistema. Verifica que el servicio del restaurante esté activo."
    );
  }
});

els.formSaldo.addEventListener("submit", async (e) => {
  e.preventDefault();
  const tarjeta = String(new FormData(e.target).get("tarjeta"))
    .trim()
    .replace(/\s|-/g, "");
  const { consulta } = getUrls();
  try {
    const res = await fetch(
      `${consulta}/api/cuentas/${encodeURIComponent(tarjeta)}/saldo`
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      els.saldoCard.hidden = true;
      const msg =
        res.status === 404
          ? "Aún no hay puntos para esta tarjeta. Registra un consumo primero."
          : "No se pudo consultar el saldo. Intenta de nuevo.";
      showResult(els.resultSaldo, false, msg);
      return;
    }
    els.resultSaldo.hidden = true;
    els.saldoCard.hidden = false;
    els.saldoValor.textContent = data.saldo_puntos;
    els.saldoTarjeta.textContent = `Tarjeta ****${String(data.numero_tarjeta).slice(-4)}`;
  } catch {
    els.saldoCard.hidden = true;
    showResult(
      els.resultSaldo,
      false,
      "No hay conexión. Espera un momento si acabas de registrar un consumo."
    );
  }
});

loadUrls();
saveUrls();
showView("restaurante");
refreshHealth();
setInterval(refreshHealth, 30000);
