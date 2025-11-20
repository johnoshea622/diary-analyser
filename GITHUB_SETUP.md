# GitHub Setup Instructions

## Push to GitHub

1. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `diary-analyser` (or your preferred name)
   - Description: "Python tool for analyzing diary entries from client/supervisor reports"
   - Privacy: Choose **Private** (recommended - contains business data)
   - **DO NOT** initialize with README, .gitignore, or license (we already have them)
   - Click "Create repository"

2. **Push your local repository to GitHub:**
   
   After creating the repository, GitHub will show you commands. Use these:
   
   ```bash
   cd "/Users/johnoshea/Library/CloudStorage/OneDrive-TCDGroup/0 TCD MyDocs/01. BMI Projects/98b. Diary analyser"
   
   git remote add origin https://github.com/YOUR-USERNAME/diary-analyser.git
   git branch -M main
   git push -u origin main
   ```
   
   Replace `YOUR-USERNAME` with your GitHub username.

3. **Set up GitHub Codespaces:**
   
   Once pushed:
   - Go to your repository on GitHub
   - Click the green "Code" button
   - Select "Codespaces" tab
   - Click "Create codespace on main"
   - Wait for the environment to build (installs Python packages automatically)

4. **Add OpenAI API Key to Codespaces:**
   
   In your repository settings:
   - Go to Settings → Secrets and variables → Codespaces
   - Click "New repository secret"
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
   - Click "Add secret"
   
   This will automatically inject the API key into all Codespaces for this repo.

## Working from Anywhere

### Option 1: GitHub Codespaces (Recommended)
- Go to github.com
- Navigate to your repository
- Click "Code" → "Codespaces" → Open existing or create new
- Full VS Code environment in your browser
- All dependencies pre-installed

### Option 2: Clone to Another Machine
```bash
git clone https://github.com/YOUR-USERNAME/diary-analyser.git
cd diary-analyser
pip install -r requirements.txt
# Create .env file with your API key
echo "OPENAI_API_KEY=your-key-here" > .env
```

### Option 3: GitHub.dev (Quick Edits)
- Press `.` on any GitHub repository page
- Opens lightweight VS Code editor in browser
- Good for quick file edits, not for running code

## Syncing Changes

### From your Mac:
```bash
git add .
git commit -m "Description of changes"
git push
```

### From Codespaces:
- Changes are automatically detected
- Use the Source Control panel (Ctrl/Cmd+Shift+G)
- Stage, commit, and push changes

### Pull latest changes:
```bash
git pull
```

## Important Notes

- **Data files**: Excel/PDF reports are committed (184 files in initial commit)
- **Excluded files**: `.env`, `diary.sqlite`, `__pycache__/` are NOT synced (security)
- **API Key**: Must be set up separately in each environment (Codespaces secrets or local `.env`)
- **Python version**: Codespaces uses Python 3.13

## Troubleshooting

### If you get authentication errors:
GitHub may require a Personal Access Token instead of password:
1. Go to Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when git asks

### If Codespaces won't start:
- Check if you have available Codespaces quota (free tier: 60 hours/month)
- Ensure the repository is accessible
- Try rebuilding the container

## Next Steps After Push

1. Verify files are on GitHub
2. Create a Codespace and test it works
3. Add the OPENAI_API_KEY secret
4. Run `make audit` in Codespaces to verify everything works
