import type { ResumeListItem } from '@/lib/api/resume';

/**
 * In-memory cache of the last full resume list from GET /resumes/list.
 * Populated by the dashboard after load; consumed by /tailor to avoid a
 * redundant list request when navigating via "Create Resume".
 */
let cachedResumeList: ResumeListItem[] | null = null;

export function setResumeListCache(list: ResumeListItem[]): void {
  cachedResumeList = list;
}

export function getResumeListCache(): ResumeListItem[] | null {
  return cachedResumeList;
}

export function clearResumeListCache(): void {
  cachedResumeList = null;
}
