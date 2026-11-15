// reserva.js — consulta los horarios libres y actualiza el resumen de la reserva.
(function () {
  const form = document.getElementById("formReserva");
  const fecha = document.getElementById("fecha");
  const hora = document.getElementById("hora");
  const cont = document.getElementById("horarios");
  const errorCliente = document.getElementById("errorCliente");

  const elegido = (nombre) => form.querySelector(`input[name="${nombre}"]:checked`);

  function fechaBonita(iso) {
    if (!iso) return "";
    const [a, m, d] = iso.split("-").map(Number);
    return new Date(a, m - 1, d).toLocaleDateString("es-SV", { weekday: "long", day: "numeric", month: "long" });
  }

  function actualizarResumen() {
    const s = elegido("servicio_id");
    const b = elegido("barbero_id");
    document.getElementById("rServicio").textContent = s ? `${s.dataset.nombre} (${s.dataset.duracion} min)` : "—";
    document.getElementById("rBarbero").textContent = b ? b.dataset.nombre : "—";
    document.getElementById("rFecha").textContent = hora.value ? `${fechaBonita(fecha.value)}, ${hora.value}` : "—";
    document.getElementById("rTotal").textContent = s ? `$${s.dataset.precio}` : "—";
  }

  async function cargarHorarios() {
    const s = elegido("servicio_id");
    const b = elegido("barbero_id");
    if (!s || !b || !fecha.value) {
      actualizarResumen();
      return;
    }
    cont.innerHTML = '<div class="text-secondary"><span class="spinner-border spinner-border-sm"></span> Buscando horarios libres…</div>';
    try {
      const params = new URLSearchParams({ servicio_id: s.value, barbero_id: b.value, fecha: fecha.value });
      const resp = await fetch(`${URL_HORARIOS}?${params}`);
      const datos = await resp.json();
      if (!resp.ok) throw new Error(datos.error || "Error al consultar horarios");

      if (!datos.horarios.length) {
        hora.value = "";
        cont.innerHTML = `<div class="alert alert-warning mb-0"><i class="bi bi-calendar-x"></i> ${datos.mensaje}</div>`;
      } else {
        if (!datos.horarios.includes(hora.value)) hora.value = "";
        cont.innerHTML = `<p class="small text-secondary mb-2">${datos.horarios.length} horarios libres · toca uno para elegirlo</p>
          <div class="d-flex flex-wrap gap-2">${datos.horarios
            .map((h) => `<button type="button" class="btn slot ${h === hora.value ? "activo" : ""}" data-hora="${h}">${h}</button>`)
            .join("")}</div>`;
      }
    } catch (e) {
      cont.innerHTML = `<div class="alert alert-danger mb-0">No se pudieron cargar los horarios. ${e.message}</div>`;
    }
    actualizarResumen();
  }

  cont.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".slot");
    if (!btn) return;
    cont.querySelectorAll(".slot").forEach((x) => x.classList.remove("activo"));
    btn.classList.add("activo");
    hora.value = btn.dataset.hora;
    actualizarResumen();
  });

  form.addEventListener("change", (ev) => {
    if (["servicio_id", "barbero_id", "fecha"].includes(ev.target.name)) cargarHorarios();
  });

  // Validación rápida en el navegador (el servidor vuelve a validar todo).
  form.addEventListener("submit", (ev) => {
    const faltan = [];
    if (!elegido("servicio_id")) faltan.push("el servicio");
    if (!elegido("barbero_id")) faltan.push("el barbero");
    if (!hora.value) faltan.push("la hora");
    if (form.nombre.value.trim().length < 3) faltan.push("tu nombre");
    if (!/^[267]\d{3}-?\d{4}$/.test(form.telefono.value.trim())) faltan.push("un teléfono válido (ej. 7123-4567)");
    if (faltan.length) {
      ev.preventDefault();
      errorCliente.textContent = "Falta elegir o escribir: " + faltan.join(", ") + ".";
      errorCliente.classList.remove("d-none");
    }
  });

  cargarHorarios();
})();
