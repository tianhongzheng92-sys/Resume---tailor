'use client';

import { SwissGrid } from '@/components/home/swiss-grid';
import { ResumeUploadDialog } from '@/components/dashboard/resume-upload-dialog';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { Card, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import Link from 'next/link';
import { useTranslations } from '@/lib/i18n';

// Optimized Imports for Performance (No Barrel Imports)
import Loader2 from 'lucide-react/dist/esm/icons/loader-2';
import AlertCircle from 'lucide-react/dist/esm/icons/alert-circle';
import RefreshCw from 'lucide-react/dist/esm/icons/refresh-cw';
import Plus from 'lucide-react/dist/esm/icons/plus';
import History from 'lucide-react/dist/esm/icons/history';
import Settings from 'lucide-react/dist/esm/icons/settings';
import AlertTriangle from 'lucide-react/dist/esm/icons/alert-triangle';

import {
  fetchResumeList,
  deleteResume,
  retryProcessing,
  fetchJobDescription,
  type ResumeListItem,
} from '@/lib/api/resume';
import { useStatusCache } from '@/lib/context/status-cache';

export default function DashboardPage() {
  const { t, locale } = useTranslations();
  const [masterResumes, setMasterResumes] = useState<ResumeListItem[]>([]);
  const [tailoredResumes, setTailoredResumes] = useState<ResumeListItem[]>([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [masterIdToDelete, setMasterIdToDelete] = useState<string | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [filterJobTitle, setFilterJobTitle] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [filterMasterResumeId, setFilterMasterResumeId] = useState('');
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const router = useRouter();

  const getMasterDisplayName = (parentId: string | null): string => {
    if (!parentId) return '—';
    const master = masterResumes.find((m) => m.resume_id === parentId);
    return master?.title || master?.filename || parentId.slice(0, 8) || '—';
  };

  /** Parse resume title into job title and company (e.g. "Software Engineer @ Mercor" → jobTitle, company) */
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

  // Status cache for optimistic counter updates and LLM status check
  const {
    status: systemStatus,
    isLoading: statusLoading,
    incrementResumes,
    decrementResumes,
    setHasMasterResume,
  } = useStatusCache();

  // Request id guard for concurrent loadTailoredResumes invocations
  const loadRequestIdRef = useRef(0);
  // Lightweight in-memory cache for job snippets to avoid N+1 refetches
  const jobSnippetCacheRef = useRef<Record<string, string>>({});

  // Check if LLM is configured (API key is set)
  const isLlmConfigured = !statusLoading && systemStatus?.llm_configured;

  const hasReadyMaster = masterResumes.some((m) => m.processing_status === 'ready');
  const isTailorEnabled = hasReadyMaster && isLlmConfigured;

  const formatDateTime = (value: string) => {
    if (!value) return t('common.unknown');
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return t('common.unknown');

    const dateLocale =
      locale === 'es' ? 'es-ES' : locale === 'zh' ? 'zh-CN' : locale === 'ja' ? 'ja-JP' : 'en-US';

    return date.toLocaleString(dateLocale, {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const filteredTailoredResumes = useMemo(() => {
    const filtered = tailoredResumes.filter((r) => {
      const fullTitle = r.title || r.jobSnippet || r.filename || '';
      const { jobTitle, company } = parseTitleAndCompany(fullTitle);
      const created = r.created_at || '';

      if (filterMasterResumeId) {
        if (r.parent_id !== filterMasterResumeId) return false;
      }
      if (filterJobTitle.trim()) {
        const q = filterJobTitle.trim().toLowerCase();
        if (!jobTitle.toLowerCase().includes(q)) return false;
      }
      if (filterCompany.trim()) {
        const q = filterCompany.trim().toLowerCase();
        if (!company.toLowerCase().includes(q)) return false;
      }
      if (filterDateFrom) {
        if (!created || created.slice(0, 10) < filterDateFrom) return false;
      }
      if (filterDateTo) {
        if (!created || created.slice(0, 10) > filterDateTo) return false;
      }
      return true;
    });
    return [...filtered].sort(
      (a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
    );
  }, [
    tailoredResumes,
    filterMasterResumeId,
    filterJobTitle,
    filterCompany,
    filterDateFrom,
    filterDateTo,
  ]);

  const loadTailoredResumes = useCallback(async () => {
    try {
      const data = await fetchResumeList(true);
      const masters = data.filter((r) => r.is_master);
      const tailored = data.filter((r) => !r.is_master);

      setMasterResumes(masters);
      setTailoredResumes(tailored);
      setHasMasterResume(masters.length > 0);

      // Keep last-used master for tailor page default; if none set, use first master
      const storedId = localStorage.getItem('master_resume_id');
      if (masters.length > 0) {
        const validStored = masters.some((m) => m.resume_id === storedId);
        if (!storedId || !validStored) {
          localStorage.setItem('master_resume_id', masters[0].resume_id);
        }
      } else {
        localStorage.removeItem('master_resume_id');
      }

      // Only fetch job descriptions for resumes that are actually tailored
      // (identified by having a non-null parent_id). This avoids N+1 calls
      const tailoredWithParent = tailored.filter((r) => r.parent_id);

      // Guard against concurrent invocations overwriting each other
      const requestId = ++loadRequestIdRef.current;

      // Fetch job description snippets for tailored resumes in parallel and attach to state
      // Use a small in-memory cache to avoid re-fetching the same snippet repeatedly.
      const jobSnippets: Record<string, string> = {};
      await Promise.all(
        tailoredWithParent.map(async (r) => {
          // Use cached snippet when available
          if (jobSnippetCacheRef.current[r.resume_id]) {
            jobSnippets[r.resume_id] = jobSnippetCacheRef.current[r.resume_id];
            return;
          }
          try {
            const jd = await fetchJobDescription(r.resume_id);
            const snippet = (jd?.content || '').slice(0, 80);
            jobSnippetCacheRef.current[r.resume_id] = snippet;
            jobSnippets[r.resume_id] = snippet;
          } catch {
            // ignore missing job descriptions and cache empty result
            jobSnippetCacheRef.current[r.resume_id] = '';
            jobSnippets[r.resume_id] = '';
          }
        })
      );

      // Only apply results if this invocation is the latest (prevents stale overwrite)
      if (requestId === loadRequestIdRef.current) {
        setTailoredResumes((prev) =>
          prev.map((r) => ({ ...r, jobSnippet: jobSnippets[r.resume_id] || '' }))
        );
      }
    } catch (err) {
      console.error('Failed to load tailored resumes:', err);
    }
  }, [setHasMasterResume]);

  useEffect(() => {
    loadTailoredResumes();
  }, [loadTailoredResumes]);

  // Refresh list when window gains focus (e.g., returning from viewer after delete)
  useEffect(() => {
    const handleFocus = () => {
      loadTailoredResumes();
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [loadTailoredResumes]);

  useEffect(() => {
    if (!showHistoryModal) return;
    // Ensure all histories are visible by default when the modal opens.
    setFilterMasterResumeId('');
    setFilterJobTitle('');
    setFilterCompany('');
    setFilterDateFrom('');
    setFilterDateTo('');
  }, [showHistoryModal]);

  const handleUploadComplete = (resumeId: string) => {
    localStorage.setItem('master_resume_id', resumeId);
    incrementResumes();
    setHasMasterResume(true);
    loadTailoredResumes();
  };

  const handleRetryProcessing = async (e: React.MouseEvent, resumeId: string) => {
    e.stopPropagation();
    setRetryingId(resumeId);
    try {
      const result = await retryProcessing(resumeId);
      if (
        result.processing_status === 'ready' ||
        result.processing_status === 'processing' ||
        result.processing_status === 'pending'
      ) {
        setMasterResumes((prev) =>
          prev.map((m) =>
            m.resume_id === resumeId ? { ...m, processing_status: result.processing_status } : m
          )
        );
      } else {
        setMasterResumes((prev) =>
          prev.map((m) => (m.resume_id === resumeId ? { ...m, processing_status: 'failed' } : m))
        );
      }
    } catch (err) {
      console.error('Retry processing failed:', err);
      setMasterResumes((prev) =>
        prev.map((m) => (m.resume_id === resumeId ? { ...m, processing_status: 'failed' } : m))
      );
    } finally {
      setRetryingId(null);
    }
  };

  const handleDeleteMaster = (e: React.MouseEvent, resumeId: string) => {
    e.stopPropagation();
    setMasterIdToDelete(resumeId);
    setShowDeleteDialog(true);
  };

  const confirmDeleteMaster = async () => {
    if (!masterIdToDelete) return;
    try {
      await deleteResume(masterIdToDelete);
      decrementResumes();
      if (localStorage.getItem('master_resume_id') === masterIdToDelete) {
        localStorage.removeItem('master_resume_id');
      }
      setMasterIdToDelete(null);
      setShowDeleteDialog(false);
      await loadTailoredResumes();
    } catch (err) {
      console.error('Failed to delete resume:', err);
    }
  };

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'loading':
        return {
          text: t('dashboard.status.checking'),
          icon: <Loader2 className="w-3 h-3 animate-spin" />,
          color: 'text-gray-500',
        };
      case 'processing':
        return {
          text: t('dashboard.status.processing'),
          icon: <Loader2 className="w-3 h-3 animate-spin" />,
          color: 'text-blue-700',
        };
      case 'ready':
        return { text: t('dashboard.status.ready'), icon: null, color: 'text-green-700' };
      case 'failed':
        return {
          text: t('dashboard.status.failed'),
          icon: <AlertCircle className="w-3 h-3" />,
          color: 'text-red-600',
        };
      default:
        return { text: t('dashboard.status.pending'), icon: null, color: 'text-gray-500' };
    }
  };

  const totalCards = masterResumes.length + 1; // masters + Add master
  const fillerCount = Math.max(0, (5 - (totalCards % 5)) % 5);
  const extraFillerCount = 5;
  // Use Tailwind classes for fillers now that we have them in config or use specific hex if needed
  // Using the hex values from before to maintain exact look, or we could map them to variants
  const fillerPalette = ['bg-[#E5E5E0]', 'bg-[#D8D8D2]', 'bg-[#CFCFC7]', 'bg-[#E0E0D8]'];

  return (
    <div className="space-y-6">
      {/* Configuration Warning Banner */}
      {masterResumes.length > 0 && !isLlmConfigured && !statusLoading && (
        <div className="border-2 border-warning bg-amber-50 p-4 shadow-sw-default mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-warning" />
            <div>
              <p className="font-mono text-sm font-bold uppercase tracking-wider text-amber-800">
                {t('dashboard.llmNotConfiguredTitle')}
              </p>
              <p className="font-mono text-xs text-amber-700 mt-0.5">
                {t('dashboard.llmNotConfiguredMessage')}
              </p>
            </div>
          </div>
          <Link href="/settings">
            <Button variant="outline" size="sm" className="border-warning text-amber-700">
              <Settings className="w-4 h-4 mr-2" />
              {t('nav.settings')}
            </Button>
          </Link>
        </div>
      )}

      <SwissGrid
        headerActions={
          <>
            <Button
              onClick={() => router.push('/tailor')}
              disabled={!isTailorEnabled}
              className="h-11 px-5 bg-blue-700 text-white border-2 border-black shadow-sw-default hover:bg-blue-800 hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition-all rounded-none font-mono text-sm uppercase flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              {t('dashboard.createResume')}
            </Button>
            <Button
              onClick={() => setShowHistoryModal(true)}
              variant="outline"
              className="h-11 px-5 border-2 border-black shadow-sw-default hover:bg-[#F0F0E8] hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition-all rounded-none font-mono text-sm uppercase flex items-center gap-2"
            >
              <History className="w-5 h-5" />
              {t('dashboard.createdResumesHistory')}
            </Button>
          </>
        }
      >
        {/* No masters: show setup or initialize card */}
        {masterResumes.length === 0 &&
          (!isLlmConfigured && !statusLoading ? (
            <Link href="/settings" className="block h-full">
              <Card
                variant="interactive"
                className="aspect-square h-full border-dashed border-warning bg-amber-50"
              >
                <div className="flex-1 flex flex-col justify-between">
                  <div className="w-14 h-14 border-2 border-warning bg-white flex items-center justify-center mb-4">
                    <AlertTriangle className="w-7 h-7 text-warning" />
                  </div>
                  <div>
                    <CardTitle className="text-lg uppercase text-amber-800 mb-2">
                      {t('dashboard.setupRequiredTitle')}
                    </CardTitle>
                    <CardDescription className="text-amber-700 text-xs">
                      {t('dashboard.setupRequiredMessage')}
                    </CardDescription>
                    <div className="flex items-center gap-2 mt-4 text-amber-700 group-hover:text-amber-900">
                      <Settings className="w-4 h-4" />
                      <span className="font-mono text-xs font-bold uppercase">
                        {t('nav.goToSettings')}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ) : (
            <ResumeUploadDialog
              open={isUploadDialogOpen}
              onOpenChange={setIsUploadDialogOpen}
              onUploadComplete={handleUploadComplete}
              trigger={
                <Card
                  variant="interactive"
                  className="aspect-square h-full hover:bg-primary hover:text-canvas"
                >
                  <div className="flex-1 flex flex-col justify-between pointer-events-none">
                    <div className="w-14 h-14 border-2 border-current flex items-center justify-center mb-4">
                      <span className="text-2xl leading-none relative top-[-2px]">+</span>
                    </div>
                    <div>
                      <CardTitle className="text-xl uppercase">
                        {t('dashboard.initializeMasterResume')}
                      </CardTitle>
                      <CardDescription className="mt-2 opacity-60 group-hover:opacity-100 text-current">
                        {'// '}
                        {t('dashboard.initializeSequence')}
                      </CardDescription>
                    </div>
                  </div>
                </Card>
              }
            />
          ))}

        {/* Master resume cards */}
        {masterResumes.map((master) => {
          const status = master.processing_status || 'pending';
          const statusDisplay = getStatusDisplay(status);
          const title = master.title || master.filename || t('dashboard.masterResume');
          return (
            <Card
              key={master.resume_id}
              variant="interactive"
              className="aspect-square h-full"
              onClick={() => router.push(`/resumes/${master.resume_id}`)}
            >
              <div className="flex-1 flex flex-col h-full">
                <div className="flex justify-between items-start mb-6">
                  <div className="w-16 h-16 border-2 border-black bg-blue-700 text-white flex items-center justify-center">
                    <span className="font-mono font-bold text-lg">M</span>
                  </div>
                  <div className="flex gap-1">
                    {(status === 'failed' || status === 'processing') && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 hover:bg-blue-100 hover:text-blue-700 z-10 rounded-none relative"
                        onClick={(e) => handleRetryProcessing(e, master.resume_id)}
                        disabled={retryingId === master.resume_id}
                        title={t('dashboard.retryProcessing')}
                      >
                        {retryingId === master.resume_id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </div>

                <CardTitle className="text-lg group-hover:text-primary line-clamp-2">
                  {title}
                </CardTitle>

                <div
                  className={`text-xs font-mono mt-auto pt-4 flex flex-col gap-2 uppercase ${statusDisplay.color}`}
                >
                  <div className="flex items-center gap-1">
                    {statusDisplay.icon}
                    {t('dashboard.statusLine', { status: statusDisplay.text })}
                  </div>
                  {(status === 'failed' || status === 'processing') && (
                    <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-7 rounded-none border-black"
                        onClick={(e) => handleRetryProcessing(e, master.resume_id)}
                        disabled={retryingId === master.resume_id}
                      >
                        {retryingId === master.resume_id
                          ? t('dashboard.retryingProcessing')
                          : t('dashboard.retryProcessing')}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-7 rounded-none border-red-600 text-red-600 hover:bg-red-50"
                        onClick={(e) => handleDeleteMaster(e, master.resume_id)}
                      >
                        {t('dashboard.deleteAndReupload')}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          );
        })}

        {/* Add another master */}
        {masterResumes.length > 0 && (
          <ResumeUploadDialog
            open={isUploadDialogOpen}
            onOpenChange={setIsUploadDialogOpen}
            onUploadComplete={handleUploadComplete}
            trigger={
              <Card
                variant="interactive"
                className="aspect-square h-full hover:bg-primary hover:text-canvas border-dashed border-black"
              >
                <div className="flex-1 flex flex-col justify-center items-center pointer-events-none">
                  <div className="w-14 h-14 border-2 border-current flex items-center justify-center mb-4">
                    <span className="text-2xl leading-none">+</span>
                  </div>
                  <CardTitle className="text-lg uppercase">
                    {t('dashboard.addMasterResume')}
                  </CardTitle>
                </div>
              </Card>
            }
          />
        )}

        {/* Fillers */}
        {Array.from({ length: fillerCount }).map((_, index) => (
          <Card
            key={`filler-${index}`}
            variant="ghost"
            noPadding
            className="hidden md:block bg-canvas aspect-square h-full opacity-50 pointer-events-none"
          />
        ))}

        {Array.from({ length: extraFillerCount }).map((_, index) => (
          <Card
            key={`extra-filler-${index}`}
            variant="ghost"
            noPadding
            className={`hidden md:block ${fillerPalette[index % fillerPalette.length]} aspect-square h-full opacity-70 pointer-events-none`}
          />
        ))}

        <ConfirmDialog
          open={showDeleteDialog}
          onOpenChange={setShowDeleteDialog}
          title={t('confirmations.deleteMasterResumeTitle')}
          description={t('confirmations.deleteMasterResumeDescription')}
          confirmLabel={t('dashboard.deleteAndReupload')}
          cancelLabel={t('confirmations.keepResumeCancelLabel')}
          onConfirm={confirmDeleteMaster}
          variant="danger"
        />
      </SwissGrid>

      {/* Created Resumes History — modal */}
      <Dialog open={showHistoryModal} onOpenChange={setShowHistoryModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
          <div className="pl-6 pr-14 pt-6 pb-0 flex-shrink-0">
            <h2 className="font-serif text-xl font-bold uppercase tracking-tight">
              {t('dashboard.tailoredResumesHistory')}
            </h2>
          </div>
          <div className="p-6 overflow-y-auto flex-1 min-h-0">
            <div className="mb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <div>
                <label className="block font-mono text-xs font-bold uppercase text-gray-600 mb-1">
                  {t('dashboard.filterMasterResume')}
                </label>
                <select
                  value={filterMasterResumeId}
                  onChange={(e) => setFilterMasterResumeId(e.target.value)}
                  className="flex h-10 w-full border border-black bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-700 rounded-none"
                >
                  <option value="">{t('dashboard.filterAllMasters')}</option>
                  {masterResumes.map((m) => (
                    <option key={m.resume_id} value={m.resume_id}>
                      {m.title || m.filename || m.resume_id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs font-bold uppercase text-gray-600 mb-1">
                  {t('dashboard.filterJobTitle')}
                </label>
                <Input
                  type="text"
                  placeholder={t('dashboard.filterJobTitlePlaceholder')}
                  value={filterJobTitle}
                  onChange={(e) => setFilterJobTitle(e.target.value)}
                  className="rounded-none"
                />
              </div>
              <div>
                <label className="block font-mono text-xs font-bold uppercase text-gray-600 mb-1">
                  {t('dashboard.filterCompany')}
                </label>
                <Input
                  type="text"
                  placeholder={t('dashboard.filterCompanyPlaceholder')}
                  value={filterCompany}
                  onChange={(e) => setFilterCompany(e.target.value)}
                  className="rounded-none"
                />
              </div>
              <div>
                <label className="block font-mono text-xs font-bold uppercase text-gray-600 mb-1">
                  {t('dashboard.filterDateFrom')}
                </label>
                <Input
                  type="date"
                  value={filterDateFrom}
                  onChange={(e) => setFilterDateFrom(e.target.value)}
                  className="rounded-none"
                />
              </div>
              <div>
                <label className="block font-mono text-xs font-bold uppercase text-gray-600 mb-1">
                  {t('dashboard.filterDateTo')}
                </label>
                <Input
                  type="date"
                  value={filterDateTo}
                  onChange={(e) => setFilterDateTo(e.target.value)}
                  className="rounded-none"
                />
              </div>
            </div>

            <div className="mb-3 font-mono text-xs uppercase text-gray-700">
              Total: {tailoredResumes.length} / Showing: {filteredTailoredResumes.length}
            </div>

            <div className="overflow-x-auto border border-black">
              <table className="w-full border-collapse font-sans text-sm">
                <thead>
                  <tr className="bg-[#F0F0E8] border-b-2 border-black">
                    <th className="text-left font-mono font-bold uppercase py-3 px-4 border-r border-black w-14">
                      {t('dashboard.tableNo')}
                    </th>
                    <th className="text-left font-mono font-bold uppercase py-3 px-4 border-r border-black">
                      {t('dashboard.tableMasterResume')}
                    </th>
                    <th className="text-left font-mono font-bold uppercase py-3 px-4 border-r border-black">
                      {t('dashboard.tableJobTitle')}
                    </th>
                    <th className="text-left font-mono font-bold uppercase py-3 px-4 border-r border-black">
                      {t('dashboard.tableCompany')}
                    </th>
                    <th className="text-left font-mono font-bold uppercase py-3 px-4">
                      {t('dashboard.tableCreatedDate')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTailoredResumes.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="py-8 px-4 text-center font-mono text-gray-500 uppercase"
                      >
                        {tailoredResumes.length === 0
                          ? t('dashboard.noTailoredResumes')
                          : t('dashboard.noMatchingResumes')}
                      </td>
                    </tr>
                  ) : (
                    filteredTailoredResumes.map((resume, index) => {
                      const fullTitle = resume.title || resume.jobSnippet || resume.filename || '';
                      const { jobTitle, company } = parseTitleAndCompany(fullTitle);
                      return (
                        <tr
                          key={resume.resume_id}
                          className="border-b border-gray-300 hover:bg-blue-50/50 cursor-pointer transition-colors"
                          onClick={() => {
                            setShowHistoryModal(false);
                            router.push(`/resumes/${resume.resume_id}`);
                          }}
                        >
                          <td className="py-3 px-4 border-r border-gray-200 font-mono">
                            {index + 1}
                          </td>
                          <td className="py-3 px-4 border-r border-gray-200">
                            {getMasterDisplayName(resume.parent_id)}
                          </td>
                          <td className="py-3 px-4 border-r border-gray-200">{jobTitle}</td>
                          <td className="py-3 px-4 border-r border-gray-200">{company}</td>
                          <td className="py-3 px-4 font-mono">
                            {formatDateTime(resume.created_at || '')}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
