import graphviz

INK = "#1B2430"
EMERALD = "#1F6F5C"
WHITE = "#FFFFFF"
LINE = "#E3E0D6"
HEADER = "#1F6F5C"

def entity(name, pk, fields):
    rows = f'<TR><TD BGCOLOR="{HEADER}"><FONT COLOR="white"><B>{name}</B></FONT></TD></TR>'
    rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10"><B>{pk}</B> (PK)</FONT></TD></TR>'
    for f in fields:
        rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">{f}</FONT></TD></TR>'
    return f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" COLOR="{LINE}">{rows}</TABLE>>'

g = graphviz.Digraph("er_diagram", format="png")
g.attr(rankdir="LR", bgcolor=WHITE, fontname="Helvetica", nodesep="0.6", ranksep="0.9")
g.attr("node", shape="plain", fontname="Helvetica")
g.attr("edge", fontname="Helvetica", fontsize="9", color=INK, arrowsize="0.7", fontcolor=INK)

g.node("users", entity("users", "id", ["full_name", "email (unique)", "password_hash", "is_admin", "is_active", "created_at"]))
g.node("categories", entity("categories", "id", ["name (unique)", "icon", "is_income"]))
g.node("transactions", entity("transactions", "id", ["user_id (FK)", "category_id (FK)", "amount", "merchant", "description", "txn_date", "is_flagged", "fraud_score", "created_at"]))
g.node("budgets", entity("budgets", "id", ["user_id (FK)", "category_id (FK)", "month", "limit_amount"]))
g.node("fraud_logs", entity("fraud_logs", "id", ["transaction_id (FK)", "user_id (FK)", "score", "reason", "reviewed", "created_at"]))
g.node("ai_suggestions", entity("ai_suggestions", "id", ["user_id (FK)", "kind", "message", "created_at"]))
g.node("receipt_scans", entity("receipt_scans", "id", ["user_id (FK)", "original_filename", "raw_text", "parsed_amount", "parsed_merchant", "parsed_date", "suggested_category_id (FK)", "confidence", "resulting_transaction_id (FK)"]))

g.edge("users", "transactions", label="1 to many")
g.edge("categories", "transactions", label="1 to many")
g.edge("users", "budgets", label="1 to many")
g.edge("categories", "budgets", label="1 to many")
g.edge("transactions", "fraud_logs", label="1 to many")
g.edge("users", "fraud_logs", label="1 to many")
g.edge("users", "ai_suggestions", label="1 to many")
g.edge("users", "receipt_scans", label="1 to many")
g.edge("categories", "receipt_scans", label="1 to many (suggested)", style="dashed")
g.edge("transactions", "receipt_scans", label="1 to 1 (resulting)", style="dashed")

g.render("er_diagram", cleanup=True)
print("done")
