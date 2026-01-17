// Main application logic

let currentBarcode = null;
let currentProductInfo = null;
let scanCooldown = false;

// DOM elements
const elements = {
    tabs: document.querySelectorAll('.tab'),
    scanTab: document.getElementById('scan-tab'),
    inventoryTab: document.getElementById('inventory-tab'),
    scanResult: document.getElementById('scan-result'),
    resultContent: document.getElementById('result-content'),
    resultActions: document.getElementById('result-actions'),
    manualBarcode: document.getElementById('manual-barcode'),
    manualLookup: document.getElementById('manual-lookup'),
    searchInput: document.getElementById('search-input'),
    inventoryList: document.getElementById('inventory-list'),
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modal-title'),
    itemForm: document.getElementById('item-form'),
    formBarcode: document.getElementById('form-barcode'),
    formName: document.getElementById('form-name'),
    formBrand: document.getElementById('form-brand'),
    formQuantity: document.getElementById('form-quantity'),
    modalCancel: document.getElementById('modal-cancel')
};

// Tab switching
elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

function switchTab(tabName) {
    elements.tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
    elements.scanTab.classList.toggle('hidden', tabName !== 'scan');
    elements.inventoryTab.classList.toggle('hidden', tabName !== 'inventory');
    
    if (tabName === 'scan') {
        startScanner();
    } else {
        scanner.stop();
        loadInventory();
    }
}

// Scanner handling
async function startScanner() {
    try {
        await scanner.start(handleScan);
    } catch (err) {
        console.error('Failed to start scanner:', err);
        // Show manual entry as fallback
    }
}

async function handleScan(barcode) {
    if (scanCooldown) return;
    
    // Prevent rapid repeated scans
    scanCooldown = true;
    setTimeout(() => { scanCooldown = false; }, 1500);
    
    // Vibrate on scan (if supported)
    if (navigator.vibrate) {
        navigator.vibrate(100);
    }
    
    await lookupBarcode(barcode);
}

async function lookupBarcode(barcode) {
    currentBarcode = barcode;
    
    try {
        const result = await api.scan(barcode);
        showScanResult(result);
    } catch (err) {
        console.error('Scan error:', err);
    }
}

function showScanResult(result) {
    elements.scanResult.classList.remove('hidden');
    
    if (result.found_in_inventory) {
        // Item exists in our system
        const item = result.item;
        const qty = result.quantity;
        
        elements.resultContent.innerHTML = `
            <div class="result-item">
                ${item.image_url ? `<img src="${item.image_url}" class="result-image" alt="">` : ''}
                <div class="result-info">
                    <div class="result-name">${escapeHtml(item.name)}</div>
                    ${item.brand ? `<div class="result-brand">${escapeHtml(item.brand)}</div>` : ''}
                    <div class="result-quantity ${qty > 0 ? 'in-stock' : 'out-of-stock'}">
                        ${qty > 0 ? `${qty} in stock` : 'Out of stock'}
                    </div>
                </div>
            </div>
        `;
        
        elements.resultActions.innerHTML = `
            <button class="btn btn-icon" onclick="adjustQty('${item.barcode}', -1)">−</button>
            <button class="btn btn-icon" onclick="adjustQty('${item.barcode}', 1)">+</button>
            <button class="btn btn-success btn-small" onclick="quickAdd('${item.barcode}')">Add 1</button>
            <button class="btn btn-secondary btn-small" onclick="hideResult()">Done</button>
        `;
    } else {
        // New item
        currentProductInfo = result.product_info;
        
        if (result.product_info) {
            // Found in Open Food Facts
            const info = result.product_info;
            elements.resultContent.innerHTML = `
                <div class="result-item">
                    ${info.image_url ? `<img src="${info.image_url}" class="result-image" alt="">` : ''}
                    <div class="result-info">
                        <div class="result-name">${escapeHtml(info.name)}</div>
                        ${info.brand ? `<div class="result-brand">${escapeHtml(info.brand)}</div>` : ''}
                        <div class="result-quantity out-of-stock">New item</div>
                    </div>
                </div>
            `;
            
            elements.resultActions.innerHTML = `
                <button class="btn btn-success" onclick="quickAdd('${currentBarcode}')">Add to inventory</button>
                <button class="btn btn-secondary btn-small" onclick="showAddModal()">Edit & Add</button>
            `;
        } else {
            // Not found anywhere
            elements.resultContent.innerHTML = `
                <div class="result-new">
                    <p>Unknown product</p>
                    <div class="result-barcode">${escapeHtml(currentBarcode)}</div>
                </div>
            `;
            
            elements.resultActions.innerHTML = `
                <button class="btn" onclick="showAddModal()">Add manually</button>
                <button class="btn btn-secondary btn-small" onclick="hideResult()">Cancel</button>
            `;
        }
    }
}

