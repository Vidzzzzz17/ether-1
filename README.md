# Multimodal Assistant Starter

FastAPI + Next.js starter for authenticated chat with editable text/code artefacts and pluggable speech, image, and language models.

## Architecture

- `web/`: Next.js App Router UI, Supabase Auth, chat history and editable Co-work Canvas.
- `api/`: FastAPI `/api/v1/chat`, auth validation, orchestration, and model adapters.
- Supabase: user accounts, Postgres persistence and private media storage.
- Model runtime: local Ollama for development, or any OpenAI-compatible endpoint for deployed inference. Speech and image services are configured independently.

Vercel hosts the web app and can run the FastAPI Python function. It does not provide free GPU inference for open model weights. Point the adapters at a separately hosted model runtime for deployment. The starter saves chat turns and artefact JSON; media uploads use Supabase Storage.

## 1. Supabase setup

Create a Supabase project. In SQL Editor, run `supabase/schema.sql`. Create a private Storage bucket named `chat-media`. Add the bucket policies in `supabase/storage-policies.sql`. Copy the project URL and publishable/anon key into the environment files below. Enable email/password auth in Supabase Authentication.

## 2. Local setup

Copy `web/.env.example` to `web/.env.local` and `api/.env.example` to `api/.env`. For a local LLM, install Ollama and pull a model such as `qwen2.5:7b`; set `LLM_BASE_URL=http://localhost:11434/v1` and `LLM_API_KEY=ollama`. Set `LLM_MODEL` to the pulled model name.

Run the API from `api/` with `python -m venv .venv`, activate it, install `pip install -e .`, then `uvicorn app.main:app --reload --port 8000`. In `web/`, run `npm install` and `npm run dev`. Open `http://localhost:3000`.

For local audio transcription, install the optional `audio` extra and configure `WHISPER_MODEL=base`. To understand uploaded images, point `LLM_BASE_URL` to a vision-capable model such as a Qwen-VL variant served through a compatible API. Image generation and TTS are HTTP adapters: configure their endpoint URLs to a compatible service. See `api/.env.example` for configuration. The TTS adapter expects a JSON response containing a browser-accessible `url`.

## 3. Deploy to Vercel

Import this directory as a Vercel project and set the root directory to `web`. Add all `NEXT_PUBLIC_*` Supabase variables and `NEXT_PUBLIC_API_URL` (the deployed API URL). Deploy `api/` as a second Vercel project rooted at this directory, or use a Vercel Services setup if available to your account. Configure the API environment variables from `api/.env.example`, set `CORS_ORIGINS` to the web deployment origin, and set the web `NEXT_PUBLIC_API_URL` to the API deployment URL. For a single Vercel project, the FastAPI entry point is `api/index.py`; adapt project routing to your Vercel project layout.

For production, run inference on a GPU-capable host or a managed endpoint. Keep all model credentials server-side. Add rate limits, upload quotas, observability, and a retention policy before opening the service to public traffic.

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

