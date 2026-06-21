"use client";

import { Camera, CameraOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type VideoPreviewProps = {
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
};

export function VideoPreview({ enabled, onEnabledChange }: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function setupVideo() {
      if (!enabled) {
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        if (videoRef.current) {
          videoRef.current.srcObject = null;
        }
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setError(null);
      } catch (cameraError) {
        const message =
          cameraError instanceof Error ? cameraError.message : "Camera access failed.";
        setError(message);
        onEnabledChange(false);
      }
    }

    void setupVideo();
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [enabled, onEnabledChange]);

  return (
    <section className="panel muted-panel stack-sm">
      <div className="row row-between wrap">
        <div>
          <p className="eyebrow">Video Mode</p>
          <h3>Optional camera preview for interview practice.</h3>
        </div>
        <button
          className="button button-secondary"
          onClick={() => onEnabledChange(!enabled)}
          type="button"
        >
          {enabled ? <CameraOff size={16} /> : <Camera size={16} />}
          {enabled ? "Disable camera" : "Enable camera"}
        </button>
      </div>

      <div className="video-frame">
        {enabled ? <video autoPlay muted playsInline ref={videoRef} /> : <p>Camera preview is off.</p>}
      </div>
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}
