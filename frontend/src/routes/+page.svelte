<script lang="ts">
    import Navbar from '#lib/ui/Navbar.svelte';
    import HeroSection from '#lib/ui/HeroSection.svelte';
    import PaytExplanation from '#lib/ui/PayExplanation.svelte';
    import { goto } from '$app/navigation';

    function handleLoginRedirect() {
        goto('/login');
    }

    function handleSmoothScroll(e: MouseEvent) {
        e.preventDefault();
        const infoSection = document.getElementById('how-it-works');
        if (infoSection) {
            infoSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
</script>

<svelte:head>
    <title>EcoRecycle - Home page</title>
</svelte:head>

<!-- Added bg-slate-950 and text-stone-100 to unify the dark theme across the page and navbar -->
<div class="min-h-screen flex flex-col justify-between bg-slate-950 text-stone-100">
    <Navbar onLoginClick={handleLoginRedirect} />
    <HeroSection onHowItWorksClick={handleSmoothScroll} />
    <PaytExplanation />
</div>