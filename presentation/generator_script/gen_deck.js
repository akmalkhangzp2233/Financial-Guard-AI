const pptxgen = require("pptxgenjs");

const INK = "1B2430", EMERALD = "1F6F5C", AMBER = "C98A2C", ALERT = "C4453A", IVORY = "FBFAF6", WHITE = "FFFFFF", GREY = "6B7280";
const D = "../docs/diagrams/";

function newPres() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  return pres;
}
const pres = newPres();

function bgSlide(title) {
  const s = pres.addSlide();
  s.background = { color: IVORY };
  s.addShape("rect", { x: 0, y: 0, w: 13.33, h: 0.9, fill: { color: INK } });
  s.addText(title, { x: 0.5, y: 0.12, w: 12.3, h: 0.65, fontSize: 24, bold: true, color: WHITE, fontFace: "Georgia" });
  return s;
}

// --- Slide 1: Title ---
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addShape("rect", { x: 0, y: 3.3, w: 13.33, h: 0.05, fill: { color: EMERALD } });
  s.addText("FinGuard AI", { x: 0.8, y: 2.3, w: 11.7, h: 1.1, fontSize: 54, bold: true, color: WHITE, fontFace: "Georgia" });
  s.addText("AI-Powered Personal Finance Tracker with Real-Time Fraud Detection,\nOCR Bill Scanning & GPT-Assisted Savings Advice", {
    x: 0.8, y: 3.5, w: 11.7, h: 1.0, fontSize: 18, color: "C7CED6", fontFace: "Helvetica",
  });
  s.addText("Final Year Project Presentation", { x: 0.8, y: 6.6, w: 8, h: 0.4, fontSize: 14, color: AMBER, bold: true });
  s.addText("[Your Name]  ·  [Your Institution]  ·  [Date]", { x: 0.8, y: 7.0, w: 8, h: 0.4, fontSize: 12, color: "9AA3AE" });
}

// --- Slide 2: Problem ---
{
  const s = bgSlide("The Problem");
  const points = [
    "Most personal finance apps just record transactions — they don't tell you anything is wrong.",
    "Financial fraud and mistakes usually show up first as an unusual transaction — but users only notice it during a monthly review, if at all.",
    "Manually re-typing every paper receipt is tedious enough that most people simply stop tracking their spending.",
    "Bank-linked aggregator apps solve some of this, but require handing over real account access — not appropriate or necessary for every use case.",
  ];
  s.addText(points.map((t, i) => ({ text: t, options: { bullet: { code: "2022" }, breakLine: true, paraSpaceAfter: 18 } })),
    { x: 0.7, y: 1.3, w: 11.9, h: 5.5, fontSize: 20, color: INK, fontFace: "Helvetica", valign: "top" });
}

// --- Slide 3: Objectives ---
{
  const s = bgSlide("Objectives");
  const objs = [
    "Secure, multi-user finance tracker with category budgeting",
    "Real-time ML fraud/anomaly scoring on every transaction",
    "Next-month expense forecasting from spend history",
    "OCR receipt scanning → user-confirmed transaction",
    "GPT-assisted savings advice with a rule-based fallback",
    "Admin panel for platform-wide oversight",
    "Real deployment readiness: Docker, CI, security hardening",
  ];
  const colW = 5.7;
  objs.forEach((t, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    s.addShape("roundRect", { x: 0.6 + col * (colW + 0.4), y: 1.25 + row * 1.35, w: colW, h: 1.1, fill: { color: WHITE }, line: { color: "E3E0D6", width: 1 }, rectRadius: 0.08 });
    s.addText(t, { x: 0.85 + col * (colW + 0.4), y: 1.25 + row * 1.35, w: colW - 0.5, h: 1.1, fontSize: 14.5, color: INK, valign: "middle", fontFace: "Helvetica" });
  });
}

// --- Slide 4: Architecture ---
{
  const s = bgSlide("System Architecture");
  s.addImage({ path: D + "architecture.png", x: 1.4, y: 1.15, w: 10.5, h: 6.0, sizing: { type: "contain", w: 10.5, h: 6.0 } });
}

