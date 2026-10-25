# BIE Codex machine (Task 044)

GPT through Navin's ChatGPT Pro plan is BIE's maker; Gemini 4 Argon (AICredits) is the checker. The maker
runs with OpenAI's own Codex CLI (`codex exec`) on one small private machine that Navin owns. This folder sets
that machine up. Nothing here is bought or created by Claude; Navin says yes first.

## Why a private machine (decided 22 October 2026)

OpenAI's rules (learn.chatgpt.com/docs/non-interactive-mode, read 22 Oct 2026): ChatGPT sign-in for automation
is for trusted private machines and "Do not use this workflow for public or open-source repositories"; the auth
file `~/.codex/auth.json` is treated like a password. This repository is public, so its GitHub Actions never
sign in to ChatGPT. Navin's laptop is never used.

| Option | Verdict |
| --- | --- |
| Codex cloud (OpenAI-hosted, in the ChatGPT plan) | Possible only as a slow hand-off: the model works as an agent inside a cloud task, not as a call BIE can make. A task starts from the ChatGPT app, an `@codex` comment on GitHub, or `codex cloud exec` (which itself needs a signed-in machine). Results come back as a diff or a pull request; every remake round is a new task taking minutes; there is no enforced output schema (`--output-schema` is a `codex exec` feature); whether the agent really looks at page images cannot be checked; the agent can edit repository files, so its outputs would need extra guarding; cloud tasks use the same 5-hour plan window as local calls and use it faster. Not reliable or automatic enough for BIE's maker loop. |
| **Private machine with `codex exec`** (chosen) | One call per maker step, the JSON schema enforced by Codex (`--output-schema`), page images attached (`--image`), token usage per call (`--json`), plan usage readable before and after a run. Same section runner, same records, same cost guard as every other route. |
| Navin's JioPC (Ubuntu cloud PC) | Not suitable: it shuts down 15 minutes after disconnect, and no reliable way around that was found. |

## Machine options (prices read 22 Oct 2026; ₹94.59 per dollar; Indian billing adds 18% GST)

| Option | Size | Price | About ₹ per month with GST | Notes |
| --- | --- | --- | --- | --- |
| **AWS Lightsail, Mumbai** (recommended) | 2 GB RAM, 2 vCPU, 60 GB SSD, 1.5 TB transfer | $12 / month | **₹1,340** | Console and browser terminal work on a tablet; a "launch script" box runs `setup.sh` on first boot; billed in rupees by AWS India |
| AWS Lightsail, Mumbai (budget) | 1 GB RAM, 2 vCPU, 40 GB SSD | $7 / month | ₹780 | Enough with the 2 GB swap file `setup.sh` adds; slower on big PDFs |
| DigitalOcean, Bangalore | 2 GB RAM, 1 vCPU, 50 GB SSD | $12 / month | ₹1,340 | Similar; 1 vCPU |
| Hetzner (Germany, Finland, Singapore or USA) | cost-optimised plans from €5.99 / month | about ₹650–700 | No India location; prices rose twice in 2026 |
| Oracle Cloud Always Free | Ampere A1 | ₹0 | Not recommended: Oracle reclaims instances that stay mostly idle for 7 days, and this machine idles between books |

At 4–5 books a day the recommended machine costs about ₹10 per book, inside the ₹50–300 per book target. The
ChatGPT Pro plan itself is Navin's existing subscription.

## What runs on the machine

- `setup.sh` (no secrets): Python, git, Node, Codex CLI 0.162.1, a 2 GB swap file, the repository at
  `/var/lib/bie/repo`, a Python environment, the `bie` user and a systemd timer.
- Checker keys (25 October 2026): besides the AICredits key, Navin added his free Google AI Studio key as
  `GEMINI_API_KEY` to `/etc/bie/bie.env` (sample content only, never student data). With both keys the direct key
  is the default Google route; jobs for it carry `"routes": "google=direct", "models": "google=gemini-3.8-flash"`
  (the free tier answers only that model; `gemini-4-argon` gives 429, `gemini-3.1-pro` 404). Google bills the free
  tier ₹0; the cost guard still prices each call at the model's list price as a safe estimate.
  `tools/codex_vm.py status` shows which keys are present and the default route, never a key.
- `bie-setup` (Navin, once): the Gemini key into `/etc/bie/bie.env` (only on this machine), a GitHub deploy key
  so the machine can publish results, and `codex login --device-auth` (a link and a code, no browser needed on
  the machine). The Codex auth file stays in `/var/lib/bie/codex` (mode 700).
- `bie-codex-poll.timer` → `tools/codex_vm.py poll` every 2 minutes: jobs are `jobs/<id>.json` on the
  `codex-jobs` branch (Claude writes them through GitHub); each job is checked against a fixed list and runs
  `tools/run_brain.py` from `main` without a shell; the run folder goes to `blindtest-results`
  (`runs/vm-<id>-brain-<section>/`) and `jobs/<id>.result.json` reports the outcome.
- Security notes for Navin's approval: the deploy key can write to the whole repository (GitHub deploy keys
  cannot be limited to one branch); the runner itself pushes only to `blindtest-results` and `codex-jobs`.
  Branch protection for `main` comes with Phase 4. If the machine is ever lost: delete the deploy key on GitHub,
  sign out of Codex in ChatGPT settings, and rotate the Gemini key.

## Navin ke steps (ek baar, tablet se, lagbhag 15 minute)

1. **AWS Lightsail** kholiye (lightsail.aws.amazon.com) → *Create instance* → Region **Mumbai** → *Linux/Unix* →
   **Ubuntu 24.04 LTS** → *Add launch script* mein yeh ek line daaliye:
   `curl -fsSL https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/main/deployment/codex-vm/setup.sh | bash`
   → plan **$12** → naam `bie-codex` → *Create instance*. 5–10 minute ruko.
2. Instance par **Connect using SSH** dabaiye (browser mein terminal khulega) aur likhiye: `sudo bie-setup`
   - Gemini key paste kijiye (screen par nahi dikhegi).
   - Ek GitHub link aur ek lambi line aayegi: link kholiye, line paste kijiye, "Allow write access" tick, *Add key*.
   - Ek aur link aur code aayega: link kholiye, ChatGPT se login, code daaliye.
3. Bas. Claude ko bata dijiye "machine ready". Aage ke saare kaam Claude karega.
