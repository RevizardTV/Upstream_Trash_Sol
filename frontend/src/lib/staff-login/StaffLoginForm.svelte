<script lang="ts">
    import axios from 'axios';

    type Props = {
        onLoginSuccess: (data: any) => void;
        onError: (msg: string) => void;
    };

    let { onLoginSuccess, onError }: Props = $props();

    let email = $state('');
    let password = $state('');
    let isLoading = $state(false);

    async function handleCredentialSubmit(e: SubmitEvent) {
        e.preventDefault();
        onError('');

        if (!email.trim() || !password.trim()) {
            onError('Please enter both email and password.');
            return;
        }

        isLoading = true;
        try {
            const response = await axios.post('/api/staff/login', {
                email: email.trim(),
                password: password.trim()
            });

            const data = response.data;

            if (response.status === 200 && data.status === 'otp_required') {
                // Synchronized session and local storage keys for staff dashboard consumption
                sessionStorage.setItem('staff_id', data.staff_id);
                sessionStorage.setItem('staff_email', data.email);
                sessionStorage.setItem('assigned_pincode', data.assigned_pincode);
                localStorage.setItem('staff_email', data.email);
                localStorage.setItem('assigned_pincode', data.assigned_pincode);

                onLoginSuccess(data);
            } else {
                onError(data.detail || 'Invalid staff credentials. Please try again.');
            }
        } catch (err: any) {
            console.error('Error during staff login:', err);
            onError(err.response?.data?.detail || 'A network error occurred while attempting to log in.');
        } finally {
            isLoading = false;
        }
    }
</script>

<form onsubmit={handleCredentialSubmit} class="space-y-4">
    <div>
        <label for="loginEmail" class="block text-xs font-semibold text-slate-300 mb-1.5">Official Email</label>
        <div class="relative">
            <input 
                type="email" 
                id="loginEmail" 
                bind:value={email} 
                required 
                placeholder="officer@ecorecycle.gov"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
            >
            <i class="fa-solid fa-envelope absolute left-3.5 top-3 text-slate-500 text-xs" aria-hidden="true"></i>
        </div>
    </div>

    <div>
        <label for="loginPassword" class="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
        <div class="relative">
            <input 
                type="password" 
                id="loginPassword" 
                bind:value={password} 
                required 
                placeholder="••••••••"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
            >
            <i class="fa-solid fa-lock absolute left-3.5 top-3 text-slate-500 text-xs" aria-hidden="true"></i>
        </div>
    </div>

    <button 
        type="submit" 
        disabled={isLoading}
        class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 cursor-pointer">
        {#if isLoading}
            <i class="fa-solid fa-spinner fa-spin text-xs" aria-hidden="true"></i> Verifying...
        {:else}
            <i class="fa-solid fa-paper-plane text-xs" aria-hidden="true"></i> Authenticate & Send Code
        {/if}
    </button>
</form>