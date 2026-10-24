export function createWebSocketConnection(endpoint: string = '/ws/chat') {
    // Read directly from Vite's env variables to avoid SvelteKit type resolution issues
    const apiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.PUBLIC_API_BASE_URL;
    let wsUrl: string;

    if (apiBase) {
        const url = new URL(apiBase);
        const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        wsUrl = `${protocol}//${url.host}${cleanEndpoint}`;
    } else {
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        wsUrl = `ws://localhost:8000${cleanEndpoint}`;
    }

    return new WebSocket(wsUrl);
}