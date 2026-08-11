# FinGuard AI

An AI-powered personal finance tracker with real-time fraud detection, OCR
receipt scanning, expense forecasting, and GPT-assisted savings advice —
built as a final year project, and packaged to actually be deployed.

## Features

- **Transactions & budgets** — manual entry or OCR receipt scan, category-wise monthly budgets
- **Real-time fraud detection** — every transaction is scored by a trained Isolation Forest model the instant it's created
- **OCR bill scanner** — photograph a receipt, Tesseract extracts the text, the amount/merchant/date/category are pre-filled for you to confirm
- **Expense forecasting** — a trained regression model predicts next month's spend
- **AI savings advice** — GPT-generated tips when `OPENAI_API_KEY` is set, rule-based tips otherwise (never breaks without one)
- **Admin panel** — platform stats, user management, fraud review queue, CSV export
- **Power BI / Excel export** — CSV endpoints for personal and platform-wide reporting

## Quick start (Docker, recommended)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend + Swagger docs: http://localhost:8000/docs

Register an account — the first one on a fresh database is auto-promoted to
admin. ML models are pre-trained and shipped in `ml/models/`, so everything
works immediately; no training step required.

Full deployment options (Render + Vercel live hosting, single VPS, environment
variable reference): see **[DEPLOYMENT.md](./DEPLOYMENT.md)**.

## Local development (without Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```
Note: OCR requires the `tesseract-ocr` binary installed on your OS
(`apt install tesseract-ocr` / `brew install tesseract`) — the Docker image
handles this automatically.

## Project structure

```
backend/            FastAPI app — routers, models, ML service, auth
frontend/            React (Vite) SPA
ml/                  Training scripts + pre-trained model files (ml/models/*.pkl)
database/            SQL schema (reference — SQLAlchemy also auto-creates tables)
docs/                SRS, Project Report, IEEE paper, User Manual, API docs, diagrams
presentation/        FinGuard_AI_Presentation.pptx
docker-compose.yml   One-command local deployment
render.yaml          Render blueprint for backend hosting
DEPLOYMENT.md         Full deployment guide (Docker / Render+Vercel / VPS)
```

## Documentation

| Document | Path |
|---|---|
| Software Requirements Specification | `docs/SRS.docx` |
| Full Project Report | `docs/Project_Report.docx` |
| IEEE-format conference paper | `docs/IEEE_Paper.docx` |
| User Manual | `docs/User_Manual.docx` |
| API reference | `docs/API_Documentation.md` (or live at `/docs`) |
| Architecture / ER / class / sequence diagrams | `docs/diagrams/` |
| Presentation slides | `presentation/FinGuard_AI_Presentation.pptx` |

## Tech stack

React 18 · Vite · Tailwind · FastAPI · SQLAlchemy · scikit-learn · Tesseract
OCR · OpenAI API · Docker · PostgreSQL/MySQL/SQLite

## License

For academic use as a final year project submission.
