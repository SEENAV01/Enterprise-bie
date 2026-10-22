# Sign in with ChatGPT (SIWC) for BIE · feasibility report

Task 044c · 22 October 2026 · report only, nothing built, no sign-in, no model call, cost ₹0 · Owner: Navin

**Verdict: conditional (shart ke saath).** SIWC plan usage could power BIE's maker, but only from a machine
that Navin alone controls (his own laptop is the only place the terms clearly allow; an unmanaged VPS is
allowed by the developer docs but conflicts with one sentence of the terms). JSON-schema output, which every BIE
section needs, is not documented. So the Task 044 Codex route stays the primary plan, and SIWC stays a
documented option until a one-time probe (which Navin must approve) settles the unknowns.

Status words used below: **confirmed** (the exact wording was read on the official page), **confirmed (excerpt)**
(the exact wording came from a search-engine excerpt of the official page because the page itself returns
HTTP 403 to our tools), **not confirmed** (we could not find or verify it), **unknown** (the docs are silent).

## Sources read (22 October 2026)

The developer pages were downloaded as their official Markdown twins (`<page>.md`), so every quote below is
exact. The terms page and the OpenAI Help Center return HTTP 403 (a browser check) to every tool available here;
for them we have only search-engine excerpts, marked "(excerpt)". Before relying on a terms quote, re-read it
on the live page.

| Page | URL |
| --- | --- |
| Overview | https://developers.openai.com/siwc/token-sharing-open-source |
| Registration and sign-in | https://developers.openai.com/siwc/token-sharing-open-source/sign-in |
| Accounts and sessions | https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions |
| Models and inference | https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference |
| Preview limitations | https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations |
| Errors and recovery | https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery |
| Self-hosted VMs | https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms |
| Token reference | https://developers.openai.com/siwc/token-sharing-open-source/token-reference |
| Codex app-server | https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server |
| Quickstart | https://developers.openai.com/siwc/quickstart |
| Cookbook article | https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt |
| User guide (Codex docs) | https://learn.chatgpt.com/docs/sign-in-with-chatgpt |
| Terms (403 here) | https://openai.com/policies/sign-in-with-chatgpt-terms/ |
| Codex non-interactive mode (Task 044 route) | https://learn.chatgpt.com/docs/non-interactive-mode |
| DevKit README | https://github.com/openai/sign-in-with-chatgpt-devkit (README, "Licence") |

## What we thought we knew, checked

