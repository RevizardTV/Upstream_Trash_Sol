<script lang="ts">
    interface Props {
        onLoginClick?: () => void;
    }

    let { onLoginClick = () => {} }: Props = $props();
</script>

<header class="border-b border-stone-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
        <a href="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-emerald-800/30 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-xl group-hover:scale-105 group-hover:border-emerald-400 transition-all">
                <i class="fa-solid fa-seedling"></i>
            </div>
            <div>
                <span class="font-extrabold text-lg tracking-tight text-stone-100 group-hover:text-emerald-400 transition">EcoRecycle</span>
                <span class="block text-[10px] uppercase tracking-widest text-emerald-500/80 font-semibold -mt-1">PAYT Initiative</span>
            </div>
        </a>

        <div class="flex items-center gap-3">
            <a href="/staff-login" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-amber-400 hover:text-amber-300 hover:bg-amber-950/40 border border-amber-500/30 transition flex items-center gap-1.5">
                <i class="fa-solid fa-user-shield"></i> Staff Portal
            </a>
            <a href="/register-profile" class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-300 hover:text-stone-100 hover:bg-stone-800/60 border border-transparent hover:border-stone-700/80 transition flex items-center gap-2">
                <i class="fa-solid fa-id-card text-emerald-400"></i> Register Profile
            </a>
            <button 
                onclick={onLoginClick} 
                class="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs transition shadow-lg shadow-emerald-950/40 flex items-center gap-2 cursor-pointer">
                <i class="fa-solid fa-arrow-right-to-bracket"></i> Log In
            </button>
        </div>
    </div>
</header>