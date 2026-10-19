<script lang="ts">
    import { onMount } from 'svelte';
    import axios from 'axios';
    import { goto } from '$app/navigation';
    import StaffHeader from '$lib/staff-dashboard/StaffHeader.svelte';
    import FilterSection from '$lib/staff-dashboard/FilterSection.svelte';
    import HouseholdProfilesTable from '$lib/staff-dashboard/HouseholdProfilesTable.svelte';

    let staffEmail = $state('');
    let staffPincode = $state('');
    let districtPrefix = $state('');
    let profiles = $state<any[]>([]);
    let pendingEntriesMap = $state<Record<number, any[]>>({});
    let isLoading = $state(true);

    let searchQuery = $state('');
    let pincodeQuery = $state('');

    function getCookie(name: string) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(';').shift();
        return null;
    }

    async function loadDistrictProfiles(search = '', pin = '') {
        if (!staffEmail || !staffPincode) return;

        isLoading = true;
        let url = `/api/admin/district-users?staff_pincode=${encodeURIComponent(staffPincode)}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (pin) url += `&exact_pincode=${encodeURIComponent(pin)}`;

        try {
            const res = await axios.get(url);
            if (res.status === 200) {
                profiles = res.data.profiles || [];

                // Fetch pending entries for each profile concurrently
                const entryPromises = profiles.map(async (user: any) => {
                    try {
                        const entriesRes = await axios.get(`/api/admin/user-pending-entries/${user.id}`);
                        return { userId: user.id, entries: entriesRes.data.entries || [] };
                    } catch {
                        return { userId: user.id, entries: [] };
                    }
                });

                const results = await Promise.all(entryPromises);
                const newMap: Record<number, any[]> = {};
                for (const item of results) {
                    newMap[item.userId] = item.entries;
                }
                pendingEntriesMap = newMap;
            }
        } catch (err: any) {
            if (err.response?.status === 401 || err.response?.status === 403) {
                goto('/staff-login');
            }
            console.error('Error loading district profiles:', err);
        } finally {
            isLoading = false;
        }
    }

    function handleFilterSubmit(search: string, pin: string) {
        loadDistrictProfiles(search, pin);
    }

    function handleResetFilters() {
        searchQuery = '';
        pincodeQuery = '';
        loadDistrictProfiles();
    }

    async function handleReviewEntry(entryId: number, action: 'approve' | 'decline', rejectionReason?: string) {
        const staffId = localStorage.getItem('staff_id') || sessionStorage.getItem('staff_id');

        try {
            const res = await axios.post(`/api/staff/entries/${entryId}/review`, {
                action: action,
                rejection_reason: rejectionReason || null,
                staff_id: staffId ? parseInt(staffId) : null
            });

            if (res.status === 200 && res.data.status === 'success') {
                loadDistrictProfiles(searchQuery, pincodeQuery);
            } else {
                alert(res.data.detail || 'Failed to update entry.');
            }
        } catch (err: any) {
            console.error('Failed to review entry:', err);
            alert(err.response?.data?.detail || 'Failed to review entry.');
        }
    }

    function handleLogout() {
        localStorage.clear();
        sessionStorage.clear();
        goto('/staff-login');
    }

    onMount(() => {
        const email = localStorage.getItem('staff_email') || sessionStorage.getItem('staff_email') || getCookie('staff_email');
        const pincode = localStorage.getItem('assigned_pincode') || sessionStorage.getItem('assigned_pincode') || getCookie('staff_pincode');

        if (!email || !pincode) {
            goto('/staff-login');
            return;
        }

        staffEmail = email;
        staffPincode = pincode;
        districtPrefix = pincode.substring(0, 3);

        loadDistrictProfiles();
    });
</script>

<svelte:head>
    <title>EcoRecycle - Staff Dashboard</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>♻️</text></svg>">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .accordion-content { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
    </style>
</svelte:head>

<div class="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans antialiased w-full">
    <!-- Top Navigation Header -->
    <StaffHeader 
        officerEmail={staffEmail} 
        districtZonePrefix={staffPincode} 
        {districtPrefix} 
        onLogout={handleLogout} 
    />

    <!-- Main Workspace Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <!-- Search & Filter Bar Section -->
        <FilterSection 
            bind:searchQuery 
            bind:pincodeQuery 
            onFilterSubmit={handleFilterSubmit} 
            onReset={handleResetFilters} 
        />

        <!-- District Household Profiles Table Workspace -->
        <HouseholdProfilesTable 
            {profiles} 
            {pendingEntriesMap} 
            {isLoading} 
            onReviewEntry={handleReviewEntry} 
        />
    </main>
</div>