<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import api from '#lib/api';
    import { goto } from '$app/navigation';

    type Props = {
        onError: (msg: string) => void;
        onChangeCredentials: () => void;
    };

    let { onError, onChangeCredentials }: Props = $props();

    let otpCode = $state('');
    let attemptsLeft = $state(3);
    let timerSeconds = $state(300);
    let timerDisplay = $state('Code expires in: 5:00');
    let isVerifying = $state(false);
    let isExpired = $state(false);

    let countdownInterval: any;

    onMount(() => {
        countdownInterval = setInterval(() => {
            if (timerSeconds <= 0) {
                clearInterval(countdownInterval);
                timerDisplay = 'OTP code expired. Please request a new code.';
                isExpired = true;
            } else {
                timerSeconds--;
                const minutes = Math.floor(timerSeconds / 60);
                const seconds = timerSeconds % 60;
                timerDisplay = `Code expires in: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            }
        }, 1000);
    });

    onDestroy(() => {
        if (countdownInterval) clearInterval(countdownInterval);
    });

    async function handleVerifyOtp(e: SubmitEvent) {
        e.preventDefault();
        onError('');

        if (!otpCode.trim() || otpCode.trim().length !== 6) {
            onError('Please enter a valid 6-digit OTP code.');
            return;
        }

        const email = sessionStorage.getItem('staff_email');
        if (!email) {
            onError('Session error. Please re-enter your credentials.');
            return;
        }

        isVerifying = true;
        try {
            const response = await api.post('/api/auth/verify-otp', {
                email_address: email,
                otp_code: otpCode.trim()
            });

            const data = response.data;

            if (response.status === 200 && data.status === 'success') {
                goto('/staff-dashboard');
            } else {
                attemptsLeft--;
                if (attemptsLeft <= 0) {
                    onError('Maximum attempts reached. Please reload and re-authenticate.');
                    isExpired = true;
                    if (countdownInterval) clearInterval(countdownInterval);
                } else {
                    onError(data.detail || 'Invalid OTP code.');
                }
            }
        } catch (err: any) {
            console.error('Error during OTP verification:', err);
            attemptsLeft--;
            if (attemptsLeft <= 0) {
                onError('Maximum attempts reached. Please reload and re-authenticate.');
                isExpired = true;
            } else {
                onError(err.response?.data?.detail || 'A network error occurred while verifying OTP.');
            }
        } finally {
            isVerifying = false;
        }
    }
</script>

<form onsubmit={handleVerifyOtp} class="space-y-4 mt-6 pt-6 border-t border-slate-800">
    <div>
        <label for="otpCode" class="block text-xs font-semibold text-slate-300 mb-1.5 text-center">Enter 6-Digit Code</label>
        <input 
            type="text" 
            id="otpCode" 
            bind:value={otpCode} 
            maxlength="6" 
            
            required 
            placeholder="000000"
            class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-center text-xl font-mono tracking-widest text-white focus:outline-none focus:border-emerald-500 transition"
        >
    </div>

    <!-- OTP Timer and Attempts Display -->
    <div class="text-center flex flex-col items-center gap-1">
        <span class="text-xs text-slate-400 font-medium">{timerDisplay}</span>
        {#if attemptsLeft < 3 && attemptsLeft > 0}
            <span class="text-xs text-amber-400 font-medium">Attempts remaining: {attemptsLeft}</span>
        {/if}
    </div>

    <button 
        type="submit" 
        disabled={isVerifying || isExpired}
        class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 cursor-pointer">
        {#if isVerifying}
            <i class="fa-solid fa-spinner fa-spin text-xs" aria-hidden="true"></i> Checking Code...
        {:else}
            <i class="fa-solid fa-right-to-bracket text-xs" aria-hidden="true"></i> Verify OTP & Access Portal
        {/if}
    </button>

    <button 
        type="button" 
        onclick={onChangeCredentials}
        class="w-full bg-transparent hover:bg-slate-800 text-slate-400 text-xs py-2 rounded-xl transition cursor-pointer">
        ← Re-enter Password
    </button>
</form>