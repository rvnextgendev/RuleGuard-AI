# RuleGuard AI — Payment Business Rule Guard POC

Docker-based demonstration of payment business-rule discovery, human approval, staged-change review, LangGraph advisory explanations, and GitHub PR checks.

## Start

```bash
cp .env.example .env
# Set GROQ_API_KEY in .env for Groq
docker compose up -d --build
```
Open http://localhost:8501. For local Ollama set `LLM_PROVIDER=ollama`, then run `docker compose --profile local-llm up -d --build` and `docker compose exec ollama ollama pull qwen2.5:3b`.

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