| Claim | Status | Exact wording and source |
| --- | --- | --- |
| Eligible: open-source projects, personal projects that run locally, selected private apps | **confirmed** | "At launch, ChatGPT plan usage is available to open-source projects, personal projects that run locally, and selected private apps." (cookbook) · "ChatGPT plan usage is available to all open-source partners and selected private clients." (quickstart) |
| Plus and Pro users | **confirmed** | "Eligible ChatGPT Plus and Pro users can use their ChatGPT plan for AI requests in your product." (quickstart) |
| Paid or remotely hosted apps use the interest form | **confirmed** | "These docs explain ChatGPT plan usage for open-source and locally hosted apps. If you're interested in offering it in a paid or remotely hosted app, complete the interest form." (overview) · "If you're building a paid or remotely hosted app, join the waitlist to request access before offering it to users." (cookbook) |
| No licence requirement | **confirmed (by absence)** | No SIWC page mentions a licence for the app. Note: OpenAI's own DevKit code is under "the Sign-in with ChatGPT DevKit Noncommercial License v1.0" (DevKit README), so BIE must not copy DevKit code. |
| `POST /v1/responses` with the OAuth bearer token | **confirmed** | "send the OAuth access token as `Authorization: Bearer <ACCESS_TOKEN>` to `POST https://api.openai.com/v1/responses`" (models and inference) |
| `store: false` and `stream: true` mandatory | **confirmed** | "Set `store` to `false` and `stream` to `true` on each HTTP inference request in this flow." (models and inference) |
| Success only after `response.completed` | **confirmed** | "Treat inference as successful only after receiving `response.completed`." (models and inference) |
| `max_output_tokens`, `temperature`, `top_p`, `background`, `metadata` rejected | **confirmed** | "Omit `background`, `conversation`, `max_output_tokens`, `max_tool_calls`, `metadata`, `moderation`, `multi_agent`, `prompt`, `prompt_cache_retention`, `safety_identifier`, `temperature`, `top_logprobs`, `top_p`, `truncation`, and `user`." (preview limitations) |
| No system-role items; use `instructions` | **confirmed** | "Use `instructions` or developer messages; explicit `{type: "message", role: "system"}` items are rejected." (preview limitations) |
| Images and files allowed if the model accepts them | **confirmed** | "Text, images, and files are supported when the selected model accepts them. Audio/video input, the Files upload API, and the transcription API are not supported by this flow." (preview limitations) |
| Image generation, file search, code interpreter unavailable | **confirmed** | "Image generation, file search, Code Interpreter, native computer use, hosted MCP/connectors, and Responses `tool_search`." (preview limitations, "Unsupported tools") |
| Structured output / JSON schema | **unknown** | No SIWC page mentions `text.format`, `json_schema` or structured output. `text` is not in the "Omit" list, so it is neither allowed nor forbidden in writing. |
| Usage-limit errors can arrive mid-stream | **confirmed** | "A usage-limit error can arrive as `response.failed` with `subscription_sharing_usage_limit_exceeded` or `subscription_sharing_usage_unavailable` after streaming has begun." (models and inference) |
| Loopback callback on 127.0.0.1, PKCE, scope `chatgpt.tokens.use.direct` | **confirmed** | "Use an HTTP loopback callback on `127.0.0.1` … Do not substitute with `localhost`." · scopes "`offline_access resource.invoke chatgpt.tokens.use.direct`" · "`code_challenge_method` `S256`" (sign-in) |
| `ext_agent_host_id` per host | **confirmed** | "An issued `client_id` can be reused across different agent hosts for the same user and workspace, but each host must have its own distinct host identifier." (overview) |
| Credential file 0600, written atomically | **confirmed** | "Write files atomically with owner-only permissions (`0600` on Unix), and never commit or log them." (sign-in) |
| Remote VM: sign in locally, transfer over SSH | **confirmed** | "A `127.0.0.1` callback reaches the computer running the browser, not the remote VM. Complete OAuth locally …" · "Transfer the selected registration's protected credential file to the tool's documented VM path over a secure channel such as SSH." (self-hosted VMs) |
| Requests only from a local runtime or a remote runtime only the user controls | **confirmed (excerpt)** | "Requests must originate from the user's local runtime or a remote runtime only that user controls." (terms) |
| Token storage local, not remote or managed | **confirmed (excerpt)** | "Any persistent storage of Authentication Tokens must be local and under the user's control, not in a remote or managed environment." (terms; one search attributed this sentence to a third-party quotation of the terms, another to the terms page itself) |
| No pooling, sharing or relaying | **partly confirmed** | The excerpt says the terms prohibit pooling, transferring, reselling, gifting or sharing plan usage or tokens, with an exception for "token handling expressly permitted by these Terms"; the exact wording and the exception's scope were not visible. Also: "Another user's activity must not trigger requests to the authenticated user's account." (terms, excerpt) |
| Background automation only with express authorisation | **confirmed (excerpt)** | "Obtain express consent before background use." · requests "must be for the authenticated user and arise from their activity or expressly authorized automations or background processes." (terms) |
| The plan may power only the connected app | **confirmed (excerpt)** | "Use the user's plan only for the application they connected. Do not provide general-purpose API access for other tools or unrelated requests." (terms) |
| OpenAI may suspend access | **not confirmed** | The excerpt shows an enforcement section beginning "We may suspend" and then cuts off; what is suspended (the app's SIWC access, the user's ChatGPT account, or both) could not be read. |
| Never ask for passwords or cookies | **confirmed (excerpt)** | "Do not ask users for their ChatGPT passwords or session cookies." (terms) |

