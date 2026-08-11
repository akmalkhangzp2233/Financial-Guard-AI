import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

INK = "#1B2430"
EMERALD = "#1F6F5C"
AMBER = "#C98A2C"
ALERT = "#C4453A"
LINE = "#E3E0D6"

def draw_sequence(actors, messages, title, filename, figsize=(11, 7)):
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    n = len(actors)
    xs = {name: (i + 1) * (10 / (n + 1)) for i, name in enumerate(actors)}
    top = len(messages) + 1.5

    # Lifeline headers + dashed lines
    for name, x in xs.items():
        ax.add_patch(mpatches.FancyBboxPatch((x - 0.9, top - 0.4), 1.8, 0.6,
                     boxstyle="round,pad=0.02", linewidth=1.2, edgecolor=INK, facecolor="#EFF4F1"))
        ax.text(x, top - 0.1, name, ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
        ax.plot([x, x], [top - 0.4, 0.3], linestyle="--", color=LINE, linewidth=1.2, zorder=0)

    # Messages, drawn top-down
    y = top - 1.1
    for frm, to, label, style in messages:
        x1, x2 = xs[frm], xs[to]
        color = {"call": INK, "return": EMERALD, "alert": ALERT, "external": AMBER}.get(style, INK)
        arrow_style = "-|>" if style != "return" else "-|>"
        linestyle = "dashed" if style == "return" else "solid"
        if x1 == x2:
            # self-call loop
            ax.annotate("", xy=(x1 + 0.6, y - 0.3), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4, connectionstyle="arc3,rad=-1.2"))
            ax.text(x1 + 0.75, y - 0.15, label, fontsize=8.5, color=color, va="center")
        else:
            arrow = FancyArrowPatch((x1, y), (x2, y), arrowstyle=arrow_style, mutation_scale=14,
                                     color=color, linewidth=1.4, linestyle=linestyle)
            ax.add_patch(arrow)
            mid = (x1 + x2) / 2
            ax.text(mid, y + 0.15, label, fontsize=8.5, color=color, ha="center", va="bottom")
        y -= 1.0

    ax.set_xlim(0, 10)
    ax.set_ylim(0, top + 0.3)
    ax.axis("off")
    ax.set_title(title, fontsize=13, fontweight="bold", color=INK, pad=14, fontfamily="serif")
    fig.tight_layout()
    fig.savefig(filename, facecolor="white")
    plt.close(fig)
    print(f"wrote {filename}")


# --- Sequence 1: Add transaction with fraud check ---
actors1 = ["User\n(Browser)", "React SPA", "FastAPI\n/transactions", "ML Service", "Database"]
messages1 = [
    ("User\n(Browser)", "React SPA", "Fill form, submit", "call"),
    ("React SPA", "FastAPI\n/transactions", "POST /transactions/\n(JWT + amount, category, date)", "call"),
    ("FastAPI\n/transactions", "ML Service", "score_transaction(amount, category)", "call"),
    ("ML Service", "ML Service", "Isolation Forest\n.decision_function()", "call"),
    ("ML Service", "FastAPI\n/transactions", "fraud_score, is_flagged, reason", "return"),
    ("FastAPI\n/transactions", "Database", "INSERT transaction\n(+ fraud_log if flagged)", "call"),
    ("Database", "FastAPI\n/transactions", "saved row", "return"),
    ("FastAPI\n/transactions", "React SPA", "200 OK — TransactionOut", "return"),
    ("React SPA", "User\n(Browser)", "Dashboard refreshes,\nalert shown if flagged", "return"),
]
draw_sequence(actors1, messages1, "Sequence Diagram — Add Transaction with Real-Time Fraud Check",
              "sequence_transaction_fraud.png", figsize=(12, 8))

# --- Sequence 2: OCR receipt scan flow ---
actors2 = ["User\n(Browser)", "React SPA", "FastAPI\n/ocr", "Tesseract\nOCR Engine", "Database"]
messages2 = [
    ("User\n(Browser)", "React SPA", "Upload receipt photo", "call"),
    ("React SPA", "FastAPI\n/ocr", "POST /ocr/scan-receipt\n(multipart image)", "call"),
    ("FastAPI\n/ocr", "FastAPI\n/ocr", "Preprocess image\n(grayscale, contrast, sharpen)", "call"),
    ("FastAPI\n/ocr", "Tesseract\nOCR Engine", "image_to_string(image)", "external"),
    ("Tesseract\nOCR Engine", "FastAPI\n/ocr", "raw extracted text", "return"),
    ("FastAPI\n/ocr", "FastAPI\n/ocr", "Regex parse: amount,\nmerchant, date + category match", "call"),
    ("FastAPI\n/ocr", "Database", "INSERT receipt_scans\n(audit trail)", "call"),
    ("FastAPI\n/ocr", "React SPA", "200 OK — parsed draft\n(editable, not yet saved)", "return"),
    ("React SPA", "User\n(Browser)", "Show pre-filled form\nfor confirmation", "return"),
    ("User\n(Browser)", "React SPA", "Confirm / edit, submit", "call"),
    ("React SPA", "FastAPI\n/ocr", "POST /transactions/\n+ link scan to transaction", "call"),
]
draw_sequence(actors2, messages2, "Sequence Diagram — OCR Bill Scanner (Scan \u2192 Confirm \u2192 Save)",
              "sequence_ocr_scan.png", figsize=(12, 9))
