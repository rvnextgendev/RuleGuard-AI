# RuleGuard AI — Payment Business Rule Guard POC

Docker-based demonstration of payment business-rule discovery, human approval, staged-change review, LangGraph advisory explanations, and GitHub PR checks.

## Start

```bash
cp .env.example .env
# Set GROQ_API_KEY in .env for Groq
docker compose up -d --build
```
Open http://localhost:8501. For local Ollama set `LLM_PROVIDER=ollama`, then run `docker compose --profile local-llm up -d --build` and `docker compose exec ollama ollama pull qwen2.5:3b`.


## LLM provider setup: Ollama and Groq

RuleGuard AI uses `LLM_PROVIDER` to choose an LLM. The deterministic rule checks do not require an LLM; the **Ask AI** explanation feature does.

### A. First-time setup on Windows (Command Prompt)

Run these commands from the cloned repository:

```cmd
cd RuleGuard-AI
copy .env.example .env
notepad .env
```

**Do not use `cp` in Windows CMD.** Edit `.env` with one of the configurations below. Never put real API keys in `.env.example` or commit `.env`.

### B. Local Ollama running inside Docker (no cloud key)

In `.env`:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
```

Start both the Streamlit app and the Ollama service:

```cmd
docker compose --profile local-llm up -d --build
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama list
docker compose ps
```

Visit **http://localhost:8501** and open **Developer Review → Ask AI**. The app connects to the Ollama container using `http://ollama:11434`. The first model download can take time.

### C. Ollama already installed on Windows (reuse your existing Ollama)

If Ollama is already running on Windows, do **not** start the Docker Ollama profile. Pull the model on the host:

```cmd
ollama pull qwen2.5:3b
ollama list
```

Set in `.env`:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
```

In `compose.yaml`, change only the app service's `OLLAMA_URL` environment entry from:

```yaml
OLLAMA_URL: http://ollama:11434
```

to:

```yaml
OLLAMA_URL: http://host.docker.internal:11434
```

Then run:

```cmd
docker compose up -d --build
```

If connection is refused, verify Ollama is running and accessible to Docker Desktop. Do not expose Ollama publicly without appropriate security.

### D. Groq Cloud (no Ollama container needed)

Get an API key from https://console.groq.com/keys and set in `.env`:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=replace_with_your_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Run:

```cmd
docker compose up -d --build
docker compose ps
```

Open **http://localhost:8501 → Developer Review → Ask AI**. Groq requires internet access and sufficient API quota. The model identifier must be supported by your Groq account.

### E. Switch providers later

Change `LLM_PROVIDER` and relevant variables in `.env`, then recreate the app:

```cmd
docker compose up -d --force-recreate app
```

| Provider | Environment values | Deployment |
| --- | --- | --- |
| Local Ollama | `LLM_PROVIDER=ollama`, `OLLAMA_MODEL` | Docker or Windows host |
| Groq | `LLM_PROVIDER=groq`, `GROQ_API_KEY`, `GROQ_MODEL` | Docker or Streamlit Cloud |
| OpenAI | `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_MODEL` | Cloud |
| Compatible API | `LLM_PROVIDER=compatible`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | Depends on provider |

Non-OpenAI-compatible cloud APIs require a separate adapter in `app/llm.py`.

### F. Deploy the Streamlit UI with Groq

Streamlit Community Cloud cannot directly reach Ollama running on your private laptop. For a hosted demo, deploy from repository `rvnextgendev/RuleGuard-AI`, branch `main`, entrypoint `app/ui.py`, and configure secrets in Streamlit's **Advanced settings → Secrets**:

```toml
LLM_PROVIDER = "groq"
GROQ_API_KEY = "replace_with_your_key"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

The current `app/llm.py` reads **environment variables** with `os.getenv`. Streamlit secrets may need to be explicitly mapped to environment variables in the app, depending on deployment behavior. Verify this before relying on the hosted demo. Also, locally written Markdown approvals are not persistent on Community Cloud; use committed approved rules or persistent storage for production.

### G. Debugging the LLM connection

```cmd
docker compose ps
docker compose logs --tail=100 app
docker compose logs --tail=100 ollama
docker compose exec ollama ollama list
```

- **Missing Groq key:** Check `.env` and recreate the app. Never paste secrets into logs or issues.
- **Groq 429/rate limit:** Check API quotas and retry later or select another available model.
- **Ollama connection refused:** Verify the model server is running and that `OLLAMA_URL` matches container versus Windows-host mode.
- **Model not found:** Pull the Ollama model or choose a supported Groq model.
- **No AI response:** Confirm `LLM_PROVIDER`, app logs, and connectivity. Deterministic discovery and validation can still work without AI.

## Demo

1. Discover rules from `samples/PaymentService.cs` and `samples/CapturePayment.sql` using Streamlit.
2. Approve each draft rule; commit generated `rules/approved/*.md` to protect it in CI.
3. Alter a sample condition, stage the edit with `git add`, and open Developer Review.
4. Install a local hook with `python install-hook.py` and try committing. It warns rather than blocks by default.
5. Open a GitHub PR. The Action checks approved rules and requests an environment approval when it detects a violation. Configure a `business-rule-exception` environment with required reviewers and protect `main` using the `merge-gate` required status check.

## Debugging

```bash
docker compose ps
docker compose logs --tail=100 app
docker compose run --rm --no-deps app python app/cli.py discover
docker compose run --rm --no-deps app python -m pdb app/cli.py discover
python -m compileall app
git diff --cached
git diff --cached --name-only
```
Use breakpoints in `app/engine.py` (`discover`, `review`), `app/llm.py` (`model`, `explain`) and `app/approval.py` (`findings`). For Groq errors verify your API key and quota; for Ollama check `docker compose logs ollama` and installed model. For CI debug open GitHub Actions run logs; review `ruleguard-report` artifact and environment approval status.

## Limitations

This is a narrow payment-pattern demonstration, not generic semantic rule extraction. LLM explanations are advisory, not trusted validation. Environment approvals are separate from Streamlit rule approvals. The current PR analyzer reads checkout source files, so validate the comparison and approval workflow for your repo before relying on it for critical protection. Docker and live API end-to-end testing remains pending. Never commit API keys.
