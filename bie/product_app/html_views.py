"""Accessible server-rendered fragments for bounded Section 18 views."""
from html import escape
def source_validation_html(view):
    status=escape(str(view.get("status","UNKNOWN")));errors=view.get("errors") or [];items="".join(f"<li>{escape(str(x))}</li>" for x in errors)
    return '<section aria-labelledby="source-validation-heading"><h2 id="source-validation-heading">Source validation</h2>'+f'<p role="status" data-status="{status}">{status}</p>'+f'<ul aria-label="Validation messages">{items}</ul></section>'
def graph_html(title,graph):
    nodes="".join(f'<li data-node-id="{escape(n["id"])}"><strong>{escape(n["label"])}</strong> <span>Sources: {escape(", ".join(n["source_refs"]))}</span></li>' for n in graph["nodes"])
    edges="".join(f'<li>{escape(e["source"])} → {escape(e["target"])}: {escape(e["relation"])} <span>Evidence: {escape(", ".join(e["evidence_refs"]))}</span></li>' for e in graph["edges"])
    return '<section class="bie-graph" aria-labelledby="graph-heading">'+f'<h2 id="graph-heading">{escape(title)}</h2><p>{len(graph["nodes"])} nodes, {len(graph["edges"])} edges</p><h3>Nodes</h3><ul>{nodes}</ul><h3>Relations</h3><ul>{edges}</ul></section>'
