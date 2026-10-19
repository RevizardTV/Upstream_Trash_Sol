<script lang="ts">
    import PendingEntriesTable from '#lib/staff-dashboard/PendingEntriesTable.svelte';

    type Profile = {
        id: number;
        full_name: string;
        email: string;
        postal_code: string;
        premise_type?: string;
        upi_id?: string;
    };

    type Props = {
        profiles: Profile[];
        pendingEntriesMap: Record<number, any[]>;
        isLoading: boolean;
        onReviewEntry: (entryId: number, action: 'approve' | 'decline', reason?: string) => void;
    };

    let { profiles, pendingEntriesMap, isLoading, onReviewEntry }: Props = $props();

    let openDropdowns = $state<Record<number, boolean>>({});

    function toggleDropdown(userId: number) {
        openDropdowns[userId] = !openDropdowns[userId];
    }
</script>

<section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl shadow-xl overflow-hidden backdrop-blur-xl">
    <!-- Table Sub-Header -->
    <div class="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
            <i class="fa-solid fa-users text-amber-400 text-lg" aria-hidden="true"></i>
            <h2 class="font-bold text-base text-white">District Household Profiles</h2>
        </div>
        <span class="bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold px-3 py-1 rounded-full text-xs font-mono">
            {profiles.length} found
        </span>
    </div>

    <!-- Profiles Master Table -->
    <div class="overflow-x-auto">
        <table class="w-full text-left text-sm border-collapse">
            <thead>
                <tr class="bg-slate-950/40 text-slate-400 border-b border-slate-800/80 text-xs uppercase tracking-wider">
                    <th class="py-3.5 px-6 font-semibold">ID</th>
                    <th class="py-3.5 px-6 font-semibold">Full Name</th>
                    <th class="py-3.5 px-6 font-semibold">Email</th>
                    <th class="py-3.5 px-6 font-semibold">Pin Code</th>
                    <th class="py-3.5 px-6 font-semibold">Premise</th>
                    <th class="py-3.5 px-6 font-semibold">UPI ID</th>
                    <th class="py-3.5 px-6 font-semibold text-right">Pending Requests</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/50">
                {#if isLoading}
                    <tr>
                        <td colspan="7" class="py-12 text-center text-slate-500">
                            <i class="fa-solid fa-circle-notch fa-spin text-2xl mb-2 text-amber-500" aria-hidden="true"></i>
                            <p class="text-xs font-medium">Fetching registered district profiles...</p>
                        </td>
                    </tr>
                {:else if profiles.length === 0}
                    <tr>
                        <td colspan="7" class="py-12 text-center text-slate-500">
                            <i class="fa-solid fa-folder-open text-3xl mb-2 opacity-40" aria-hidden="true"></i>
                            <p class="text-xs font-medium">No household profiles found for this district prefix.</p>
                        </td>
                    </tr>
                {:else}
                    {#each profiles as user}
                        {@const entries = pendingEntriesMap[user.id] || []}
                        {@const isOpen = openDropdowns[user.id]}
                        <!-- svelte-ignore a11y_click_events_have_key_events -->
                        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                        <tr 
                            onclick={() => toggleDropdown(user.id)}
                            class="hover:bg-slate-800/40 transition cursor-pointer group border-b border-slate-800/50">
                            <td class="py-4 px-6 font-mono text-slate-400 text-xs">#{user.id}</td>
                            <td class="py-4 px-6 font-semibold text-white group-hover:text-amber-400 transition">{user.full_name}</td>
                            <td class="py-4 px-6 text-slate-300">{user.email}</td>
                            <td class="py-4 px-6">
                                <span class="bg-slate-800 border border-slate-700/80 px-2.5 py-1 rounded-md font-mono text-xs text-amber-400">
                                    {user.postal_code}
                                </span>
                            </td>
                            <td class="py-4 px-6 text-slate-300 capitalize">{user.premise_type || 'House'}</td>
                            <td class="py-4 px-6 font-mono text-xs text-slate-400">{user.upi_id || 'N/A'}</td>
                            <td class="py-4 px-6 text-right">
                                <button type="button" class="inline-flex items-center gap-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 px-3 py-1.5 rounded-xl font-bold text-xs transition cursor-pointer">
                                    <span>Pending Requests</span>
                                    <span class="bg-amber-500 text-slate-950 font-extrabold rounded-full px-2 py-0.5 text-[10px]">
                                        {entries.length}
                                    </span>
                                    <i class={`fa-solid fa-chevron-down text-[10px] ml-1 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true"></i>
                                </button>
                            </td>
                        </tr>

                        {#if isOpen}
                            <PendingEntriesTable 
                                userId={user.id} 
                                pendingEntries={entries} 
                                onReview={(id, act, reason) => {
                                    // Stop propagation context is handled inside sub-components via event
                                    onReviewEntry(id, act, reason);
                                }} 
                            />
                        {/if}
                    {/each}
                {/if}
            </tbody>
        </table>
    </div>
</section>