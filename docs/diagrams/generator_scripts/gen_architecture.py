import graphviz

INK = "#1B2430"
EMERALD = "#1F6F5C"
AMBER = "#C98A2C"
ALERT = "#C4453A"
IVORY = "#FBFAF6"
LINE = "#E3E0D6"
WHITE = "#FFFFFF"

g = graphviz.Digraph("architecture", format="png")
g.attr(rankdir="TB", bgcolor=WHITE, fontname="Helvetica", nodesep="0.4", ranksep="0.55", splines="ortho")
g.attr("node", fontname="Helvetica", fontsize="11", style="filled", color=LINE, penwidth="1.2")
g.attr("edge", fontname="Helvetica", fontsize="9", color=INK, arrowsize="0.7")

# --- Client layer ---
with g.subgraph(name="cluster_client") as c:
    c.attr(label="CLIENT LAYER", fontsize="12", fontcolor=INK, style="rounded", color=LINE, bgcolor=IVORY, labeljust="l")
    c.node("browser", "React SPA\n(Vite + Tailwind)\nhosted on Vercel / Nginx", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")

# --- API layer ---
with g.subgraph(name="cluster_api") as c:
    c.attr(label="APPLICATION LAYER — FastAPI (Docker container)", fontsize="12", fontcolor=INK, style="rounded", color=LINE, bgcolor="#EFF4F1", labeljust="l")
    c.node("gateway", "CORS + Rate Limiting +\nSecurity Headers Middleware", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")
    c.node("auth", "Auth Service\n(JWT + bcrypt)", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")
    c.node("txn", "Transaction &\nBudget Service", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")
    c.node("ocr", "OCR Service\n(Tesseract)", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")
    c.node("ml", "ML Service\n(Fraud + Forecast)", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")
    c.node("ai", "AI Advice Service\n(GPT + rule fallback)", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")
    c.node("admin", "Admin & Reports\nService", fillcolor=WHITE, fontcolor=INK, shape="box", style="filled,rounded")

# --- Data layer ---
with g.subgraph(name="cluster_data") as c:
    c.attr(label="DATA LAYER", fontsize="12", fontcolor=INK, style="rounded", color=LINE, bgcolor="#F6F0E4", labeljust="l")
    c.node("db", "SQLite / PostgreSQL\n(users, transactions, budgets,\nfraud_logs, receipt_scans)", fillcolor=WHITE, fontcolor=INK, shape="cylinder", style="filled")
    c.node("models", "Trained model files\n(fraud_isolation_forest.pkl\nexpense_forecaster.pkl)", fillcolor=WHITE, fontcolor=INK, shape="folder", style="filled")

# --- External services ---
with g.subgraph(name="cluster_ext") as c:
    c.attr(label="EXTERNAL SERVICES", fontsize="12", fontcolor=INK, style="rounded", color=LINE, bgcolor="#F7EAE8", labeljust="l")
    c.node("openai", "OpenAI GPT API\n(optional)", fillcolor=WHITE, fontcolor=ALERT, shape="box", style="filled,rounded")

g.edge("browser", "gateway", label="HTTPS / REST + JWT")
g.edge("gateway", "auth")
g.edge("gateway", "txn")
g.edge("gateway", "ocr")
g.edge("gateway", "ml")
g.edge("gateway", "ai")
g.edge("gateway", "admin")

g.edge("auth", "db")
g.edge("txn", "db")
g.edge("admin", "db")
g.edge("ocr", "txn", style="dashed", label="parsed draft")
g.edge("ml", "models")
g.edge("ml", "db")
g.edge("ai", "openai", label="HTTPS", color=ALERT, fontcolor=ALERT)
g.edge("ai", "db")

g.render("architecture", cleanup=True)
print("architecture.png written")
