// Connect YouTube from the browser: OAuth code flow with PKCE against a Google "Web application" client.
// Google sends the person back to the app URL with ?code=&state=; app.js parks that in sessionStorage and opens
// Settings, which calls finishYouTubeAuth() with the saved client id and secret and stores the refresh token.
export const YT_SCOPES = [
  "https://www.googleapis.com/auth/youtube.upload",
  "https://www.googleapis.com/auth/youtube.readonly",
  "https://www.googleapis.com/auth/yt-analytics.readonly",
];
const STATE_KEY = "vf.ytstate", RESULT_KEY = "vf.ytauth", PREFIX = "vfyt-";

// The exact URL registered as the client's redirect URI, e.g. https://ayushratan1.github.io/vidforge/
export function redirectUri() { return location.origin + location.pathname.replace(/index\.html$/, ""); }

const b64url = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

export async function startYouTubeAuth(clientId) {
  const state = PREFIX + crypto.randomUUID();
  const verifier = b64url(crypto.getRandomValues(new Uint8Array(48)));
  const challenge = b64url(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))));
  sessionStorage.setItem(STATE_KEY, JSON.stringify({state, verifier}));
  const q = new URLSearchParams({client_id: clientId.trim(), redirect_uri: redirectUri(), response_type: "code", scope: YT_SCOPES.join(" "),
    access_type: "offline", prompt: "consent select_account", include_granted_scopes: "true", state,
    code_challenge: challenge, code_challenge_method: "S256"});
  location.assign("https://accounts.google.com/o/oauth2/v2/auth?" + q);
}

// Called once at boot: true when this page load is Google's redirect back to us.
export function captureYouTubeRedirect(params) {
  if (!(params.get("state") || "").startsWith(PREFIX)) return false;
  try { sessionStorage.setItem(RESULT_KEY, JSON.stringify({code: params.get("code"), state: params.get("state"), error: params.get("error")})); } catch {}
  return true;
}

export function takePendingYouTubeAuth() {
  try { const v = JSON.parse(sessionStorage.getItem(RESULT_KEY) || "null"); sessionStorage.removeItem(RESULT_KEY); return v; } catch { return null; }
}

// Exchange the code for tokens. Returns {refresh_token, channel: "Title|UC..."}.
export async function finishYouTubeAuth(pending, clientId, clientSecret) {
  let started = null;
  try { started = JSON.parse(sessionStorage.getItem(STATE_KEY) || "null"); sessionStorage.removeItem(STATE_KEY); } catch {}
  if (pending.error) throw new Error(pending.error === "access_denied" ? "Google sign-in was cancelled." : "Google said: " + pending.error);
  if (!started || started.state !== pending.state) throw new Error("This sign-in was not started on this tab. Press Connect YouTube again.");
  const r = await fetch("https://oauth2.googleapis.com/token", {method: "POST", headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: new URLSearchParams({grant_type: "authorization_code", code: pending.code, client_id: clientId.trim(), client_secret: clientSecret.trim(),
      redirect_uri: redirectUri(), code_verifier: started.verifier})});
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error_description || j.error || `Google returned ${r.status}`);
  if (!j.refresh_token) throw new Error("Google sent no refresh token. Remove VidForge at myaccount.google.com/permissions, then connect again.");
  let channel = "";
  try {
    const c = await fetch("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", {headers: {Authorization: "Bearer " + j.access_token}}).then(x => x.json());
    const it = c.items?.[0];
    if (it) channel = `${it.snippet.title}|${it.id}`;
  } catch {}
  return {refresh_token: j.refresh_token, channel};
}
