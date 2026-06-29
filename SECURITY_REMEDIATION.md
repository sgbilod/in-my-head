# Security Remediation & v0.1.0 Cleanup Runbook
_Prepared 2026-06-29. Run the steps in order. 🔴 = you must do it; 🟢 = Claude can run it for you._

> **Why this order:** rotating keys must come first (purging history does **not** un-leak an
> already-pushed key). Then commit the legitimate work + cleanup, rewrite history to erase the
> leaked artifacts, force-push, rename the repo, and tag. Do not skip Step 0.

---

## 🔴 STEP 0 — Rotate the leaked keys (DO THIS FIRST, at the provider consoles)
The committed `backups/backup_20251014_101721.zip` (on `origin/main`) and
`in-my-head-backup-20251005-124618/` both contain a `.env` with **real** keys. Treat all three as compromised:
- **Anthropic** (`sk-ant-…`): https://console.anthropic.com/settings/keys → revoke + create new
- **OpenAI** (`sk-proj-…`): https://platform.openai.com/api-keys → revoke + create new
- **Google** (`AIzaSy…`): https://aistudio.google.com/app/apikey → delete + create new

Put the new keys only in `services/*/.env.local` (gitignored), never in tracked files.

## 🔴 STEP 1 — Delete the loose plaintext key file
```
del "C:\Users\sgbil\Claude_Desktop\Projects\In-My-Head\In My Head-API.txt"
```

---

## 🟢 STEP 2 — Repo cleanup (file operations, on a clean working tree)
Run from the repo root `C:\Users\sgbil\In My Head` (Git Bash):
```bash
# 2a. Archive the 57 loose root status/report markdown files (keep the essentials)
mkdir -p docs/archive
git ls-files '*.md' ':(top)' | grep -vE '^(README|LICENSE|CLAUDE|ACTION_PLAN|SECURITY_REMEDIATION)\.md$' \
  | grep -E '^[^/]+\.md$' | while read f; do git mv "$f" "docs/archive/" 2>/dev/null || mv "$f" docs/archive/; done

# 2b. Remove root-level debug/fix/check one-off scripts (review the list first!)
git rm -f --ignore-unmatch fix_*.py check_*.py debug_*.py 2>/dev/null
git rm -f --ignore-unmatch scripts/fix_*.py services/ai-engine/fix_*.py services/ai-engine/check_*.py 2>/dev/null

# 2c. Delete the empty Electron scaffold and the committed venv (gitignore already covers venv)
rm -rf frontend/desktop-app
git rm -r --cached --ignore-unmatch venv 2>/dev/null; rm -rf venv

# 2d. Stop tracking the leaked artifacts (gitignore already lists backups/)
git rm -r --cached --ignore-unmatch backups/backup_20251014_101721.zip "in-my-head-backup-20251005-124618" 2>/dev/null
rm -f backups/backup_20251014_101721.zip
rm -rf "in-my-head-backup-20251005-124618"
```

## 🟢 STEP 3 — Commit this session's work + the cleanup
```bash
# Safety: confirm NO secrets are about to be committed (should print nothing)
git add -A
git diff --cached | grep -iE 'sk-ant-|sk-proj-|AIzaSy|JWT_SECRET=.+|SECRET_KEY=.+' && echo '!!! SECRET DETECTED - STOP' || echo 'clean'

git commit -m "v0.1.0 foundation: no-OpenAI, DB source of truth, real conversations, dashboard; cut scaffolds; repo cleanup"
```

---

## 🔴/🟢 STEP 4 — Purge the leaked artifacts from ALL git history
`git-filter-repo` rewrites every commit. **This is irreversible** — make a safety mirror first.
```bash
# Safety backup of the current repo (outside the tree)
git clone --mirror . ../in-my-head-PREPURGE-backup.git

# Ensure the tool is installed
git filter-repo --version || pip install git-filter-repo

# Remove the leaked paths from the entire history
git filter-repo --force \
  --path "backups/backup_20251014_101721.zip" \
  --path "in-my-head-backup-20251005-124618/" \
  --invert-paths

# (Optional, stronger) also strip any historical .env copies:
# git filter-repo --force --path-glob '*/.env' --path .env --invert-paths
```
> `git-filter-repo` removes the `origin` remote by design (safety). Re-add it in Step 6.

## 🔴 STEP 5 — Rename the GitHub repo `sgbilod/4` → `in-my-head`
Either with the CLI:
```bash
gh repo rename in-my-head -R sgbilod/4
```
…or in the browser: GitHub → repo **Settings** → **Rename**.

## 🟢 STEP 6 — Re-point origin and force-push the rewritten history
```bash
git remote add origin https://github.com/sgbilod/in-my-head.git
git push origin --force --all
git push origin --force --tags
```
Then update the README badge URLs (replace the `[USERNAME]`/`sgbilod/4` placeholders with `sgbilod/in-my-head`).

## 🟢 STEP 7 — Rotate the committed dev secrets in config
The compose/.env dev values (`SECRET_KEY`, `JWT_SECRET`, `dev_password_123`, `minioadmin_CHANGE_ME`) were exposed. Regenerate for any non-local use:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48)); print('JWT_SECRET=' + secrets.token_urlsafe(48))"
```
Put the new values in `.env.local` (gitignored).

## 🟢 STEP 8 — Tag v0.1.0
```bash
git tag -a v0.1.0 -m "In My Head v0.1.0 — local-first RAG knowledge base (document ingest, hybrid search, persistent Ollama chat)"
git push origin v0.1.0
```

---

### After this runbook
- All leaked keys rotated and erased from history; repo renamed; clean v0.1.0 tagged.
- The 90+ stale dependabot branches can be pruned separately (low priority).
- Revoke/delete the safety mirror `../in-my-head-PREPURGE-backup.git` once you've confirmed the push is good and nothing was lost.
