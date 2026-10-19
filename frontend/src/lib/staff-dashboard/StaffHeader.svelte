<script lang="ts">
    type Props = {
        officerEmail: string;
        districtZonePrefix: string;
        districtPrefix: string;
        onLogout: () => void;
    };

    let { officerEmail, districtZonePrefix, districtPrefix, onLogout }: Props = $props();
</script>

<header class="bg-slate-900 border-b border-slate-800/80 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-bold text-xl shadow-lg shadow-amber-500/5">
                <i class="fa-solid fa-building-user" aria-hidden="true"></i>
            </div>
            <div>
                <h1 class="font-bold text-lg tracking-tight text-white flex items-center gap-2">
                    District Control Console
                </h1>
                <p class="text-xs text-slate-400">
                    Assigned Officer: <span class="text-slate-200 font-medium">{officerEmail}</span> 
                    <span class="mx-1 text-slate-600">|</span> 
                    District Zone Prefix: <span class="text-amber-400 font-semibold font-mono">{districtZonePrefix}</span> 
                    <span class="text-slate-400 text-[11px]">(District Prefix: <span class="font-mono">{districtPrefix}</span>)</span>
                </p>
            </div>
        </div>

        <button 
            type="button" 
            onclick={onLogout}
            class="flex items-center gap-2 px-3.5 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 border border-rose-500/20 hover:border-rose-500/40 transition text-xs font-semibold cursor-pointer">
            <i class="fa-solid fa-right-from-bracket" aria-hidden="true"></i>
            <span>Log Out</span>
        </button>
    </div>
</header>