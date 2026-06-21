"use client";

import { ArrowRight } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { FinalFeedbackPanel } from "@/components/final-feedback-panel";
import { getInterviewSession } from "@/lib/api";
import type { BootstrapResponse, InterviewSession } from "@/lib/types";

const STORAGE_KEY = "interviewing-agent.bootstrap";

export function ReviewShell() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [session, setSession] = useState<InterviewSession | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    const sessionId = searchParams.get("session");

    if (raw) {
      const bootstrap = JSON.parse(raw) as BootstrapResponse;
      if (!sessionId || bootstrap.session.id === sessionId) {
        setSession(bootstrap.session);
      }
    }

    if (!sessionId) {
      return;
    }

    void (async () => {
      try {
        const restored = await getInterviewSession(sessionId);
        setSession(restored);
      } catch {
        // Keep local fallback if available.
      }
    })();
  }, [searchParams]);

  if (!session) {
    return (
      <section className="panel stack-md">
        <div>
          <p className="eyebrow">Review</p>
          <h2>No review session found.</h2>
        </div>
        <p className="supporting">
          Go back to the home page, parse a resume, and start an interview first.
        </p>
        <button
          className="button button-primary"
          onClick={() => {
            router.push("/");
          }}
          type="button"
        >
          <ArrowRight size={16} />
          Back to home
        </button>
      </section>
    );
  }

  return (
    <div className="stack-lg">
      <FinalFeedbackPanel session={session} />

      <div className="row gap-sm wrap review-actions">
        <button
          className="button button-primary"
          onClick={() => {
            router.push("/");
          }}
          type="button"
        >
          <ArrowRight size={16} />
          Start another interview
        </button>
      </div>
    </div>
  );
}
