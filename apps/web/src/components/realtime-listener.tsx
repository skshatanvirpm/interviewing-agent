"use client";

import { Radio, Square } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

type RecognitionResult = {
  isFinal: boolean;
  0: { transcript: string };
};

type RecognitionEvent = {
  resultIndex: number;
  results: ArrayLike<RecognitionResult>;
};

type RecognitionErrorEvent = {
  error: string;
};

type BrowserSpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onresult: ((event: RecognitionEvent) => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionCtor = new () => BrowserSpeechRecognition;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  }
}

type RealtimeListenerProps = {
  enabled: boolean;
  onTranscript: (transcript: string) => void;
  onSpeakingStart: () => void;
};

export function RealtimeListener({
  enabled,
  onTranscript,
  onSpeakingStart,
}: RealtimeListenerProps) {
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interim, setInterim] = useState("");

  const Recognition = useMemo(
    () =>
      typeof window === "undefined"
        ? undefined
        : window.SpeechRecognition ?? window.webkitSpeechRecognition,
    [],
  );

  useEffect(() => {
    if (!enabled || !Recognition) {
      recognitionRef.current?.stop();
      recognitionRef.current = null;
      setActive(false);
      setInterim("");
      return;
    }

    const recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onstart = () => setActive(true);
    recognition.onerror = (event) => setError(event.error);
    recognition.onend = () => setActive(false);
    recognition.onresult = (event) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      setInterim(interimTranscript.trim());
      if (finalTranscript.trim()) {
        onSpeakingStart();
        onTranscript(finalTranscript.trim());
      }
    };

    recognitionRef.current = recognition;
    recognition.start();

    return () => recognition.stop();
  }, [Recognition, enabled, onSpeakingStart, onTranscript]);

  if (!enabled) {
    return null;
  }

  if (!Recognition) {
    return (
      <section className="panel muted-panel">
        <p className="error-line">Browser speech recognition is not available here.</p>
      </section>
    );
  }

  return (
    <section className="panel muted-panel stack-sm">
      <div className="row row-between wrap">
        <div>
          <p className="eyebrow">Realtime Assist</p>
          <h3>Continuous browser transcription for lower-latency turns.</h3>
        </div>
        <div className="pill">
          {active ? <Radio size={16} /> : <Square size={16} />}
          {active ? "Listening" : "Idle"}
        </div>
      </div>
      {interim ? <p className="supporting">{interim}</p> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}
