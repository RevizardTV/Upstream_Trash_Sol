<script lang="ts">
    type Props = {
        activeView: string;
        onViewChange: (viewId: string) => void;
        profileName?: string;
        profileEmail?: string;
        userUpi?: string;
    };

    let { 
        activeView = 'view-options', 
        onViewChange, 
        profileName = 'Eco Member', 
        profileEmail = 'Loading...', 
        userUpi = '' 
    }: Props = $props();

    function handleLogout() {
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = '/login';
    }

    const navItems = [
        { id: 'view-options', label: 'Dashboard Overview', icon: 'fa-chart-pie' },
        { id: 'view-register', label: 'Register Waste Payment', icon: 'fa-plus-circle' },
        { id: 'view-pending', label: 'Pending Queue', icon: 'fa-clock' },
        { id: 'view-reviewed', label: 'Reviewed & Paid', icon: 'fa-check-circle' },
        { id: 'view-info', label: 'PAYT Guide', icon: 'fa-book-open' }
    ];
</script>

<aside class="w-72 bg-slate-900 border-r border-slate-800 p-6 flex flex-col justify-between shrink-0 min-h-screen">
    <div>
        <!-- BRANDING -->
        <div class="flex items-center gap-3 mb-8">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-lg">
                E
            </div>
            <div>
                <span class="font-bold text-slate-100 tracking-wide block leading-tight">EcoRecycle</span>
                <span class="text-[10px] text-emerald-400 font-medium uppercase tracking-wider">Payment Portal</span>
            </div>
        </div>

        <!-- USER PROFILE CARD -->
        <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 mb-6">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center text-sm uppercase shrink-0">
                    {profileName.charAt(0)}
                </div>
                <div class="overflow-hidden">
                    <p class="text-xs font-semibold text-slate-200 truncate" title={profileName}>{profileName}</p>
                    <p class="text-[11px] text-slate-400 truncate" title={profileEmail}>{profileEmail}</p>
                </div>
            </div>
            {#if userUpi}
                <div class="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                    <span class="text-slate-500">Payout UPI:</span>
                    <span class="font-mono text-emerald-400 truncate max-w-[120px]">{userUpi}</span>
                </div>
            {/if}
        </div>

        <!-- NAVIGATION LINKS -->
        <nav class="space-y-1">
            {#each navItems as item}
                <button 
                    onclick={() => onViewChange(item.id)}
                    class={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                        activeView === item.id 
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm' 
                            : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent'
                    }`}
                >
                    <i class={`fa-solid ${item.icon} w-4 text-center text-xs`}></i>
                    <span>{item.label}</span>
                </button>
            {/each}
        </nav>
    </div>

    <!-- LOGOUT ACTION -->
    <div class="pt-4 border-t border-slate-800">
        <button 
            onclick={handleLogout}
            class="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-500/10 hover:border-rose-500/20 border border-transparent transition-all cursor-pointer"
        >
            <i class="fa-solid fa-right-from-bracket w-4 text-center text-xs"></i>
            <span>Log Out</span>
        </button>
    </div>
</aside>