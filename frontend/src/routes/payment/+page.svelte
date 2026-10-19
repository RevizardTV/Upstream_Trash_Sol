<script lang="ts">
    import { onMount } from 'svelte';
    import axios from 'axios';
    import Sidebar from '#lib/dashboard/Sidebar.svelte';
    import PaymentOptionsView from '#lib/dashboard/PaymentOptionsView.svelte';
    import RegisterPaymentView from '#lib/dashboard/RegisterPaymentView.svelte';
    import PendingQueueView from '#lib/dashboard/PendingQueueView.svelte';
    import ReviewedRequestsView from '#lib/dashboard/ReviewedRequestsView.svelte';
    import PaytGuideView from '#lib/dashboard/PaytGuideView.svelte';

    let activeView = $state('view-options');
    let currentUser = $state<any>(null);
    let summaryData = $state<any>({ total_earnings: 0, pending_release: 0, eco_credits: 0, entries: [] });
    let pendingEntries = $state<any[]>([]);
    let reviewedEntries = $state<any[]>([]);
    let totalPendingAmount = $state('₹0.00');
    let totalApprovedEarnings = $state('₹0.00');

    async function loadUserData() {
        const storedEmail = localStorage.getItem('user_email') || sessionStorage.getItem('user_email');
        if (!storedEmail) return;

        try {
            const res = await axios.get(`/api/user/profile?email=${encodeURIComponent(storedEmail)}`);
            if (res.data.status === 'success' && res.data.profile) {
                currentUser = res.data.profile;
                fetchDashboardData();
            }
        } catch (err) {
            console.error('Failed to load user profile:', err);
        }
    }

    async function fetchDashboardData() {
        if (!currentUser) return;
        try {
            const [summaryRes, pendingRes, reviewedRes] = await Promise.all([
                axios.get(`/api/recycling/summary?user_id=${currentUser.id}`),
                axios.get(`/api/recycling/pending-payments?user_id=${currentUser.id}`),
                axios.get(`/api/recycling/reviewed-requests?user_id=${currentUser.id}`)
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

    function handleViewChange(viewId: string) {
        activeView = viewId;
        if (currentUser) fetchDashboardData();
    }

    onMount(() => {
        loadUserData();
    });
</script>

<svelte:head>
    <title>EcoRecycle - Unified Payment Hub</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</svelte:head>

<div class="bg-slate-900 text-slate-100 min-h-screen flex relative overflow-x-hidden w-full">
    <!-- MASTER SIDEBAR -->
    <Sidebar 
        {activeView} 
        onViewChange={handleViewChange} 
        profileName={currentUser?.full_name || 'Eco Member'} 
        profileEmail={currentUser?.email || 'Loading...'} 
        userUpi={currentUser?.upi_id || ''} 
    />

    <!-- DYNAMIC VIEW CONTAINER -->
    <main class="flex-1 p-6 md:p-10 overflow-y-auto w-full max-w-full">
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
    </main>
</div>