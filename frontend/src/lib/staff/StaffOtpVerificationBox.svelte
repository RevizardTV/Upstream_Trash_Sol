<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import api from '#lib/api';
    import { goto } from '$app/navigation';

    type Props = {
        email: string;
        staffPayload: any;
        onExpired: () => void;
    };

    let { email, staffPayload, onExpired }: Props = $props();

    let otpCode = $state('');
    let timeLeft = $state(60);
    let timerText = $state('Expires in 60s | Max 3 Attempts Allowed');
    let timerClass = $state('text-xs text-slate-400 mt-2 font-mono text-center');
    let errorMessage = $state('');
    let isVerifying = $state(false);

    let timerInterval: any;

    onMount(() => {
        timerInterval = setInterval(() => {
            if (timeLeft <= 1) {
                clearInterval(timerInterval);
                timerText = 'Code expired. Please request a new OTP.';
                timerClass = 'text-xs text-rose-400 mt-2 font-mono text-center';
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

    async function handleVerifyAndRegister(e: SubmitEvent) {
        e.preventDefault();
        errorMessage = '';

        if (otpCode.trim().length !== 6) {
            errorMessage = 'Please enter the full 6-digit verification code.';
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
                // 2. Register Staff Account
                const regRes = await api.post('/api/staff/register', staffPayload);

                if (regRes.status === 200) {
                    if (timerInterval) clearInterval(timerInterval);
                    alert('Staff account registered and verified successfully!');
                    goto('/staff-login');
                } else {
                    errorMessage = regRes.data?.detail || 'Registration failed.';
                }
            }
        } catch (err: any) {
            errorMessage = err.response?.data?.detail || 'Invalid verification code or server error.';
        } finally {
            isVerifying = false;
        }
    }
</script>

<form onsubmit={handleVerifyAndRegister} class="space-y-4 mt-4 pt-4 border-t border-slate-700">
    {#if errorMessage}
        <div class="text-rose-400 text-xs text-center font-semibold" role="alert">
            {errorMessage}
        </div>
    {/if}

    <div>
        <label for="staffRegOtpCode" class="block text-sm font-medium text-slate-300 mb-1">Enter 6-Digit Staff Verification Code</label>
        <input 
            type="text" 
            id="staffRegOtpCode" 
            bind:value={otpCode} 
            maxlength="6" 
            placeholder="123456" 
            required
            class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-mono text-center text-lg tracking-widest focus:outline-none focus:border-emerald-500"
        >
        <p class={timerClass}>{timerText}</p>
    </div>

    <button 
        type="submit" 
        disabled={isVerifying || timeLeft <= 0} 
        class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/25 cursor-pointer">
        {#if isVerifying}
            <i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Verifying...
        {:else}
            Verify Code & Complete Registration
        {/if}
    </button>
</form>