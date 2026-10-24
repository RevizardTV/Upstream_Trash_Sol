<script lang="ts">
    import api from '#lib/api';
    import { onMount } from 'svelte';

    type Props = {
        userId: number | null;
        onSuccessSubmit: () => void;
    };

    let { userId, onSuccessSubmit }: Props = $props();

    let selectedMaterial = $state('plastic');
    let weight = $state<number | ''>('');
    let stationId = $state('');
    let payoutMethod = $state('upi');
    let isSubmitting = $state(false);
    let activeTip = $state<string | null>(null);
    let sensorStatus = $state('Listening for smart bin telemetry...');

    const categories = [
        { id: 'plastic', label: 'Plastic', rate: 15.00, type: 'payout', icon: 'fa-bottle-water', color: 'emerald', tip: 'Ensure bottles are rinsed and flattened. Caps can be included.' },
        { id: 'metal', label: 'Metal', rate: 45.00, type: 'payout', icon: 'fa-layer-group', color: 'amber', tip: 'Separate aluminum cans from heavy steel scrap for accurate weighing.' },
        { id: 'paper', label: 'Paper', rate: 8.00, type: 'payout', icon: 'fa-box', color: 'sky', tip: 'Keep cardboard dry and flattened. Waxed milk cartons are not accepted.' },
        { id: 'ewaste', label: 'E-Waste', rate: 65.00, type: 'payout', icon: 'fa-plug', color: 'purple', tip: 'Disconnect batteries and salvage high-value circuit boards separately where allowed.' },
        { id: 'landfill', label: 'Landfill', rate: -12.00, type: 'charge', icon: 'fa-trash-can', color: 'rose', tip: 'Non-recyclable waste incurs a PAYT tipping fee of ₹12/kg.' }
    ];

    let currentCategory = $derived(categories.find(c => c.id === selectedMaterial) || categories[0]);
    let liveTotal = $derived(typeof weight === 'number' ? currentCategory.rate * weight : 0);

    // Optional: Listen for simulated MQTT / WebSocket events coming from the global layout
    onMount(() => {
        function handleIoTSensorEvent(e: CustomEvent) {
            const data = e.detail;
            if (data && data.weight_kg) {
                weight = data.weight_kg;
                stationId = data.station_id || 'BIN-COIMBATORE-01';
                const match = categories.find(c => c.label.toLowerCase() === data.waste_category.toLowerCase());
                if (match) {
                    selectedMaterial = match.id;
                }
                sensorStatus = `Live telemetry received from ${stationId}!`;
                setTimeout(() => sensorStatus = 'Listening for smart bin telemetry...', 4000);
            }
        }

        window.addEventListener('iot-sensor-update' as any, handleIoTSensorEvent as any);
        return () => {
            window.removeEventListener('iot-sensor-update' as any, handleIoTSensorEvent as any);
        };
    });

    async function handleSubmit(e: SubmitEvent) {
        e.preventDefault();
        if (!userId) {
            alert('User profile not loaded properly.');
            return;
        }
        if (weight === '' || weight <= 0) {
            alert('Please enter a valid weight.');
            return;
        }

        isSubmitting = true;
        try {
            await api.post('/api/recycling/entry', {
                user_id: userId,
                waste_category: currentCategory.label,
                weight_kg: weight,
                payout_amount: liveTotal,
                station_id: stationId.trim() || 'STATION-GENERIC',
                payout_method: payoutMethod
            });

            alert('Waste entry registered successfully!');
            weight = '';
            stationId = '';
            onSuccessSubmit();
        } catch (err: any) {
            alert(`Error: ${err.response?.data?.detail || 'Submission failed'}`);
        } finally {
            isSubmitting = false;
        }
    }
</script>

