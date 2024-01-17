// script.js
async function fetchPrices() {
    const response = await fetch('/prices');
    const data = await response.json();
    const gasolinePrice = document.getElementById('gasolinePrice');
    const dieselPrice = document.getElementById('dieselPrice');

    // Actualizar precios y animar si ha cambiado
    updatePrice(gasolinePrice, data.gasoline_price);
    updatePrice(dieselPrice, data.diesel_price);
}

function updatePrice(element, newPrice) {
    if (element.innerText !== newPrice.toString()) {
        element.innerText = newPrice;
        element.classList.add('updated');
        setTimeout(() => element.classList.remove('updated'), 1000);
    }
}

setInterval(fetchPrices, 1000);

// Forzar la primera actualización al cargar la página
document.addEventListener('DOMContentLoaded', fetchPrices);
