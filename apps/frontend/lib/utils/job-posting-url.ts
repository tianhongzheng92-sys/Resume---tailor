/**
 * Normalize a job posting URL for duplicate comparison (scheme, host, path; no hash).
 * Accepts URLs with or without a scheme; non-URL text is lowercased and trimmed.
 */
export function normalizeJobPostingUrl(raw: string | null | undefined): string {
  const s = (raw ?? '').trim();
  if (!s) return '';
  try {
    const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(s) ? s : `https://${s}`;
    const u = new URL(withScheme);
    u.hash = '';
    const path = u.pathname.replace(/\/+$/, '') || '/';
    return `${u.protocol}//${u.host.toLowerCase()}${path}`.toLowerCase();
  } catch {
    return s.toLowerCase().replace(/\/+$/, '');
  }
}
