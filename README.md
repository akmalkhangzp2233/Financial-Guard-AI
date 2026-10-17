# 🛡️ FinGuard AI
### Intelligent Personal Finance, Fraud Detection & Spending Analytics

**FinGuard AI** is a full-stack financial management application that combines
personal expense tracking, machine learning-based fraud detection, receipt
scanning, spending forecasts, and AI-assisted savings guidance in one
interactive dashboard.

The project brings together financial data management, predictive analytics,
and automated risk monitoring to help users understand their spending
patterns and review potentially suspicious transactions.

<p align="center">
  <a href="https://github.com/akmalkhangzp2233/Financial-Guard-AI">
    <img src="https://img.shields.io/badge/Project-FinGuard%20AI-0D9488?style=for-the-badge"
         alt="FinGuard AI">
  </a>
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge&logo=react&logoColor=black"
       alt="React">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"
       alt="FastAPI">
  <img src="https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white"
       alt="scikit-learn">
</p>

<p align="center">
  <a href="https://github.com/akmalkhangzp2233/Financial-Guard-AI">
    <strong>GitHub Repository</strong>
  </a>
  &nbsp; • &nbsp;
  <a href="https://financial-guard-ai.vercel.app">
    <strong>Live Demo</strong>
  </a>
  &nbsp; • &nbsp;
  <a href="DEPLOYMENT.md">
    <strong>Deployment Guide</strong>
  </a>
