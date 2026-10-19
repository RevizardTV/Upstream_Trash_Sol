// src/lib/axios.js
import axios from 'axios';

// Pull from Vite environment variables, fallback to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true, // Crucial if you are sending/receiving cookies (like session/auth cookies)
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

export default api;