function hideResult() {
    elements.scanResult.classList.add('hidden');
    currentBarcode = null;
    currentProductInfo = null;
}

async function quickAdd(barcode) {
    try {
        await api.quickAdd(barcode);
        // Refresh the result to show updated quantity
        await lookupBarcode(barcode);
    } catch (err) {
        console.error('Quick add error:', err);
    }
}

async function adjustQty(barcode, delta) {
    try {
        await api.adjustQuantity(barcode, delta);
        await lookupBarcode(barcode);
    } catch (err) {
        console.error('Adjust error:', err);
    }
}

// Manual barcode entry
elements.manualLookup.addEventListener('click', () => {
    const barcode = elements.manualBarcode.value.trim();
    if (barcode) {
        lookupBarcode(barcode);
        elements.manualBarcode.value = '';
    }
});

elements.manualBarcode.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        elements.manualLookup.click();
    }
});

// Modal handling
function showAddModal() {
    elements.modal.classList.remove('hidden');
    elements.modalTitle.textContent = 'Add Item';
    elements.formBarcode.value = currentBarcode;
    
    if (currentProductInfo) {
        elements.formName.value = currentProductInfo.name || '';
        elements.formBrand.value = currentProductInfo.brand || '';
    } else {
        elements.formName.value = '';
        elements.formBrand.value = '';
    }
    elements.formQuantity.value = 1;
    elements.formName.focus();
}

function hideModal() {
    elements.modal.classList.add('hidden');
}

elements.modalCancel.addEventListener('click', hideModal);
elements.modal.addEventListener('click', (e) => {
    if (e.target === elements.modal) hideModal();
});

elements.itemForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const barcode = elements.formBarcode.value;
    const name = elements.formName.value.trim();
    const brand = elements.formBrand.value.trim();
    const quantity = parseInt(elements.formQuantity.value) || 1;
    
    if (!name) return;
    
    try {
        // Create item
        await api.createItem({
            barcode,
            name,
            brand: brand || null,
            image_url: currentProductInfo?.image_url || null
        });
        
        // Add to inventory (quantity - 1 more times since createItem doesn't add inventory)
        await api.quickAdd(barcode);
        for (let i = 1; i < quantity; i++) {
            await api.adjustQuantity(barcode, 1);
        }
        
        hideModal();
        await lookupBarcode(barcode);
    } catch (err) {
        console.error('Add item error:', err);
    }
});

// Inventory list
let searchTimeout = null;

elements.searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadInventory(elements.searchInput.value);
    }, 300);
});

async function loadInventory(search = '') {
    try {
        const items = await api.getInventory(search);
        renderInventory(items);
    } catch (err) {
        console.error('Load inventory error:', err);
    }
}

function renderInventory(items) {
    if (items.length === 0) {
        elements.inventoryList.innerHTML = `
            <div class="empty-state">
                <p>No items found</p>
                <p>Scan a barcode to add items</p>
            </div>
        `;
        return;
    }
    
    elements.inventoryList.innerHTML = items.map(inv => {
        const item = inv.item;
        return `
            <div class="inventory-item">
                ${item.image_url 
                    ? `<img src="${item.image_url}" class="inventory-item-image" alt="">`
                    : '<div class="inventory-item-image"></div>'
                }
                <div class="inventory-item-info">
                    <div class="inventory-item-name">${escapeHtml(item.name)}</div>
                    ${item.brand ? `<div class="inventory-item-brand">${escapeHtml(item.brand)}</div>` : ''}
                </div>
                <div class="inventory-item-quantity">
                    <button class="btn btn-icon btn-small" onclick="adjustAndRefresh('${item.barcode}', -1)">−</button>
                    <span class="quantity-display">${inv.quantity}</span>
                    <button class="btn btn-icon btn-small" onclick="adjustAndRefresh('${item.barcode}', 1)">+</button>
                </div>
            </div>
        `;
    }).join('');
}

async function adjustAndRefresh(barcode, delta) {
    try {
        await api.adjustQuantity(barcode, delta);
        loadInventory(elements.searchInput.value);
    } catch (err) {
        console.error('Adjust error:', err);
    }
}

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startScanner();
});
