# Deploy Steps — Run These In Order

## Step 1: Local Login (do this first)

Open Terminal in Cursor, then:

```powershell
cd "c:\Users\Administrator\Desktop\Telegram Aviator bot"

$env:API_ID="YOUR_API_ID"
$env:API_HASH="YOUR_API_HASH"
$env:SOURCE_CHANNEL="Avibum"
$env:DEST_CHANNEL="KE7ZONE"

python repost.py
```

Enter phone number → code → 2FA if asked. When you see `Bot is running...`, press **Ctrl+C**.  
Verify `session_name.session` exists.

---

## Step 2: Install Git (if not installed)

Download from: https://git-scm.com/download/win  
Install, then **restart Cursor** so the terminal picks up Git.

---

## Step 3: Push to GitHub

```powershell
cd "c:\Users\Administrator\Desktop\Telegram Aviator bot"

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your GitHub repo. Create the repo on GitHub first (empty, no README).

---

## Step 4: Deploy to Railway

1. Go to https://railway.app
2. **New Project** → **Deploy from GitHub** → select your repo
3. **Variables** → Add:
   - `API_ID` = your_api_id
   - `API_HASH` = your_api_hash
   - `SOURCE_CHANNEL` = Avibum
   - `DEST_CHANNEL` = KE7ZONE
4. **Redeploy**
5. Check logs for `Bot is running...`
