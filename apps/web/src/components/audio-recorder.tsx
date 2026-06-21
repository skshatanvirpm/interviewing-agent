"use client";

import { AudioWaveform, Mic, Pause, Play, RotateCcw, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { transcribeAudio } from "@/lib/api";

type AudioRecorderProps = {
  onTranscript: (
    transcript: string,
    meta: { source: "audio"; retryCount: number },
  ) => void;
};

export function AudioRecorder({ onTranscript }: AudioRecorderProps) {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const lastAudioBlobRef = useRef<Blob | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    return () => {
      recorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function transcribeBlob(audioBlob: Blob, retryCountValue: number = retryCount) {
    setIsBusy(true);
    setError(null);
    setStatus("Transcribing candidate audio...");

    try {
      const result = await transcribeAudio(audioBlob);
      onTranscript(result.transcript, { source: "audio", retryCount: retryCountValue });
      setStatus("Transcript ready. Review or edit it before sending.");
    } catch (transcriptionError) {
      const message =
        transcriptionError instanceof Error
          ? transcriptionError.message
          : "Audio transcription failed.";
      setError(`${message} Retry the transcription or record again.`);
      setStatus("Audio turn failed. Retry the transcription or record again.");
    } finally {
      setIsBusy(false);
    }
  }

  async function startRecording() {
    setError(null);
    setStatus(null);

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser does not support microphone capture.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      chunksRef.current = [];
      lastAudioBlobRef.current = null;
      setRetryCount(0);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        recorderRef.current = null;
        setIsPaused(false);

        if (audioBlob.size === 0) {
          setError("No audio was captured. Please record again.");
          setStatus("No audio was captured.");
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        lastAudioBlobRef.current = audioBlob;
        setStatus("Processing your audio turn...");

        try {
          await transcribeBlob(audioBlob, 0);
        } finally {
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      recorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setIsPaused(false);
      setStatus("Recording in progress.");
    } catch (recordingError) {
      const message =
        recordingError instanceof Error
          ? recordingError.message
          : "Microphone access failed.";
      setError(message);
      setStatus("Microphone access failed.");
    }
  }

  function pauseRecording() {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") {
      return;
    }

    recorder.pause();
    setIsPaused(true);
    setStatus("Recording paused. Resume when you are ready.");
  }

  function resumeRecording() {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "paused") {
      return;
    }

    recorder.resume();
    setIsPaused(false);
    setStatus("Recording resumed.");
  }

  async function retryTranscription() {
    if (!lastAudioBlobRef.current) {
      return;
    }

    const nextRetryCount = retryCount + 1;
    setRetryCount(nextRetryCount);
    await transcribeBlob(lastAudioBlobRef.current, nextRetryCount);
  }

  function stopRecording() {
    recorderRef.current?.stop();
    setIsRecording(false);
    setIsPaused(false);
    setStatus("Stopping the recording...");
  }

  return (
    <div className="panel muted-panel recorder">
      <div className="row row-between">
        <div>
          <p className="eyebrow">Turn-Based Audio</p>
          <h3>Record your answer, then let the agent transcribe it.</h3>
        </div>
        <AudioWaveform className="icon-accent" />
      </div>

      <div className="row gap-sm wrap">
        <button
          className="button button-primary"
          disabled={isBusy || isRecording}
          onClick={startRecording}
          type="button"
        >
          <Mic size={16} />
          Start recording
        </button>
        <button
          className="button button-secondary"
          disabled={!isRecording || isPaused}
          onClick={pauseRecording}
          type="button"
        >
          <Pause size={16} />
          Pause
        </button>
        <button
          className="button button-secondary"
          disabled={!isRecording || !isPaused}
          onClick={resumeRecording}
          type="button"
        >
          <Play size={16} />
          Resume
        </button>
        <button
          className="button button-secondary"
          disabled={!isRecording}
          onClick={stopRecording}
          type="button"
        >
          <Square size={16} />
          Stop
        </button>
        <button
          className="button button-secondary"
          disabled={isRecording || isBusy || !lastAudioBlobRef.current}
          onClick={retryTranscription}
          type="button"
        >
          <RotateCcw size={16} />
          Retry transcription
        </button>
      </div>

      {status ? <p className="status-line">{status}</p> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </div>
  );
}
