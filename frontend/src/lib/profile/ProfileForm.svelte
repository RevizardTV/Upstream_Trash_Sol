<script lang="ts">
    import api from '#lib/api';

    type Props = {
        onOtpSent: (email: string, profileData: any) => void;
    };

    let { onOtpSent }: Props = $props();

    let email = $state('');
    let fullName = $state('');
    let phoneNumber = $state('');
    let city = $state('');
    let postalCode = $state('');
    let premiseType = $state('house');
    let householdSize = $state<number | ''>(1);
    let upiId = $state('');

    let isLoading = $state(false);
    let errorMessage = $state('');

    async function handleRequestOtp(e: SubmitEvent) {
        e.preventDefault();
        errorMessage = '';

        if (!email.trim()) {
            errorMessage = 'Please provide a valid email address.';
            return;
        }

        isLoading = true;
        try {
            const res = await api.post('/api/auth/request-otp', {
                email_address: email.trim()
            });

            if (res.status === 200 || res.data.status === 'success') {
                const profilePayload = {
                    email: email.trim(),
                    full_name: fullName.trim(),
                    phone_number: phoneNumber.trim(),
                    city: city.trim(),
                    postal_code: postalCode.trim(),
                    premise_type: premiseType,
                    household_size: Number(householdSize) || 1,
                    upi_id: upiId.trim() || null
                };
                onOtpSent(email.trim(), profilePayload);
            }
        } catch (err: any) {
            errorMessage = err.response?.data?.detail || 'Unable to send verification code.';
        } finally {
            isLoading = false;
        }
    }
</script>

<form onsubmit={handleRequestOtp} class="space-y-4">
    {#if errorMessage}
        <div class="text-red-400 text-xs text-center mb-4 font-semibold" role="alert">
            {errorMessage}
        </div>
    {/if}

    <div>
        <label for="email" class="block text-xs font-semibold text-slate-300 mb-1">Email Address (OTP Verification Sent Here)</label>
        <div class="relative">
            <input 
                type="email" 
                id="email" 
                bind:value={email} 
                required 
                placeholder="name@example.com" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
            <i class="fa-solid fa-envelope absolute left-3.5 top-3 text-slate-500 text-xs" aria-hidden="true"></i>
        </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
            <label for="fullName" class="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
            <input 
                type="text" 
                id="fullName" 
                bind:value={fullName} 
                required 
                placeholder="Alex Morgan" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
        </div>
        <div>
            <label for="phoneNumber" class="block text-xs font-semibold text-slate-300 mb-1">Phone Number</label>
            <input 
                type="tel" 
                id="phoneNumber" 
                bind:value={phoneNumber} 
                required 
                placeholder="+91 98765 43210" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
        </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
            <label for="city" class="block text-xs font-semibold text-slate-300 mb-1">City / Ward</label>
            <input 
                type="text" 
                id="city" 
                bind:value={city} 
                required 
                placeholder="Coimbatore" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
        </div>
        <div>
            <label for="postalCode" class="block text-xs font-semibold text-slate-300 mb-1">PIN / Zip Code</label>
            <input 
                type="text" 
                id="postalCode" 
                bind:value={postalCode} 
                required 
                placeholder="641001" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
        </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
            <label for="premiseType" class="block text-xs font-semibold text-slate-300 mb-1">Premise Type</label>
            <select 
                id="premiseType" 
                bind:value={premiseType} 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500">
                <option value="house">Single Family House</option>
                <option value="apartment">Apartment / Flat</option>
                <option value="commercial">Commercial Business</option>
            </select>
        </div>
        <div>
            <label for="householdSize" class="block text-xs font-semibold text-slate-300 mb-1">Household Size</label>
            <input 
                type="number" 
                id="householdSize" 
                bind:value={householdSize} 
                min="1" 
                class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
        </div>
    </div>

    <div>
        <label for="upiId" class="block text-xs font-semibold text-slate-300 mb-1">Payout Method (UPI ID)</label>
        <input 
            type="text" 
            id="upiId" 
            bind:value={upiId} 
            placeholder="alex@okicici" 
            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
        >
    </div>

    <button 
        type="submit" 
        disabled={isLoading} 
        class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold py-3 rounded-xl transition mt-4 text-sm flex items-center justify-center gap-2 cursor-pointer">
        {#if isLoading}
            <i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Sending Code...
        {:else}
            <i class="fa-solid fa-paper-plane" aria-hidden="true"></i> Send OTP & Register Profile
        {/if}
    </button>
</form>