<script>
    import { page } from '$app/stores';
    let error = '';
    if ($page.error) {
        let error = $page.error.message;
    }
  </script>
  
  <h1>{$page.status}: {error}</h1>