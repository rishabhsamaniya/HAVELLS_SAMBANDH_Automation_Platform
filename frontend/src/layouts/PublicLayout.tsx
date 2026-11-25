import React from "react";

export const PublicLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-surface-bg flex flex-col">
      <div className="h-1 bg-brand-primary w-full" />
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-[480px] bg-surface-white border border-line rounded-2xl shadow-modal p-6 sm:p-8">
          {children}
        </div>
      </main>
      <footer className="py-4 text-center text-xs text-ink-secondary">
        Copyright @ 2007- 2026 Story Experiences Pvt. Ltd.
      </footer>
    </div>
  );
};
