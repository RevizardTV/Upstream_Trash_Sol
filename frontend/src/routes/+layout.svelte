<script lang="ts">
    import '../app.css'; // Global Tailwind styles

    let { children } = $props();
</script>

<div class="min-h-screen bg-slate-950 text-stone-100 selection:bg-emerald-500 selection:text-slate-950">
    {@render children()}
</div>