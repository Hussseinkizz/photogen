# Photogen

## What

A local app that turns a photo into an AI edit and keeps the original and the result.

## Inspiration (why)

You want a better social profile pic: more professional, or cartoonized, or a specific look. You already have a photo. The app is that loop: upload, describe the look, get an image back, refine.

## Key components and architecture

Cookie auth, profile (HTTP and the AI tool share `get_profile`), `/photos`, public `/uploads` and `/generated`, frontend-only presets, then a two-step OpenRouter call (tool, then image). The user only ever sees the image.

```
photogen/
  backend/
    app/main.py              # FastAPI, CORS, static mounts
    app/auth.py              # username/password, HTTP-only session cookie
    app/profile.py           # get_profile - HTTP + tool
    app/photos.py            # source image: latest generated, else original
    app/storage.py           # disk files
    app/ai/                  # edit_image
    app/ai/tools/            # get_profile tool loop
    app/routes/              # /api/auth, /api/profile, /api/photos
    .env.example             # each model: name, key, url
  frontend/
    src/presets.ts           # prompt presets (frontend only)
    src/lib/api.ts           # credentials: "include"
```

## Phases overview

1. Backend - cookie auth, profile, photos, OpenRouter tool then image.
2. Frontend - register preferences, presets, gallery.
3. Integration - cookie + CORS, generate and refine in the browser.

## Each phase checklist

**Phase 1 - Backend**

```bash
cd backend
cp .env.example .env
uv sync
uv run poe dev
```

**Phase 2 - Frontend**

```bash
cd frontend
npm install
npm run dev
```

Login/register UI (preferences on register), presets only change the prompt, gallery shows original and generated.

**Phase 3 - Integration**

Both running. Vite proxies `/api`, `/uploads`, `/generated`. Cookie + CORS. Register prefs → profile matches the form → generate → gallery shows both → public image URLs load → refine → logout.

## Tech stack and prerequisites

Python 3.11+, Node, uv, OpenRouter key.

FastAPI, Pydantic, SQLAlchemy, SQLite, OpenRouter Python SDK, poethepoet.

Vite, React, TypeScript, Tailwind, shadcn/ui, TanStack Query.

## Terms and glossary

- **Session cookie** - HTTP-only `session` cookie. JavaScript cannot read it.
- **Profile** - username, favorite colors, hobbies, notes. Same data for `GET /api/profile` and the `get_profile` tool.
- **Tool calling** - the chat model calls `get_profile`, then the image model runs.
- **Original** - the uploaded photo at `/uploads`.
- **Generated** - each AI result at `/generated`.
- **Parent photo** - a prior photo used as the source (`parent_id`).
- **Prompt preset** - a frontend-only prompt string. The API never sees a preset id.

## References

- [uv](https://docs.astral.sh/uv/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [OpenRouter Python SDK](https://github.com/OpenRouterTeam/python-sdk)
- [OpenRouter image API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [OpenRouter tool calling](https://openrouter.ai/docs/guides/features/tool-calling)
- [Vite](https://vite.dev/)
- [shadcn/ui](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [poethepoet](https://poethepoet.github.io/poethepoet/)
