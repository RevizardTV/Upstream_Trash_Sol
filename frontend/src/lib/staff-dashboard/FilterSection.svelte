<script lang="ts">
    type Props = {
        searchQuery: string;
        pincodeQuery: string;
        onFilterSubmit: (search: string, pin: string) => void;
        onReset: () => void;
    };

    let { searchQuery = $bindable(''), pincodeQuery = $bindable(''), onFilterSubmit, onReset }: Props = $props();

    function handleSubmit(e: SubmitEvent) {
        e.preventDefault();
        onFilterSubmit(searchQuery, pincodeQuery);
    }
</script>

<section class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 sm:p-5 backdrop-blur-xl shadow-xl">
    <form onsubmit={handleSubmit} class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        <!-- Search Name / Email -->
        <div class="md:col-span-4 space-y-1.5">
            <label for="searchInput" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Search Household / Email</label>
            <div class="relative">
                <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-sm" aria-hidden="true"></i>
                <input 
                    type="text" 
                    id="searchInput" 
                    bind:value={searchQuery} 
                    placeholder="Name or email address..." 
                    class="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition"
                >
            </div>
        </div>

        <!-- Exact PIN Search -->
        <div class="md:col-span-4 space-y-1.5">
            <label for="pincodeInput" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Filter by Exact PIN Code</label>
            <div class="relative">
                <i class="fa-solid fa-location-dot absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-sm" aria-hidden="true"></i>
                <input 
                    type="text" 
                    id="pincodeInput" 
                    bind:value={pincodeQuery} 
                    placeholder="e.g. 641001" 
                    class="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition"
                >
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="md:col-span-4 flex items-end gap-3 pt-2 md:pt-0">
            <button type="submit" class="flex-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-2.5 px-4 rounded-xl shadow-lg shadow-amber-500/10 hover:shadow-amber-500/20 transition flex items-center justify-center gap-2 text-sm cursor-pointer">
                <i class="fa-solid fa-filter text-xs" aria-hidden="true"></i>
                <span>Apply Filters</span>
            </button>

            <button type="button" onclick={onReset} class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 hover:border-slate-600 transition text-sm font-semibold cursor-pointer">
                Reset
            </button>
        </div>
    </form>
</section>