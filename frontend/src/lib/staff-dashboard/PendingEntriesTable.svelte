<script lang="ts">
    type Entry = {
        entry_id: number;
        waste_category: string;
        weight_kg: number;
        payout_amount: number;
    };

    type Props = {
        userId: number;
        pendingEntries: Entry[];
        onReview: (entryId: number, action: 'approve' | 'decline', reason?: string) => void;
    };

    let { userId, pendingEntries, onReview }: Props = $props();

    function handleDecline(entryId: number) {
        const reason = prompt('Enter reason for declining this request:') || 'Declined by staff officer';
        onReview(entryId, 'decline', reason);
    }
</script>

<tr id={`dropdown-user-${userId}`} class="accordion-content bg-slate-950/80 border-b border-slate-800/80">
    <td colspan="7" class="p-4 sm:p-6">
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-inner">
            <div class="flex items-center justify-between mb-3 px-1">
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                    <i class="fa-solid fa-box-archive text-amber-400" aria-hidden="true"></i>
                    Pending Recycling Requests for Household #{userId}
                </h3>
                <span class="text-[11px] text-slate-500">Requires officer verification</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs border-collapse">
                    <thead>
                        <tr class="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase font-semibold">
                            <th class="py-2.5 px-4">Trash ID</th>
                            <th class="py-2.5 px-4">Trash Category</th>
                            <th class="py-2.5 px-4">Weight (in KG)</th>
                            <th class="py-2.5 px-4">Estimated Payout Amount</th>
                            <th class="py-2.5 px-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60">
                        {#if pendingEntries.length === 0}
                            <tr>
                                <td colspan="5" class="py-6 text-center text-slate-500 italic">
                                    No active pending requests for this household.
                                </td>
                            </tr>
                        {:else}
                            {#each pendingEntries as entry}
                                <tr class="hover:bg-slate-800/30 transition">
                                    <td class="py-3 px-4 font-mono text-slate-400">#TRASH-{entry.entry_id}</td>
                                    <td class="py-3 px-4 font-semibold text-white capitalize">{entry.waste_category}</td>
                                    <td class="py-3 px-4 font-mono text-slate-300">{entry.weight_kg.toFixed(2)} kg</td>
                                    <td class="py-3 px-4 font-bold text-emerald-400">₹{entry.payout_amount.toFixed(2)}</td>
                                    <td class="py-3 px-4 text-right">
                                        <div class="inline-flex items-center gap-2">
                                            <button 
                                                type="button" 
                                                onclick={() => onReview(entry.entry_id, 'approve')} 
                                                class="bg-lime-500 hover:bg-lime-400 text-slate-950 font-extrabold px-3.5 py-1.5 rounded-lg shadow-md transition text-[11px] tracking-wide uppercase cursor-pointer">
                                                Approve
                                            </button>
                                            <button 
                                                type="button" 
                                                onclick={() => handleDecline(entry.entry_id)} 
                                                class="bg-red-600 hover:bg-red-500 text-white font-extrabold px-3.5 py-1.5 rounded-lg shadow-md transition text-[11px] tracking-wide uppercase cursor-pointer">
                                                Decline
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            {/each}
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
    </td>
</tr>