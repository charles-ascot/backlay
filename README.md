# CHIMERA Backtest Simulator

Interactive backtesting tool for the CHIMERA lay betting strategy on historical Betfair data.

## Features

- **Upload Multiple Markets**: Drag-and-drop NDJSON stream files (Betfair historical data format)
- **Configurable Timing**: Test strategy at different time offsets (5min to 2hrs before race)
- **Automatic Bet Placement**: Apply rules to historical odds and simulate bet placement
- **Instant Results**: P&L calculated from actual race settlements
- **Detailed Analytics**: Win rates, rule breakdown, exportable CSV

## Architecture

- **Frontend**: React + Vite + Tailwind CSS (glassmorphic UI)
- **Backend**: FastAPI + Python
- **Deployment**: Cloudflare Pages (frontend) + Google Cloud Run (backend)

## Local Development

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

The frontend proxies API requests to `http://localhost:8000` automatically.

## Data Format

Upload Betfair Historical Stream files in NDJSON format. Each file contains:
- Market definition (metadata, runners, venue)
- Price updates over time (`batl` = best available to lay)
- Settlement (final result with WINNER/LOSER status)

Example filename: `ADVANCED_2016_Mar_18_27569497_1.121231864`

## Strategy Rules

The backtest simulator applies the same rules as the live CHIMERA engine:

1. **RULE_1**: Favourite odds < 2.0 → LAY £3
2. **RULE_2**: Favourite odds 2.0-5.0 → LAY £2
3. **RULE_3A**: Favourite odds > 5.0, gap to 2nd fav < 2 → LAY fav £1 + LAY 2nd fav £1
4. **RULE_3B**: Favourite odds > 5.0, gap to 2nd fav ≥ 2 → LAY fav £1

## Deployment

### Backend (Google Cloud Run)

1. Build and push Docker image:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/chimera-backtest
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy chimera-backtest \
  --image gcr.io/YOUR_PROJECT/chimera-backtest \
  --platform managed \
  --region europe-west2 \
  --allow-unauthenticated \
  --port 8080
```

3. Note the service URL (e.g., `https://chimera-backtest-xyz.run.app`)

### Frontend (Cloudflare Pages)

1. Build frontend with backend URL:
```bash
cd frontend
VITE_API_URL=https://chimera-backtest-xyz.run.app npm run build
```

2. Push to GitHub

3. Connect GitHub repo to Cloudflare Pages:
   - Build command: `cd frontend && npm install && npm run build`
   - Build output: `frontend/dist`
   - Environment variable: `VITE_API_URL=https://chimera-backtest-xyz.run.app`

4. Assign custom domain in Cloudflare DNS

## Usage

1. Upload one or more NDJSON files (historical markets)
2. Select bet timing (e.g., 30 minutes before race)
3. Click "Run Simulation"
4. View results:
   - Summary statistics (win rate, P&L)
   - Individual bet outcomes
   - Rule-by-rule breakdown
   - Export to CSV

## Project Structure

```
chimera-backtest/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── stream_parser.py     # Parse NDJSON stream files
│   ├── backtest_engine.py   # Simulate betting & calculate P&L
│   ├── rules.py             # Strategy rules (from live engine)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── TimeSelector.jsx
│   │   │   ├── ResultsTable.jsx
│   │   │   └── Summary.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── Dockerfile
└── README.md
```

## License

Proprietary - Ascot Wealth Management / Cape Berkshire Ltd
