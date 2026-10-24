<script lang="ts">
    interface Props {
        onHowItWorksClick?: (e: MouseEvent) => void;
    }

    let { onHowItWorksClick = () => {} }: Props = $props();
</script>

<main class="max-w-6xl mx-auto px-6 py-16 flex-1 flex flex-col justify-center">
    <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
        <span class="inline-flex items-center gap-2 bg-emerald-950/80 border border-emerald-700/50 text-emerald-300 px-3.5 py-1.5 rounded-full text-xs font-medium tracking-wide">
            <i class="fa-solid fa-leaf text-emerald-400"></i> Smart Waste Management & Instant Rewards
        </span>
        <h1 class="text-4xl md:text-6xl font-extrabold text-stone-100 tracking-tight leading-tight">
            Turn Your Recyclables Into <span class="text-transparent bg-clip-text bg-linear-to-r from-emerald-400 via-teal-300 to-amber-300">Direct Earnings</span>
        </h1>
        <p class="text-stone-400 text-sm md:text-base leading-relaxed max-w-2xl mx-auto">
            Schedule drop-offs, track dry and e-waste weights transparently, and balance your waste fees with cash rebates through our dual-incentive Pay-As-You-Throw model.
        </p>
        <div class="flex flex-wrap items-center justify-center gap-4 pt-4">
            <a href="/register-profile" class="bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-slate-950 font-bold px-6 py-3.5 rounded-xl text-sm transition shadow-lg shadow-emerald-900/30 flex items-center gap-2">
                <i class="fa-solid fa-user-plus"></i> Complete Registration
            </a>
            <a 
                href="#how-it-works" 
                onclick={onHowItWorksClick}
                class="bg-stone-900 hover:bg-stone-800 text-stone-200 font-semibold px-6 py-3.5 rounded-xl text-sm border border-stone-800 hover:border-stone-700 transition flex items-center gap-2">
                <i class="fa-solid fa-circle-info text-amber-400"></i> How PAYT Works
            </a>
        </div>
    </div>
</main>