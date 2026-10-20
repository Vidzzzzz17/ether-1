# Ether 1 — Multimodal Assistant Platform

Ether 1 is a multimodal assistant shell that connects a hosted Next.js workspace to model services running on the user's own computer. This repository contains a FastAPI local runtime, Next.js app, optional Supabase persistence, and modular model adapters.

## Architecture

- `web/`: Next.js App Router UI, Supabase Auth, chat history and editable Co-work Canvas.
- `api/`: FastAPI `/api/v1/chat`, auth validation, orchestration, and model adapters.
- Supabase: user accounts, Postgres persistence and private media storage.
- Model runtime: Ollama on the user's computer. The API's OpenAI-compatible text adapter points at Ollama; speech and image adapters can point at local services too.

Vercel hosts the web app. Do not deploy the local runtime as a public inference service: in local mode it has no user authentication and is intended to listen only on the user's own computer. The hosted browser UI can call that local runtime by setting `NEXT_PUBLIC_API_URL` to `http://127.0.0.1:8000` in its build environment; browsers may ask the user to allow local network access. Without Supabase, chat history is stored in that browser only. Supabase is optional and adds sign-in and cloud-saved history.

## 1. Supabase setup

Create a Supabase project. In SQL Editor, run `supabase/schema.sql`. Create a private Storage bucket named `chat-media`. Add the bucket policies in `supabase/storage-policies.sql`. Copy the project URL and publishable/anon key into the environment files below. Enable email/password auth in Supabase Authentication.

## 2. Local setup

Copy `web/.env.example` to `web/.env.local` and `api/.env.example` to `api/.env`. Install Ollama on the computer that will run Ether 1 and download `qwen2.5:7b` (about 4.7 GB in Ollama's library). Qwen2.5-7B-Instruct is Apache-2.0 licensed; users should review model and dependency licenses before redistributing weights. Set `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, and `LLM_MODEL=qwen2.5:7b`.

For a personal-only local run, set `AUTH_MODE=local` in `api/.env`. Keep the API bound to `127.0.0.1`; do not expose this mode to a network or the public internet. Set `CORS_ORIGINS` to the exact origin of the web UI (for local development, `http://localhost:3000`; for the hosted Ether 1 site, its Vercel domain). Set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` for the web build that should use the user's local runtime.

Run the API from `api/` with `python -m venv .venv`, activate it, install `pip install -e .`, then `uvicorn app.main:app --reload --port 8000`. In `web/`, run `npm install` and `npm run dev`. Open `http://localhost:3000`.

For local audio transcription, install the optional `audio` extra and configure `WHISPER_MODEL=base`. To understand uploaded images, point `LLM_BASE_URL` to a vision-capable model such as a Qwen-VL variant served through a compatible API. Image generation and TTS are HTTP adapters: configure their endpoint URLs to a compatible service. See `api/.env.example` for configuration. The TTS adapter expects a JSON response containing a browser-accessible `url`.

## 3. Deploy to Vercel

Import this directory as a Vercel project and set the root directory to `web`. Add all `NEXT_PUBLIC_*` Supabase variables and `NEXT_PUBLIC_API_URL` (the deployed API URL). Deploy `api/` as a second Vercel project rooted at this directory, or use a Vercel Services setup if available to your account. Configure the API environment variables from `api/.env.example`, set `CORS_ORIGINS` to the web deployment origin, and set the web `NEXT_PUBLIC_API_URL` to the API deployment URL. For a single Vercel project, the FastAPI entry point is `api/index.py`; adapt project routing to your Vercel project layout.

The hosted API deployment is only useful for inference if configured to reach a separately operated runtime. For the intended user-owned-computer setup, run the API locally instead. Audio transcription and image generation require their own local provider services; the text model is the only local provider configured by default. Do not send sensitive files to a hosted provider unless the user has explicitly chosen that provider.

## 4. API

`POST /api/v1/chat` accepts multipart form data (`message`, optional `file`, optional `intent`, optional JSON-string `history`). It returns `{ reply, artifacts, intent }`. The browser sends a Supabase access token as `Authorization: Bearer …`; the API validates it with Supabase Auth before processing. Attached files are stored in the private `chat-media` bucket under the user's folder before being sent to inference.

Artifact types currently rendered are `text`, `code`, `image`, `audio`, and `document`. Code and text are editable in the right-hand canvas. Generated media URLs are persisted as artifact metadata; use the private Supabase bucket for user media.

## Project tree

```text
multimodal-assistant/
├── README.md
├── api/
│   ├── app/{main.py,config.py,auth.py,schemas.py,orchestrator.py}
│   ├── app/handlers/{text.py,speech.py,image.py}
│   ├── index.py
│   ├── pyproject.toml
│   └── .env.example
├── supabase/{schema.sql,storage-policies.sql}
└── web/
    ├── app/{page.tsx,layout.tsx,globals.css,auth/page.tsx}
    ├── components/{assistant.tsx,auth-form.tsx}
    ├── lib/{supabase/{client.ts,server.ts},types.ts}
    ├── middleware.ts
    ├── package.json,tsconfig.json,next.config.ts,postcss.config.mjs
    └── .env.example
```

## Important operational notes

- The API authenticates every request; never put a Supabase service role key or model API key in `NEXT_PUBLIC_*` variables.
- Configure CORS narrowly to your real web origin.
- The demo persists conversations from the browser using RLS. The API does not use privileged database credentials.
- The image adapter expects an OpenAI-compatible image generation endpoint. The speech adapter expects Whisper-compatible transcription and a simple JSON TTS endpoint; adjust the adapter if your selected runtime differs.
- This is a service starter, not a complete production operations package. Load testing, abuse controls, billing, deletion/export flows, and data retention should be added before broad launch.

