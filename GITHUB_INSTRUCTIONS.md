# GitHub Deployment Instructions

1. **Initialize Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Local Video Tool"
   ```

2. **Create Repository on GitHub**
   - Go to GitHub.com -> New Repository.
   - Name it `local-video-tool` (or similar).
   - Do not initialize with README/gitignore (we have them).

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

4. **Notes**
   - The `storage/` folder should probably be in `.gitignore` so you don't upload large video files.
   - The `.venv/` and `node_modules/` folders should also be ignored.

## Recommended .gitignore
Create a `.gitignore` file with:
```
.venv/
__pycache__/
node_modules/
storage/
*.pem
.env
.DS_Store
```
