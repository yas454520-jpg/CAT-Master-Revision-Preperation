# CAT Master Prep Tracker

A personal CAT preparation dashboard built with **Python + Flask + HTML/CSS/JavaScript**.

The UI is designed around the supplied screenshots:
- Light mode only
- Indigo/blue primary actions
- Daily Random Generator
- QA & Chapter Revision Log
- EOD Summary & Analytics
- Settings & Module Limits
- Automatic 7-day / 30-day revision scheduling
- Responsive desktop/tablet/mobile layout

## Important: question bank

This version does **not** need your question bank files.

It generates identifiers from your configured bounds, for example:
- `M1(E)04`
- `M3(M)18`
- `CR Q142`
- `VA Q21`
- `M2(DI)03`
- `M4(LR)12`

You solve those questions on your existing question-bank website and enter completion + accuracy in the tracker.

## Data storage

When `GITHUB_TOKEN` and `GITHUB_REPO` are configured, the Flask server stores:
- settings
- generated daily sets
- QA/revision records
- EOD logs

inside JSON files in the configured private GitHub repository.

The token is **server-side only**. Never put it into frontend JavaScript.

If GitHub credentials are not configured, the app uses local JSON files under `data/` for development.

## Run locally

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GITHUB_TOKEN="YOUR_TOKEN"
$env:GITHUB_REPO="YOUR_USERNAME/YOUR_PRIVATE_REPO"
py app.py
```

Then open:

```text
http://127.0.0.1:5000
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GITHUB_TOKEN="YOUR_TOKEN"
export GITHUB_REPO="YOUR_USERNAME/YOUR_PRIVATE_REPO"
python app.py
```

## GitHub token

Use a fine-grained GitHub Personal Access Token with access limited to the private repository and repository **Contents: Read and write** permission.

Do not commit the token.

## Deploying

A simple architecture is:

```text
Browser
   ↓
Flask app
   ↓
GitHub Contents API
   ↓
Private GitHub repository
```

Deploy the Flask app to a Python host such as Render or Railway and add the same environment variables there.

## DILR generation

The default generator creates 4 DILR identifiers:
- 2 DI
- 2 LR

The module limits in Settings determine the available number range for each module/type.

## Revision scheduling

- New Concept → next revision in 7 days
- Revision 1 (7-Day) → next revision in 30 days
- Revision 2 / Mastered → no automatic next date in this starter version

## Optional demo data

For a local preview, POST to:

```text
/api/seed-demo
```

or use your browser developer tools/Postman.

Remove the demo endpoint before exposing the app publicly if you do not want it available.
