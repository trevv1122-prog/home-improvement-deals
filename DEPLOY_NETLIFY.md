# Deploying to GitHub & Netlify for 100% Automated Daily Updates

This setup creates a completely hands-free cloud architecture:
1. **GitHub Actions** runs the scraper every morning at **06:00 AM Central** (11:00 UTC) on GitHub's free cloud runners.
2. The workflow compiles the fresh markdowns into `deals.json` and `deals.csv` and commits them back to your repository.
3. **Netlify** automatically detects the new commit and redeploys your live website in seconds.
4. **Zero maintenance**: You never need to leave your computer running, keep terminal windows open, or worry about sleep mode.

---

## Step 1: Create a Repository on GitHub

1. Go to https://github.com/new and log in.
2. Enter a repository name (e.g., `prodeal-scanner` or `home-improvement-deals`).
3. Set the repository to **Public** or **Private** (both work with free GitHub Actions).
4. Leave "Add a README file" unchecked (we already have one).
5. Click **Create repository**.

---

## Step 2: Push This Project to GitHub

In your computer's terminal, unzip the project and push it to your new GitHub repo:

```bash
# 1. Unzip the downloaded package
unzip home_improvement_deal_scraper.zip -d prodeal-scanner
cd prodeal-scanner

# 2. Link your GitHub repo
git init
git add .
git commit -m "feat: initial commit of Home Depot & Lowe's deal scanner"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

# 3. Push to GitHub
git push -u origin main
```

*(Alternatively, if you prefer not using the terminal, you can drag and drop all files from the unzipped folder directly into the GitHub web interface by clicking "Upload files" on your new repository).*

---

## Step 3: Enable GitHub Actions Workflow Permissions

To allow GitHub Actions to commit the daily `deals.json` back to your repo:
1. On your GitHub repo page, click **Settings** (top tabs).
2. On the left sidebar, click **Actions** -> **General**.
3. Scroll down to **Workflow permissions**.
4. Select **"Read and write permissions"** and click **Save**.

---

## Step 4: Connect to Netlify (Free 1-Click Hosting)

1. Go to https://app.netlify.com and sign up or log in (you can log in with GitHub).
2. Click **Add new site** -> **Import an existing project**.
3. Select **GitHub** as your Git provider and authorize Netlify.
4. Pick your `prodeal-scanner` repository from the list.
5. Netlify will automatically detect the settings from `netlify.toml`:
   - **Branch to deploy**: `main`
   - **Publish directory**: `.` (root)
6. Click **Deploy prodeal-scanner**.

Within 30 seconds, Netlify will give you a live URL (e.g., `https://prodeal-scanner-xyz.netlify.app`).

---

## Step 5: How It Updates Daily Automatically

* **Scheduled Execution**: Every morning at `06:00 AM Central` (`11:00 UTC`), GitHub's cloud servers wake up and run `.github/workflows/daily_scan.yml`.
* **Scraping & Categorizing**: It scrapes Home Depot and Lowe's clearance and Special Buys, tags new markdowns (`🔥 NEW TODAY`), and generates `deals.json` and `deals.csv`.
* **Automatic Redeploy**: It commits the updated files to your `main` branch. Netlify immediately detects the commit and updates your live dashboard.
* **Manual Refresh**: You can also trigger a scan on demand anytime by going to the **Actions** tab on your GitHub repository, selecting **Daily Morning Deal Scan**, and clicking **Run workflow**.
* **Daily Report Download**: You and anyone visiting your Netlify site can click **Export CSV** to download the exact morning deal sheet.