</p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Project Objectives](#-project-objectives)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Configuration](#-environment-configuration)
- [API Documentation](#-api-documentation)
- [Machine Learning](#-machine-learning)
- [Database](#-database)
- [Deployment](#-deployment)
- [Security and Responsible Use](#-security-and-responsible-use)
- [Documentation](#-documentation)
- [Future Improvements](#-future-improvements)
- [Author](#-author)

---

## 🎯 Overview

Managing personal finances involves more than recording income and expenses.
Users also need to understand spending behavior, manage budgets, identify
unusual transactions, and anticipate future expenses.

FinGuard AI brings these activities together in a single web application.

The platform provides a dashboard for financial summaries, transaction
management, budget tracking, fraud alerts, receipt OCR, spending forecasts,
and savings guidance.

Its backend is built with FastAPI and SQLAlchemy, while the frontend uses
React and Vite. Machine learning functionality supports transaction anomaly
detection and spending forecasting.

The application can run locally and includes deployment configuration for
containerized and cloud-hosted environments.

### Project at a Glance

| Component | Description |
|---|---|
| Application | FinGuard AI |
| Frontend | React with Vite |
| Backend | Python with FastAPI |
| Database layer | SQLAlchemy |
| Machine learning | scikit-learn |
| Fraud detection | Isolation Forest-based anomaly detection |
| Receipt processing | Tesseract OCR |
| AI-assisted guidance | Optional OpenAI API integration |
| Local database | SQLite by default |
| Additional database options | PostgreSQL and MySQL through configuration |
| Containerization | Docker and Docker Compose |
| Deployment | Render and Vercel configuration |

---

## 🎯 Project Objectives

FinGuard AI was developed to demonstrate how web development, database
management, and machine learning can be combined to address practical
personal-finance problems.

The main objectives are to:

- Simplify transaction and expense management.
- Provide clear summaries of income, spending, and savings.
- Identify transactions that may require additional review.
- Reduce manual data entry through receipt scanning.
- Use historical spending data to estimate future expenses.
- Provide budget tracking and savings guidance.
- Support financial data analysis through CSV exports.
- Demonstrate a deployable full-stack application.

---

## 🚀 Key Features

### 1. 📊 Financial Dashboard

The dashboard brings important financial information together in one place.

It provides:

- Total spending.
- Total income.
- Savings calculated from income and spending.
- Expense breakdown by category.
- Flagged transaction counts.
- Spending forecast information.
- Fraud alert information.

The dashboard communicates with the backend through API requests and
presents the returned information in the frontend.

### 2. 💳 Transaction Management

FinGuard AI supports financial transaction management for authenticated
users.

Transactions provide the underlying data for financial summaries,
spending analysis, forecasts, and fraud monitoring.

Keeping transaction records organized helps users understand where their
money goes and identify spending patterns.

### 3. 🛡️ Machine Learning-Based Fraud Detection

The application uses an Isolation Forest-based anomaly detection approach
to identify potentially unusual transactions.

The fraud detection workflow supports:

- Machine learning-based anomaly scoring.
- Recording detected fraud alerts.
- Classifying alerts into risk categories.
- Displaying suspicious transactions for review.
- Tracking whether an alert has been reviewed.

**Important:** An anomaly score indicates unusual behavior relative to the
model's learned patterns. It is not, by itself, proof of fraud or a
calibrated probability that a transaction is fraudulent.

### 4. 🧾 OCR Receipt Scanner

The receipt-scanning functionality uses Tesseract OCR to extract text
from receipt images.

The extracted information can help prefill transaction details, including
the merchant, date, amount, and category, for the user to review.

This reduces manual entry when recording expenses.

OCR accuracy depends on receipt quality, image clarity, formatting,
and the text-recognition process. Extracted values should be checked
before saving.

### 5. 📈 Spending Forecast

FinGuard AI includes a spending forecast feature that uses a trained
regression model to estimate the next month's spending.

The forecast workflow uses historical transaction information and the
machine learning service to generate a prediction.

The result is intended to support budgeting and financial planning.
It should be treated as an estimate rather than a guarantee of future
spending.

### 6. 💡 AI-Assisted Savings Guidance

The application can provide savings guidance using the OpenAI API when
`OPENAI_API_KEY` is configured.

When that key is not configured, the application can fall back to
rule-based guidance.

This allows the application to retain basic savings-guidance functionality
without requiring an OpenAI API key.

### 7. 💰 Budget Management

Budget functionality helps users organize spending limits and monitor
expenses against their budgets.

Category-based budgeting provides a practical way to review spending
and identify areas where expenses may need attention.

### 8. 🛠️ Administrative Features

The project includes administrative functionality for platform oversight,
including:

- Platform statistics.
- User management.
- Fraud alert review.
- CSV exports for reporting.

Administrative access and account permissions should be configured
carefully before deploying the application for real users.

### 9. 📁 Financial Data Export

CSV export functionality supports additional analysis outside the
application.

Exported data can be used with tools such as:

- Microsoft Excel.
- Microsoft Power BI.
- Other applications that support CSV files.

This makes the project useful for financial reporting and exploratory
data analysis.

---

## 🔄 How It Works

The application follows a frontend-backend architecture.

### Typical Application Workflow

1. A user accesses the React dashboard.
2. The frontend sends requests to the FastAPI backend.
3. Authentication and application logic determine which data the user
   can access.
4. SQLAlchemy interacts with the configured database.
5. Financial records are used to calculate summaries and spending
   information.
6. The machine learning service supports fraud anomaly scoring and
   spending forecasts.
7. Receipt images can be processed through the OCR functionality.
8. The backend returns structured API responses.
9. The frontend displays financial summaries, charts, forecasts,
   budgets, and fraud alerts.

### Fraud Monitoring Workflow

Transaction data
       ↓
Feature preparation
       ↓
Isolation Forest anomaly detection
       ↓
Anomaly score
       ↓
Risk classification
       ↓
Fraud alert
       ↓
User review

The risk classification is intended to help prioritize review. It does
not replace a complete fraud investigation.

### Spending Forecast Workflow

Historical transaction data
       ↓
Monthly spending aggregation
       ↓
Machine learning forecasting service
       ↓
Predicted next-month spending
       ↓
Dashboard visualization

Forecast quality depends on the available data and the behavior of the
trained model.

---

## 🧰 Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| React | Component-based user interface |
| Vite | Frontend development and build tooling |
| Tailwind CSS | User interface styling |
| JavaScript | Frontend application logic |

### Backend

| Technology | Purpose |
|---|---|
| Python | Backend and machine learning language |
| FastAPI | REST API framework |
| SQLAlchemy | Database access and ORM |
| Pydantic | Data validation and API schemas |
| Uvicorn | ASGI application server |

### Machine Learning and Data Processing

| Technology | Purpose |
|---|---|
| scikit-learn | Machine learning functionality |
| Isolation Forest | Transaction anomaly detection |
| Regression model | Spending forecasting |
| Tesseract OCR | Text extraction from receipts |
| OpenAI API | Optional AI-assisted savings guidance |

### Database and Deployment

| Technology | Purpose |
|---|---|
| SQLite | Default local database |
| PostgreSQL | Configurable database option |
| MySQL | Configurable database option |
| Docker | Application containerization |
| Docker Compose | Multi-service local startup |
| Render | Backend deployment configuration |
| Vercel | Frontend deployment configuration |
| Git and GitHub | Version control and source hosting |

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────────┐
                    │        User             │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ React + Vite Frontend   │
                    │                         │
                    │ Dashboard               │
                    │ Transactions            │
                    │ Budgets                 │
                    │ Fraud Alerts            │
                    │ Spending Forecast       │
                    └────────────┬────────────┘
                                 │
                           REST API / HTTP
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ FastAPI Backend         │
                    │                         │
                    │ Authentication          │
                    │ Business Logic           │
                    │ API Routers             │
                    │ Request Validation      │
                    └───────┬─────────┬───────┘
                            │         │
                ┌───────────▼──┐   ┌──▼────────────────┐
                │ SQLAlchemy   │   │ ML / OCR Services │
                │              │   │                   │
                │ Database     │   │ Fraud Detection   │
                │ Queries      │   │ Spending Forecast │
                │ Transactions │   │ Receipt OCR       │
                └───────┬──────┘   └───────────────────┘
                        │
                        ▼
                ┌───────────────────┐
                │ SQLite / Postgres │
                │ / MySQL           │
                └───────────────────┘
