import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Download, Upload, Plus, Search, X, FileSpreadsheet } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextInput";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { campaignsApi } from "@/features/confirmations/campaignsApi";
import { usersApi } from "@/features/users/usersApi";
import { extractApiErrorMessage } from "@/utils/errorExtractor";
import { dealersApi, DealerImportSummary } from "./dealersApi";

export const DealersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [campaignFilter, setCampaignFilter] = useState("");
  const [importSummary, setImportSummary] = useState<DealerImportSummary | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  // Add Dealer Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [dealerCode, setDealerCode] = useState("");
  const [dealerMobile, setDealerMobile] = useState("");
  const [assignedRm, setAssignedRm] = useState("");
  const [dealerCampaign, setDealerCampaign] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  // Import Excel Modal (with Campaign mapping)
  const [showImportModal, setShowImportModal] = useState(false);
  const [importCampaignId, setImportCampaignId] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["dealers", search, statusFilter, campaignFilter],
    queryFn: () =>
      dealersApi.list({
        ...(search ? { search } : {}),
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(campaignFilter ? { campaign: campaignFilter } : {}),
      }),
  });

  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns"],
    queryFn: campaignsApi.list,
  });

  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list(),
    enabled: showAddModal,
  });

  const createDealerMutation = useMutation({
    mutationFn: () =>
      dealersApi.create({
        dealer_code: dealerCode,
        mobile_number: dealerMobile,
        assigned_rm: assignedRm,
        campaign: dealerCampaign || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dealers"] });
      setShowAddModal(false);
      setDealerCode("");
      setDealerMobile("");
      setAssignedRm("");
      setDealerCampaign("");
      setFormError(null);
    },
    onError: (err) => {
      setFormError(extractApiErrorMessage(err, "Unable to create dealer."));
    },
  });

  const importMutation = useMutation({
    mutationFn: ({ file, campaignId }: { file: File; campaignId?: string }) =>
      dealersApi.importExcel(file, campaignId),
    onSuccess: (summary) => {
      setImportSummary(summary);
      setImportError(null);
      setShowImportModal(false);
      setImportFile(null);
      setImportCampaignId("");
      queryClient.invalidateQueries({ queryKey: ["dealers"] });
    },
    onError: (err) => {
      setImportSummary(null);
      setImportError(
        extractApiErrorMessage(
          err,
          "Failed to import Excel file. Please download the template and verify required columns."
        )
      );
    },
  });

  const handleDownloadTemplate = async () => {
    const blob = await dealersApi.downloadTemplate();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "havells_dealers_import_template.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExport = async (format: "xlsx" | "csv") => {
    const blob = await dealersApi.exportFile(format);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `havells_dealers.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const dealers = data?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Dealer Management</h1>
          <p className="text-xs text-ink-secondary mt-1">
            Manage authorized Havells dealers, campaign mapping, RM assignments, and bulk Excel imports.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <PermissionGate permission="dealers.export">
            <Button variant="secondary" size="md" leftIcon={<Download className="h-4 w-4" />} onClick={() => handleExport("xlsx")}>
              Export Excel
            </Button>
          </PermissionGate>
          <PermissionGate permission="dealers.import">
            <Button
              variant="secondary"
              size="md"
              leftIcon={<FileSpreadsheet className="h-4 w-4" />}
              onClick={handleDownloadTemplate}
            >
              Download Template
            </Button>
            <Button
              variant="outline-red"
              size="md"
              leftIcon={<Upload className="h-4 w-4" />}
              onClick={() => {
                setImportError(null);
                setShowImportModal(true);
              }}
            >
              Import Excel
            </Button>
          </PermissionGate>
          <PermissionGate permission="dealers.add">
            <Button size="md" leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowAddModal(true)}>
              Add Dealer
            </Button>
          </PermissionGate>
        </div>
      </div>

      {importError && !showImportModal && <AlertBanner variant="error" message={importError} />}
      {importSummary && (
        <div className="space-y-3">
          <AlertBanner
            variant={importSummary.failed_count > 0 ? "warning" : "success"}
            title="Dealer Import Summary"
            message={`Processed ${importSummary.total_rows} row(s): ${importSummary.created_count} created, ${importSummary.failed_count} failed.`}
          />
          {importSummary.errors.length > 0 && (
            <div className="bg-surface-white border border-line rounded-xl overflow-hidden shadow-card">
              <div className="px-4 py-2.5 bg-[#FEF2F2] border-b border-[#FECACA] text-xs font-semibold text-status-error">
                Row-Level Import Errors ({importSummary.errors.length})
              </div>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-surface-bg border-b border-line text-ink-secondary">
                      <th className="py-2 px-4">Row #</th>
                      <th className="py-2 px-4">Dealer Code</th>
                      <th className="py-2 px-4">Error Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {importSummary.errors.map((item, idx) => (
                      <tr key={idx}>
                        <td className="py-2 px-4 tabular-nums font-medium">{item.row_number}</td>
                        <td className="py-2 px-4 tabular-nums">{item.dealer_code || "—"}</td>
                        <td className="py-2 px-4 text-status-error">{item.errors.join(" • ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-surface-white border border-line rounded-xl p-4 shadow-card flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="h-4 w-4 text-ink-secondary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Dealer Code, Mobile Number, or Campaign..."
            className="w-full h-[40px] pl-9 pr-3 text-sm rounded-lg border border-line focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/15"
          />
        </div>
        <select
          value={campaignFilter}
          onChange={(e) => setCampaignFilter(e.target.value)}
          className="h-[40px] px-3 text-sm rounded-lg border border-line bg-surface-white focus:outline-none focus:border-brand-primary"
        >
          <option value="">All Campaigns</option>
          {campaigns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.campaign_name} ({c.campaign_code})
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-[40px] px-3 text-sm rounded-lg border border-line bg-surface-white focus:outline-none focus:border-brand-primary"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {/* Data Table */}
      <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="py-3 px-4">Dealer Code</th>
                <th className="py-3 px-4">Mobile Number</th>
                <th className="py-3 px-4">Campaign</th>
                <th className="py-3 px-4">Assigned RM</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-secondary">
                    Loading dealers...
                  </td>
                </tr>
              ) : dealers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-secondary">
                    No dealers found matching the current filters.
                  </td>
                </tr>
              ) : (
                dealers.map((dealer) => (
                  <tr key={dealer.id} className="hover:bg-surface-bg/60 transition-colors">
                    <td className="py-3 px-4 font-semibold text-ink-primary tabular-nums">
                      {dealer.dealer_code}
                    </td>
                    <td className="py-3 px-4 tabular-nums text-ink-primary">
                      +91 {dealer.mobile_number}
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {dealer.campaign_name ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-brand-tint text-brand-primary font-medium">
                          {dealer.campaign_name}
                        </span>
                      ) : (
                        <span className="text-ink-secondary">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-ink-primary">{dealer.assigned_rm_name}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={dealer.status} />
                    </td>
                    <td className="py-3 px-4 text-xs text-ink-secondary tabular-nums">
                      {new Date(dealer.created_at).toLocaleDateString("en-IN")}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Dealer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface-white rounded-2xl shadow-modal max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-ink-primary">Add Dealer</h2>
              <button type="button" onClick={() => setShowAddModal(false)} className="text-ink-secondary">
                <X className="h-5 w-5" />
              </button>
            </div>
            {formError && <AlertBanner variant="error" message={formError} />}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createDealerMutation.mutate();
              }}
              className="space-y-3.5"
            >
              <TextInput
                label="Dealer Code"
                required
                placeholder="e.g. HVL-1001"
                value={dealerCode}
                onChange={(e) => setDealerCode(e.target.value)}
              />
              <TextInput
                label="Mobile Number"
                prefixText="+91"
                required
                maxLength={10}
                placeholder="10-digit Indian mobile"
                value={dealerMobile}
                onChange={(e) => setDealerMobile(e.target.value)}
              />
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Assigned RM<span className="text-brand-primary ml-0.5">*</span>
                </label>
                <select
                  required
                  value={assignedRm}
                  onChange={(e) => setAssignedRm(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Select Relationship Manager</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} (+91 {u.mobile_number})
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Map Campaign
                </label>
                <select
                  value={dealerCampaign}
                  onChange={(e) => setDealerCampaign(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Optional — Select Campaign</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.campaign_name} ({c.campaign_code})
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createDealerMutation.isPending}>
                  Save Dealer
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import Dealers Excel Modal (with Campaign Mapping) */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface-white rounded-2xl shadow-modal max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-ink-primary">Import Dealers from Excel</h2>
              <button type="button" onClick={() => setShowImportModal(false)} className="text-ink-secondary">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-xs text-ink-secondary leading-relaxed">
              Select a Campaign below to map all uploaded dealers automatically, or include a{" "}
              <code className="font-mono text-ink-primary">campaign_code</code> column per row in your{" "}
              <code className="font-mono text-ink-primary">.xlsx</code> file.
            </p>
            {importError && <AlertBanner variant="error" message={importError} />}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (importFile) {
                  importMutation.mutate({
                    file: importFile,
                    campaignId: importCampaignId || undefined,
                  });
                }
              }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Map Campaign (Optional Default for All Rows)
                </label>
                <select
                  value={importCampaignId}
                  onChange={(e) => setImportCampaignId(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Use campaign_code column in Excel (or leave unmapped)</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.campaign_name} ({c.campaign_code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">
                  Excel File (.xlsx)<span className="text-brand-primary ml-0.5">*</span>
                </label>
                <input
                  type="file"
                  accept=".xlsx"
                  required
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-ink-primary file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border file:border-line file:bg-surface-bg file:text-xs file:font-medium hover:file:bg-surface-muted"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={handleDownloadTemplate}
                  className="text-xs font-medium text-brand-primary hover:text-brand-dark underline"
                >
                  Download .xlsx Template
                </button>
                <div className="flex gap-2">
                  <Button type="button" variant="secondary" onClick={() => setShowImportModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" isLoading={importMutation.isPending} disabled={!importFile}>
                    Upload &amp; Import
                  </Button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
