# 🚀 Push to GitHub - Quick Guide

Your local git repository is ready! Follow these steps to push to GitHub:

## Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** button in the top-right corner
3. Select **"New repository"**
4. Fill in:
   - **Repository name**: `fire-evacuation-simulator` (or your preferred name)
   - **Description**: "Emergency Building Sweep Simulator - HiMCM 2025 MVP"
   - **Visibility**: Choose Public or Private
   - ⚠️ **DO NOT** check "Initialize with README" (we already have one)
5. Click **"Create repository"**

## Step 2: Push Your Code

GitHub will show you instructions. Use these commands in your terminal:

```bash
cd /Users/anders/Downloads/fire-evacuation-simulator-master

# Add GitHub as remote (replace YOUR_USERNAME and YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Example:
If your GitHub username is `johndoe` and repo is `fire-evacuation-simulator`:
```bash
git remote add origin https://github.com/johndoe/fire-evacuation-simulator.git
git branch -M main
git push -u origin main
```

## Step 3: Verify

1. Refresh your GitHub repository page
2. You should see all your files!
3. The README.md will display automatically

## 📝 Current Commit Status

✅ All files committed locally:
- 28 files changed, 4,614+ lines
- Commit message: "Initial commit: Emergency Building Sweep Simulator MVP"
- Branch: master (can rename to main in Step 2)

## 🔒 Authentication

If GitHub asks for credentials:

### Option 1: Personal Access Token (Recommended)
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use token as password when pushing

### Option 2: SSH Key
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
```

Then use SSH URL instead:
```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

## 📋 What's Included

Your repository contains:
- ✅ Complete source code (~2,800 lines)
- ✅ Documentation (README, USAGE, PROJECT_SUMMARY, DELIVERABLES)
- ✅ Test suite (6 acceptance tests)
- ✅ Sample layouts (1-floor and 3-floor buildings)
- ✅ Configuration files
- ✅ Demo scripts
- ✅ .gitignore (excludes outputs and __pycache__)

## 🎯 After Pushing

### Add Topics/Tags (Recommended)
On your GitHub repo page, click "⚙️ Settings" or the gear icon near "About", then add topics:
- `simulation`
- `emergency-response`
- `agent-based-modeling`
- `pygame`
- `python`
- `himcm-2025`

### Enable GitHub Pages (Optional)
Your README will be visible, but you can also:
1. Go to Settings → Pages
2. Source: Deploy from branch → main
3. Your documentation will be available at: `https://YOUR_USERNAME.github.io/YOUR_REPO`

### Add a License Badge (Optional)
Your README already includes badges, but you can:
1. Go to GitHub → Insights → Community
2. Add LICENSE file (MIT is already mentioned in README)

## 🔄 Future Updates

After making changes:
```bash
git add .
git commit -m "Your commit message"
git push
```

## 📦 Quick Commands Reference

```bash
# Check status
git status

# See commit history
git log --oneline

# View remote
git remote -v

# Pull latest changes
git pull

# Create new branch
git checkout -b feature-name
```

## ✅ Checklist

- [ ] Created GitHub repository
- [ ] Added remote origin
- [ ] Pushed to main branch
- [ ] Verified files on GitHub
- [ ] Added repository description
- [ ] Added topics/tags
- [ ] Checked README displays correctly

## 🎉 You're Done!

Once pushed, your repository will be live at:
`https://github.com/YOUR_USERNAME/YOUR_REPO`

Share the link with your team or use it for your HiMCM 2025 submission!

---

**Need Help?**
- GitHub Docs: https://docs.github.com
- Git Basics: https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control

