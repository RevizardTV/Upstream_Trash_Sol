<script lang="ts">
    import axios from 'axios';

    type Props = {
        onOtpSent: (email: string, staffData: any) => void;
    };

    let { onOtpSent }: Props = $props();

    let fullName = $state('');
    let email = $state('');
    let assignedPincode = $state('');
    let password = $state('');
    let isLoading = $state(false);
    let errorMessage = $state('');

    async function handleRequestOtp(e: SubmitEvent) {
        e.preventDefault();
        errorMessage = '';

        if (!fullName.trim() || !email.trim() || !assignedPincode.trim() || !password) {
            errorMessage = 'Please fill in all registration fields.';
            return;
        }

        isLoading = true;
        try {
            const res = await axios.post('/api/auth/request-otp', {
                email_address: email.trim(),
                type: 'staff'
            });

            if (res.status === 200 || res.data?.status === 'success') {
                const staffPayload = {
                    full_name: fullName.trim(),
                    email: email.trim(),
                    assigned_pincode: assignedPincode.trim(),
                    password: password
                };
                onOtpSent(email.trim(), staffPayload);
            }
        } catch (err: any) {
            errorMessage = err.response?.data?.detail || 'Failed to send authorization code.';
        } finally {
            isLoading = false;
        }
    }
</script>

<form onsubmit={handleRequestOtp} class="space-y-4">
    {#if errorMessage}
        <div class="text-rose-400 text-xs text-center font-semibold" role="alert">
            {errorMessage}
        </div>
    {/if}

    <div>
        <label for="fullName" class="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
        <input 
            type="text" 
            id="fullName" 
            bind:value={fullName} 
            required 
            placeholder="Officer Name"
            class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 transition"
        >
    </div>

    <div>
        <label for="email" class="block text-sm font-medium text-slate-300 mb-1">Official Email Address</label>
        <input 
            type="email" 
            id="email" 
            bind:value={email} 
            required 
            placeholder="officer@ecorecycle.gov"
            class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 transition"
        >
    </div>

    <div>
        <label for="assignedPincode" class="block text-sm font-medium text-slate-300 mb-1">Assigned Postal / PIN Code</label>
        <input 
            type="text" 
            id="assignedPincode" 
            bind:value={assignedPincode} 
            required 
            placeholder="641001" 
            maxlength="6"
            class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 transition"
        >
    </div>

    <div>
        <label for="password" class="block text-sm font-medium text-slate-300 mb-1">Password</label>
        <input 
            type="password" 
            id="password" 
            bind:value={password} 
            required 
            placeholder="••••••••"
            class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 transition"
        >
    </div>

    <button 
        type="submit" 
        disabled={isLoading}
        class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 text-slate-900 font-bold py-3 rounded-lg transition shadow-lg shadow-emerald-500/20 cursor-pointer">
        {#if isLoading}
            <i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Sending Code...
        {:else}
            Send Authorization Code
        {/if}
    </button>
</form>