Two more facts that matter for BIE:

- **Same usage pool as Codex:** "It uses your Codex / ChatGPT work usage included in your plan." · "App usage counts toward your existing plan limits. Connecting an app does not add a new allowance" · "An app's limit is a cap, not a separate allowance" (learn.chatgpt.com/docs/sign-in-with-chatgpt).
- **Pro and the 5-hour window:** "The five-hour usage limit does not apply for Pro users." (accounts and sessions). Weekly limits and per-app weekly caps still exist (the same pages); their size for Pro is not published.

## 1. Eligibility

**Today (public repository, no LICENSE file, Navin is the only operator, his own books): not confirmed.**

- BIE is public on GitHub but has **no licence file**. Without a licence the code is "all rights reserved", so
  it is not open source in the usual sense. The SIWC docs never define "open-source", so whether OpenAI would
  treat BIE as an open-source project is **unknown**. Adding a licence is Navin's decision and is not part of
  this task.
- "Personal projects that run locally" fits a run on Navin's own machine for his own use. But BIE produces
  course content Navin plans to sell, and the docs do not say whether a personal project may serve a business.
  **Unknown.**
- BIE is not offered to other users today, so it is not a "paid app" in the sense of selling the app. Running
  it on a rented server would make it "remotely hosted"; the docs send those cases to the interest form, while
  the self-hosted VM page describes exactly that case for open-source apps. **Unclear.**

**If the repository becomes private:** BIE can no longer claim the open-source path. Only "personal projects
that run locally" (laptop) or "selected private apps" remain, and "selected" means OpenAI picks; the interest
form becomes the way in for anything not on Navin's own machine.

**Interest form:** not strictly required for a laptop-only personal run; **advisable** before any server use, and
**required** before Phase 4, when other people would use BIE (the terms forbid one user's plan serving others).
Filling it in is free and commits to nothing.

**Genuinely unclear:** what counts as open-source without a licence; whether a commercial personal project
qualifies; whether a VM the user rents counts as "locally hosted".

## 2. Where it could run

| Place | Verdict | Why (terms and docs) | Fit with CLAUDE.md |
| --- | --- | --- | --- |
| Navin's Windows laptop (4 GB), with or without WSL2 | **Allowed** by the terms | A "local runtime"; tokens stored "local and under the user's control". The browser and the 127.0.0.1 callback are on the same machine, so sign-in works as documented. A direct SIWC client is only HTTPS calls and needs far less memory than the Codex CLI; BIE's PDF page images still need memory. | **Conflicts** with "Never ask him to run builds, tests or renders locally; do heavy work in the cloud workspace or GitHub Actions." Needs an explicit exception from Navin (Task 044b, the laptop variant, was never approved). Uptime depends on his home power, network and Windows updates. |
| A VPS only Navin controls (unmanaged, he holds root) | **Allowed by the developer docs, unclear under the terms** | Fits "a remote runtime only that user controls", and the self-hosted VM page describes this case. But the token file would live on that VPS, and the terms say persistent token storage must be "local … not in a remote or managed environment". The two texts conflict for this case. Also: "Host-specific usage attribution and revocation of ChatGPT plan access for transferred sessions are not yet available." | Fits "heavy work in the cloud". Needs Navin's yes to rent it (Task 044's machine) and, before relying on it, a written answer from OpenAI (interest form or support) on the storage sentence. |
| A "fully managed" VPS where the host's staff can log in (for example the eWebGuru plan Navin mentioned) | **Not allowed** | Not "only that user controls", and it is a "managed environment" for token storage. | — |
| GitHub Actions (this public repository) | **Not allowed** | Tokens would be stored as GitHub secrets (remote and managed); the runner is GitHub's, not Navin's; the rotating refresh token cannot be kept safely between runs. The Codex docs say the same for ChatGPT sign-in: "Do not use this workflow for public or open-source repositories." | — |
| GitHub Codespaces | **Not allowed** | A GitHub-managed environment; token storage would be remote and managed. | — |

