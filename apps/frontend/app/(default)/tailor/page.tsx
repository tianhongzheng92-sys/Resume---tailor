'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useResumePreview } from '@/components/common/resume_previewer_context';
import type { ImprovedResult } from '@/components/common/resume_previewer_context';
import type { ResumeData } from '@/components/dashboard/resume-component';
import {
  uploadJobDescriptions,
  previewImproveResume,
  confirmImproveResume,
  fetchResumeList,
  fetchJobDescriptionsByParent,
} from '@/lib/api/resume';
import {
  clearResumeListCache,
  getResumeListCache,
  setResumeListCache,
} from '@/lib/resume-list-cache';
import type { ResumeListItem } from '@/lib/api/resume';
import { fetchPromptConfig, type PromptOption } from '@/lib/api/config';
import { Dropdown } from '@/components/ui/dropdown';
import { useStatusCache } from '@/lib/context/status-cache';
import { Loader2, ArrowLeft, AlertTriangle, Settings } from 'lucide-react';
import { useTranslations } from '@/lib/i18n';
import { DiffPreviewModal } from '@/components/tailor/diff-preview-modal';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { calculateJdKeywordOverlap, extractKeywords } from '@/lib/utils/keyword-matcher';
import { normalizeJobPostingUrl } from '@/lib/utils/job-posting-url';

