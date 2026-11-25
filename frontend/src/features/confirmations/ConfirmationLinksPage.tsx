import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Check, Ban, Plus, X, Layers, RefreshCw, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { dealersApi } from "@/features/dealers/dealersApi";
import { extractApiErrorMessage } from "@/utils/errorExtractor";
import { campaignsApi } from "./campaignsApi";
import {
  BulkGenerateResultDTO,
  confirmationLinksApi,
} from "./confirmationLinksApi";

function buildWhatsAppUrl(mobile: string, message: string): string {
  const digits = (mobile || "").replace(/\D/g, "");
  const phone = digits.length === 10 ? `91${digits}` : digits;
  const encodedText = encodeURIComponent(message);
  return phone
    ? `https://wa.me/${phone}?text=${encodedText}`
    : `https://wa.me/?text=${encodedText}`;
}

export const ConfirmationLinksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [bulkSummary, setBulkSummary] = useState<BulkGenerateResultDTO | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Single Generate Modal
  const [showGenModal, setShowGenModal] = useState(false);
  const [selectedDealer, setSelectedDealer] = useState("");
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [genError, setGenError] = useState<string | null>(null);

  // Bulk Generate Modal
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkCampaign, setBulkCampaign] = useState("");
  const [bulkDealerIds, setBulkDealerIds] = useState<string[]>([]);
  const [selectAllActive, setSelectAllActive] = useState(false);
  const [bulkError, setBulkError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["confirmation-links", statusFilter],
    queryFn: () =>
      confirmationLinksApi.list(statusFilter ? { status: statusFilter } : undefined),
  });

  const { data: dealersRes } = useQuery({
    queryKey: ["dealers-for-link"],
    queryFn: () => dealersApi.list({ status: "active" }),
    enabled: showGenModal || showBulkModal,
  });

  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns"],
    queryFn: campaignsApi.list,
    enabled: showGenModal || showBulkModal,
  });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ["confirmation-links"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-analytics"] });
  };

  const generateMutation = useMutation({
    mutationFn: () =>
      confirmationLinksApi.generate({
        dealer: selectedDealer,
        campaign: selectedCampaign,
      }),
    onSuccess: () => {
      setShowGenModal(false);
      setGenError(null);
      setSelectedDealer("");
      invalidateAll();
    },
    onError: (err) => {
      setGenError(extractApiErrorMessage(err, "Failed to generate confirmation link."));
    },
  });

  const bulkGenerateMutation = useMutation({
    mutationFn: () =>
      confirmationLinksApi.bulkGenerate({
        campaign: bulkCampaign,
        dealer_ids: selectAllActive ? [] : bulkDealerIds,
        select_all_active: selectAllActive,
      }),
    onSuccess: (summary) => {
      setBulkSummary(summary);
      setShowBulkModal(false);
      setBulkError(null);
      setBulkDealerIds([]);
      setSelectAllActive(false);
      invalidateAll();
    },
    onError: (err) => {
      setBulkError(extractApiErrorMessage(err, "Bulk generation failed."));
    },
  });

  const copyShareMutation = useMutation({
    mutationFn: async ({
      id,
      mode,
      waWindow,
    }: {
      id: string;
      mode: "url" | "whatsapp";
      waWindow?: Window | null;
    }) => {
      try {
        const res = await confirmationLinksApi.copyShare(id);
        if (mode === "whatsapp") {
          const message = res.share_message || res.shareable_url || "";
          const waUrl = buildWhatsAppUrl(res.dealer_mobile, message);
          if (message && navigator.clipboard) {
            navigator.clipboard.writeText(message).catch(() => {});
          }
          if (waWindow && !waWindow.closed) {
            waWindow.location.href = waUrl;
          } else {
            window.open(waUrl, "_blank", "noopener,noreferrer");
          }
        } else {
          const textToCopy = res.shareable_url || "";
          if (textToCopy && navigator.clipboard) {
            await navigator.clipboard.writeText(textToCopy);
          }
        }
        return { res, mode };
      } catch (err) {
        if (waWindow && !waWindow.closed) {
          waWindow.close();
        }
        throw err;
      }
    },
    onSuccess: ({ res, mode }) => {
      setCopiedKey(`${res.id}:${mode}`);
      setActionError(null);
      setTimeout(() => setCopiedKey(null), 2000);
      invalidateAll();
    },
    onError: (err) => {
      setActionError(extractApiErrorMessage(err, "Unable to open WhatsApp or copy confirmation link."));
    },
  });

  const handleOpenWhatsApp = (linkId: string) => {
    // Open tab synchronously within user click gesture so browser popup blockers do not block it
    const waWindow = window.open("about:blank", "_blank");
    if (waWindow) {
      waWindow.opener = null;
    }
    copyShareMutation.mutate({ id: linkId, mode: "whatsapp", waWindow });
  };

  const regenerateMutation = useMutation({
    mutationFn: (id: string) => confirmationLinksApi.regenerate(id),
    onSuccess: () => {
      setActionError(null);
      invalidateAll();
    },
    onError: (err) => {
      setActionError(extractApiErrorMessage(err, "Unable to regenerate confirmation link."));
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => confirmationLinksApi.deactivate(id),
    onSuccess: () => invalidateAll(),
  });

  const links = data?.data || [];
  const activeDealers = dealersRes?.data || [];
  const bulkEligibleDealers = bulkCampaign
    ? activeDealers.filter((d) => !d.campaign || d.campaign === bulkCampaign)
    : activeDealers;

  // Track which dealers already have an active/shared/used link for the chosen campaign
  const existingDealerSetForSingle = new Set(
    links
      .filter(
        (l) =>
          l.campaign === selectedCampaign &&
          ["active", "shared", "used"].includes(l.status)
      )
      .map((l) => l.dealer)
  );

  const toggleBulkDealer = (id: string) => {
    setBulkDealerIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Confirmation Links</h1>
          <p className="text-xs text-ink-secondary mt-1">
            Generate single or bulk dealer links, copy &amp; share anytime (auto-tracked on Dashboard), or regenerate links.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-[40px] px-3 text-sm rounded-lg border border-line bg-surface-white focus:outline-none focus:border-brand-primary"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="shared">Shared</option>
            <option value="used">Used</option>
            <option value="expired">Expired</option>
            <option value="deactivated">Deactivated</option>
          </select>
          <PermissionGate permission="confirmation_links.add">
            <Button
              variant="outline-red"
              size="md"
              leftIcon={<Layers className="h-4 w-4" />}
              onClick={() => setShowBulkModal(true)}
            >
              Bulk Generate
            </Button>
            <Button
              size="md"
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => setShowGenModal(true)}
            >
              Generate Link
            </Button>
          </PermissionGate>
        </div>
      </div>

      {actionError && <AlertBanner variant="error" message={actionError} />}

      {bulkSummary && (
        <AlertBanner
          variant={bulkSummary.skipped_count > 0 ? "warning" : "success"}
          title="Bulk Link Generation Summary"
          message={`Created ${bulkSummary.created_count} new link(s). Skipped ${bulkSummary.skipped_count} dealer(s) who already have an existing link (use Regenerate on their row if needed).`}
        />
      )}

      <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="py-3 px-4">Dealer Code</th>
                <th className="py-3 px-4">Campaign</th>
                <th className="py-3 px-4">Month</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Submissions</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ink-secondary">
                    Loading confirmation links...
                  </td>
                </tr>
              ) : links.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ink-secondary">
                    No confirmation links generated yet. Use Generate Link or Bulk Generate above.
                  </td>
                </tr>
              ) : (
                links.map((link) => (
                  <tr key={link.id} className="hover:bg-surface-bg/60">
                    <td className="py-3 px-4 font-semibold tabular-nums">{link.dealer_code}</td>
                    <td className="py-3 px-4">{link.campaign_name}</td>
                    <td className="py-3 px-4 tabular-nums">{link.allowed_month}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={link.status} />
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {link.is_regenerated ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#FFFBEB] text-[#B45309] font-medium">
                          <RefreshCw className="h-3 w-3" />
                          Regenerated #{link.regeneration_count}
                        </span>
                      ) : (
                        <span className="text-ink-secondary">Original</span>
                      )}
                    </td>
                    <td className="py-3 px-4 tabular-nums">
                      {link.submission_count} / {link.max_submissions}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex flex-wrap items-center justify-end gap-1.5">
                        {link.can_copy && (
                          <>
                            <Button
                              variant="secondary"
                              size="sm"
                              leftIcon={copiedKey === `${link.id}:url` ? <Check className="h-3.5 w-3.5 text-status-success" /> : <Copy className="h-3.5 w-3.5" />}
                              onClick={() => copyShareMutation.mutate({ id: link.id, mode: "url" })}
                            >
                              {copiedKey === `${link.id}:url` ? "Copied" : "Copy Link"}
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              leftIcon={
                                copiedKey === `${link.id}:whatsapp` ? (
                                  <Check className="h-3.5 w-3.5 text-status-success" />
                                ) : (
                                  <MessageSquare className="h-3.5 w-3.5 text-[#16A34A]" />
                                )
                              }
                              onClick={() => handleOpenWhatsApp(link.id)}
                            >
                              {copiedKey === `${link.id}:whatsapp` ? "WhatsApp Opened" : "WhatsApp"}
                            </Button>
                          </>
                        )}
                        {link.can_regenerate && (
                          <PermissionGate permission={["confirmation_links.add", "confirmation_links.edit"]}>
                            <Button
                              variant="outline-red"
                              size="sm"
                              leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
                              isLoading={regenerateMutation.isPending && regenerateMutation.variables === link.id}
                              onClick={() => regenerateMutation.mutate(link.id)}
                            >
                              Regenerate
                            </Button>
                          </PermissionGate>
                        )}
                        {(link.status === "active" || link.status === "shared") && (
                          <PermissionGate permission="confirmation_links.delete">
                            <Button
                              variant="ghost"
                              size="sm"
                              leftIcon={<Ban className="h-3.5 w-3.5 text-status-error" />}
                              onClick={() => deactivateMutation.mutate(link.id)}
                            >
                              Revoke
                            </Button>
                          </PermissionGate>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Single Generate Modal */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface-white rounded-2xl shadow-modal max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-ink-primary">Generate Confirmation Link</h2>
              <button type="button" onClick={() => setShowGenModal(false)} className="text-ink-secondary">
                <X className="h-5 w-5" />
              </button>
            </div>
            {genError && <AlertBanner variant="error" message={genError} />}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                generateMutation.mutate();
              }}
              className="space-y-3.5"
            >
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Select Campaign<span className="text-brand-primary ml-0.5">*</span>
                </label>
                <select
                  required
                  value={selectedCampaign}
                  onChange={(e) => setSelectedCampaign(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Choose active campaign</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.campaign_name} ({c.campaign_code})
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Select Dealer<span className="text-brand-primary ml-0.5">*</span>
                </label>
                <select
                  required
                  value={selectedDealer}
                  onChange={(e) => setSelectedDealer(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Choose active dealer</option>
                  {activeDealers.map((d) => {
                    const exists = existingDealerSetForSingle.has(d.id);
                    return (
                      <option key={d.id} value={d.id} disabled={exists}>
                        {d.dealer_code} (+91 {d.mobile_number}){exists ? " — Link exists (use Regenerate)" : ""}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowGenModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={generateMutation.isPending}>
                  Generate Secure Link
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Generate Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface-white rounded-2xl shadow-modal max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-ink-primary">Bulk Generate Confirmation Links</h2>
              <button type="button" onClick={() => setShowBulkModal(false)} className="text-ink-secondary">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-xs text-ink-secondary">
              Dealers who already have an active, shared, or confirmed link for the selected campaign are automatically skipped (no duplicates).
            </p>
            {bulkError && <AlertBanner variant="error" message={bulkError} />}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                bulkGenerateMutation.mutate();
              }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Select Campaign<span className="text-brand-primary ml-0.5">*</span>
                </label>
                <select
                  required
                  value={bulkCampaign}
                  onChange={(e) => setBulkCampaign(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Choose active campaign</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.campaign_name} ({c.campaign_code})
                    </option>
                  ))}
                </select>
              </div>

              <label className="flex items-center gap-2.5 p-3 rounded-lg bg-surface-bg border border-line text-sm font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectAllActive}
                  onChange={(e) => setSelectAllActive(e.target.checked)}
                  className="accent-[#D71920]"
                />
                <span>
                  Select all eligible active dealers for this campaign ({bulkEligibleDealers.length})
                </span>
              </label>

              {!selectAllActive && (
                <div className="max-h-52 overflow-y-auto border border-line rounded-lg divide-y divide-line">
                  {bulkEligibleDealers.map((d) => (
                    <label
                      key={d.id}
                      className="flex items-center justify-between px-3 py-2.5 hover:bg-surface-bg cursor-pointer text-xs"
                    >
                      <span className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={bulkDealerIds.includes(d.id)}
                          onChange={() => toggleBulkDealer(d.id)}
                          className="accent-[#D71920]"
                        />
                        <span className="font-semibold tabular-nums">{d.dealer_code}</span>
                        {d.campaign_code && (
                          <span className="px-1.5 py-0.5 rounded bg-brand-tint text-brand-primary text-[10px] font-medium">
                            {d.campaign_code}
                          </span>
                        )}
                      </span>
                      <span className="text-ink-secondary tabular-nums">+91 {d.mobile_number}</span>
                    </label>
                  ))}
                  {bulkEligibleDealers.length === 0 && (
                    <p className="p-4 text-center text-xs text-ink-secondary">No active dealers mapped to this campaign.</p>
                  )}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowBulkModal(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  isLoading={bulkGenerateMutation.isPending}
                  disabled={!bulkCampaign || (!selectAllActive && bulkDealerIds.length === 0)}
                >
                  Generate Links in Bulk
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
