// Server state for the listings tab lives here, not in the components: one hook owns the
// fetch, the refresh and the error, the components only render what it hands them.

import { useCallback, useEffect, useState } from "react";

import { type Listing, listListings } from "./api";

export function useListings() {
  const [items, setItems] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // useCallback keeps `refresh` referentially stable, so the mount effect below runs once
  // instead of on every render.
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listListings());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { items, error, setError, loading, refresh };
}
