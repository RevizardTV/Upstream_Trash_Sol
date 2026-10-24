<script lang="ts">
    type Props = {
        entries?: any[];
        totalApproved?: string;
    };

    let { entries = [], totalApproved = '₹0.00' }: Props = $props();
</script>

<div class="space-y-6">
    <header class="flex items-center justify-between mb-6">
        <div>
            <h1 class="text-2xl md:text-3xl font-bold text-white">Reviewed Requests</h1>
            <p class="text-slate-400 text-sm mt-1">Processed transactions and receipt generation.</p>
        </div>
        <div class="text-right">
            <span class="text-xs text-slate-400 uppercase tracking-wider block font-medium">Approved Lifetime Payouts</span>
            <span class="text-xl font-bold text-emerald-400">{totalApproved}</span>
        </div>
    </header>

    <div class="bg-slate-800/60 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl">
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
                <thead>
                    <tr class="text-slate-400 border-b border-slate-700/60 text-xs uppercase tracking-wider bg-slate-800/40">
                        <th class="pb-3 px-4">Entry ID</th>
                        <th class="pb-3 px-4">Category</th>
                        <th class="pb-3 px-4">Weight (kg)</th>
                        <th class="pb-3 px-4">Amount</th>
                        <th class="pb-3 px-4">Status</th>
                        <th class="pb-3 px-4 text-right">Record / Reason</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/40">
                    {#if entries.length === 0}
                        <tr><td colspan="6" class="py-8 text-center text-slate-500">No reviewed entries found.</td></tr>
                    {:else}
                        {#each entries as e}
                            {@const isApproved = e.status === 'approved'}
                            <tr class="border-b border-slate-700/40 hover:bg-slate-800/30 transition">
                                <td class="py-3.5 px-4 font-mono text-xs text-slate-400">#{e.entry_id}</td>
                                <td class="py-3.5 px-4 font-medium text-white">{e.waste_category}</td>
                                <td class="py-3.5 px-4 text-slate-300">{e.weight_kg} kg</td>
                                <td class="py-3.5 px-4 font-semibold text-emerald-400">₹{parseFloat(e.payout_amount).toFixed(2)}</td>
                                <td class="py-3.5 px-4">
                                    {#if isApproved}
                                        <span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs px-2.5 py-1 rounded-full font-medium inline-flex items-center gap-1.5">
                                            <i class="fa-solid fa-circle-check text-[10px]"></i> Approved
                                        </span>
                                    {:else}
                                        <span class="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs px-2.5 py-1 rounded-full font-medium inline-flex items-center gap-1.5">
                                            <i class="fa-solid fa-circle-xmark text-[10px]"></i> Declined
                                        </span>
                                    {/if}
                                </td>
                                <td class="py-3.5 px-4 text-right">
                                    {#if isApproved}
                                        <a href={`/api/recycling/receipt/${e.entry_id}`} target="_blank" class="text-xs text-emerald-400 hover:text-emerald-300 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 rounded-lg transition inline-flex items-center gap-2 font-medium">
                                            <i class="fa-solid fa-file-arrow-down text-sm"></i> <span>Receipt</span>
                                        </a>
                                    {:else}
                                        <div class="inline-flex items-center justify-end">
                                            <span 
                                                class="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg inline-flex items-center gap-2 font-medium max-w-60 text-left"
                                                title={e.rejection_reason || 'Declined by district officer'}
                                            >
                                                <i class="fa-solid fa-triangle-exclamation text-xs shrink-0"></i>
                                                <span class="truncate">{e.rejection_reason || 'Declined by district officer'}</span>
                                            </span>
                                        </div>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    {/if}
                </tbody>
            </table>
        </div>
    </div>
</div>