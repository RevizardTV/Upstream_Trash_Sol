<script lang="ts">
    import axios from 'axios';

    const API_URL = '/api/auth';

    // Svelte 5 Runes State
    let step = $state<'email' | 'otp'>('email');
    let email = $state('');
    let otpCode = $state('');
    let errorMessage = $state('');
    let isLoading = $state(false);
    let timerText = $state('01:00');
    let isTimerExpired = $state(false);
    let timerInterval: ReturnType<typeof setInterval> | null = null;

    function startCountdownTimer(durationSeconds: number = 60) {
        if (timerInterval) clearInterval(timerInterval);
        let timeRemaining = durationSeconds;
        isTimerExpired = false;

        function tick() {
            if (timeRemaining <= 0) {
                if (timerInterval) clearInterval(timerInterval);
                timerText = 'Code expired. Please request a new one.';
                isTimerExpired = true;
                return;
            }
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            timerText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            timeRemaining--;
        }

        tick();
        timerInterval = setInterval(tick, 1000);
    }

    async function handleSendOTP(event: SubmitEvent) {
        event.preventDefault();
        errorMessage = '';
        if (!email.trim()) return;

        isLoading = true;
        try {
            await axios.post(`${API_URL}/request-otp`, { email_address: email.trim() });
            sessionStorage.setItem('pending_email', email.trim());
            step = 'otp';
            startCountdownTimer(60);
        } catch (err: any) {
            errorMessage = err.response?.data?.detail || err.message || 'Failed to send verification code.';
        } finally {
            isLoading = false;
        }
    }

    async function handleVerifyOTP(event: SubmitEvent) {
        event.preventDefault();
        errorMessage = '';
        if (!otpCode.trim()) return;

        isLoading = true;
        try {
            const response = await axios.post(`${API_URL}/verify-otp`, {
                email_address: email.trim(),
                otp_code: otpCode.trim()
            });

            if (response.data.status === 'success' || response.data.success) {
                if (timerInterval) clearInterval(timerInterval);
                sessionStorage.setItem('verified_email', email.trim());
                localStorage.setItem('user_email', email.trim());
                sessionStorage.removeItem('pending_email');

                window.location.href = '/payment';
            }
        } catch (err: any) {
            errorMessage = err.response?.data?.detail || err.message || 'Invalid verification code.';
            otpCode = '';
        } finally {
            isLoading = false;
        }
    }

    function handleChangeEmail() {
        if (timerInterval) clearInterval(timerInterval);
        step = 'email';
        otpCode = '';
        errorMessage = '';
    }
</script>

<div>
    <!-- Error Banner -->
    {#if errorMessage}
        <div class="text-rose-400 text-xs text-center mb-4 font-medium bg-rose-500/10 border border-rose-500/30 p-2.5 rounded-xl">
            {errorMessage}
        </div>
    {/if}

    {#if step === 'email'}
        <!-- View 1: Request OTP -->
        <form class="space-y-4" onsubmit={handleSendOTP}>
            <div>
                <label for="emailInput" class="block text-xs font-semibold text-slate-300 mb-1.5">Email Address</label>
                <div class="relative">
                    <input 
                        type="email" 
                        id="emailInput" 
                        required 
                        bind:value={email}
                        placeholder="example@gmail.com"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 placeholder-slate-500"
                    />
                    <i class="fa-solid fa-envelope absolute left-3.5 top-3 text-slate-500 text-xs"></i>
                </div>
            </div>

            <button 
                type="submit" 
                disabled={isLoading}
                class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 cursor-pointer">
                {#if isLoading}
                    <i class="fa-solid fa-spinner fa-spin text-xs"></i> Sending...
                {:else}
                    <i class="fa-solid fa-paper-plane text-xs"></i> Send Access Code
                {/if}
            </button>
            
            <p class="text-center text-xs text-slate-500 mt-4">
                Don't have a profile yet? <a href="/register-profile" class="text-emerald-400 hover:underline font-medium">Create One Here</a>
            </p>
        </form>
    {:else}
        <!-- View 2: Verify OTP -->
        <form class="space-y-4" onsubmit={handleVerifyOTP}>
            <div>
                <label for="otpInput" class="block text-xs font-semibold text-slate-300 mb-1.5">Enter 6-Digit Code</label>
                <div class="relative">
                    <input 
                        type="text" 
                        id="otpInput" 
                        required 
                        maxlength="6" 
                         
                        bind:value={otpCode}
                        placeholder="000000" 
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-center tracking-widest font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                    />
                </div>
            </div>

            <div class="text-center">
                <span class={`text-xs font-medium ${isTimerExpired ? 'text-rose-400' : 'text-slate-400'}`}>
                    {timerText}
                </span>
            </div>

            <button 
                type="submit" 
                disabled={isLoading || isTimerExpired}
                class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 cursor-pointer">
                {#if isLoading}
                    <i class="fa-solid fa-spinner fa-spin text-xs"></i> Verifying...
                {:else}
                    <i class="fa-solid fa-right-to-bracket text-xs"></i> Verify & Access Portal
                {/if}
            </button>

            <button 
                type="button" 
                onclick={handleChangeEmail} 
                class="w-full bg-transparent hover:bg-slate-700/50 text-slate-400 text-xs py-2 rounded-xl transition cursor-pointer">
                ← Change Email Address
            </button>
        </form>
    {/if}
</div>