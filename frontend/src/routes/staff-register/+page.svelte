<script lang="ts">
    import StaffRegisterForm from '$lib/staff/StaffRegisterForm.svelte';
    import StaffOtpVerificationBox from '$lib/staff/StaffOtpVerificationBox.svelte';

    let isOtpSent = $state(false);
    let registeredEmail = $state('');
    let savedStaffPayload = $state<any>(null);

    function handleOtpSent(email: string, staffData: any) {
        registeredEmail = email;
        savedStaffPayload = staffData;
        isOtpSent = true;
    }

    function handleOtpExpired() {
        isOtpSent = false;
    }
</script>

<svelte:head>
    <title>EcoRecycle - Staff Registration</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>♻️</text></svg>">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</svelte:head>

<div class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4 w-full">
    <div class="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        <!-- Back to Home Link -->
        <a href="/" class="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-emerald-400 transition mb-6">
            <i class="fa-solid fa-arrow-left" aria-hidden="true"></i> Back to Home
        </a>

        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-400 mb-4">
                <i class="fa-solid fa-user-shield text-2xl" aria-hidden="true"></i>
            </div>
            <h1 class="text-2xl font-bold text-white">Staff Registration</h1>
            <p class="text-slate-400 text-sm mt-1">Create a district officer account</p>
        </div>

        {#if !isOtpSent}
            <StaffRegisterForm onOtpSent={handleOtpSent} />
        {:else}
            <StaffOtpVerificationBox 
                email={registeredEmail} 
                staffPayload={savedStaffPayload} 
                onExpired={handleOtpExpired} 
            />
        {/if}

        <div class="mt-6 text-center text-sm text-slate-400">
            Already registered? <a href="/staff-login" class="text-emerald-400 hover:underline">Log in here</a>
        </div>
    </div>
</div>