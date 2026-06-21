import { Suspense } from "react";

import { InterviewShell } from "@/components/interview-shell";

export default function InterviewPage() {
  return (
    <main className="page-shell">
      <Suspense fallback={<section className="panel">Loading interview session...</section>}>
        <InterviewShell />
      </Suspense>
    </main>
  );
}
