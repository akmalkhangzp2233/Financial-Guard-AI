import graphviz

INK = "#1B2430"
EMERALD = "#1F6F5C"
AMBER = "#C98A2C"
WHITE = "#FFFFFF"
IVORY = "#FBFAF6"
LINE = "#E3E0D6"

g = graphviz.Digraph("use_case_diagram", format="png")
g.attr(rankdir="LR", bgcolor=WHITE, fontname="Helvetica", nodesep="0.35", ranksep="1.1")
g.attr("edge", color=INK, arrowhead="none", fontname="Helvetica", fontsize="9")

g.node("user", "User", shape="plaintext", fontname="Helvetica", fontsize="12", fontcolor=INK,
       image="", width="0.6")
g.node("admin", "Admin", shape="plaintext", fontname="Helvetica", fontsize="12", fontcolor=INK)

g.attr("node", shape="ellipse", style="filled", fontname="Helvetica", fontsize="10", fontcolor=INK,
       color=LINE, penwidth="1.2")

user_cases = [
    "uc_register", "uc_login", "uc_dashboard", "uc_add_txn", "uc_scan_receipt",
    "uc_set_budget", "uc_view_fraud", "uc_ai_tips", "uc_export_own",
]
labels = {
    "uc_register": "Register account",
    "uc_login": "Login",
    "uc_dashboard": "View dashboard\n& spend summary",
    "uc_add_txn": "Add transaction\n(manual)",
    "uc_scan_receipt": "Scan receipt (OCR)\n& confirm transaction",
    "uc_set_budget": "Set monthly\nbudget",
    "uc_view_fraud": "View fraud\nalerts",
    "uc_ai_tips": "Get AI\nsavings tips",
    "uc_export_own": "Export own\ntransactions (CSV)",
}
for uc in user_cases:
    g.node(uc, labels[uc], fillcolor=IVORY)
    g.edge("user", uc)

admin_cases = ["uc_manage_users", "uc_review_fraud", "uc_platform_stats", "uc_export_all"]
labels_admin = {
    "uc_manage_users": "Manage users\n(enable/disable, promote)",
    "uc_review_fraud": "Review flagged\ntransactions",
    "uc_platform_stats": "View platform-wide\nstatistics",
    "uc_export_all": "Export all\ntransactions (CSV)",
}
for uc in admin_cases:
    g.node(uc, labels_admin[uc], fillcolor="#F6E9DC")
    g.edge("admin", uc)

# Admin inherits User use cases too (is-a relationship)
g.edge("admin", "user", arrowhead="empty", style="dashed", label="  extends", constraint="false")

g.render("use_case_diagram", cleanup=True)
print("done")
