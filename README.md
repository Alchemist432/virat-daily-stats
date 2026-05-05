## Virat Kohli Daily Cricket Stat Image Generator

### CLI generation
```bash
python generate_virat_daily_image.py
```
This writes SVG/JSON/history files in `output/`.

### Web app (generate + download + history)
Run locally:
```bash
python web_app.py
```
Then open `http://localhost:8000`.

### Public deployment (Render)
This repo includes `render.yaml` for one-click deploy on Render.
After deployment, open your Render URL on iPhone (for example: `https://virat-daily-stats.onrender.com`).

Detailed steps: see `DEPLOY_RENDER.md`.

Features:
- **Generate New Image** button
- renders the SVG directly in browser
- **Download SVG** link for each generated image
- historical generated images shown below the button

The backend tries live ESPNcricinfo Statsguru data first and falls back to `data/virat_seed_stats.json` when network is blocked.
