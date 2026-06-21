"use client";

import { LoaderCircle, Mic, RotateCcw, SendHorizontal, Square } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";

import {
  beginInterview,
  completeInterview,
  getInterviewSession,
  sendInterviewTurn,
  transcribeAudio,
} from "@/lib/api";
import type {
  BootstrapResponse,
  InterviewPhase,
  InterviewSession,
  TurnMetadata,
} from "@/lib/types";

const STORAGE_KEY = "interviewing-agent.bootstrap";

const phaseLabels: Record<InterviewPhase, string> = {
  phase_1_intro: "Introduction",
  phase_2_deep_dive: "Deep dive",
  phase_3_breadth: "Breadth",
  phase_4_factual: "Factual",
  phase_5_behavioral: "Behavioral",
  complete: "Complete",
};

export function InterviewShell() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const lastAudioBlobRef = useRef<Blob | null>(null);
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [candidateName, setCandidateName] = useState("Candidate");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const [turnSource, setTurnSource] = useState<TurnMetadata["source"]>("text");
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [windowBlurCount, setWindowBlurCount] = useState(0);
  const [usedPaste, setUsedPaste] = useState(false);
  const [draftStartedAt, setDraftStartedAt] = useState<number | null>(null);
  const [transcriptRetryCount, setTranscriptRetryCount] = useState(0);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    const sessionId = searchParams.get("session");

    if (raw) {
      const bootstrap = JSON.parse(raw) as BootstrapResponse;
      if (!sessionId || bootstrap.session.id === sessionId) {
        setSession(bootstrap.session);
        setCandidateName(bootstrap.resume.candidate_name || "Candidate");
      }
    }

    if (!sessionId) {
      return;
    }

    void (async () => {
      try {
        const restored = await getInterviewSession(sessionId);
        setSession(restored);
        setCandidateName(restored.resume.candidate_name || "Candidate");
      } catch {
        // Keep local bootstrap fallback.
      }
    })();
  }, [searchParams]);

  useEffect(() => {
    function handleVisibility() {
      if (document.hidden) {
        setTabSwitchCount((current) => current + 1);
      }
    }

    function handleBlur() {
      setWindowBlurCount((current) => current + 1);
    }

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("blur", handleBlur);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("blur", handleBlur);
      recorderRef.current?.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  useEffect(() => {
    if (session?.current_phase === "complete") {
      router.replace(`/review?session=${session.id}`);
    }
  }, [router, session]);

  useEffect(() => {
    if (!session || session.current_phase !== "phase_1_intro") {
      return;
    }

    const candidateMessageCount = session.messages.filter((message) => message.role === "candidate").length;
    const hasBackgroundPrompt = session.messages.some(
      (message) =>
        message.role === "interviewer" &&
        message.phase === "phase_1_intro" &&
        message.text.toLowerCase().includes("tell me about yourself"),
    );

    if (candidateMessageCount > 0 || hasBackgroundPrompt) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void (async () => {
        try {
          const started = await beginInterview(session.id);
          setSession(started);
          setCandidateName(started.resume.candidate_name || "Candidate");
          localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify({
              resume: {
                candidate_name: started.resume.candidate_name || "Candidate",
              },
              session: started,
            }),
          );
        } catch {
          // Leave the greeting visible if the delayed start request fails.
        }
      })();
    }, 5000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [session]);

  function persistSession(nextSession: InterviewSession) {
    setSession(nextSession);
    setCandidateName(nextSession.resume.candidate_name || candidateName);
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        resume: {
          candidate_name: nextSession.resume.candidate_name || candidateName,
        },
        session: nextSession,
      }),
    );
  }

  function resetDraftSignals() {
    setText("");
    setTurnSource("text");
    setUsedPaste(false);
    setDraftStartedAt(null);
    setTranscriptRetryCount(0);
    setAudioStatus(null);
    lastAudioBlobRef.current = null;
  }

  function startDraftIfNeeded() {
    setDraftStartedAt((current) => current ?? Date.now());
  }

  async function submitTurnWithValue(
    candidateResponse: string,
    source: TurnMetadata["source"],
    retryCount: number = transcriptRetryCount,
  ) {
    if (!session || !candidateResponse.trim()) {
      return;
    }

    setLoading(true);
    setError(null);

    const metadata: TurnMetadata = {
      source,
      answer_duration_seconds: draftStartedAt ? (Date.now() - draftStartedAt) / 1000 : null,
      transcript_retry_count: retryCount,
      tab_switch_count: tabSwitchCount,
      window_blur_count: windowBlurCount,
      used_paste: usedPaste,
      camera_enabled: false,
      realtime_enabled: source === "realtime",
    };

    try {
      const result = await sendInterviewTurn(session.id, candidateResponse.trim(), metadata);
      persistSession(result.session);
      resetDraftSignals();
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "Interview turn failed.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitTurnWithValue(text, turnSource);
  }

  async function handleEndInterview() {
    if (!session) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const completed = await completeInterview(session.id);
      persistSession(completed);
      router.replace(`/review?session=${completed.id}`);
    } catch (completionError) {
      const message =
        completionError instanceof Error
          ? completionError.message
          : "Failed to end the interview.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function transcribeAndSubmit(audioBlob: Blob, retryCountValue: number) {
    setIsTranscribing(true);
    setError(null);
    setAudioStatus("Transcribing your answer...");

    try {
      const result = await transcribeAudio(audioBlob);
      const transcript = result.transcript.trim();
      if (!transcript) {
        throw new Error("The audio was captured, but no transcript was returned.");
      }

      setText(transcript);
      setTurnSource("audio");
      setAudioStatus("Transcript ready. Sending your answer...");
      await submitTurnWithValue(transcript, "audio", retryCountValue);
    } catch (transcriptionError) {
      const message =
        transcriptionError instanceof Error
          ? transcriptionError.message
          : "Audio transcription failed.";
      setError(`${message} Retry the transcription or record again.`);
      setAudioStatus("Audio turn failed. Retry the transcription or record again.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function startRecording() {
    setError(null);
    setAudioStatus(null);

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser does not support microphone capture.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredMimeType =
        typeof MediaRecorder !== "undefined" &&
        MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : undefined;
      const recorder = preferredMimeType
        ? new MediaRecorder(stream, { mimeType: preferredMimeType })
        : new MediaRecorder(stream);

      streamRef.current = stream;
      recorderRef.current = recorder;
      chunksRef.current = [];
      lastAudioBlobRef.current = null;
      setTranscriptRetryCount(0);
      startDraftIfNeeded();

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const mimeType = recorder.mimeType || "audio/webm";
        const audioBlob = new Blob(chunksRef.current, { type: mimeType });
        chunksRef.current = [];
        recorderRef.current = null;
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setIsRecording(false);

        if (audioBlob.size === 0) {
          setError("No audio was captured. Please record again.");
          setAudioStatus("No audio was captured.");
          return;
        }

        lastAudioBlobRef.current = audioBlob;
        void transcribeAndSubmit(audioBlob, 0);
      };

      recorder.start();
      setIsRecording(true);
      setTurnSource("audio");
      setAudioStatus("Recording... click the stop icon when you are done.");
    } catch (recordingError) {
      const message =
        recordingError instanceof Error
          ? recordingError.message
          : "Microphone access failed.";
      setError(message);
      setAudioStatus("Microphone access failed.");
    }
  }

  function stopRecording() {
    if (!recorderRef.current || recorderRef.current.state === "inactive") {
      return;
    }
    setAudioStatus("Finishing recording...");
    recorderRef.current.stop();
  }

  async function toggleVoiceInput() {
    if (isRecording) {
      stopRecording();
      return;
    }

    await startRecording();
  }

  async function retryTranscription() {
    if (!lastAudioBlobRef.current || isRecording || isTranscribing || loading) {
      return;
    }

    const nextRetryCount = transcriptRetryCount + 1;
    setTranscriptRetryCount(nextRetryCount);
    await transcribeAndSubmit(lastAudioBlobRef.current, nextRetryCount);
  }

  if (!session) {
    return (
      <section className="panel">
        <p className="eyebrow">Interview session</p>
        <h2>No interview session found.</h2>
        <p className="supporting">
          Go back to the home page, upload a resume, and start from there.
        </p>
      </section>
    );
  }

  const isBusy = loading || isTranscribing;

  return (
    <div className="stack-lg">
      <section className="panel panel-glow chat-header">
        <div className="row row-between wrap gap-sm">
          <div>
            <p className="eyebrow">Interview</p>
            <h1>{candidateName}</h1>
            <p className="supporting">
              Current phase: {phaseLabels[session.current_phase]}
            </p>
          </div>
          <button
            className="button button-secondary"
            disabled={isBusy}
            onClick={() => {
              void handleEndInterview();
            }}
            type="button"
          >
            End interview
          </button>
        </div>
      </section>

      <section className="panel chat-shell">
        <div className="chat-feed">
          {session.messages.map((message) => (
            <article
              className={`chat-bubble ${message.role === "interviewer" ? "chat-bubble-ai" : "chat-bubble-user"}`}
              key={message.id}
            >
              <p className="message-meta">
                {message.role === "interviewer" ? "Interviewer" : "You"} ·{" "}
                {phaseLabels[message.phase]}
              </p>
              <p>{message.text}</p>
            </article>
          ))}
        </div>

        <form className="chat-composer" onSubmit={handleSubmit}>
          <textarea
            className="chat-input"
            onChange={(event) => {
              setText(event.target.value);
              setTurnSource("text");
              startDraftIfNeeded();
            }}
            onPaste={() => setUsedPaste(true)}
            placeholder="Type your answer here, or use the mic."
            rows={3}
            value={text}
          />
          <div className="row row-between wrap gap-sm">
            <div className="row gap-sm wrap">
              <button
                aria-label={isRecording ? "Stop recording" : "Record your answer"}
                className={`icon-button ${isRecording ? "icon-button-live" : ""}`}
                disabled={isBusy}
                onClick={() => {
                  void toggleVoiceInput();
                }}
                type="button"
              >
                {isRecording ? <Square size={18} /> : <Mic size={18} />}
              </button>
              {lastAudioBlobRef.current && error ? (
                <button
                  aria-label="Retry the previous transcription"
                  className="icon-button"
                  disabled={isRecording || isBusy}
                  onClick={() => {
                    void retryTranscription();
                  }}
                  type="button"
                >
                  <RotateCcw size={18} />
                </button>
              ) : null}
            </div>
            <button
              className="button button-primary"
              disabled={isBusy || isRecording || !text.trim()}
              type="submit"
            >
              {isBusy ? <LoaderCircle className="spin" size={16} /> : <SendHorizontal size={16} />}
              {isBusy ? "Working..." : "Send answer"}
            </button>
          </div>
          {audioStatus ? <p className="status-line">{audioStatus}</p> : null}
          {error ? <p className="error-line">{error}</p> : null}
        </form>
      </section>
    </div>
  );
}
