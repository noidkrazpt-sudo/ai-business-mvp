"""Small dependency-free web dashboard for the AI business MVP."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent_business import AnalyticsAgent, ContentAgent, MarketResearchAgent, OfferAgent, load_data, save_data, AIClient


HOST = "127.0.0.1"
PORT = 8000


def html_page() -> str:
    data = load_data()
    metrics = AnalyticsAgent().run(data)["metrics"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>AI Business MVP</title>
<style>
body {{ font: 16px system-ui, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; color:#172033 }}
.cards {{ display:flex; flex-wrap:wrap; gap:12px }} .card {{ padding:18px; background:#eef3ff; border-radius:10px; min-width:140px }}
form {{ margin:18px 0; padding:18px; border:1px solid #d9dfeb; border-radius:10px }}
input,button {{ font:inherit; padding:9px; margin:4px }} button {{ cursor:pointer; background:#2457d6; color:white; border:0; border-radius:6px }}
pre {{ white-space:pre-wrap; background:#f6f7f9; padding:14px; border-radius:8px }}
</style></head><body>
<h1>AI Business MVP</h1><p>Approval-first dashboard for global small-business services.</p>
<div class="cards">
<div class="card"><b>Leads</b><br>{metrics["leads"]}</div>
<div class="card"><b>Won leads</b><br>{metrics["won_leads"]}</div>
<div class="card"><b>Offers</b><br>{metrics["offers"]}</div>
<div class="card"><b>Supplier candidates</b><br>{metrics["supplier_candidates"]}</div>
</div>
<form method="post" action="/run"><h2>Run an agent</h2>
<input name="agent" value="research" type="hidden"><label>Niche
<input name="niche" value="global small businesses"></label><button>Research market</button></form>
<form method="post" action="/run"><input name="agent" value="offer" type="hidden"><label>Service
<input name="service" value="AI lead follow-up setup"></label><button>Create offer</button></form>
<form method="post" action="/run"><input name="agent" value="content" type="hidden"><label>Offer
<input name="offer" value="AI lead follow-up setup"></label><button>Draft content</button></form>
<h2>Recent data</h2><pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self.send_html(html_page())
            return
        self.send_html("Not found", 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/run":
            self.send_html("Not found", 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        values = parse_qs(self.rfile.read(length).decode("utf-8"))
        agent = values.get("agent", [""])[0]
        ai = AIClient()
        if agent == "research":
            result = MarketResearchAgent().run(values.get("niche", ["global small businesses"])[0], ai)
        elif agent == "offer":
            result = OfferAgent().run(values.get("service", ["AI lead follow-up setup"])[0], ai)
            data = load_data()
            data["offers"].append(result)
            save_data(data)
        elif agent == "content":
            result = ContentAgent().run(values.get("offer", ["AI lead follow-up setup"])[0], ai)
            data = load_data()
            data["content"].extend(result)
            save_data(data)
        else:
            self.send_html("Invalid agent", 400)
            return
        self.send_html(f"<h1>Agent result</h1><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre><p><a href='/'>Back to dashboard</a></p>")


if __name__ == "__main__":
    print(f"Dashboard running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