<div class="space-y-8 w-full">
    <header class="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
            <h1 class="text-2xl md:text-3xl font-bold text-white">Register Waste Drop-Off</h1>
            <p class="text-slate-400 text-sm mt-1">Log waste categories to calculate payouts or calculate PAYT municipal disposal charges.</p>
        </div>
        <div class="bg-slate-900 border border-emerald-500/30 text-emerald-400 text-xs px-3 py-2 rounded-xl flex items-center gap-2 shadow-sm self-start">
            <span class="relative flex h-2.5 w-2.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span>{sensorStatus}</span>
        </div>
    </header>

    <form onsubmit={handleSubmit} class="w-full bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 md:p-8 space-y-6 shadow-xl">
        <div>
            <span id="category-group-label" class="block text-sm font-semibold text-slate-200 mb-4">1. Select Waste Category</span>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4" role="radiogroup" aria-labelledby="category-group-label">
                {#each categories as cat}
                    <label class={`cursor-pointer border rounded-xl p-4 flex flex-col items-center justify-between text-center gap-3 transition min-h-35 ${
                        selectedMaterial === cat.id 
                            ? (cat.type === 'charge' ? 'border-rose-500 bg-rose-500/10' : 'border-emerald-500 bg-emerald-500/10')
                            : 'border-slate-700/80 bg-slate-800/40 hover:border-slate-500'
                    }`}>
                        <input type="radio" name="material" value={cat.id} bind:group={selectedMaterial} class="sr-only">
                        <div class="flex flex-col items-center gap-1.5">
                            <i class={`fa-solid ${cat.icon} text-${cat.color}-400 text-3xl`}></i>
                            <span class="text-xs font-semibold text-slate-200">
                                {cat.label} 
                                <span class={`block text-[11px] text-${cat.color}-400 font-normal`}>
                                    {cat.type === 'charge' ? '' : '+' }₹{Math.abs(cat.rate)}/kg
                                </span>
                            </span>
                        </div>
                        <button type="button" aria-label={`Information about ${cat.label}`} onclick={() => activeTip = cat.tip} class="text-slate-400 hover:text-white transition p-1.5 rounded-full text-xs cursor-pointer">
                            <i class="fa-solid fa-circle-info text-base"></i>
                        </button>
                    </label>
                {/each}
            </div>
        </div>

        {#if activeTip}
            <div class="bg-slate-900/90 border border-slate-700/90 rounded-xl p-4 shadow-lg flex items-start justify-between gap-3">
                <div class="flex items-start gap-3">
                    <i class="fa-solid fa-circle-info text-emerald-400 text-lg mt-0.5"></i>
                    <div>
                        <h4 class="text-sm font-bold text-white mb-1">Category Guide</h4>
                        <p class="text-xs text-slate-300 leading-relaxed">{activeTip}</p>
                    </div>
                </div>
                <button type="button" aria-label="Close guide" onclick={() => activeTip = null} class="text-slate-400 hover:text-white p-1 cursor-pointer">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        {/if}

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div>
                <label for="stationInput" class="block text-sm font-semibold text-slate-200 mb-2">Station / Bin ID</label>
                <input id="stationInput" bind:value={stationId} type="text" placeholder="e.g. BIN-COIMBATORE-08" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <label for="weightInput" class="block text-sm font-semibold text-slate-200 mb-2">Measured Weight (kg)</label>
                <input id="weightInput" bind:value={weight} type="number" step="0.1" min="0" placeholder="0.0" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-emerald-500" required>
            </div>
            <div>
                <label for="payoutMethodSelect" class="block text-sm font-semibold text-slate-200 mb-2">Payout Method</label>
                <select id="payoutMethodSelect" bind:value={payoutMethod} class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-emerald-500">
                    <option value="upi">UPI / Direct Transfer</option>
                    <option value="credits">Eco Credits</option>
                </select>
            </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-700 flex items-center justify-between shadow-inner">
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-calculator text-slate-400 text-lg"></i>
                <span class="text-sm font-medium text-slate-300">Live Transaction Value:</span>
            </div>
            <span class={`text-lg font-bold ${liveTotal < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                ₹{Math.abs(liveTotal).toFixed(2)} ({currentCategory.type === 'charge' ? 'Disposal Fee' : 'Payout'})
            </span>
        </div>

        <button type="submit" disabled={isSubmitting} class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold py-3.5 rounded-xl transition flex items-center justify-center gap-2 cursor-pointer">
            {#if isSubmitting}
                <i class="fa-solid fa-spinner fa-spin"></i> Submitting...
            {:else}
                <i class="fa-solid fa-paper-plane"></i> Submit Entry
            {/if}
        </button>
    </form>
</div>