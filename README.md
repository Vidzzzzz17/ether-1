# Ether 1 — Kernel's local model pipeline

**Substrate** is the organization. **Kernel** is its assistant product. **Ether 1** is the model experience Kernel offers: a local-first orchestrated system that routes work to specialist open-source models and combines their results. Ether 1 is not a claim that several models have been merged into one set of weights.

## Architecture

- `web/`: Next.js chat, history, and editable Co-work Canvas.
- `api/`: FastAPI local runtime. It plans tasks with a router model, sends them to specialist roles, and synthesizes a final answer.
- Ollama-compatible runtime: hosts local text, code, vision, router, and synthesis models on each user's computer.
- Optional local modality adapters: faster-whisper for transcription; an HTTP speech service for TTS; an OpenAI-compatible image endpoint for image generation.
- Vercel hosts the web interface. Inference is intended to run on the user's computer.

The first pipeline includes text, code, image understanding and generation, and speech input/output. The user selects a task mode when useful (such as Image); Ether 1 selects model roles automatically. The route trace on each answer reports the roles used.

## Model roles

The default role lineup is configurable in `api/.env`:

| Role | Default | Work |
| --- | --- | --- |
| Router | `qwen2.5:3b` | Selects specialist steps for a prompt |
| Text | `qwen2.5:7b` | General writing and reasoning |
| Code | `qwen2.5-coder:7b` | Programming and code artefacts |
| Vision | `qwen2.5vl:7b` | Interprets attached images |
| Combiner | `qwen2.5:7b` | Combines specialist results into the user-facing response |
| Image generation | `FLUX.1-schnell` | Image-generation service role; configure its endpoint separately |
| Speech recognition | faster-whisper `base` | Transcribes local audio |
| Speech synthesis | `Kokoro` | Speech service role; configure its endpoint separately |

These are replaceable defaults, not a fixed or fused Ether 1 model. The runtime currently calls text/vision/code/router roles through Ollama's OpenAI-compatible chat endpoint. Image generation and speech synthesis need compatible local HTTP services configured below. Whisper can run inside the API process.

## Run locally

1. Install Ollama and download the default language models on the computer that will run Ether 1:

```sh
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5vl:7b
```

2. Copy `api/.env.example` to `api/.env`. For a personal local session, set `AUTH_MODE=local`. Keep the API bound to `127.0.0.1` and set `CORS_ORIGINS` to the exact UI origin.

3. Start the API:

```sh
cd api
python -m venv .venv
# Activate the virtual environment, then:
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Start the web app in another terminal:

```sh
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. With Supabase unconfigured, conversations stay in that browser's local storage. Supabase sign-in and cloud history are optional; see `supabase/schema.sql` if you choose to configure them.

## Modality services

- **Speech recognition:** install the API's `audio` extra and set `WHISPER_MODEL=base` or `small` to run faster-whisper locally. Alternatively configure `WHISPER_API_URL` for a local Whisper-compatible transcription service.
- **Speech synthesis:** configure `TTS_API_URL` for a local service that accepts the submitted text and returns JSON containing a browser-accessible `url` to audio. Set `TTS_MODEL` to the model/service name for the route trace.
- **Image generation:** configure `IMAGE_API_URL` for a local OpenAI-compatible image endpoint accepting `prompt`, `n`, and `size`, and returning `data[0].url` or `data[0].b64_json`. Set `IMAGE_MODEL` to the model/service name. FLUX.1-schnell is a candidate model, but serving it locally requires a compatible runtime and suitable hardware.

These adapter settings point to services the user runs locally; the repo does not download or install large model weights automatically.

## Vercel

Import the repository as a Vercel project with root directory `web`. Vercel serves the UI only. Each user runs the FastAPI runtime and models on their own computer; `NEXT_PUBLIC_API_URL` must point to that user's local API, typically `http://127.0.0.1:8000`. Hosted browsers may restrict requests to local-network addresses; deployment behavior depends on browser permissions and network-access policies. Do not deploy `AUTH_MODE=local` on a public API.

## API contract

`POST /api/v1/chat` accepts multipart form data: `message`, optional `file`, optional `intent` (`text`, `image`, or `audio`), and optional JSON `history`. The response contains `reply`, `artifacts`, `intent`, and `route`. The UI renders code, documents, images, and audio in the editable side canvas. `GET /api/health` reports local API availability.

## Scope and next steps

Ether 1 currently orchestrates existing specialist models; it does not train, fine-tune, or merge their weights. The router uses a constrained specialist list and falls back to basic intent rules if the local router is unavailable. Production evolution should add streaming progress, per-role health checks, cancellation/timeouts, resource-aware model loading, and native adapters for popular local image and TTS runtimes.

