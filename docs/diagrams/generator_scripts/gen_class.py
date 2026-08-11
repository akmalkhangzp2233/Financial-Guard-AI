import graphviz

WHITE = "#FFFFFF"
LINE = "#E3E0D6"
HEADER = "#1B2430"

def uml_class(name, attrs, methods=None):
    rows = f'<TR><TD BGCOLOR="{HEADER}"><FONT COLOR="white"><B>{name}</B></FONT></TD></TR>'
    for a in attrs:
        rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" FACE="Courier">{a}</FONT></TD></TR>'
    if methods:
        rows += '<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="1"> </FONT></TD></TR>'
        for m in methods:
            rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" FACE="Courier" COLOR="#1F6F5C">{m}</FONT></TD></TR>'
    return f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" COLOR="{LINE}">{rows}</TABLE>>'

g = graphviz.Digraph("class_diagram", format="png")
g.attr(rankdir="TB", bgcolor=WHITE, fontname="Helvetica", nodesep="0.5", ranksep="0.7")
g.attr("node", shape="plain", fontname="Helvetica")
g.attr("edge", color=HEADER, fontname="Helvetica", fontsize="9")

g.node("User", uml_class("User", [
    "+ id: int", "+ full_name: str", "+ email: str", "+ password_hash: str",
    "+ is_admin: bool", "+ is_active: bool", "+ created_at: datetime",
], ["+ verify_password()", "+ create_access_token()"]))

g.node("Category", uml_class("Category", ["+ id: int", "+ name: str", "+ icon: str", "+ is_income: bool"]))

g.node("Transaction", uml_class("Transaction", [
    "+ id: int", "+ user_id: FK", "+ category_id: FK", "+ amount: float",
    "+ merchant: str", "+ txn_date: date", "+ is_flagged: bool", "+ fraud_score: float",
], ["+ score_transaction()"]))

g.node("Budget", uml_class("Budget", ["+ id: int", "+ user_id: FK", "+ category_id: FK", "+ month: str", "+ limit_amount: float"]))

g.node("FraudLog", uml_class("FraudLog", [
    "+ id: int", "+ transaction_id: FK", "+ user_id: FK", "+ score: float",
    "+ reason: str", "+ reviewed: bool",
]))

g.node("AISuggestion", uml_class("AISuggestion", ["+ id: int", "+ user_id: FK", "+ kind: str", "+ message: str"]))

g.node("ReceiptScan", uml_class("ReceiptScan", [
    "+ id: int", "+ user_id: FK", "+ raw_text: str", "+ parsed_amount: float",
    "+ parsed_merchant: str", "+ suggested_category_id: FK", "+ confidence: float",
], ["+ extract_amount()", "+ extract_merchant()", "+ suggest_category()"]))

g.edge("User", "Transaction", label="1..*", arrowhead="vee")
g.edge("User", "Budget", label="1..*", arrowhead="vee")
g.edge("User", "FraudLog", label="1..*", arrowhead="vee")
g.edge("User", "AISuggestion", label="1..*", arrowhead="vee")
g.edge("User", "ReceiptScan", label="1..*", arrowhead="vee")
g.edge("Category", "Transaction", label="1..*", arrowhead="vee")
g.edge("Category", "Budget", label="1..*", arrowhead="vee")
g.edge("Transaction", "FraudLog", label="1..*", arrowhead="vee")
g.edge("ReceiptScan", "Transaction", label="0..1", style="dashed", arrowhead="vee")

g.render("class_diagram", cleanup=True)
print("done")