// --- Slide 5: Tech Stack ---
{
  const s = bgSlide("Technology Stack");
  const rows = [
    ["Frontend", "React 18, Vite, Tailwind CSS, Axios, Recharts"],
    ["Backend", "Python 3.11, FastAPI, SQLAlchemy, Pydantic"],
    ["Auth & Security", "JWT (python-jose), bcrypt, slowapi rate limiting"],
    ["Machine Learning", "scikit-learn — Isolation Forest + Linear Regression"],
    ["OCR", "Tesseract OCR engine + pytesseract + Pillow"],
    ["AI Advice", "OpenAI GPT API, with rule-based fallback"],
    ["Database", "SQLite (dev) / PostgreSQL / MySQL (prod)"],
    ["Infra", "Docker, Docker Compose, Nginx, Gunicorn, GitHub Actions"],
  ];
  s.addTable(
    rows.map(([a, b], i) => ([
      { text: a, options: { bold: true, color: i === -1 ? WHITE : INK, fill: { color: i % 2 === 0 ? "FFFFFF" : "F3F1EA" }, fontSize: 14 } },
      { text: b, options: { color: INK, fill: { color: i % 2 === 0 ? "FFFFFF" : "F3F1EA" }, fontSize: 14 } },
    ])),
    { x: 0.6, y: 1.2, w: 12.1, h: 5.8, colW: [3.0, 9.1], border: { type: "solid", color: "E3E0D6", pt: 0.75 }, autoPage: false }
  );
}

// --- Slide 6: Feature — Fraud Detection ---
{
  const s = bgSlide("Feature: Real-Time Fraud Detection");
  s.addText("Every transaction is scored the instant it's created — not in a nightly batch job.", { x: 0.6, y: 1.15, w: 12.1, h: 0.5, fontSize: 16, italics: true, color: GREY });
  s.addImage({ path: D + "sequence_transaction_fraud.png", x: 2.0, y: 1.75, w: 9.3, h: 5.3, sizing: { type: "contain", w: 9.3, h: 5.3 } });
}

// --- Slide 7: Feature — OCR ---
{
  const s = bgSlide("Feature: OCR Bill Scanner");
  s.addText("Photograph a receipt → Tesseract extracts text → fields are parsed → user confirms before saving.", { x: 0.6, y: 1.15, w: 12.1, h: 0.5, fontSize: 16, italics: true, color: GREY });
  s.addImage({ path: D + "sequence_ocr_scan.png", x: 2.4, y: 1.7, w: 8.5, h: 5.4, sizing: { type: "contain", w: 8.5, h: 5.4 } });
}

// --- Slide 8: ML Results ---
{
  const s = bgSlide("Machine Learning — Results");
  s.addText("Fraud Detector (Isolation Forest)", { x: 0.7, y: 1.25, w: 5.6, h: 0.5, fontSize: 18, bold: true, color: EMERALD });
  s.addChart(pres.ChartType.bar, [
    { name: "Score", labels: ["Precision", "Recall"], values: [0.95, 0.98] },
  ], {
    x: 0.7, y: 1.85, w: 5.6, h: 3.6, chartColors: [EMERALD], showTitle: false, showValue: true,
    dataLabelColor: INK, dataLabelPosition: "outEnd", valAxisMaxVal: 1, valAxisLabelColor: GREY,
    catAxisLabelColor: INK, showLegend: false, valGridLine: { color: "E3E0D6", size: 1 }, catGridLine: { style: "none" },
  });
  s.addText("Trained on a synthetic-but-realistic labelled dataset (no real fraud data available for this project).", { x: 0.7, y: 5.55, w: 5.6, h: 0.9, fontSize: 12, italics: true, color: GREY });

  s.addText("Expense Forecaster (Linear Regression)", { x: 6.9, y: 1.25, w: 5.8, h: 0.5, fontSize: 18, bold: true, color: AMBER });
  s.addShape("roundRect", { x: 6.9, y: 1.95, w: 5.8, h: 2.2, fill: { color: WHITE }, line: { color: "E3E0D6", width: 1 }, rectRadius: 0.08 });
  s.addText("MAE ≈ 34.75", { x: 6.9, y: 2.15, w: 5.8, h: 1.0, fontSize: 40, bold: true, color: AMBER, align: "center", fontFace: "Georgia" });
  s.addText("average error on predicted monthly spend", { x: 6.9, y: 3.15, w: 5.8, h: 0.6, fontSize: 13, align: "center", color: GREY });
  s.addText("Predicts next month's total spend from trailing 3-month history + category mix.", { x: 6.9, y: 4.45, w: 5.8, h: 1.5, fontSize: 13, italics: true, color: GREY });
}

