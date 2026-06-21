# Pushing this repo to GitHub

```bash
cd happyrobot-carrier-sales
git init
git add .
git commit -m "Inbound carrier sales: TMS+FMCSA middleware, negotiation, call logging, ops dashboard"
git branch -M main
git remote add origin <your-empty-github-repo-url>
git push -u origin main
```

Both `.env` files are already gitignored (`middleware/.gitignore`,
`dashboard/.gitignore`) — only `.env.example` placeholders get
committed. Double-check with `git status` before the first commit that
no real `.env`, `.aws-sam/`, or `__pycache__/` made it in.
