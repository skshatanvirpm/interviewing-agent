const apiBaseUrl = process.env.API_BASE_URL?.replace(/\/$/, "");
const webOrigin = process.env.WEB_ORIGIN?.replace(/\/$/, "");

if (!apiBaseUrl || !webOrigin) {
  throw new Error("API_BASE_URL and WEB_ORIGIN are required.");
}

for (const path of ["", "/interview", "/review"]) {
  const response = await fetch(`${webOrigin}${path}`);
  const html = await response.text();
  console.log(
    JSON.stringify({
      check: `web route ${path || "/"}`,
      status: response.status,
      html: response.headers.get("content-type")?.includes("text/html") ?? false,
    }),
  );
  if (!response.ok || !html) {
    throw new Error(`Hosted web route ${path || "/"} failed.`);
  }
  if (path === "" && !html.includes("Deployment access token")) {
    throw new Error("Hosted home page is missing the deployment access-token control.");
  }
}

const preflight = await fetch(`${apiBaseUrl}/sessions/bootstrap`, {
  method: "OPTIONS",
  headers: {
    Origin: webOrigin,
    "Access-Control-Request-Headers": "authorization,content-type",
    "Access-Control-Request-Method": "POST",
  },
});
console.log(
  JSON.stringify({
    check: "CORS preflight",
    status: preflight.status,
    allowedOrigin: preflight.headers.get("access-control-allow-origin"),
  }),
);
if (
  !preflight.ok ||
  preflight.headers.get("access-control-allow-origin") !== webOrigin
) {
  throw new Error("Hosted CORS preflight failed.");
}
