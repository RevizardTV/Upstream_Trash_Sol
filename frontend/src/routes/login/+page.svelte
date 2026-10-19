<script lang="ts">
    import LoginHeader from '#lib/auth/LoginHeader.svelte';
    import LoginForm from '#lib/auth/LoginForm.svelte';
</script>

<svelte:head>
    <title>EcoRecycle - Portal Login</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center p-6 bg-slate-900">
    <main class="max-w-md w-full bg-slate-800/60 border border-slate-700/80 rounded-2xl p-8 shadow-xl">
        <LoginHeader />
        <LoginForm />
    </main>
</div>