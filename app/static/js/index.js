// Funciones para el modal de anuncios
function abrirModal() {
  document.getElementById("modalAnuncio").style.display = "flex";
}

function cerrarModal() {
  document.getElementById("modalAnuncio").style.display = "none";
}

// Funciones para el modal de detalle de vivienda
function mostrarDetalleVivienda(elemento) {
  const card = elemento.closest(".casa-card");

  // Información de la vivienda
  const vivienda = {
    id_vivienda: card.getAttribute("data-id"),
    nombres: card.getAttribute("data-nombres"),
    apellidos: card.getAttribute("data-apellidos"),
    correo_electronico: card.getAttribute("data-correo"),
    estado_financiero: card.getAttribute("data-estado"),
    tiene_vehiculo:
      card.getAttribute("data-vehiculo") === "True" ||
      card.getAttribute("data-vehiculo") === "true",
  };

  // Construir el HTML del detalle
  const contenido = `
          <div class="info-row">
            <div class="info-label">🏠 Vivienda:</div>
            <div class="info-value">Casa ${vivienda.id_vivienda}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">👤 Residente:</div>
            <div class="info-value">${vivienda.nombres ? vivienda.nombres + " " + vivienda.apellidos : "Sin residente asignado"}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">📧 Correo:</div>
            <div class="info-value">${vivienda.correo_electronico || "No registrado"}</div>
          </div>
          
          <div class="info-row">
            <div class="info-label">💰 Estado financiero:</div>
            <div class="info-value">
              <span class="badge ${vivienda.estado_financiero === "al dia" ? "success" : vivienda.estado_financiero === "pendiente" ? "warning" : "danger"}">
                ${vivienda.estado_financiero || "No disponible"}
              </span>
            </div>
          </div>
          
          <div class="info-row">
            <div class="info-label">🚗 Tiene vehículo:</div>
            <div class="info-value">${vivienda.tiene_vehiculo ? "Sí" : "No"}</div>
          </div>
        `;

  // Actualizar el contenido del modal
  document.getElementById("detalleViviendaContent").innerHTML = contenido;
  document.getElementById("modalDetalleTitulo").innerText =
    `Casa ${vivienda.id_vivienda}`;

  // Mostrar el modal
  document.getElementById("modalDetalleVivienda").style.display = "flex";
}

function cerrarModalDetalle() {
  document.getElementById("modalDetalleVivienda").style.display = "none";
}

// Cerrar modales haciendo clic fuera de ellos
window.onclick = function (event) {
  const modalAnuncio = document.getElementById("modalAnuncio");
  const modalDetalle = document.getElementById("modalDetalleVivienda");

  if (event.target === modalAnuncio) {
    cerrarModal();
  }
  if (event.target === modalDetalle) {
    cerrarModalDetalle();
  }
};
