<script lang="ts">
    type Props = {
        totalEarnings?: string;
        pendingRelease?: string;
        ecoCredits?: string;
        pendingCount?: number;
        onViewChange: (view: string) => void;
    };

    let { 
        totalEarnings = '₹0.00', 
        pendingRelease = '₹0.00', 
        ecoCredits = '0 pts', 
        pendingCount = 0, 
        onViewChange 
    }: Props = $props();
</script>

<div class="space-y-8">
    <header class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-white">Payment Portal</h1>
        <p class="text-slate-400 text-sm mt-1">Manage payout registrations and transaction options.</p>
    </header>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-slate-800/60 border border-slate-700/80 p-5 rounded-2xl shadow-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Earnings</span>
            <p class="text-2xl font-bold text-emerald-400 mt-2">{totalEarnings}</p>
        </div>
        <div class="bg-slate-800/60 border border-slate-700/80 p-5 rounded-2xl shadow-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Release</span>
            <p class="text-2xl font-bold text-amber-400 mt-2">{pendingRelease}</p>
        </div>
        <div class="bg-slate-800/60 border border-slate-700/80 p-5 rounded-2xl shadow-lg">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Eco Credits Balance</span>
            <p class="text-2xl font-bold text-sky-400 mt-2">{ecoCredits}</p>
        </div>
    </div>

    <!-- Quick Navigation Cards (Converted to interactive buttons for accessibility) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button 
            type="button" 
            onclick={() => onViewChange('view-register')} 
            class="text-left cursor-pointer bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 p-6 rounded-2xl transition shadow-lg w-full">
            <i class="fa-solid fa-plus-circle text-emerald-400 text-2xl mb-4"></i>
            <h3 class="text-lg font-bold text-white">Register Payment</h3>
            <p class="text-slate-400 text-sm mt-2">Log recycling volume or submit land-fill waste drop-offs.</p>
        </button>

        <button 
            type="button" 
            onclick={() => onViewChange('view-pending')} 
            class="text-left cursor-pointer bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 p-6 rounded-2xl transition shadow-lg w-full">
            <i class="fa-solid fa-hourglass-half text-amber-400 text-2xl mb-4"></i>
            <h3 class="text-lg font-bold text-white">Pending Queue</h3>
            <p class="text-slate-400 text-sm mt-2">Review ongoing entry verification statuses.</p>
            <span class="inline-block mt-4 text-xs font-semibold text-amber-400 bg-amber-400/10 px-3 py-1 rounded-full border border-amber-400/20">View {pendingCount} Pending</span>
        </button>

        <button 
            type="button" 
            onclick={() => onViewChange('view-reviewed')} 
            class="text-left cursor-pointer bg-slate-800/60 hover:bg-slate-800 border border-slate-700/80 p-6 rounded-2xl transition shadow-lg w-full">
            <i class="fa-solid fa-clipboard-check text-emerald-400 text-2xl mb-4"></i>
            <h3 class="text-lg font-bold text-white">Reviewed Requests</h3>
            <p class="text-slate-400 text-sm mt-2">Check finalized payouts and historical records.</p>
        </button>
    </div>
</div>