<script lang="ts">
    import { onMount } from 'svelte';
    import api from '#lib/api';
    import Sidebar from '#lib/dashboard/Sidebar.svelte';
    import PaymentOptionsView from '#lib/dashboard/PaymentOptionsView.svelte';
    import RegisterPaymentView from '#lib/dashboard/RegisterPaymentView.svelte';
    import PendingQueueView from '#lib/dashboard/PendingQueueView.svelte';
    import ReviewedRequestsView from '#lib/dashboard/ReviewedRequestsView.svelte';
    import PaytGuideView from '#lib/dashboard/PaytGuideView.svelte';

    // State Management
    let activeView = $state('view-options');
    let currentUser = $state<any>(null);
    let isLoadingProfile = $state(true);
    let profileError = $state('');

    // Dashboard Metrics State
    let summaryData = $state<any>({ total_earnings: 0, pending_release: 0, eco_credits: 0, entries: [] });
    let pendingEntries = $state<any[]>([]);
    let reviewedEntries = $state<any[]>([]);
    let totalPendingAmount = $state('₹0.00');
    let totalApprovedEarnings = $state('₹0.00');

    /**
     * Loads the authenticated user profile using stored credentials
     */
    async function loadUserData() {
        isLoadingProfile = true;
        profileError = '';

        const storedEmail = localStorage.getItem('user_email') || sessionStorage.getItem('user_email');
        if (!storedEmail) {
            profileError = 'No authenticated session found. Please log in.';
            isLoadingProfile = false;
            return;
        }

        try {
            // Include credentials so session cookies are automatically forwarded
            const res = await api.get(`/api/user/profile?email=${encodeURIComponent(storedEmail)}`, {
                withCredentials: true
            });

            if (res.data.status === 'success' && res.data.profile) {
                currentUser = res.data.profile;
                await fetchDashboardData();
            }
        } catch (err: any) {
            console.error('Failed to load user profile:', err);
            profileError = err.response?.data?.detail || 'Unable to retrieve user session.';
        } finally {
            isLoadingProfile = false;
        }
    }

    /**
     * Fetches user recycling summaries, pending payments, and reviewed logs in parallel
     */
    async function fetchDashboardData() {
        if (!currentUser) return;
        try {
            const [summaryRes, pendingRes, reviewedRes] = await Promise.all([
                api.get(`/api/recycling/summary?user_id=${currentUser.id}`, { withCredentials: true }),
                api.get(`/api/recycling/pending-payments?user_id=${currentUser.id}`, { withCredentials: true }),
                api.get(`/api/recycling/reviewed-requests?user_id=${currentUser.id}`, { withCredentials: true })
            ]);

            summaryData = summaryRes.data;
            pendingEntries = pendingRes.data.entries || [];
            totalPendingAmount = `₹${parseFloat(pendingRes.data.total_pending_amount || 0).toFixed(2)}`;
            
            reviewedEntries = reviewedRes.data.entries || [];
            totalApprovedEarnings = `₹${parseFloat(reviewedRes.data.total_approved_earnings || 0).toFixed(2)}`;
        } catch (err) {
            console.error('Error fetching dashboard metrics:', err);
        }
    }

    /**
     * View Switcher Handler
     */
    function handleViewChange(viewId: string) {
        activeView = viewId;
        if (currentUser) {
            fetchDashboardData();
        }
    }

    onMount(() => {
        loadUserData();
    });
</script>

<svelte:head>
    <title>EcoRecycle - Payment Hub</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</svelte:head>

<div class="bg-slate-950 text-slate-100 min-h-screen flex relative overflow-x-hidden w-full">
    <!-- MASTER SIDEBAR / PAYMENT NAVBAR -->
    <Sidebar 
        {activeView} 
        onViewChange={handleViewChange} 
        profileName={currentUser?.full_name || 'Eco Member'} 
        profileEmail={currentUser?.email || (isLoadingProfile ? 'Loading session...' : 'Guest User')} 
        userUpi={currentUser?.upi_id || ''} 
    />

    <!-- DYNAMIC VIEW CONTAINER -->
    <main class="flex-1 p-6 md:p-10 overflow-y-auto w-full max-w-full">
        {#if isLoadingProfile}
            <!-- LOADING SKELETON -->
            <div class="flex flex-col items-center justify-center h-full min-h-100 gap-3 text-slate-400">
                <i class="fa-solid fa-circle-notch fa-spin text-3xl text-emerald-500"></i>
                <p class="text-sm font-medium">Loading user profile & account ledger...</p>
            </div>
        {:else if profileError}
            <!-- SESSION ERROR STATE -->
            <div class="max-w-md mx-auto my-12 bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center shadow-xl">
                <div class="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-4 text-xl">
                    <i class="fa-solid fa-lock"></i>
                </div>
                <h2 class="text-lg font-bold text-slate-100 mb-2">Authentication Required</h2>
                <p class="text-xs text-slate-400 mb-6">{profileError}</p>
                <a href="/login" class="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-xs transition">
                    <i class="fa-solid fa-right-to-bracket"></i> Log In to Portal
                </a>
            </div>
        {:else}
            <!-- ACTIVE VIEWS -->
            {#if activeView === 'view-options'}
                <PaymentOptionsView 
                    totalEarnings={`₹${parseFloat(summaryData.total_earnings || 0).toFixed(2)}`}
                    pendingRelease={`₹${parseFloat(summaryData.pending_release || 0).toFixed(2)}`}
                    ecoCredits={`${summaryData.eco_credits || 0} pts`}
                    pendingCount={pendingEntries.length}
                    onViewChange={handleViewChange}
                />
            {:else if activeView === 'view-register'}
                <RegisterPaymentView 
                    userId={currentUser?.id || null} 
                    onSuccessSubmit={() => handleViewChange('view-pending')} 
                />
            {:else if activeView === 'view-pending'}
                <PendingQueueView 
                    entries={pendingEntries} 
                    totalPending={totalPendingAmount} 
                />
            {:else if activeView === 'view-reviewed'}
                <ReviewedRequestsView 
                    entries={reviewedEntries} 
                    totalApproved={totalApprovedEarnings} 
                />
            {:else if activeView === 'view-info'}
                <PaytGuideView />
            {/if}
        {/if}
    </main>
</div>