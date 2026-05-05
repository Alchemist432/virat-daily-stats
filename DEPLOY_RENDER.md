## Deploy to Render (iPhone-friendly)

1. Push this repo to GitHub.
2. In Render dashboard, choose **New +** -> **Blueprint**.
3. Select your GitHub repo; Render auto-detects `render.yaml`.
4. Click **Apply**.
5. After deploy completes, open the generated public URL (for example `https://virat-daily-stats.onrender.com`) on iPhone.

The app serves:
- `/` website UI with Generate button and history
- `/generate` backend generation endpoint
- `/history` generated image history API
