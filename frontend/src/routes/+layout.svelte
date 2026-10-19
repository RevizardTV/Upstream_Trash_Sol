<script lang="ts">
    import '../app.css';
    import axios from 'axios';
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { page } from '$app/state';

    // Configure global Axios defaults for all components across the app
    axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    axios.defaults.withCredentials = true;

    let { children } = $props();

    onMount(() => {
        const publicPaths = ['/login', '/staff-login', '/register', '/register-staff', '/register-profile', '/'];
        if (publicPaths.includes(page.url.pathname)) return;

        const userId = localStorage.getItem('user_id');
        const verifiedEmail = sessionStorage.getItem('verified_email') || localStorage.getItem('verified_email');
        const staffEmail = localStorage.getItem('staff_email') || sessionStorage.getItem('staff_email');
        const hasSessionCookie = document.cookie.split(';').some(item => 
            item.trim().startsWith('user_authenticated=') || item.trim().startsWith('staff_authenticated=')
        );

        if (!userId && !verifiedEmail && !staffEmail && !hasSessionCookie) {
            goto('/login');
        }
    });
</script>

<svelte:head>
    <!-- Global Redis Inspection & Management Console Toolkit -->
    <script src="/js/redis_check.js"></script>
    <!-- Database Admin Debug Toolkit -->
    <script src="/js/debug.js"></script>
</svelte:head>

{@render children()}