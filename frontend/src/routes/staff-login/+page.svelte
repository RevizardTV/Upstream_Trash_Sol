<script lang="ts">
    import StaffLoginForm from '$lib/staff-login/StaffLoginForm.svelte';
    import StaffOtpForm from '$lib/staff-login/StaffOtpForm.svelte';

    let isOtpStage = $state(false);
    let errorMessage = $state('');
    let portalSubtitle = $state('Verify staff credentials to request authorization OTP.');

    function handleLoginSuccess(_data: any) {
        isOtpStage = true;
        errorMessage = '';
        portalSubtitle = 'Enter the 6-digit code sent to your official email.';
    }

    function handleChangeCredentials() {
        isOtpStage = false;
        errorMessage = '';
        portalSubtitle = 'Verify staff credentials to request authorization OTP.';
    }

    function handleError(msg: string) {
        errorMessage = msg;
    }
</script>

<svelte:head>
    <title>EcoRecycle - Staff Login</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>♻️</text></svg>">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</svelte:head>

<div class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4 w-full">
    <main class="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        <!-- Back to Home Link -->
        <a href="/" class="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-emerald-400 transition mb-6">
            <i class="fa-solid fa-arrow-left" aria-hidden="true"></i> Back to Home
        </a>

        <!-- Header -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-400 mb-4">
                <i class="fa-solid fa-shield-halved text-2xl" aria-hidden="true"></i>
            </div>
            <h1 class="text-2xl font-bold text-white tracking-tight">Staff Portal Login</h1>
            <p class="text-slate-400 text-xs mt-1">{portalSubtitle}</p>
        </div>

        <!-- Error Message Placeholder -->
        {#if errorMessage}
            <div class="text-rose-400 text-xs text-center mb-4 font-medium bg-rose-500/10 border border-rose-500/30 p-2.5 rounded-xl" role="alert">
                {errorMessage}
            </div>
        {/if}

        {#if !isOtpStage}
            <StaffLoginForm onLoginSuccess={handleLoginSuccess} onError={handleError} />
        {:else}
            <StaffOtpForm onError={handleError} onChangeCredentials={handleChangeCredentials} />
        {/if}

        <div class="mt-6 text-center text-xs text-slate-500">
            Need a staff account? <a href="/register-staff" class="text-emerald-400 hover:underline font-medium">Register here</a>
        </div>
    </main>
</div>