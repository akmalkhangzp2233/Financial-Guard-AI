# FinGuard AI — API Documentation

Base URL: `http://localhost:8000` (dev) or your deployed backend URL.
Full interactive Swagger UI is always available at **`/docs`** on any running instance, and the raw OpenAPI schema at `/openapi.json` — this file is a quick-reference summary, not a replacement for it.

Auth: every endpoint except `/auth/register` and `/auth/login` requires
`Authorization: Bearer <token>`. Admin-only endpoints additionally require
the logged-in user to have `is_admin = true`.

## Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account. First user on an empty DB is auto-promoted to admin. Rate-limited 10/min. |
| POST | `/auth/login` | Returns a JWT access token. Rate-limited 5/min. |
| GET | `/auth/me` | Current user's profile (includes `is_admin`). |

## Transactions
| Method | Path | Description |
|---|---|---|
| POST | `/transactions/` | Create a transaction (runs synchronous fraud scoring). |
| GET | `/transactions/` | List the current user's transactions. |
| DELETE | `/transactions/{id}` | Delete a transaction (owner only). |

## OCR Bill Scanner
| Method | Path | Description |
|---|---|---|
| POST | `/ocr/scan-receipt` | Multipart image upload → returns a parsed, editable draft (amount, merchant, date, suggested category). Does **not** save a transaction. |
| POST | `/ocr/scans/{scan_id}/link/{transaction_id}` | Links a confirmed transaction back to its originating scan (audit trail). |
| GET | `/ocr/scans/history` | Last 25 scans for the current user. |

## Budgets
| Method | Path | Description |
|---|---|---|
| POST | `/budgets/` | Create/update a monthly category budget (upsert). |
| GET | `/budgets/` | List current user's budgets with actual-vs-limit. |

## ML / Insights
| Method | Path | Description |
|---|---|---|
| GET | `/ml/forecast` | Next month's predicted total spend. |
| GET | `/insights/ai-advice` | 2-3 savings tips (GPT if `OPENAI_API_KEY` set, else rule-based). |

## Categories
| Method | Path | Description |
|---|---|---|
| GET | `/categories/` | List all spending/income categories. |

## Admin (requires `is_admin = true`)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/stats` | Platform-wide statistics. |
| GET | `/admin/users` | All users with transaction/spend/flag counts. |
| PATCH | `/admin/users/{id}/toggle-active` | Enable/disable a user account. |
| PATCH | `/admin/users/{id}/toggle-admin` | Grant/revoke admin rights. |
| GET | `/admin/transactions` | All transactions across all users (`?flagged_only=true` to filter). |
| GET | `/admin/fraud-logs` | Fraud log entries (`?reviewed=false` to filter). |
| PATCH | `/admin/fraud-logs/{id}/review` | Mark a fraud log entry reviewed. |

## Reports / Export
| Method | Path | Description |
|---|---|---|
| GET | `/reports/export/my-transactions.csv` | Current user's transactions as CSV. |
| GET | `/reports/export/all-transactions.csv` | **Admin only** — all transactions as CSV (Power BI feed). |
| GET | `/reports/export/monthly-summary.csv` | **Admin only** — pre-aggregated month × category totals. |

## System
| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check + environment info. |
| GET | `/health` | Liveness probe (used by Docker/Render health checks). |

## Error format
All errors return a consistent shape:
```json
{ "error": { "code": 404, "message": "Transaction not found" } }
```
Validation errors (422) additionally include a `details` array from Pydantic.
