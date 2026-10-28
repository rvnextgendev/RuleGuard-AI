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


## GitHub business-owner approval setup

Configure the environment for approval-gated pull requests at:

**[RuleGuard AI — GitHub Environment Settings](https://github.com/rvnextgendev/RuleGuard-AI/settings/environments)**

1. Open the link above and choose **New environment**, or open the existing `business-rule-exception` environment.
2. Name it **`business-rule-exception`** (exact match with `.github/workflows/rule-guard.yml`).
3. Under **Deployment protection rules**, enable **Required reviewers**.
4. Search for and **select a GitHub username or team from the dropdown**. Typing an email address alone does not select a reviewer.
5. For a quick single-account POC, leave **Prevent self-review** unchecked. For real governance, enable it and use a separate authorized business-owner account.
6. Save the environment's protection rules.
7. Configure branch protection/rulesets for `main` to require the **`merge-gate`** status check. Otherwise an approval job by itself does not guarantee merge blocking.

### Test the approval gate

- Make sure at least one baseline rule (for example `rules/approved/PAY-001.md`) is **committed to GitHub**, not just present in the local or Streamlit Cloud filesystem.
- On a feature branch, remove the payment amount validation from `samples/PaymentService.cs` and open a PR into `main`.
- In **Actions → RuleGuard Business Approval**, inspect the `detect`, `owner-approval`, and `merge-gate` jobs.
- If a recognized approved rule violation exists, `owner-approval` should wait for a GitHub environment reviewer. After a reviewer approves the deployment, `merge-gate` may pass if the other required checks succeed.
- If `owner-approval` is **skipped**, inspect the `detect` report; the current POC only enforces its predefined `PAY-001` through `PAY-004` conditions.

### Streamlit Cloud approval versus GitHub approval

These are different actions:

| Approval | What it does | GitHub impact |
| --- | --- | --- |
| **Rule approval in Streamlit** | Writes `rules/approved/*.md` inside the app's filesystem | **Does not automatically commit/sync** to GitHub |
| **Environment approval in GitHub** | Allows a gated workflow job to continue for a detected exception | Can satisfy the required `merge-gate` check |

**Current limitation:** Streamlit Community Cloud storage is ephemeral. An approved Markdown rule there may disappear on redeploy and will **not** become available to GitHub Actions unless the file is separately committed to the repository. Also, dynamically discovered AI rules are advisory until a validator is implemented for them. Future enhancements should synchronize approved rules using a properly authenticated GitHub App and validate newly approved AI rules in CI.

## Local debugging on Windows (VS Code + Docker)

### 1. Prepare the project

In Windows CMD:

```cmd
cd C:\Users\RajeshDas\RuleGuard-AI
git pull origin main
copy .env.example .env
notepad .env
```

If `.env` already exists, **do not overwrite it**; just open it with Notepad. Select either Ollama or Groq as documented above.

### 2. Run the Docker app and inspect logs

For Ollama **inside Docker**:

```cmd
docker compose --profile local-llm up -d --build
docker compose exec ollama ollama pull qwen2.5:3b
```

For Groq or an Ollama server **already running on Windows** (with the appropriate `OLLAMA_URL`):

```cmd
docker compose up -d --build
```

Then:

```cmd
docker compose ps
docker compose logs -f app
```

Open http://localhost:8501. Press Ctrl+C to stop following logs; this does not stop the container.

### 3. Step through Python with pdb

The Docker service mounts the repository at `/workspace`. To debug discovery:

```cmd
docker compose run --rm --no-deps -it app python -m pdb app/cli.py discover
```

At the `(Pdb)` prompt, use:

```text
b app/engine.py:12
l
n
s
p results
c
q
```

**Note:** Line numbers may change. Use `l` to inspect code and set the breakpoint at the relevant executable line. The command above tests **pattern-based discovery**. For AI discovery, the UI calls `app/discovery_ai.py:discover_ai()`, which invokes the selected LLM; inspect that function and `app/llm.py:model()` when troubleshooting.

To check staged changes:

```cmd
git diff --cached
docker compose run --rm --no-deps -T app python app/cli.py review
```

### 4. VS Code breakpoints (local Python)

Install Python 3.11+ and the VS Code Python extension. From the project folder, create a virtual environment:

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
code .
```

If Python 3.11 is not installed, use your installed supported Python version and adjust the `py` command.

Create `.vscode/launch.json` with:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "RuleGuard Streamlit",
      "type": "debugpy",
      "request": "launch",
      "module": "streamlit",
      "args": ["run", "app/ui.py", "--server.port=8502"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": true
    },
    {
      "name": "RuleGuard Pattern Discovery",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/app/cli.py",
      "args": ["discover"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

Select the `.venv` interpreter in VS Code, set breakpoints in `app/ui.py`, `app/discovery_ai.py`, `app/engine.py`, or `app/llm.py`, and press **F5**. Open http://localhost:8502 for the debugger-run UI. Stop the Docker app first if you want to avoid confusion between two instances.

If debugging against Ollama running **on Windows**, set `OLLAMA_URL=http://localhost:11434` in your local `.env`. If the debugger runs outside Docker, `http://ollama:11434` will not resolve.

### 5. Reproduce a rule violation locally

1. In Streamlit, run **Discover → Pattern-based baseline**, then approve `PAY-001` in **Manage Rules**.
2. Create a feature branch: `git switch -c test/payment-validation`.
3. Remove `if (amount <= 0) return false;` from `samples/PaymentService.cs`.
4. Stage the change: `git add samples/PaymentService.cs`.
5. Run `docker compose run --rm --no-deps -T app python app/cli.py review` and inspect the `PAY-001` warning.
6. Restore the sample after testing, or commit only to your test branch. Never push the intentional violation to `main`.

### 6. Troubleshooting checklist

| Symptom | Check |
| --- | --- |
| Streamlit doesn't open | `docker compose ps`, `docker compose logs app`, port 8501 |
| Groq returns 401 or 429 | API key, model access, rate limits, quota |
| Ollama connection refused | Container versus Windows-host `OLLAMA_URL`, model availability |
| AI discovery returns no drafts | `app/discovery_ai.py`, LLM JSON output, exact evidence matching |
| Rule file disappears in cloud | Streamlit Cloud filesystem is ephemeral |
| GitHub approval skipped | Approved Markdown committed to repo; `detect` job report |
| Pre-commit hook doesn't run | `python install-hook.py`, Git hooks path, Docker Desktop running |

**Security:** Do not print or commit your `.env` or API keys. The AI discovery feature is experimental; generated Markdown must be reviewed before approval, and AI-discovered rules are not yet enforced by the baseline CI validator.

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
