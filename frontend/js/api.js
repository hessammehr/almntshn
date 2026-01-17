// API client for backend communication

const API_BASE = '/api';

const api = {
    // Scan a barcode (check if we have it)
    async scan(barcode) {
        const response = await fetch(`${API_BASE}/inventory/scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ barcode })
        });
        return response.json();
    },

    // Quick add (scan and add 1)
    async quickAdd(barcode, name = null) {
        const response = await fetch(`${API_BASE}/inventory/quick-add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ barcode, name })
        });
        return response.json();
    },

    // Adjust quantity
    async adjustQuantity(barcode, delta) {
        const response = await fetch(`${API_BASE}/inventory/adjust`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ barcode, delta })
        });
        if (!response.ok) {
            throw new Error('Failed to adjust quantity');
        }
        return response.json();
    },

    // Get inventory list
    async getInventory(search = null) {
        let url = `${API_BASE}/inventory/`;
        if (search) {
            url += `?search=${encodeURIComponent(search)}`;
        }
        const response = await fetch(url);
        return response.json();
    },

    // Create item manually
    async createItem(item) {
        const response = await fetch(`${API_BASE}/items/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item)
        });
        return response.json();
    },

    // Delete item
    async deleteItem(itemId) {
        const response = await fetch(`${API_BASE}/items/${itemId}`, {
            method: 'DELETE'
        });
        return response.json();
    }
};
