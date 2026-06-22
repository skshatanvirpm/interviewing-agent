import { readFile } from "node:fs/promises";

const apiBaseUrl = process.env.API_BASE_URL?.replace(/\/$/, "");
const webOrigin = process.env.WEB_ORIGIN?.replace(/\/$/, "");
const accessToken = process.env.API_ACCESS_TOKEN;

if (!apiBaseUrl || !webOrigin || !accessToken) {
  throw new Error("API_BASE_URL, WEB_ORIGIN, and API_ACCESS_TOKEN are required.");
}

const browserHeaders = {
  Accept: "application/json",
  Origin: webOrigin,
  "User-Agent": "Mozilla/5.0",
};
const authenticatedHeaders = {
  ...browserHeaders,
  Authorization: `Bearer ${accessToken}`,
};

async function responseBody(response) {
  const text = await response.text();
  return { text, json: text ? JSON.parse(text) : null };
}

const health = await fetch(`${apiBaseUrl}/health`, { headers: browserHeaders });
const healthBody = await health.json();
console.log(
  JSON.stringify({
    check: "health",
    status: health.status,
    openaiConfigured: healthBody.openai_configured,
    supabaseConfigured: healthBody.supabase_configured,
  }),
);
if (!health.ok || !healthBody.openai_configured) {
  throw new Error("Hosted health check failed.");
}

const anonymous = await fetch(`${apiBaseUrl}/sessions/bootstrap-from-parsed`, {
  method: "POST",
  headers: { ...browserHeaders, "Content-Type": "application/json" },
  body: JSON.stringify({ resume: { candidate_name: "Synthetic Candidate" } }),
});
console.log(JSON.stringify({ check: "anonymous rejection", status: anonymous.status }));
if (anonymous.status !== 401) {
  throw new Error("Anonymous API access was not rejected.");
}

const resumeBytes = await readFile("docs/examples/sample-resume.pdf");
const resumeForm = new FormData();
resumeForm.append(
  "resume",
  new Blob([resumeBytes], { type: "application/pdf" }),
  "sample-resume.pdf",
);
const bootstrap = await fetch(`${apiBaseUrl}/sessions/bootstrap`, {
  method: "POST",
  headers: authenticatedHeaders,
  body: resumeForm,
});
const bootstrapBody = await responseBody(bootstrap);
if (!bootstrap.ok) {
  throw new Error(
    `PDF bootstrap failed with HTTP ${bootstrap.status}: ${bootstrapBody.text.slice(0, 300)}`,
  );
}
const sessionId = bootstrapBody.json.session.id;
console.log(
  JSON.stringify({
    check: "PDF bootstrap",
    status: bootstrap.status,
    candidate: bootstrapBody.json.resume.candidate_name,
    sessionCreated: Boolean(sessionId),
  }),
);

const turn = await fetch(`${apiBaseUrl}/interviews/${sessionId}/turn`, {
  method: "POST",
  headers: { ...authenticatedHeaders, "Content-Type": "application/json" },
  body: JSON.stringify({
    candidate_response:
      "I build retrieval and recommendation systems with measurable offline and online evaluation.",
    metadata: {
      source: "text",
      transcript_retry_count: 0,
      tab_switch_count: 0,
      window_blur_count: 0,
      used_paste: false,
      camera_enabled: false,
      realtime_enabled: false,
    },
  }),
});
const turnBody = await responseBody(turn);
if (!turn.ok) {
  throw new Error(
    `Interview turn failed with HTTP ${turn.status}: ${turnBody.text.slice(0, 300)}`,
  );
}
console.log(
  JSON.stringify({
    check: "interview turn",
    status: turn.status,
    phase: turnBody.json.session.current_phase,
    replyPresent: Boolean(turnBody.json.latest_reply?.text),
  }),
);

const completed = await fetch(`${apiBaseUrl}/interviews/${sessionId}/complete`, {
  method: "POST",
  headers: { ...authenticatedHeaders, "Content-Type": "application/json" },
});
const completedBody = await responseBody(completed);
console.log(
  JSON.stringify({
    check: "interview completion",
    status: completed.status,
    phase: completedBody.json?.current_phase,
    scorePresent: completedBody.json?.scores?.overall != null,
    feedbackPresent: Boolean(completedBody.json?.final_feedback),
  }),
);
if (
  !completed.ok ||
  completedBody.json?.current_phase !== "complete" ||
  completedBody.json?.scores?.overall == null ||
  !completedBody.json?.final_feedback
) {
  throw new Error("Hosted interview completion failed.");
}

const speech = await fetch(`${apiBaseUrl}/audio/speak`, {
  method: "POST",
  headers: { ...authenticatedHeaders, "Content-Type": "application/json" },
  body: JSON.stringify({ text: "Welcome to the interview." }),
});
const speechBytes = Buffer.from(await speech.arrayBuffer());
console.log(
  JSON.stringify({
    check: "speech",
    status: speech.status,
    contentType: speech.headers.get("content-type"),
    bytes: speechBytes.length,
  }),
);
if (!speech.ok || speechBytes.length < 100) {
  throw new Error("Hosted speech generation failed.");
}
