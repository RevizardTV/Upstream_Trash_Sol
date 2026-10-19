<script lang="ts">
    type Props = {
        entries?: any[];
        totalPending?: string;
    };

    let { entries = [], totalPending = '₹0.00' }: Props = $props();
</script>

<div class="space-y-6">
    <header class="flex items-center justify-between mb-6">
        <div>
            <h1 class="text-2xl md:text-3xl font-bold text-white">Pending Requests</h1>
            <p class="text-slate-400 text-sm mt-1">Waste drop-offs awaiting municipal verification.</p>
        </div>
        <div class="text-right">
            <span class="text-xs text-slate-400 uppercase tracking-wider block font-medium">Pending Total</span>
            <span class="text-xl font-bold text-amber-400">{totalPending}</span>
        </div>
    </header>

    <div class="bg-slate-800/60 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl">
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
                <thead>
                    <tr class="text-slate-400 border-b border-slate-700/60 text-xs uppercase tracking-wider bg-slate-800/40">
                        <th class="p-4">Entry ID</th>
                        <th class="p-4">Category</th>
                        <th class="p-4">Weight</th>
                        <th class="p-4">Est. Amount</th>
                        <th class="p-4">Logged Time</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/40">
                    {#if entries.length === 0}
                        <tr><td colspan="5" class="text-center py-6 text-slate-400">No pending transactions in queue.</td></tr>
                    {:else}
                        {#each entries as entry}
                            {@const isCharge = entry.payout_amount < 0}
                            <tr class="hover:bg-slate-800/40 transition">
                                <td class="p-4 font-mono text-xs text-slate-300">#{entry.entry_id}</td>
                                <td class="p-4 font-medium text-white">{entry.waste_category}</td>
                                <td class="p-4 text-slate-300">{entry.weight_kg} kg</td>
                                <td class={`p-4 font-semibold ${isCharge ? 'text-rose-400' : 'text-emerald-400'}`}>
                                    {isCharge ? '-' : ''}₹{Math.abs(entry.payout_amount).toFixed(2)}
                                </td>
                                <td class="p-4 text-xs text-slate-400">
                                    {entry.created_at ? new Date(entry.created_at).toLocaleString() : 'Recent'}
                                </td>
                            </tr>
                        {/each}
                    {/if}
                </tbody>
            </table>
        </div>
    </div>
</div>