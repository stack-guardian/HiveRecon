# Steps to push HiveRecon to GitHub

## 1. Create Repository on GitHub

Go to GitHub and create a new repository:
- URL: https://github.com/new
- Repository name: HiveRecon
- Description: AI-powered reconnaissance framework for bug bounty hunting
- Visibility: Public (recommended for open source)
- DO NOT initialize with README, .gitignore, or license (we already have these)

## 2. Push to GitHub

Run these commands in the terminal:

```bash
cd /home/vibhxr/hiverecon

# Push to GitHub
git push -u origin main

# If you get an authentication error, use a personal access token:
# git push https://YOUR_GITHUB_TOKEN@github.com/stack-guardian/HiveRecon.git main
```

## 3. Verify Push

After pushing, verify on GitHub:
- Go to: https://github.com/stack-guardian/HiveRecon
- Check that all files are uploaded

## 4. Set Repository Topics (Optional)

On GitHub, add these topics to the repository:
- bug-bounty
- security-tools
- reconnaissance
- ai
- ollama
- langchain
- cybersecurity
- python
- fastapi
- react

## 5. Enable GitHub Actions (Optional)

If you want CI/CD:
- Go to repository Settings > Actions
- Enable actions
- The CI workflow will run on every push

---

After pushing, we can continue with step-by-step integration of tools.
