# Ubuntu Public Deployment

This project can be deployed on a single Ubuntu host with:

- `Caddy` as the public reverse proxy
- `systemd` managing the Python backend
- the backend serving `frontend/dist/`

## Runtime layout

Recommended server path:

```text
/opt/tcm-classic-rag
```

Expected runtime files:

- source code cloned from GitHub
- `.env`
- `artifacts/zjshl_v1.db`
- `artifacts/dense_chunks.faiss`
- `artifacts/dense_main_passages.faiss`
- `artifacts/dense_chunks_meta.json`
- `artifacts/dense_main_passages_meta.json`
- `artifacts/hf_cache/` (recommended to pre-sync if outbound model download is unstable)

## Why source push is not enough

The repository intentionally does not track the SQLite runtime database, FAISS indexes, or Hugging Face cache.
After cloning on the server, you must either:

1. sync those runtime assets from a prepared local environment, or
2. rebuild the database and indexes on the server and let the host download model weights at first startup.

For a small cloud host, pre-syncing runtime assets is the safer path.

## Service config

Install the provided unit file:

```bash
cp deploy/systemd/tcm-classic-rag.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now tcm-classic-rag
```

## Reverse proxy

Without a domain, use the provided IPv4 Caddy config:

```bash
cp deploy/caddy/Caddyfile.ipv4 /etc/caddy/Caddyfile
systemctl reload caddy
```

Once a domain is available and DNS points to the host, replace `:80` with the domain name so Caddy can issue HTTPS certificates automatically.

## Environment file

Minimum `.env` for an offline-safe first boot:

```dotenv
TCM_RAG_LLM_ENABLED=false
```

If LLM should be enabled later, add:

```dotenv
TCM_RAG_LLM_API_KEY=...
TCM_RAG_LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
TCM_RAG_LLM_MODEL=qwen-plus
TCM_RAG_LLM_ENABLED=true
```
