import { useEffect, useState } from "react";

// Tiny data-fetching hook: re-fetches whenever the url (incl. query string) changes.
export function useApi(url) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch((e) => !cancelled && setState({ data: null, error: e.message, loading: false }));
    return () => {
      cancelled = true;
    };
  }, [url]);

  return state;
}

export const fmt = (n) => (n ?? 0).toLocaleString("en-GB");
