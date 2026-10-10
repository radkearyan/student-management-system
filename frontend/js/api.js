// API Fetch Helpers for Student Management System

const API = {
    async get(url) {
        try {
            const res = await fetch(url);
            return await res.json();
        } catch (e) {
            console.error(`GET ${url} failed`, e);
            return null;
        }
    },
    async post(url, data) {
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await res.json();
        } catch (e) {
            console.error(`POST ${url} failed`, e);
            return { success: false, message: "Server connection failed." };
        }
    },
    async put(url, data) {
        try {
            const res = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await res.json();
        } catch (e) {
            console.error(`PUT ${url} failed`, e);
            return { success: false, message: "Server connection failed." };
        }
    },
    async delete(url) {
        try {
            const res = await fetch(url, { method: 'DELETE' });
            return await res.json();
        } catch (e) {
            console.error(`DELETE ${url} failed`, e);
            return { success: false, message: "Server connection failed." };
        }
    }
};

async function apiFetch(url, method = 'GET', body = null) {
    const m = method.toUpperCase();
    try {
        const options = { method: m, headers: {} };
        if (body && (m === 'POST' || m === 'PUT')) {
            options.headers['Content-Type'] = 'application/json';
            options.body = typeof body === 'string' ? body : JSON.stringify(body);
        }
        const res = await fetch(url, options);
        return await res.json();
    } catch (e) {
        console.error(`${m} ${url} failed`, e);
        return { success: false, message: "Server connection failed." };
    }
}
