"use client";

import { ArrowRight, ChevronDown, ChevronUp, FileClock, FileText, History } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import {
  API_ACCESS_TOKEN_REQUIRED,
  bootstrapInterview,
  bootstrapInterviewFromParsedResume,
  getApiAccessToken,
  setApiAccessToken,
} from "@/lib/api";
import type { BootstrapResponse, ParsedResumeHistoryEntry } from "@/lib/types";

const STORAGE_KEY = "interviewing-agent.bootstrap";
const HISTORY_KEY = "interviewing-agent.resume-history";
const MAX_HISTORY_ITEMS = 8;

export function ResumeUploader() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<BootstrapResponse | null>(null);
  const [previewLabel, setPreviewLabel] = useState("Resume ready");
  const [history, setHistory] = useState<ParsedResumeHistoryEntry[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  const [showParsedDetails, setShowParsedDetails] = useState(false);
  const [accessToken, setAccessToken] = useState("");

  useEffect(() => {
    setAccessToken(getApiAccessToken());
    try {
      const rawHistory = localStorage.getItem(HISTORY_KEY);
      if (rawHistory) {
        setHistory(JSON.parse(rawHistory) as ParsedResumeHistoryEntry[]);
      }
    } catch {
      localStorage.removeItem(HISTORY_KEY);
    }
  }, []);

  function startInterview() {
    if (!preview) {
      return;
    }
    router.push(`/interview?session=${preview.session.id}`);
  }

  function persistHistory(nextHistory: ParsedResumeHistoryEntry[]) {
    setHistory(nextHistory);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
  }

  function applyPreview(
    bootstrap: BootstrapResponse,
    label: string,
    historyId: string | null,
    nextInfo: string | null = null,
  ) {
    setPreview(bootstrap);
    setPreviewLabel(label);
    setSelectedHistoryId(historyId);
    setInfo(nextInfo);
    setShowParsedDetails(false);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bootstrap));
  }

  function rememberResume(entry: ParsedResumeHistoryEntry): ParsedResumeHistoryEntry[] {
    const nextHistory = [entry, ...history.filter((item) => item.fingerprint !== entry.fingerprint)].slice(
      0,
      MAX_HISTORY_ITEMS,
    );
    persistHistory(nextHistory);
    return nextHistory;
  }

  async function fingerprintFile(candidateFile: File): Promise<string> {
    const fallback = `${candidateFile.name}-${candidateFile.size}-${candidateFile.lastModified}`;
    if (!window.crypto?.subtle) {
      return fallback;
    }

    try {
      const buffer = await candidateFile.arrayBuffer();
      const digest = await window.crypto.subtle.digest("SHA-256", buffer);
      return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
    } catch {
      return fallback;
    }
  }

  async function reuseParsedResume(entry: ParsedResumeHistoryEntry) {
    if (API_ACCESS_TOKEN_REQUIRED && !accessToken.trim()) {
      setError("Enter the deployment access token before starting an interview.");
      return;
    }

    setLoading(true);
    setError(null);
    setInfo(null);

    try {
      const bootstrap = await bootstrapInterviewFromParsedResume({
        resume: entry.resume,
        resume_label: entry.label,
        candidate_id: entry.candidate_id,
        resume_id: entry.resume_id,
      });
      rememberResume(entry);
      applyPreview(
        bootstrap,
        entry.label,
        entry.id,
        "Loaded the previously parsed resume from history. No reparse was needed.",
      );
    } catch (reuseError) {
      const message =
        reuseError instanceof Error ? reuseError.message : "Failed to reuse the parsed resume.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setInfo(null);

    if (API_ACCESS_TOKEN_REQUIRED && !accessToken.trim()) {
      setError("Enter the deployment access token before starting an interview.");
      return;
    }

    if (!file) {
      setError("Upload a PDF resume to start the interview.");
      return;
    }

    setLoading(true);

    try {
      const fingerprint = await fingerprintFile(file);
      const cached = history.find((entry) => entry.fingerprint === fingerprint);

      if (cached) {
        await reuseParsedResume(cached);
        return;
      }

      const bootstrap = await bootstrapInterview(file);
      const nextEntry: ParsedResumeHistoryEntry = {
        id: window.crypto?.randomUUID?.() ?? fingerprint,
        fingerprint,
        label: file.name,
        parsed_at: new Date().toISOString(),
        candidate_id: bootstrap.session.candidate_id ?? null,
        resume_id: bootstrap.session.resume_id ?? null,
        resume: bootstrap.resume,
      };

      rememberResume(nextEntry);
      applyPreview(
        bootstrap,
        file.name,
        nextEntry.id,
        "Resume parsed and saved to history for one-click reuse.",
      );
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "Failed to parse the resume.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  function handleFileChange(nextFile: File | null) {
    setFile(nextFile);
    setError(null);
    setInfo(null);

    if (nextFile) {
      setPreview(null);
      setPreviewLabel("Resume ready");
      setSelectedHistoryId(null);
      setShowParsedDetails(false);
    }
  }

  function chooseAnotherResume() {
    setFile(null);
    setPreview(null);
    setPreviewLabel("Resume ready");
    setSelectedHistoryId(null);
    setShowParsedDetails(false);
    setError(null);
    setInfo(null);
  }

  return (
    <section className="panel panel-glow parsed-flow">
      <div className="row row-between wrap gap-sm">
        <div>
          <p className="eyebrow">Bootstrap</p>
          <h2>Upload one resume and begin when it is ready.</h2>
        </div>
        <FileText className="icon-accent" />
      </div>

      <p className="supporting">
        Keep the flow simple: parse once, start the interview, and only expand the parsed details
        if you want to inspect them.
      </p>

      {API_ACCESS_TOKEN_REQUIRED ? (
        <label className="access-field stack-xs" htmlFor="deployment-access-token">
          <span className="summary-label">Deployment access token</span>
          <input
            autoComplete="off"
            className="text-input"
            id="deployment-access-token"
            onChange={(event) => {
              setAccessToken(event.target.value);
              setApiAccessToken(event.target.value);
              setError(null);
            }}
            placeholder="Enter access token"
            type="password"
            value={accessToken}
          />
          <span className="supporting">
            The token is kept in this browser tab and sent only to the interview API.
          </span>
        </label>
      ) : null}

      {!preview && history.length ? (
        <section className="resume-history stack-md">
          <div className="row row-between wrap">
            <div>
              <p className="eyebrow">History</p>
              <h3>Previously parsed resumes</h3>
            </div>
            <div className="pill">
              <History size={14} />
              {history.length} saved
            </div>
          </div>

          <div className="history-grid">
            {history.map((entry) => (
              <article
                className={`summary-card history-card ${
                  selectedHistoryId === entry.id ? "history-card-active" : ""
                }`}
                key={entry.id}
              >
                <div className="stack-xs">
                  <div className="row row-between wrap">
                    <p className="summary-label">Resume</p>
                    <p className="history-date">{formatTimestamp(entry.parsed_at)}</p>
                  </div>
                  <p className="summary-value">{entry.resume.candidate_name || entry.label}</p>
                  <p className="summary-copy">{entry.label}</p>
                  <p className="supporting history-headline">
                    {entry.resume.headline || "Structured resume available from history."}
                  </p>
                </div>
                <button
                  className="button button-secondary"
                  disabled={loading}
                  onClick={() => {
                    void reuseParsedResume(entry);
                  }}
                  type="button"
                >
                  <FileClock size={16} />
                  Use this resume
                </button>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {!preview ? (
        <form className="stack-md" onSubmit={handleSubmit}>
          <label className="upload-zone" htmlFor="resume">
            <input
              accept="application/pdf"
              id="resume"
              onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
              type="file"
            />
            <span>{file ? file.name : "Choose a PDF resume"}</span>
          </label>

          <button className="button button-primary bootstrap-primary" disabled={loading} type="submit">
            <ArrowRight size={16} />
            {loading ? "Preparing resume..." : "Parse resume"}
          </button>
        </form>
      ) : null}

      {preview ? (
        <section className="summary-card parsed-summary-box stack-md">
          <div className="row row-between wrap">
            <div>
              <p className="summary-label">Resume ready</p>
              <p className="parsed-title">{preview.resume.candidate_name || "Candidate"}</p>
              <p className="supporting">{preview.resume.headline || "Structured resume prepared."}</p>
            </div>
            <div className="pill">{previewLabel}</div>
          </div>

          <div className="parsed-meta-row">
            <span>{preview.resume.projects.length} projects</span>
            <span>{preview.resume.skills.length} skills</span>
            <span>{preview.resume.inferred_domains.length} focus areas</span>
          </div>

          <div className="row gap-sm wrap">
            <button className="button button-primary" onClick={startInterview} type="button">
              <ArrowRight size={16} />
              Start interview
            </button>
            <button
              className="button button-secondary"
              onClick={() => {
                setShowParsedDetails((current) => !current);
              }}
              type="button"
            >
              {showParsedDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              {showParsedDetails ? "Hide parsed resume" : "Show parsed resume"}
            </button>
            <button className="button button-ghost" onClick={chooseAnotherResume} type="button">
              Choose another resume
            </button>
          </div>

          {showParsedDetails ? (
            <div className="parsed-detail-box stack-md">
              <article className="parsed-detail-section">
                <p className="summary-label">Summary</p>
                <p className="summary-copy">{preview.resume.summary || "Not found"}</p>
              </article>
              <ParsedSection title="Skills" values={preview.resume.skills} />
              <ParsedSection title="Projects" values={preview.resume.projects} />
              <ParsedSection title="Experience" values={preview.resume.experience} />
              <ParsedSection title="Education" values={preview.resume.education} />
              <ParsedSection title="Inferred domains" values={preview.resume.inferred_domains} />
              <ParsedSection title="Parser notes" values={preview.resume.notes} />
            </div>
          ) : null}
        </section>
      ) : null}

      {info ? <p className="status-line">{info}</p> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}

type ParsedSectionProps = {
  title: string;
  values: string[];
};

function ParsedSection({ title, values }: ParsedSectionProps) {
  return (
    <article className="parsed-detail-section">
      <p className="summary-label">{title}</p>
      {values.length ? (
        <ul className="flat-list">
          {values.map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
      ) : (
        <p className="summary-copy">Nothing detected</p>
      )}
    </article>
  );
}

function formatTimestamp(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Saved earlier";
  }

  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