export default function TailorPage() {
  const { t } = useTranslations();
  const [jobDescription, setJobDescription] = useState('');
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [masterResumeId, setMasterResumeId] = useState<string | null>(null);
  const [masterResumes, setMasterResumes] = useState<ResumeListItem[]>([]);
  const [promptOptions, setPromptOptions] = useState<PromptOption[]>([]);
  const [selectedPromptId, setSelectedPromptId] = useState('other');
  const [promptLoading, setPromptLoading] = useState(false);
  const hasUserSelectedPrompt = useRef(false);
  const missingDiffConfirmInFlight = useRef(false);

  /** Prefer i18n; if key missing (t returns path), use API labels from backend. */
  const dropdownOptionFromPrompt = (opt: PromptOption) => {
    const labelKey = `tailor.promptOptions.${opt.id}.label`;
    const descKey = `tailor.promptOptions.${opt.id}.description`;
    const label = t(labelKey);
    const description = t(descKey);
    return {
      id: opt.id,
      label: label === labelKey ? opt.label : label,
      description: description === descKey ? opt.description : description,
    };
  };

  // Diff preview modal state
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [pendingResult, setPendingResult] = useState<ImprovedResult | null>(null);
  const [diffConfirmError, setDiffConfirmError] = useState<string | null>(null);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);
  const [showMissingDiffDialog, setShowMissingDiffDialog] = useState(false);
  const [missingDiffResult, setMissingDiffResult] = useState<ImprovedResult | null>(null);
  const [missingDiffError, setMissingDiffError] = useState<string | null>(null);
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<{
    resumeId: string;
    jobTitle: string;
    company: string;
    createdAt: string;
    duplicateByUrl?: boolean;
    matchedUrl?: string;
  } | null>(null);
  const [pendingGenerate, setPendingGenerate] = useState<{
    resumeId: string;
    description: string;
    postingUrl: string;
  } | null>(null);

  /** Past tailored resumes for selected master + fetched JD text (for keyword comparison). */
  const [pastTailoredForMaster, setPastTailoredForMaster] = useState<ResumeListItem[]>([]);
  const [jdContentByResumeId, setJdContentByResumeId] = useState<Record<string, string>>({});
  const [jdCompareLoading, setJdCompareLoading] = useState(false);
  const [debouncedJobDescription, setDebouncedJobDescription] = useState('');

  const router = useRouter();
  const searchParams = useSearchParams();
  const { setImprovedData } = useResumePreview();
  const {
    status: systemStatus,
    isLoading: statusLoading,
    incrementJobs,
    incrementImprovements,
    incrementResumes,
  } = useStatusCache();

  // Check if LLM is configured
  const isLlmConfigured = !statusLoading && systemStatus?.llm_configured;

  useEffect(() => {
    let cancelled = false;
    const urlMasterId = searchParams.get('master');
    const storedId =
      typeof window !== 'undefined' ? localStorage.getItem('master_resume_id') : null;

    const resolve = async () => {
      let list = getResumeListCache();
      if (!list) {
        list = await fetchResumeList(true);
        if (cancelled) return;
        setResumeListCache(list);
      }
      if (cancelled) return;
      const masters = list.filter((r) => r.is_master);
      setMasterResumes(masters);
      if (masters.length === 0) {
        router.replace('/dashboard');
        return;
      }
      const id =
        urlMasterId && masters.some((m) => m.resume_id === urlMasterId)
          ? urlMasterId
          : storedId && masters.some((m) => m.resume_id === storedId)
            ? storedId
            : masters[0].resume_id;
      setMasterResumeId(id);
      if (typeof window !== 'undefined' && id !== storedId) {
        localStorage.setItem('master_resume_id', id);
      }
    };

    resolve();
    return () => {
      cancelled = true;
    };
  }, [router, searchParams]);

  useEffect(() => {
    const id = window.setTimeout(() => setDebouncedJobDescription(jobDescription), 450);
    return () => window.clearTimeout(id);
  }, [jobDescription]);

  useEffect(() => {
    if (!masterResumeId) {
      setPastTailoredForMaster([]);
      setJdContentByResumeId({});
      return;
    }

    let cancelled = false;

    const loadPastJds = async () => {
      setJdCompareLoading(true);
      try {
        let list = getResumeListCache();
        if (!list) {
          list = await fetchResumeList(true);
          if (cancelled) return;
          setResumeListCache(list);
        }
        if (cancelled) return;
        const related = list.filter((r) => !r.is_master && r.parent_id === masterResumeId);
        setPastTailoredForMaster(related);

        let jdMap: Record<string, { job_id: string; content: string }> = {};
        try {
          jdMap = await fetchJobDescriptionsByParent(masterResumeId);
        } catch (e) {
          console.error('Batch job description load failed', e);
        }
        if (cancelled) return;
        const contentById: Record<string, string> = {};
        for (const r of related) {
          contentById[r.resume_id] = jdMap[r.resume_id]?.content ?? '';
        }
        setJdContentByResumeId(contentById);
      } catch (e) {
        console.error('Failed to load past job descriptions for comparison', e);
        if (!cancelled) {
          setPastTailoredForMaster([]);
          setJdContentByResumeId({});
        }
      } finally {
        if (!cancelled) setJdCompareLoading(false);
      }
    };

    loadPastJds();
    return () => {
      cancelled = true;
    };
  }, [masterResumeId]);

  useEffect(() => {
    let cancelled = false;

    const loadPromptConfig = async () => {
      setPromptLoading(true);
      try {
        const config = await fetchPromptConfig();
        if (!cancelled) {
          setPromptOptions(config.prompt_options || []);
          if (!hasUserSelectedPrompt.current) {
            setSelectedPromptId(config.default_prompt_id || 'other');
          }
        }
      } catch (err) {
        console.error('Failed to load prompt config', err);
      } finally {
        if (!cancelled) {
          setPromptLoading(false);
        }
      }
    };

    loadPromptConfig();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleTextareaKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') e.stopPropagation();
  };

  const normalizeText = (value: string) => value.trim().toLowerCase().replace(/\s+/g, ' ');

  const parseTitleAndCompany = (
    title: string | null | undefined
  ): { jobTitle: string; company: string } => {
    const raw = title?.trim() || '';
    const atIndex = raw.indexOf(' @ ');
    if (atIndex >= 0) {
      return {
        jobTitle: raw.slice(0, atIndex).trim() || '—',
        company: raw.slice(atIndex + 3).trim() || '—',
      };
    }
    return { jobTitle: raw || '—', company: '—' };
  };

  const formatDateTime = (value: string) => {
    if (!value) return t('common.unknown');
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return t('common.unknown');
    return date.toLocaleString(undefined, {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const extractTitleCompanyFromDescription = (
    description: string
  ): { jobTitle: string | null; company: string | null } => {
    const lines = description
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    const normalized = normalizeText(description);

    const titleMatch = normalized.match(
      /(?:job\s*title|title|position|role)\s*[:\-]\s*([^\n\r|]+)/i
    );
    const companyMatch = normalized.match(
      /(?:company|organization|employer)\s*[:\-]\s*([^\n\r|]+)/i
    );

    if (titleMatch?.[1] && companyMatch?.[1]) {
      return {
        jobTitle: titleMatch[1].trim(),
        company: companyMatch[1].trim(),
      };
    }

    // Common shorthand: "Role @ Company"
    const atLine = lines.find((line) => line.includes(' @ '));
    if (atLine) {
      const [rawTitle, rawCompany] = atLine.split(' @ ');
      return {
        jobTitle: rawTitle?.trim() || null,
        company: rawCompany?.trim() || null,
      };
    }

    return { jobTitle: null, company: null };
  };

  /** True when pasted JD matches a past role (title + company), same rules as duplicate detection. */
  const currentPasteMatchesPastRole = (
    normalizedDescription: string,
    extracted: { jobTitle: string | null; company: string | null },
    pastJobTitle: string,
    pastCompany: string
  ): boolean => {
    const nt = normalizeText(pastJobTitle);
    const nc = normalizeText(pastCompany);
    if (!nt || !nc) return false;
    const targetTitle = extracted.jobTitle ? normalizeText(extracted.jobTitle) : null;
    const targetCompany = extracted.company ? normalizeText(extracted.company) : null;
    if (targetTitle && targetCompany) {
      return nt === targetTitle && nc === targetCompany;
    }
    return normalizedDescription.includes(nt) && normalizedDescription.includes(nc);
  };

  const jdComparisonRows = useMemo(() => {
    const trimmed = debouncedJobDescription.trim();
    if (trimmed.length < 30 || pastTailoredForMaster.length === 0) return [];

    const normalizedDescription = normalizeText(trimmed);
    const extracted = extractTitleCompanyFromDescription(trimmed);

    const labelFor = (item: ResumeListItem) => {
      const full = item.title || item.filename || item.resume_id.slice(0, 8);
      const { jobTitle, company } = parseTitleAndCompany(full);
      if (jobTitle !== '—' && company !== '—') return `${jobTitle} @ ${company}`;
      return full;
    };

    const rows = pastTailoredForMaster
      .map((item) => {
        const storedJd = jdContentByResumeId[item.resume_id] ?? '';
        const hasStoredJd = Boolean(storedJd.trim());

        const fullTitle = item.title || item.filename || '';
        const parsedFromResume = parseTitleAndCompany(fullTitle);

        let matches = currentPasteMatchesPastRole(
          normalizedDescription,
          extracted,
          parsedFromResume.jobTitle === '—' ? '' : parsedFromResume.jobTitle,
          parsedFromResume.company === '—' ? '' : parsedFromResume.company
        );

        if (!matches && hasStoredJd) {
          const fromStored = extractTitleCompanyFromDescription(storedJd);
          if (fromStored.jobTitle && fromStored.company) {
            matches = currentPasteMatchesPastRole(
              normalizedDescription,
              extracted,
              fromStored.jobTitle,
              fromStored.company
            );
          }
        }

        if (!matches) return null;

        const refKw = extractKeywords(trimmed).size;
        const overlap =
          hasStoredJd && refKw > 0 && extractKeywords(storedJd).size > 0
            ? calculateJdKeywordOverlap(trimmed, storedJd)
            : {
                matchedCount: 0,
                referenceKeywordCount: refKw,
                otherKeywordCount: hasStoredJd ? extractKeywords(storedJd).size : 0,
                matchPercentage: 0,
                jaccardPercentage: 0,
              };

        return {
          resumeId: item.resume_id,
          label: labelFor(item),
          createdAt: item.created_at,
          hasStoredJd,
          ...overlap,
        };
      })
      .filter((row): row is NonNullable<typeof row> => row !== null)
      .sort((a, b) => {
        if (b.matchPercentage !== a.matchPercentage) return b.matchPercentage - a.matchPercentage;
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });

    return rows.slice(0, 12);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- currentPasteMatchesPastRole / extract helpers are pure; full deps would recompute every render
  }, [debouncedJobDescription, pastTailoredForMaster, jdContentByResumeId]);

  const jdCompareDetectedRole = useMemo(() => {
    const ex = extractTitleCompanyFromDescription(debouncedJobDescription.trim());
    return ex.jobTitle && ex.company ? ex : null;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- extractTitleCompanyFromDescription is pure
  }, [debouncedJobDescription]);

  const findDuplicateResume = async (
    resumeId: string,
    description: string,
    postingUrlRaw: string
  ) => {
    const normalizedDescription = normalizeText(description);
    if (!normalizedDescription) return null;

    let list = getResumeListCache();
    if (!list) {
      list = await fetchResumeList(true);
      setResumeListCache(list);
    }
    const relatedTailored = list.filter((item) => !item.is_master && item.parent_id === resumeId);
    if (relatedTailored.length === 0) return null;

    const normIncomingUrl = normalizeJobPostingUrl(postingUrlRaw);
    if (normIncomingUrl) {
      const urlMatches = relatedTailored.filter((item) => {
        const stored = item.job_source_url;
        if (!stored?.trim()) return false;
        return normalizeJobPostingUrl(stored) === normIncomingUrl;
      });
      const urlDup = [...urlMatches].sort(
        (a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
      )[0];
      if (urlDup) {
        const fullTitle = urlDup.title || urlDup.filename || '';
        const { jobTitle, company } = parseTitleAndCompany(fullTitle);
        return {
          resumeId: urlDup.resume_id,
          jobTitle,
          company,
          createdAt: formatDateTime(urlDup.created_at || ''),
          duplicateByUrl: true,
          matchedUrl: urlDup.job_source_url?.trim() || postingUrlRaw.trim(),
        };
      }
    }

    const extracted = extractTitleCompanyFromDescription(description);
    const matches = relatedTailored.filter((item) => {
      const fullTitle = item.title || item.filename || '';
      const { jobTitle, company } = parseTitleAndCompany(fullTitle);
      return currentPasteMatchesPastRole(
        normalizedDescription,
        extracted,
        jobTitle === '—' ? '' : jobTitle,
        company === '—' ? '' : company
      );
    });
    const duplicated = [...matches].sort(
      (a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
    )[0];
    if (!duplicated) return null;
    const fullTitle = duplicated.title || duplicated.filename || '';
    const { jobTitle, company } = parseTitleAndCompany(fullTitle);
    return {
      resumeId: duplicated.resume_id,
      jobTitle,
      company,
      createdAt: formatDateTime(duplicated.created_at || ''),
    };
  };

  const buildConfirmPayload = (result: ImprovedResult) => {
    if (!masterResumeId) {
      throw new Error('Master resume ID is missing.');
    }
    const resumePreview = result.data.resume_preview;
    if (!resumePreview || typeof resumePreview !== 'object' || Array.isArray(resumePreview)) {
      throw new Error('Resume preview data is invalid.');
    }
    const previewRecord = resumePreview as unknown as Record<string, unknown>;
    if (
      !previewRecord.personalInfo ||
      typeof previewRecord.personalInfo !== 'object' ||
      Array.isArray(previewRecord.personalInfo)
    ) {
      throw new Error('Resume preview data is invalid.');
    }
    return {
      resume_id: masterResumeId,
      job_id: result.data.job_id,
      improved_data: resumePreview as ResumeData,
      improvements:
        result.data.improvements?.map((item) => ({
          suggestion: item.suggestion,
          lineNumber: typeof item.lineNumber === 'number' ? item.lineNumber : null,
        })) ?? [],
    };
  };

  const confirmAndNavigate = async (result: ImprovedResult) => {
    const confirmed = await confirmImproveResume(buildConfirmPayload(result));
    incrementImprovements();
    incrementResumes();
    clearResumeListCache();
    setImprovedData(confirmed);

    const newResumeId = confirmed?.data?.resume_id;
    if (newResumeId) {
      router.push(`/resumes/${newResumeId}`);
    } else {
      router.push('/builder');
    }
  };

  const getGenerateValidationError = (trimmedDescription: string) => {
    if (!trimmedDescription) return null;
    if (trimmedDescription.length < 50) {
      return t('tailor.errors.jobDescriptionTooShort');
    }
    return null;
  };

  const runGenerate = async (resumeId: string, description: string, postingUrl: string) => {
    try {
      // 1. Upload Job Description
      // The API expects an array of strings
      const trimmedUrl = postingUrl.trim();
      const jobId = await uploadJobDescriptions(
        [description],
        resumeId,
        trimmedUrl ? [trimmedUrl] : undefined
      );
      incrementJobs(); // Update cached counter

      // 2. Preview Resume
      const result = await previewImproveResume(resumeId, jobId, selectedPromptId);

      if (!result?.data?.diff_summary || !result?.data?.detailed_changes) {
        console.warn('Diff data missing for tailor preview; requesting user confirmation.');
        setDiffConfirmError(null);
        setPendingResult(null);
        setShowDiffModal(false);
        setMissingDiffError(null);
        setMissingDiffResult(result);
        setShowMissingDiffDialog(true);
        return;
      }

      // 3. Show diff preview modal
      setDiffConfirmError(null);
      setMissingDiffError(null);
      setPendingResult(result);
      setShowDiffModal(true);
    } catch (err) {
      console.error(err);
      // Check for common error patterns
      const errorMessage = err instanceof Error ? err.message : '';
      if (
        errorMessage.toLowerCase().includes('api key') ||
        errorMessage.toLowerCase().includes('unauthorized') ||
        errorMessage.toLowerCase().includes('authentication') ||
        errorMessage.includes('401')
      ) {
        setError(t('tailor.errors.apiKeyError'));
      } else if (
        errorMessage.toLowerCase().includes('rate limit') ||
        errorMessage.includes('429')
      ) {
        setError(t('tailor.errors.rateLimit'));
      } else {
        setError(t('tailor.errors.failedToPreview'));
      }
    }
  };

  const handleGenerate = async () => {
    const trimmedDescription = jobDescription.trim();
    if (!trimmedDescription || !masterResumeId) return;
    const validationError = getGenerateValidationError(trimmedDescription);
    if (validationError) {
      setError(validationError);
      return;
    }
    const resumeId = masterResumeId;
    const trimmedUrl = jobPostingUrl.trim();
    setIsLoading(true);
    setError(null);
    try {
      const duplicate = await findDuplicateResume(resumeId, trimmedDescription, trimmedUrl);
      if (duplicate) {
        setPendingGenerate({
          resumeId,
          description: trimmedDescription,
          postingUrl: trimmedUrl,
        });
        setDuplicateInfo(duplicate);
        setShowDuplicateDialog(true);
        return;
      }
      await runGenerate(resumeId, trimmedDescription, trimmedUrl);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDuplicateContinue = async () => {
    if (!pendingGenerate || !masterResumeId) return;
    setShowDuplicateDialog(false);
    setIsLoading(true);
    setError(null);
    try {
      await runGenerate(
        pendingGenerate.resumeId,
        pendingGenerate.description,
        pendingGenerate.postingUrl
      );
    } finally {
      setPendingGenerate(null);
      setDuplicateInfo(null);
      setIsLoading(false);
    }
  };

  const handleDuplicateCancel = () => {
    setShowDuplicateDialog(false);
    setPendingGenerate(null);
    setDuplicateInfo(null);
  };

  // User confirms changes
  const handleConfirmChanges = async () => {
    // Guard against double-clicks - isLoading already tracks confirm in progress
    if (!pendingResult || isLoading) return;

    setIsLoading(true);
    setError(null);
    setDiffConfirmError(null);

    try {
      await confirmAndNavigate(pendingResult);
      setShowDiffModal(false);
      setPendingResult(null);
    } catch (err) {
      console.error(err);
      const errorMessage = t('tailor.errors.failedToConfirm');
      setError(errorMessage);
      setDiffConfirmError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // User rejects changes
  const handleRejectChanges = () => {
    setShowDiffModal(false);
    setPendingResult(null);
    setDiffConfirmError(null);
    setShowRegenerateDialog(true);
  };

  const handleCloseDiffModal = () => {
    setShowDiffModal(false);
    setPendingResult(null);
    setDiffConfirmError(null);
  };

  const handleCloseMissingDiffDialog = () => {
    setShowMissingDiffDialog(false);
    setMissingDiffResult(null);
    setMissingDiffError(null);
    missingDiffConfirmInFlight.current = false;
  };

  const handleMissingDiffConfirm = async () => {
    if (!missingDiffResult || isLoading || missingDiffConfirmInFlight.current) return;
    missingDiffConfirmInFlight.current = true;
    setIsLoading(true);
    setError(null);
    setMissingDiffError(null);
    try {
      await confirmAndNavigate(missingDiffResult);
      handleCloseMissingDiffDialog();
    } catch (err) {
      console.error(err);
      const errorMessage = t('tailor.errors.failedToConfirm');
      setError(errorMessage);
      setMissingDiffError(errorMessage);
    } finally {
      missingDiffConfirmInFlight.current = false;
      setIsLoading(false);
    }
  };

  const handleRegenerateConfirm = async () => {
    setShowRegenerateDialog(false);
    const trimmedDescription = jobDescription.trim();
    if (!trimmedDescription || !masterResumeId) return;
    const validationError = getGenerateValidationError(trimmedDescription);
    if (validationError) {
      setError(validationError);
      return;
    }
    const resumeId = masterResumeId;
    const trimmedUrl = jobPostingUrl.trim();
    setIsLoading(true);
    setError(null);
    try {
      await runGenerate(resumeId, trimmedDescription, trimmedUrl);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full bg-[#F6F5EE] flex flex-col items-center justify-center p-4 md:p-8 font-sans"
      style={{
        backgroundImage:
          'linear-gradient(rgba(29, 78, 216, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(29, 78, 216, 0.1) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }}
    >
      <div className="w-full max-w-4xl bg-white border border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,0.1)] p-8 md:p-12 lg:p-14 relative">
        {/* Back Button */}
        <Button variant="link" className="absolute top-4 left-4" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4" />
          {t('common.back')}
        </Button>

        <div className="mb-8 mt-4 text-center">
          <h1 className="font-serif text-4xl font-bold uppercase tracking-tight mb-2">
            {t('tailor.heroTitle')}
          </h1>
          <p className="font-mono text-sm text-blue-700 font-bold uppercase">
            {'// '}
            {t('tailor.pasteJobDescriptionBelow')}
          </p>
        </div>

        {/* LLM Not Configured Warning */}
        {!statusLoading && !isLlmConfigured && (
          <div className="mb-6 border-2 border-amber-500 bg-amber-50 p-4 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-mono text-sm font-bold uppercase tracking-wider text-amber-800">
                  {t('tailor.setupRequiredTitle')}
                </p>
                <p className="font-mono text-xs text-amber-700 mt-1">
                  {t('tailor.noApiKeyMessage')}
                </p>
                <Link
                  href="/settings"
                  className="inline-flex items-center gap-2 mt-3 text-amber-700 hover:text-amber-900 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span className="font-mono text-xs font-bold uppercase underline">
                    {t('tailor.configureApiKey')}
                  </span>
                </Link>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {masterResumes.length > 1 && (
            <Dropdown
              options={masterResumes.map((m) => ({
                id: m.resume_id,
                label: m.title || m.filename || m.resume_id.slice(0, 8),
                description:
                  m.processing_status === 'ready'
                    ? t('dashboard.status.ready')
                    : m.processing_status,
              }))}
              value={masterResumeId ?? ''}
              onChange={(id) => {
                setMasterResumeId(id);
                if (typeof window !== 'undefined') {
                  localStorage.setItem('master_resume_id', id);
                }
              }}
              label={t('tailor.masterResumeLabel')}
              description={t('tailor.masterResumeDescription')}
              disabled={isLoading}
            />
          )}

          <Dropdown
            options={
              promptOptions.length > 0
                ? promptOptions.map(dropdownOptionFromPrompt)
                : [
                    {
                      id: 'nudge',
                      label: t('tailor.promptOptions.nudge.label'),
                      description: t('tailor.promptOptions.nudge.description'),
                    },
                    {
                      id: 'keywords',
                      label: t('tailor.promptOptions.keywords.label'),
                      description: t('tailor.promptOptions.keywords.description'),
                    },
                    {
                      id: 'full',
                      label: t('tailor.promptOptions.full.label'),
                      description: t('tailor.promptOptions.full.description'),
                    },
                    {
                      id: 'other',
                      label: t('tailor.promptOptions.other.label'),
                      description: t('tailor.promptOptions.other.description'),
                    },
                  ]
            }
            value={selectedPromptId}
            onChange={(value) => {
              hasUserSelectedPrompt.current = true;
              setSelectedPromptId(value);
            }}
            label={t('tailor.promptLabel')}
            description={t('tailor.promptDescription')}
            disabled={isLoading || promptLoading}
          />

          <div className="space-y-1">
            <label className="block font-mono text-xs font-bold uppercase text-gray-700">
              {t('tailor.jobPostingUrlLabel')}
            </label>
            <Input
              type="text"
              inputMode="url"
              autoComplete="url"
              placeholder={t('tailor.jobPostingUrlPlaceholder')}
              value={jobPostingUrl}
              onChange={(e) => setJobPostingUrl(e.target.value)}
              disabled={isLoading}
              className="rounded-none border-2 border-black bg-[#F0F0E8] font-mono text-sm"
            />
            <p className="font-mono text-[11px] text-gray-600">{t('tailor.jobPostingUrlHint')}</p>
          </div>

          <div className="relative">
            <Textarea
              placeholder={t('tailor.jobDescriptionPlaceholder')}
              className="min-h-[300px] font-mono text-sm bg-[#F0F0E8] border-2 border-black focus:ring-0 focus:border-blue-700 resize-none p-4 rounded-none"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              onKeyDown={handleTextareaKeyDown}
              disabled={isLoading}
            />
            <div className="absolute bottom-2 right-2 text-xs font-mono text-gray-400 pointer-events-none">
              {t('tailor.charactersCount', { count: jobDescription.length })}
            </div>
          </div>

          {pastTailoredForMaster.length > 0 && (
            <div className="border-2 border-black bg-[#F0F0E8] p-4 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.08)]">
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-gray-800 mb-1">
                {t('tailor.jdCompare.title')}
              </h3>
              <p className="font-mono text-[11px] text-gray-600 mb-2 leading-relaxed">
                {t('tailor.jdCompare.hint')}
              </p>
              {jdCompareDetectedRole && (
                <p className="font-mono text-[11px] font-bold text-blue-800 mb-3 uppercase tracking-wide">
                  {t('tailor.jdCompare.comparingAs', {
                    title: jdCompareDetectedRole.jobTitle ?? '',
                    company: jdCompareDetectedRole.company ?? '',
                  })}
                </p>
              )}
              {jdCompareLoading ? (
                <div className="flex items-center gap-2 font-mono text-xs text-gray-600">
                  <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                  {t('tailor.jdCompare.loading')}
                </div>
              ) : debouncedJobDescription.trim().length < 30 ? (
                <p className="font-mono text-xs text-gray-500">{t('tailor.jdCompare.pasteMore')}</p>
              ) : jdComparisonRows.length === 0 ? (
                <div className="space-y-2">
                  <p className="font-mono text-xs text-gray-500">
                    {t('tailor.jdCompare.noMatchingRole')}
                  </p>
                  {Object.values(jdContentByResumeId).every((c) => !c?.trim()) && (
                    <p className="font-mono text-[10px] text-gray-400">
                      {t('tailor.jdCompare.noSavedJdFootnote')}
                    </p>
                  )}
                </div>
              ) : (
                <ul className="space-y-0 border border-black divide-y divide-gray-300 bg-white">
                  {jdComparisonRows.map((row) => (
                    <li key={row.resumeId}>
                      <button
                        type="button"
                        className="w-full text-left px-3 py-2.5 hover:bg-blue-50/60 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                        onClick={() => router.push(`/resumes/${row.resumeId}`)}
                      >
                        <div className="min-w-0">
                          <div className="font-mono text-xs font-bold text-gray-900 truncate">
                            {row.label}
                          </div>
                          <div className="font-mono text-[10px] text-emerald-800 uppercase mt-0.5">
                            {t('tailor.jdCompare.roleMatchBadge')}
                          </div>
                          <div className="font-mono text-[10px] text-gray-500 uppercase mt-0.5">
                            {t('tailor.jdCompare.rowCreated')}: {formatDateTime(row.createdAt)}
                          </div>
                        </div>
                        <div className="flex flex-col items-start sm:items-end shrink-0 gap-0.5">
                          {row.hasStoredJd ? (
                            <>
                              <span className="font-mono text-sm font-bold text-blue-800">
                                {t('tailor.jdCompare.matchRate')}: {row.matchPercentage}%
                              </span>
                              <span className="font-mono text-[10px] text-gray-600">
                                {t('tailor.jdCompare.matchedOfTotal', {
                                  matched: row.matchedCount,
                                  total: row.referenceKeywordCount,
                                })}
                              </span>
                              <span className="font-mono text-[10px] text-gray-500">
                                {t('tailor.jdCompare.jaccard', { percent: row.jaccardPercentage })}
                              </span>
                            </>
                          ) : (
                            <span className="font-mono text-[10px] text-gray-500 text-right max-w-[14rem]">
                              {t('tailor.jdCompare.keywordsUnavailable')}
                            </span>
                          )}
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm font-mono flex items-center gap-2">
              <span>!</span> {error}
            </div>
          )}

          <Button
            size="lg"
            onClick={handleGenerate}
            disabled={
              isLoading ||
              statusLoading ||
              !masterResumeId ||
              !jobDescription.trim() ||
              !isLlmConfigured
            }
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('common.processing')}
              </>
            ) : statusLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('common.checking')}
              </>
            ) : !isLlmConfigured ? (
              t('tailor.configureApiKeyFirst')
            ) : (
              t('tailor.generateTailored')
            )}
          </Button>
        </div>
      </div>

      {/* Diff preview modal */}
      {showDiffModal && pendingResult && (
        <DiffPreviewModal
          isOpen={showDiffModal}
          onClose={handleCloseDiffModal}
          onReject={handleRejectChanges}
          onConfirm={handleConfirmChanges}
          diffSummary={pendingResult?.data?.diff_summary}
          detailedChanges={pendingResult?.data?.detailed_changes}
          errorMessage={diffConfirmError ?? undefined}
        />
      )}

      <ConfirmDialog
        open={showRegenerateDialog}
        onOpenChange={setShowRegenerateDialog}
        title={t('tailor.regenerateDialog.title')}
        description={t('tailor.regenerateDialog.description')}
        confirmLabel={t('tailor.regenerateDialog.confirmLabel')}
        cancelLabel={t('common.cancel')}
        variant="warning"
        onConfirm={handleRegenerateConfirm}
      />

      <ConfirmDialog
        open={showMissingDiffDialog}
        onOpenChange={(open) => {
          if (!open) {
            handleCloseMissingDiffDialog();
          }
        }}
        title={t('tailor.missingDiffDialog.title')}
        description={t('tailor.missingDiffDialog.description')}
        confirmLabel={t('tailor.missingDiffDialog.confirmLabel')}
        cancelLabel={t('common.cancel')}
        variant="warning"
        closeOnConfirm={false}
        onConfirm={handleMissingDiffConfirm}
        onCancel={handleCloseMissingDiffDialog}
        confirmDisabled={isLoading || !missingDiffResult}
        errorMessage={missingDiffError ?? undefined}
      />

      <ConfirmDialog
        open={showDuplicateDialog}
        onOpenChange={(open) => {
          if (!open) {
            handleDuplicateCancel();
          }
        }}
        title={t('tailor.duplicateDialog.title')}
        description={
          duplicateInfo?.duplicateByUrl
            ? t('tailor.duplicateDialog.descriptionByUrl', {
                url: duplicateInfo.matchedUrl || '—',
                jobTitle: duplicateInfo.jobTitle || '—',
                company: duplicateInfo.company || '—',
                createdAt: duplicateInfo.createdAt || t('common.unknown'),
              })
            : t('tailor.duplicateDialog.description', {
                jobTitle: duplicateInfo?.jobTitle || '—',
                company: duplicateInfo?.company || '—',
                createdAt: duplicateInfo?.createdAt || t('common.unknown'),
              })
        }
        confirmLabel={t('tailor.duplicateDialog.continueLabel')}
        cancelLabel={t('common.cancel')}
        variant="warning"
        closeOnConfirm={false}
        onConfirm={handleDuplicateContinue}
        onCancel={handleDuplicateCancel}
        confirmDisabled={isLoading || !pendingGenerate}
      />
    </div>
  );
}
