<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import api from '#lib/api';
    import { goto } from '$app/navigation';

    type Props = {
        email: string;
        profilePayload: any;
        onExpired: () => void;
    };

    let { email, profilePayload, onExpired }: Props = $props();

    let otpCode = $state('');
    let timeLeft = $state(60);
    let timerText = $state('Expires in 60s | Max 3 Attempts Allowed');
    let errorMessage = $state('');
    let isVerifying = $state(false);

    let timerInterval: any;

    onMount(() => {
        timerInterval = setInterval(() => {
            if (timeLeft <= 1) {
                clearInterval(timerInterval);
                onExpired();
            } else {
                timeLeft--;
                timerText = `Expires in ${timeLeft}s | Max 3 Attempts Allowed`;
            }
        }, 1000);
    });

    onDestroy(() => {
        if (timerInterval) clearInterval(timerInterval);
    });

    async function handleVerifyAndSubmit(e: SubmitEvent) {
        e.preventDefault();
        errorMessage = '';

        if (otpCode.trim().length !== 6) {
            errorMessage = 'Please enter a valid 6-digit OTP code.';
            return;
        }

        isVerifying = true;
        try {
            // 1. Verify OTP
            const verifyRes = await api.post('/api/auth/verify-otp', {
                email_address: email,
                otp_code: otpCode.trim()
            });

            if (verifyRes.status === 200) {
                // 2. Save Profile Details
                const saveRes = await api.post('/api/auth/complete-profile', profilePayload);

                if (saveRes.status === 200 && saveRes.data.status === 'success') {
                    localStorage.setItem('user_id', saveRes.data.user_id);
                    alert('Email verified and profile created successfully!');
                    goto('/login');
                } else {
                    errorMessage = saveRes.data.detail || 'Profile saving failed.';
                }
            }
        } catch (err: any) {
            errorMessage = err.response?.data?.detail || 'Invalid verification code.';
        } finally {
            isVerifying = false;
        }
    }
</script>

<form onsubmit={handleVerifyAndSubmit} class="space-y-4 pt-4 border-t border-slate-700 mt-4">
    {#if errorMessage}
        <div class="text-red-400 text-xs text-center font-semibold" role="alert">
            {errorMessage}
        </div>
    {/if}

    <div>
        <label for="otpInput" class="block text-xs font-semibold text-slate-300 mb-1">Verification Code</label>
        <input 
            type="text" 
            id="otpInput" 
            bind:value={otpCode} 
            required 
            placeholder="Enter 6-digit OTP" 
            maxlength="6" 
            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-center tracking-widest text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
        >
    </div>

    <div class="text-center">
        <span class="text-xs text-slate-400 font-mono">{timerText}</span>
    </div>

    <button 
        type="submit" 
        disabled={isVerifying} 
        class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 cursor-pointer">
        {#if isVerifying}
            <i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Verifying...
        {:else}
            <i class="fa-solid fa-check-double" aria-hidden="true"></i> Verify OTP & Finalize Profile
        {/if}
    </button>
</form>