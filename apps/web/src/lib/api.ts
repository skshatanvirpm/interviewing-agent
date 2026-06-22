import type {
  BootstrapResponse,
  ParsedResume,
  InterviewSession,
  InterviewTurnResponse,
  TranscriptResponse,
  TurnMetadata,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const ACCESS_TOKEN_STORAGE_KEY = "interviewing-agent.api-access-token";

export const API_ACCESS_TOKEN_REQUIRED =
  process.env.NEXT_PUBLIC_REQUIRE_ACCESS_TOKEN === "true";

export function getApiAccessToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? "";
}

export function setApiAccessToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  const normalized = token.trim();
  if (normalized) {
    window.sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, normalized);
  } else {
    window.sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  }
}

function authenticatedHeaders(
  headers: Record<string, string> = {},
): Record<string, string> {
  const token = getApiAccessToken();
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
}

async function extractErrorMessage(response: Response): Promise<string> {
  const body = await response.text();
  if (!body) {
    return "Request failed";
  }

  try {
    const parsed = JSON.parse(body) as { detail?: string };
    return parsed.detail || body;
  } catch {
    return body;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  return (await response.json()) as T;
}

export async function bootstrapInterview(file: File): Promise<BootstrapResponse> {
  const formData = new FormData();
  formData.append("resume", file);

  const response = await fetch(`${API_BASE_URL}/sessions/bootstrap`, {
    method: "POST",
    headers: authenticatedHeaders(),
    body: formData,
  });

  return handleResponse<BootstrapResponse>(response);
}

export async function bootstrapInterviewFromParsedResume(payload: {
  resume: ParsedResume;
  resume_label?: string;
  candidate_id?: string | null;
  resume_id?: string | null;
}): Promise<BootstrapResponse> {
  const response = await fetch(`${API_BASE_URL}/sessions/bootstrap-from-parsed`, {
    method: "POST",
    headers: authenticatedHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(payload),
  });

  return handleResponse<BootstrapResponse>(response);
}

export async function sendInterviewTurn(
  sessionId: string,
  candidateResponse: string,
  metadata: TurnMetadata,
): Promise<InterviewTurnResponse> {
  const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}/turn`, {
    method: "POST",
    headers: authenticatedHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({
      candidate_response: candidateResponse,
      metadata,
    }),
  });

  return handleResponse<InterviewTurnResponse>(response);
}

export async function getInterviewSession(
  sessionId: string,
): Promise<InterviewSession> {
  const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}`, {
    method: "GET",
    headers: authenticatedHeaders(),
    cache: "no-store",
  });
  return handleResponse<InterviewSession>(response);
}

export async function beginInterview(
  sessionId: string,
): Promise<InterviewSession> {
  const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}/begin`, {
    method: "POST",
    headers: authenticatedHeaders({
      "Content-Type": "application/json",
    }),
  });
  return handleResponse<InterviewSession>(response);
}

export async function completeInterview(
  sessionId: string,
): Promise<InterviewSession> {
  const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}/complete`, {
    method: "POST",
    headers: authenticatedHeaders({
      "Content-Type": "application/json",
    }),
  });
  return handleResponse<InterviewSession>(response);
}

export async function transcribeAudio(file: Blob): Promise<TranscriptResponse> {
  const formData = new FormData();
  formData.append("audio", file, "candidate-turn.webm");

  const response = await fetch(`${API_BASE_URL}/audio/transcribe`, {
    method: "POST",
    headers: authenticatedHeaders(),
    body: formData,
  });

  return handleResponse<TranscriptResponse>(response);
}

export async function speakText(text: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/audio/speak`, {
    method: "POST",
    headers: authenticatedHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  return response.blob();
}
