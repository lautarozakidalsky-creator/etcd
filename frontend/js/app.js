/**
 * app.js
 * Consume el JSON generado por el watcher de Python
 * y actualiza la interfaz en tiempo real.
 */

// =============================================================================
// CONFIGURACIÓN
// =============================================================================

// Ruta al JSON (sale de frontend/ y entra a datos_publicos/)
const JSON_URL = '../datos_publicos/datos_heroes.json';

// Intervalo de actualización (milisegundos)
const UPDATE_INTERVAL = 2000;

// =============================================================================
// FUNCIONES
// =============================================================================

/**
 * Obtiene los datos del archivo JSON
 */
async function cargarDatos() {
    try {
        const respuesta = await fetch(JSON_URL, {
            cache: 'no-store'  // Evitar caché del navegador
        });
        
        if (!respuesta.ok) {
            throw new Error(`HTTP error! status: ${respuesta.status}`);
        }
        
        const datos = await respuesta.json();
        actualizarInterfaz(datos);
        actualizarEstado(true);
        
    } catch (error) {
        console.error("❌ Error cargando datos:", error);
        actualizarEstado(false);
    }
}

/**
 * Actualiza el estado de conexión en el header
 */
function actualizarEstado(online) {
    const statusDot = document.querySelector('.dot');
    const statusText = document.getElementById('status-text');
    
    if (online) {
        statusDot.classList.add('online');
        statusText.textContent = 'En línea';
        statusText.style.color = '#00ff88';
    } else {
        statusDot.classList.remove('online');
        statusText.textContent = 'Desconectado';
        statusText.style.color = '#ff6b6b';
    }
}

/**
 * Actualiza toda la interfaz con los nuevos datos
 */
function actualizarInterfaz(datos) {
    // Actualizar contador total
    const totalElement = document.getElementById('total-heroes');
    if (totalElement && datos.heroes) {
        totalElement.textContent = Object.keys(datos.heroes).length;
    }
    
    // Actualizar timestamp
    const timeElement = document.getElementById('last-update');
    if (timeElement && datos.timestamp) {
        const fecha = new Date(datos.timestamp);
        timeElement.textContent = fecha.toLocaleTimeString();
    }
    
    // Renderizar la grilla de héroes
    renderizarHeroes(datos.heroes);
}

/**
 * Renderiza las tarjetas de héroes en el DOM
 */
function renderizarHeroes(heroes) {
    const grid = document.getElementById('heroes-grid');
    
    if (!grid) return;
    
    // Limpiar grid
    grid.innerHTML = '';
    
    // Verificar si hay héroes
    if (!heroes || Object.keys(heroes).length === 0) {
        grid.innerHTML = '<div class="no-heroes">📭 No hay héroes activos actualmente</div>';
        return;
    }
    
    // Crear tarjeta para cada héroe
    Object.entries(heroes).forEach(([key, data]) => {
        const card = document.createElement('div');
        card.className = 'hero-card';
        
        // Extraer nombre de la clave (ej: /heroes/activo/gandalf -> gandalf)
        const nombre = key.split('/').pop() || key;
        
        // Construir HTML de propiedades
        let propiedadesHTML = '';
        if (typeof data === 'object' && data !== null) {
            Object.entries(data).forEach(([prop, valor]) => {
                propiedadesHTML += `
                    <div class="hero-property">
                        <span class="property-name">${prop}</span>
                        <span class="property-value">${valor}</span>
                    </div>
                `;
            });
        } else {
            propiedadesHTML = `
                <div class="hero-property">
                    <span class="property-name">valor</span>
                    <span class="property-value">${data}</span>
                </div>
            `;
        }
        
        card.innerHTML = `
            <h3>🦸 ${nombre}</h3>
            ${propiedadesHTML}
        `;
        
        grid.appendChild(card);
    });
}

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

// Cargar datos inmediatamente al iniciar
document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Dashboard de Héroes iniciado");
    cargarDatos();
    
    // Actualizar periódicamente
    setInterval(cargarDatos, UPDATE_INTERVAL);
});