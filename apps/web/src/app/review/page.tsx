import { Suspense } from "react";

import { ReviewShell } from "@/components/review-shell";

export default function ReviewPage() {
  return (
    <main className="page-shell">
      <Suspense fallback={<section className="panel">Loading review...</section>}>
        <ReviewShell />
      </Suspense>
    </main>
  );
}
