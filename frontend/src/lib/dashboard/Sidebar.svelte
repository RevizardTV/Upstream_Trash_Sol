<script lang="ts">
    import { goto } from '$app/navigation';

    // Type definition for props
    type Props = {
        activeView?: string;
        onViewChange: (view: string) => void;
        profileName?: string;
        profileEmail?: string;
        userUpi?: string;
    };

    // Apply the type to the destructured object, NOT inside $props()
    let { 
        activeView = 'view-options', 
        onViewChange, 
        profileName = 'Loading...', 
        profileEmail = '...', 
        userUpi = '' 
    }: Props = $props();

    function handleLogout() {
        localStorage.clear();
        sessionStorage.clear();
        goto('/login');
    }
</script>