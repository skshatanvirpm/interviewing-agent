"use client";

import { ArrowRight, Trash2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { FinalFeedbackPanel } from "@/components/final-feedback-panel";
import {
  deleteInterviewSession,
  getInterviewSession,
  rememberBootstrapSessionAccess,
} from "@/lib/api";
import type { BootstrapResponse, InterviewSession } from "@/lib/types";

const STORAGE_KEY = "interviewing-agent.bootstrap";
const HISTORY_KEY = "interviewing-agent.resume-history";

export function ReviewShell() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    const sessionId = searchParams.get("session");

    if (raw) {
      const bootstrap = JSON.parse(raw) as BootstrapResponse;
      if (!sessionId || bootstrap.session.id === sessionId) {
        rememberBootstrapSessionAccess(bootstrap);
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

  async function handleDeleteSession() {
    if (!session) {
      return;
    }

    setDeleting(true);
    setError(null);

    try {
      await deleteInterviewSession(session.id);
      clearLocalSessionArtifacts(session);
      router.push("/");
    } catch (deleteError) {
      const message =
        deleteError instanceof Error
          ? deleteError.message
          : "Failed to delete the interview data.";
      setError(message);
    } finally {
      setDeleting(false);
    }
  }

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
        <button
          className="button button-secondary"
          disabled={deleting}
          onClick={() => {
            void handleDeleteSession();
          }}
          type="button"
        >
          <Trash2 size={16} />
          {deleting ? "Deleting..." : "Delete interview data"}
        </button>
      </div>
      {error ? <p className="error-line">{error}</p> : null}
    </div>
  );
}

function clearLocalSessionArtifacts(session: InterviewSession): void {
  localStorage.removeItem(STORAGE_KEY);

  try {
    const rawHistory = localStorage.getItem(HISTORY_KEY);
    if (!rawHistory) {
      return;
    }
    const parsedHistory = JSON.parse(rawHistory) as Array<{
      candidate_id?: string | null;
      resume_id?: string | null;
    }>;
    const nextHistory = parsedHistory.filter((entry) => {
      if (session.candidate_id && entry.candidate_id === session.candidate_id) {
        return false;
      }
      if (session.resume_id && entry.resume_id === session.resume_id) {
        return false;
      }
      return true;
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
  } catch {
    localStorage.removeItem(HISTORY_KEY);
  }
}
