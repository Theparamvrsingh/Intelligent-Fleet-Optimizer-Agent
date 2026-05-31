# GitHub Push and Streamlit Community Cloud Deployment Guide

This guide details the procedures for pushing the Intelligent Fleet Operations Agent repository to GitHub and deploying the live application to Streamlit Community Cloud.

---

## Phase 1: Pushing the Project to GitHub

A dedicated Git repository has been initialized locally inside the project directory with a pre-configured `.gitignore` file to isolate local parameters (e.g. `.env`) and Python environments (e.g. `venv/`).

To publish your local commits to GitHub:

### Step 1: Create a New GitHub Repository
1. Navigate to the GitHub repository creation page: [github.com/new](https://github.com/new).
2. Set the repository name to `Intelligent-Fleet-Optimizer-Agent`.
3. Select the **Public** visibility setting (required for the free hosting tier of Streamlit Community Cloud).
4. Do not initialize the repository with a README, `.gitignore`, or License, as these have already been configured and committed locally.
5. Click **Create repository**.

### Step 2: Establish the Remote Origin and Push
Open your local terminal, navigate to your workspace directory, and execute the following commands to link and upload your branch:

```bash
cd "/Users/paramveersingh/Desktop/Intelligent Fleet Operations Agent"

# Link the local repository to your remote GitHub repository
git remote add origin https://github.com/Theparamvrsingh/Intelligent-Fleet-Optimizer-Agent.git

# Push the committed main branch to GitHub
git push -u origin main
```

---

## Phase 2: Deploying to Streamlit Community Cloud

Streamlit Community Cloud provides zero-cost application hosting with automated server updates triggered directly by GitHub pushes.

### Step 1: Authentication
1. Go to the Streamlit Community Cloud console: [share.streamlit.io](https://share.streamlit.io/).
2. Log in using your GitHub account and authorize the necessary permissions.

### Step 2: Application Configuration
1. On the cloud console dashboard, select **Create app** (or **New app**).
2. Input the following configuration details into the deployment form:
   * **Repository:** `Theparamvrsingh/Intelligent-Fleet-Optimizer-Agent`
   * **Branch:** `main`
   * **Main file path:** `app.py`
3. Click the **Advanced settings...** link located at the bottom of the form.

### Step 3: Secret Keys Configuration
The system requires a Google Gemini API Key to orchestrate agent operations. This key must be securely injected using Streamlit Secrets.
Copy and paste the following configuration string into the **Secrets** textbox (replace with your active API credential):

```toml
GOOGLE_GEMINI_API_KEY = "AIzaSy..."
```

4. Click **Save**.
5. Click **Deploy!**

The Streamlit deployment pipeline will spin up a host container, automatically install the dependencies defined in your `requirements.txt` file, and generate a live application URL.

---

## Phase 3: Linking Deployment to your GitHub Repository

Once the Streamlit host pipeline completes:
1. Copy the active subdomain URL of your live application (e.g., `https://fleet-operations.streamlit.app/`).
2. Navigate to your GitHub repository page.
3. In the right-hand sidebar, click the settings gear icon next to the **About** section.
4. Input the deployment URL into the **Website** field.
5. Click **Save changes**.

Your repository will now prominently showcase the live execution link, providing a professional presentation for interviews and portfolio review.
