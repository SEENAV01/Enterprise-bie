# BIE — Option A: Free Render Test

This package is prepared for a temporary/free Render Web Service test.

## What Render will do

1. Build the included Dockerfile.
2. Start `main.py` using Render's `PORT` environment variable.
3. Expose the service at an `onrender.com` HTTPS URL.
4. Keep `OPENAI_API_KEY` as a runtime secret.
5. Use `/health` as the deployment health check.

## Render settings

The included `render.yaml` already defines:

- Docker runtime
- Free web-service plan
- `/health` health check
- `OPENAI_API_KEY` as a secret (`sync: false`)
- `gpt-5.6-luna` for the BIE provider and Agent SDK

## Important free-tier limitation

The free Render web service has 512 MB RAM, can spin down after 15 minutes without inbound traffic, and has an ephemeral filesystem. Do **not** use it yet for a full 500-page production run. Use it first for `/health`, Agent SDK startup, and a small PDF/chapter validation.

## Deployment

1. Create a GitHub repository and upload the contents of this directory to its repository root.
2. In Render: New → Web Service.
3. Connect that GitHub repository.
4. Select the Free plan and Docker runtime if Render asks.
5. Set `OPENAI_API_KEY` in Environment/Secrets. Never commit the key.
6. Deploy.
7. Confirm `https://<your-service>.onrender.com/health` returns HTTP 200.
8. Open the root URL to use the BIE web UI.

## Test order

First test:

`GET /health`

Second test:

`GET /v1/agent/schema`

Third test:

`POST /v1/agent/run`

Fourth test:

Upload a small PDF through the web UI or `POST /v1/jobs`.

Only after those pass should we run Indian Polity.