// --- Slide 9: Security ---
{
  const s = bgSlide("Production Security");
  const items = [
    "bcrypt password hashing — never stored in plaintext",
    "JWT-signed sessions; production refuses to boot with a default secret",
    "Rate limiting: global + tighter limit on login (5/min) against brute force",
    "Environment-driven CORS — no wildcard origins in production",
    "Structured global error handling — no stack traces ever reach the client",
    "Security response headers (X-Frame-Options, HSTS in production, etc.)",
  ];
  s.addText(items.map((t) => ({ text: t, options: { bullet: { code: "2713", color: EMERALD }, breakLine: true, paraSpaceAfter: 16 } })),
    { x: 0.7, y: 1.3, w: 11.9, h: 5.5, fontSize: 19, color: INK, fontFace: "Helvetica" });
}

// --- Slide 10: Admin Panel ---
{
  const s = bgSlide("Admin Panel");
  const items = [
    "Platform-wide stats: users, transactions, flagged count, total volume",
    "User management — enable/disable accounts, grant/revoke admin",
    "Fraud review queue across all users, with mark-as-reviewed",
    "One-click CSV export for Power BI / Excel reporting",
    "First registered account on a fresh database is auto-promoted to admin",
  ];
  s.addText(items.map((t) => ({ text: t, options: { bullet: { code: "2022" }, breakLine: true, paraSpaceAfter: 18 } })),
    { x: 0.7, y: 1.3, w: 11.9, h: 5.5, fontSize: 20, color: INK, fontFace: "Helvetica" });
}

// --- Slide 11: Deployment ---
{
  const s = bgSlide("Deployment");
  const cols = [
    ["Docker Compose", "One command, fully offline demo:\ndocker compose up --build"],
    ["Render + Vercel", "Live public URL — backend on Render,\nfrontend on Vercel, split hosting"],
    ["Single VPS", "Same Docker images behind\nnginx/Caddy for a custom domain"],
  ];
  cols.forEach(([title, desc], i) => {
    const x = 0.6 + i * 4.1;
    s.addShape("roundRect", { x, y: 1.4, w: 3.8, h: 3.2, fill: { color: WHITE }, line: { color: "E3E0D6", width: 1 }, rectRadius: 0.1 });
    s.addText(title, { x: x + 0.25, y: 1.6, w: 3.3, h: 0.6, fontSize: 17, bold: true, color: EMERALD });
    s.addText(desc, { x: x + 0.25, y: 2.3, w: 3.3, h: 2.0, fontSize: 13, color: INK });
  });
  s.addText("ML models are pre-trained and shipped inside the Docker image — zero setup steps before the app is fully functional.", { x: 0.6, y: 5.0, w: 12.1, h: 0.8, fontSize: 14, italics: true, color: GREY, align: "center" });
}

// --- Slide 12: Future Scope ---
{
  const s = bgSlide("Future Scope");
  const items = [
    "Re-train and validate the fraud model on real labelled fraud data",
    "React Native mobile app reusing the same REST API",
    "Multi-item receipt parsing (split one bill into several transactions)",
    "Bank statement (CSV/PDF) bulk import",
    "Shared/family budgets with per-member visibility controls",
  ];
  s.addText(items.map((t) => ({ text: t, options: { bullet: { code: "2192", color: AMBER }, breakLine: true, paraSpaceAfter: 18 } })),
    { x: 0.7, y: 1.3, w: 11.9, h: 5.5, fontSize: 20, color: INK, fontFace: "Helvetica" });
}

// --- Slide 13: Thank you ---
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addText("Thank You", { x: 0.8, y: 2.8, w: 11.7, h: 1.2, fontSize: 48, bold: true, color: WHITE, fontFace: "Georgia" });
  s.addText("Questions?", { x: 0.8, y: 3.9, w: 11.7, h: 0.6, fontSize: 20, color: AMBER });
  s.addText("Full source, documentation, and deployment guide included in the project ZIP.", { x: 0.8, y: 6.8, w: 11.7, h: 0.5, fontSize: 12, color: "9AA3AE" });
}

pres.writeFile({ fileName: "FinGuard_AI_Presentation.pptx" }).then(() => console.log("pptx written"));