## 3. Compared with the Task 044 Codex route

| | Codex route (Task 044, built) | SIWC direct route (not built) |
| --- | --- | --- |
| Official tool | OpenAI's Codex CLI, `codex exec`, ChatGPT sign-in | Plain HTTPS to the public Responses API with an OAuth token |
| Sign-in on a server | `codex login --device-auth` on the machine itself (a link and a code; works from the tablet) | Browser on the same machine (127.0.0.1 callback); for a server: sign in elsewhere and copy the credential file over SSH |
| JSON schema | **Enforced** (`--output-schema`) | **Unknown** (not documented) |
| Images | Yes (`--image`) | Yes, when the model accepts them |
| Streaming and control | Codex runs an agent turn (read-only sandbox, empty folder); BIE sees the final message and token counts | BIE sends `instructions` and `input` itself and reads the stream; no agent in between; `max_output_tokens`, `temperature` and others are rejected |
| Plan usage visible | Yes, before and after a run (`account/rateLimits/read` through `codex app-server`) | No documented endpoint; ChatGPT Settings → Usage only |
| Usage pool | ChatGPT/Codex plan usage | The same pool ("It uses your Codex / ChatGPT work usage included in your plan.") |
| Policy text | Codex docs: ChatGPT sign-in on trusted private machines, "Do not use this workflow for public or open-source repositories" (written for CI runners of public repositories; BIE's machine runs only reviewed `main`) | SIWC terms: storage "local … not in a remote or managed environment"; express consent for background use; only the connected app |
| Maturity | Established CLI | "Preview limitations" page; behaviour may change |
| Setup effort for Navin | One command and a code on the machine | Python on his laptop, a browser sign-in, then (for a server) a file copy over SSH |
| Machine memory | Codex CLI plus BIE | BIE only (lighter) |

**Recommendation:** prefer the Codex route. It has the one thing BIE cannot do without (an enforced JSON
schema), it signs in on the server itself, and it shows plan usage. SIWC becomes interesting only if the probe
in section 5 proves JSON-schema output and images, and if OpenAI confirms where tokens may live.

**What happens to the Task 044 files:** `bie/model_gateway/live/codex_client.py`, `tools/codex_vm.py` and
`deployment/codex-vm/` **stay** and keep **waiting** for Navin's yes to the machine. Nothing is retired or deleted.

## 4. Design of a `chatgpt_oauth` route (text only, not built)

- **Where:** a new `bie/model_gateway/live/chatgpt_oauth_client.py` with a client that offers `responses_create(...)`,
  so the existing `GPTAdapter`, `LiveGateway`, runner, ledger and cost guard are used unchanged. Route name
  `chatgpt`, `via = "chatgpt_plan"`, added to `SUBSCRIPTION_VIAS`. It is used only when chosen explicitly
  (`--maker chatgpt`); it never becomes a default and never falls back to an API key or a fake.
- **Request body:** `model`, `instructions` (the joined system text), `input` (user turns as `input_text` and
  `input_image` parts; remake turns as earlier `assistant` output followed by the findings), `store: false`,
  `stream: true`. Dropped on purpose: `max_output_tokens`, `temperature`, `top_p`, `metadata`, `background`,
  `prompt_cache_retention`, `user`, `previous_response_id` (the full history is sent each time, as BIE's runner
  already does).
- **JSON schema:** if the probe shows `text: {format: {type: "json_schema", strict: true, schema}}` is accepted, send
  BIE's schema there (stripped to OpenAI keywords, as today). If not, put the schema into `instructions` and rely
  on BIE's own strict validation plus its one repair turn (the AICredits path already works this way). Either way,
  the gateway validates every answer locally.
- **Streaming:** read server-sent events with the existing `HttpTransport.request_events`; collect
  `response.output_text.delta`; accept only `response.completed` (take `usage` from it); `response.failed` and
  `response.incomplete` are mapped below; a stream that ends without a terminal event is `provider_unavailable`.
- **Error mapping (to existing kinds):** `subscription_sharing_usage_limit_exceeded` (429) → `plan_limit`
  (run ends "stopped: plan limit", resumable); `subscription_sharing_usage_unavailable` and
  `subscription_sharing_user_unavailable` (503) → `provider_unavailable` (bounded retry);
  `subscription_sharing_user_not_eligible`, `subscription_sharing_invalid_user`, `chatpass_v2_*` → `auth` (stop,
  no OAuth loop); `subscription_sharing_unsupported_capability` → `bad_request` (no retry);
  `subscription_sharing_route_not_supported` → `config`; admission bodies `{"detail": …}` with 401/403/503 →
  `auth`/`auth`/`provider_unavailable`. The request ID is kept; the body text is redacted.
- **Token store:** outside the repository. Linux: `~/.config/bie/chatgpt/<client_id>.json`, folder 0700, file
  0600; Windows: `%LOCALAPPDATA%\bie\chatgpt\`, readable by Navin's user only. Written atomically (temporary
  file, flush, rename). The path comes from `BIE_CHATGPT_CREDENTIALS`; the token never goes into an environment
  variable, a child process, a URL, a log or a record.
- **Refresh:** before a call when `exp` is under five minutes away (or from `earliest_refresh_at`), under a file
  lock so two workers never race the rotating refresh token; the new access token, refresh token, scopes and
  expiry replace the old ones together. `invalid_grant`, `refresh_token_reused` and similar → stop with
  "sign in again" (kind `auth`).
- **Host ID:** one `urn:uuid:` per machine, generated once and kept beside the credentials; a copied file keeps
  the receiving machine's own host ID.
- **Cost:** rupees stay 0 (`billing: subscription`); the ledger keeps token counts and time; the cost guard's
  rules still apply (preflight, cap for the Gemini checker, stop kinds). Preflight for this route: credential file
  present with `chatgpt.tokens.use.direct`, `GET /v1/models` lists the chosen model, one tiny streamed call, the
  "47" picture call. Plan usage is reported as "see ChatGPT Settings → Usage" unless an endpoint is found.
- **Tests:** a fake transport that replays recorded SSE sequences (completed, usage limit mid-stream, incomplete,
  admission 401 with `detail`, cut stream) and a fake token store with a canary token; no change to the
  existing gateways or their tests.

## 5. Design of a one-time probe (text only, not written, not run)

**What:** one file, `siwc_probe.py`, Python standard library only, run **once** by Navin on his Windows laptop,
which has the browser that the 127.0.0.1 callback needs. It would be added in a later task, only after his yes.
It is a one-time exception to "never run things locally", which Navin must approve.

**What it does, in order:**
1. Creates a folder outside the repository (`%LOCALAPPDATA%\bie-siwc-probe\`), a host ID, and a loopback
   listener on `127.0.0.1:1455/auth/callback`; fresh `state`, `nonce` and PKCE.
2. Opens the browser at `https://auth.openai.com/api/accounts/authorize` with `client_id=dynamic_agent_client`,
   `agent_name_hint=BIE`, the host ID, the identity and plan scopes and `resource=https://api.openai.com/v1`.
3. Exchanges the code, checks the granted scopes include `chatgpt.tokens.use.direct`, verifies the ID token
   signature against OpenAI's published keys (RSA check written with the standard library), issuer, audience and
   nonce.
4. Runs five checks and prints only the step, PASS or FAIL, the HTTP status, the `error.code` and the request ID:
   list models; one tiny streamed call; one call with a JSON schema (does `text.format` work, and does the answer
   validate?); one call with a small built-in picture of "47"; one call shaped like a BIE page step (instructions
   plus a page image) to see time and token counts.
5. Revokes the refresh token and deletes the folder, unless Navin chooses to keep it for a later server copy.

**What Navin would click:** install Python from the Microsoft Store (if not already there) → double-click or run
one command → the browser opens → sign in to ChatGPT → choose his account/workspace → keep the name "BIE" →
allow **Use your ChatGPT plan** → Continue → close the browser tab when it says done → send Claude the printed
PASS/FAIL lines (they contain no tokens).

**Cost:** a few tiny calls from his plan; ₹0.

## 6. Security

- **Where the token lives:** only in the credential file described in section 4, outside the repository, readable
  by one user. Never in GitHub secrets, never in BIE's run folders, records, ledger, SUMMARY.json, annotations,
  `RUN_LOG.txt`, chat or tickets.
- **Redaction:** extend `bie/model_gateway/live/errors.redact` with JWT-shaped tokens (three base64url parts
  separated by dots) and any `Authorization: Bearer …` header; redact authorization URLs that carry
  `id_token_hint`. The client ID and host ID are identifiers, not secrets, but are kept out of public outputs anyway.
- **.gitignore (with the code task, not now):** `*siwc*.json`, `chatgpt-auth*.json`, `chatgpt-host.json`,
  `.config/bie/`.
- **Tests that would prove it:** run the fake route with a canary token and fail if the canary, a JWT-shaped string
  or the word `Bearer` appears in any output folder file, log or annotation; check the credential file mode is
  0600 on Linux; check no child process environment contains the token.
- **If anything leaks:** Navin disconnects BIE in ChatGPT Settings → Security and login → Sign in with ChatGPT
  ("If credentials are compromised, instruct the user to disconnect the app in ChatGPT Settings." · accounts and
  sessions).

## 7. Risks in plain words

- **Preview:** OpenAI calls the current rules "Preview behavior and limitations"; fields, errors or eligibility can
  change without BIE changing.
- **Suspension:** the terms say "We may suspend …" but the rest could not be read here. Navin uses the same
  ChatGPT account for his own work and coding. If a use were judged against the terms, the risk is not only
  BIE losing access; how far a suspension reaches is **unknown**.
- **Policy fit:** BIE as a commercial course factory on a rented server is the least clearly covered case
  (sections 1 and 2). Asking OpenAI through the interest form first is the safe order.
- **Usage size:** BIE is heavy. Task 039's measured maker use for Section 1 was about 13,000 output and 10,000 input
  tokens per page; a 300-page book would need millions of tokens per section. Pro has no 5-hour limit for apps,
  but weekly limits and per-app caps apply and their size is **not published**. The same pool is shared with
  Codex, so BIE could crowd out Navin's own coding.
- **How to measure cheaply:** note ChatGPT Settings → Usage before and after the probe's page-shaped call; with the
  Codex route, read `account/rateLimits/read` before and after one real page (already built into Task 044's
  preflight).
- **No silent fallback:** "ChatGPT plan usage errors stop inference. OpenAI does not silently switch the request to
  another billing path." BIE keeps the same rule: a stop, never a switch to a paid key or a fake.

## 8. Where this fits in the roadmap

No new phase and no change to Tasks 045–052. One line under Task 044 in ROADMAP: the Codex route stays primary;
SIWC is an optional later route after a one-time probe (needs Navin's yes) and an answer from OpenAI on where
tokens may live. If both come back positive, a small task after the 044 live test would build the
`chatgpt_oauth` route from section 4.

## What Navin decides

1. Nothing is needed for this report.
2. Optional: approve the one-time laptop probe (section 5) as an exception to "never run things locally".
3. Optional: fill in OpenAI's interest form (https://openai.com/form/sign-in-with-chatgpt-interest/) to ask whether
   BIE on his own rented server is allowed; Claude can draft the answers.
4. Still open from Task 044: yes or no to the Codex machine.
