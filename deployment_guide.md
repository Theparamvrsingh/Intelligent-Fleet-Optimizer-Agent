# 🚀 GitHub Push & Streamlit Community Cloud Deployment Guide

This guide walks you through pushing the newly completed and optimized **Intelligent Fleet Operations Agent** to your GitHub account and deploying it to **Streamlit Community Cloud** for free.

---

## 📂 Phase 1: Push Project to GitHub

A dedicated Git repository has already been initialized and committed locally inside `/Users/paramveersingh/Desktop/Intelligent Fleet Operations Agent/` with a clean `.gitignore` (ignoring venv, caching, and `.env` secrets).

To push this repository to GitHub:

### Step 1: Create a New Repo on GitHub
1. Go to [github.com/new](https://github.com/new).
2. Set the repository name to **`Intelligent-Fleet-Operations-Agent`**.
3. Choose **Public** (required for the free tier of Streamlit Community Cloud).
4. **DO NOT** initialize the repository with a README, `.gitignore`, or License (since we have already created and committed them locally!).
5. Click **Create repository**.

### Step 2: Push Local Files to GitHub
Open your terminal and run the following commands (replace `yourusername` with your real GitHub username):

```bash
cd "/Users/paramveersingh/Desktop/Intelligent Fleet Operations Agent"

# Link the local repo to your GitHub remote
git remote add origin https://github.com/yourusername/Intelligent-Fleet-Operations-Agent.git

# Push your main branch to GitHub
git push -u origin main
```

---

## ☁️ Phase 2: Deploy to Streamlit Community Cloud

Streamlit Community Cloud offers free, instant server hosting for Streamlit projects with direct auto-builds on GitHub pushes.

### Step 1: Sign Up / Sign In
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **Continue with GitHub** and authorize Streamlit to access your repositories.

### Step 2: Deploy the Application
1. Once logged in to the dashboard, click **Create app** (or **New app**) in the top right.
2. In the deployment form, configure the following:
   * **Repository:** `yourusername/Intelligent-Fleet-Operations-Agent`
   * **Branch:** `main`
   * **Main file path:** `app.py`
3. Click on the **Advanced settings...** link at the bottom of the form.

### Step 3: Add API Secrets (Crucial!)
Because the app requires the Gemini API key, you must inject it securely using Streamlit Secrets.
In the **Secrets** textbox, paste the following configuration (replace with your actual Gemini API key):

```toml
GOOGLE_GEMINI_API_KEY = "AIzaSy..."
```

4. Click **Save**.
5. Click **Deploy!**

Streamlit will now spin up a container, install all dependencies listed in your `requirements.txt` file (like Streamlit, Folium, LangGraph, etc.), and host your app live!

---

## 🔗 Phase 3: Add Deployed Link to GitHub

Once your Streamlit app is live:
1. Copy the live URL of your Streamlit app (e.g. `https://fleet-operations-agent.streamlit.app/`).
2. Go to your GitHub repository page.
3. On the right side, click the **Settings icon (Gear)** next to the **About** section.
4. Paste the live Streamlit URL into the **Website** field.
5. Click **Save changes**.

Your repository will now proudly show a live preview link, perfect for internships, showcase portfolios, and coding interviews!
