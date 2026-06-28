#!/usr/bin/env bash
# deploy.sh — one-shot deploy to GitHub + Render
# Run this once from Terminal in the project folder:
#   cd "/Users/georgejacobplamoottil/Documents/Claude/Projects/Practice/Source questions"
#   bash deploy.sh

set -e
REPO_NAME="p3-maths-practice"

echo ""
echo "=== P3 Maths Practice — Deploy Script ==="
echo ""

# ── 1. Clean up any stale git state ──────────────────────────────────────
echo "▶ Initialising git repo..."
rm -f .git/index.lock 2>/dev/null || true
git init -b main
git config user.email "gpjacob@gmail.com"
git config user.name "George Jacob"

# ── 2. Ensure data/ directory exists (Render disk mount point) ───────────
mkdir -p data

# ── 3. Stage everything ──────────────────────────────────────────────────
git add .
git commit -m "Initial commit: P3 Maths practice app" --allow-empty 2>/dev/null || \
git commit -m "Deploy: P3 Maths practice app" 2>/dev/null || true

echo "✓ Local repo ready"

# ── 4. Push to GitHub ────────────────────────────────────────────────────
if command -v gh &>/dev/null; then
  echo ""
  echo "▶ Creating GitHub repo via gh CLI..."
  # Create repo (public so Render can read it; change to --private if preferred)
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push \
    --description "Singapore P3 Maths practice app" 2>/dev/null || {
      # Repo may already exist — just push
      echo "  (repo already exists, pushing...)"
      git remote add origin "https://github.com/$(gh api user -q .login)/$REPO_NAME.git" 2>/dev/null || true
      git push -u origin main --force
  }
  GITHUB_URL="https://github.com/$(gh api user -q .login)/$REPO_NAME"
  echo "✓ Pushed to GitHub: $GITHUB_URL"
else
  echo ""
  echo "⚠  GitHub CLI (gh) not found."
  echo "   Install it from https://cli.github.com then re-run this script."
  echo "   Or manually:"
  echo "     1. Create a new repo at https://github.com/new  (name: $REPO_NAME)"
  echo "     2. Run:"
  echo "          git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
  echo "          git push -u origin main"
  GITHUB_URL="https://github.com/YOUR_USERNAME/$REPO_NAME"
fi

# ── 5. Print Render instructions ─────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════"
echo "  NEXT: Connect to Render"
echo "════════════════════════════════════════════════"
echo ""
echo "  1. Go to https://render.com and sign in (free tier is fine)"
echo "  2. Click  New +  →  Web Service"
echo "  3. Connect your GitHub account and select:"
echo "       $GITHUB_URL"
echo "  4. Render will auto-detect render.yaml — click  Deploy"
echo "  5. Your app will be live at:"
echo "       https://$REPO_NAME.onrender.com"
echo ""
echo "  (First deploy takes ~3 min. Free tier spins down after 15 min"
echo "   of inactivity — first request after that takes ~30 sec.)"
echo ""
echo "Done! ✓"
