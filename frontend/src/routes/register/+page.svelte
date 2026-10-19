<script lang="ts">
    import ProfileForm from '$lib/profile/ProfileForm.svelte';
    import OtpVerificationBox from '$lib/profile/OtpVerificationBox.svelte';

    let isOtpSent = $state(false);
    let registeredEmail = $state('');
    let savedPayload = $state<any>(null);

    function handleOtpSent(email: string, profileData: any) {
        registeredEmail = email;
        savedPayload = profileData;
        isOtpSent = true;
    }

    function handleOtpExpired() {
        isOtpSent = false;
        alert('Verification code expired. Please request a new one.');
    }
</script>

<svelte:head>
    <title>EcoRecycle - Profile Registration</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>♻️</text></svg>">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</svelte:head>

<div class="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center p-6 w-full">
    <main class="max-w-xl w-full bg-slate-800/60 border border-slate-700/80 rounded-2xl p-8 shadow-xl">
        <!-- Back to Home Link -->
        <a href="/" class="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-emerald-400 transition mb-6">
            <i class="fa-solid fa-arrow-left" aria-hidden="true"></i> Back to Home
        </a>

        <header class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-xl">
                <i class="fa-solid fa-user-gear" aria-hidden="true"></i>
            </div>
            <div>
                <h1 class="text-xl font-bold text-white">Complete Your Profile</h1>
                <p class="text-slate-400 text-xs">Link your email, address, and payout account.</p>
            </div>
        </header>

        {#if !isOtpSent}
            <ProfileForm onOtpSent={handleOtpSent} />
        {:else}
            <OtpVerificationBox 
                email={registeredEmail} 
                profilePayload={savedPayload} 
                onExpired={handleOtpExpired} 
            />
        {/if}
    </main>
</div>