"""Zero-cost starter system for AI-assisted online business operations.

The agents are intentionally approval-first: they research and prepare work, but
never send outreach, place orders, or spend money without a human decision.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_FILE = Path("business_data.json")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {"created_at": now(), "leads": [], "suppliers": [], "offers": [], "content": []}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_data(data: dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class AIClient:
    """Optional OpenAI-compatible client; the local fallback keeps the MVP usable."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, instruction: str) -> str:
        if not self.api_key:
            return ""
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a concise business operations assistant."},
                {"role": "user", "content": instruction},
            ],
            "temperature": 0.4,
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"AI provider request failed: {exc}") from exc


@dataclass
class Lead:
    company: str
    website: str
    problem: str
    status: str = "needs_review"
    source: str = "manual"
    created_at: str = ""


@dataclass
class Supplier:
    name: str
    url: str
    product: str
    unit_cost: str
    shipping: str
    notes: str
    status: str = "needs_review"


class MarketResearchAgent:
    def run(self, niche: str, ai: AIClient) -> dict[str, Any]:
        prompt = (
            f"Create 5 specific, urgent problems that {niche} businesses have and "
            "map each to a service or digital product they could buy. Return a numbered list."
        )
        generated = ai.complete(prompt)
        return {"agent": "market_research", "niche": niche, "result": generated or (
            f"1. Inconsistent content -> monthly content system\n"
            f"2. Slow lead response -> FAQ and follow-up automation\n"
            f"3. Weak offers -> landing-page and offer rewrite\n"
            f"4. Manual admin -> spreadsheet workflow\n"
            f"5. No reporting -> weekly KPI dashboard"
        ), "created_at": now()}


class OfferAgent:
    def run(self, service: str, ai: AIClient) -> dict[str, Any]:
        prompt = f"Design a simple fixed-scope English offer for small businesses: {service}. Include deliverables, timeframe, price test, and guarantee limits."
        generated = ai.complete(prompt)
        return {"agent": "offer", "service": service, "result": generated or (
            f"{service} Starter: audit, implementation checklist, and 7-day support. "
            "Test price: $149-$299. Delivery: 3 business days. No guaranteed revenue claims."
        ), "created_at": now()}


class ContentAgent:
    def run(self, offer: str, ai: AIClient) -> list[dict[str, Any]]:
        prompt = f"Write 3 short LinkedIn posts and 1 cold email draft for this offer: {offer}. Use ethical, personalized outreach and include an opt-out."
        generated = ai.complete(prompt)
        text = generated or (
            f"Post 1: Most small businesses do not need more tools; they need a clear {offer} workflow.\n"
            "Post 2: Audit one repetitive task today. If it happens weekly, document it.\n"
            "Post 3: A useful automation starts with a measurable outcome, not a chatbot.\n"
            "Email draft: Hi {{first_name}}, I noticed {{specific_observation}}. I help small businesses with "
            f"{offer}. Would a 15-minute fit check be useful? If not, reply 'no' and I will not follow up."
        )
        return [{"agent": "content", "offer": offer, "result": text, "status": "needs_review", "created_at": now()}]


class LeadResearchAgent:
    def run(self, companies: list[dict[str, str]]) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        for company in companies:
            lead = Lead(
                company=company["company"],
                website=company.get("website", ""),
                problem=company.get("problem", "Needs a clearer online acquisition process"),
                created_at=now(),
            )
            leads.append(asdict(lead))
        return leads


class SupplierAgent:
    def run(self, candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
        return [asdict(Supplier(
            name=item["name"],
            url=item["url"],
            product=item["product"],
            unit_cost=item.get("unit_cost", "unknown"),
            shipping=item.get("shipping", "verify"),
            notes=item.get("notes", "Verify samples, returns, taxes, delivery times, and product compliance."),
        )) for item in candidates]


class DeliveryAgent:
    def run(self, client_name: str, deliverables: list[str], ai: AIClient) -> dict[str, Any]:
        prompt = f"Create a concise delivery checklist for {client_name}: {', '.join(deliverables)}."
        return {"agent": "delivery", "client": client_name, "checklist": ai.complete(prompt) or "\n".join(
            f"[ ] {item}" for item in deliverables
        ), "status": "needs_review", "created_at": now()}


class AnalyticsAgent:
    def run(self, data: dict[str, Any]) -> dict[str, Any]:
        leads = data.get("leads", [])
        won = sum(lead.get("status") == "won" for lead in leads)
        return {
            "agent": "analytics",
            "created_at": now(),
            "metrics": {
                "leads": len(leads),
                "won_leads": won,
                "conversion_rate": round(won / len(leads), 4) if leads else 0,
                "offers": len(data.get("offers", [])),
                "supplier_candidates": len(data.get("suppliers", [])),
            },
        }


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Approval-first multi-agent business MVP")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create the local business data file")
    research = sub.add_parser("research")
    research.add_argument("--niche", default="global small businesses")
    offer = sub.add_parser("offer")
    offer.add_argument("--service", default="AI content and lead workflow setup")
    content = sub.add_parser("content")
    content.add_argument("--offer", required=True)
    leads = sub.add_parser("leads")
    leads.add_argument("--companies", required=True, help='JSON list, e.g. [{"company":"Acme","website":"https://acme.test"}]')
    suppliers = sub.add_parser("suppliers")
    suppliers.add_argument("--candidates", required=True, help='JSON list with name,url,product')
    delivery = sub.add_parser("delivery")
    delivery.add_argument("--client", required=True)
    delivery.add_argument("--items", required=True, help="Comma-separated deliverables")
    sub.add_parser("analytics")
    args = parser.parse_args()
    data = load_data()
    ai = AIClient()

    if args.command == "init":
        save_data(data)
        print(f"Initialized {DATA_FILE}")
    elif args.command == "research":
        result = MarketResearchAgent().run(args.niche, ai)
        print(json.dumps(result, indent=2))
    elif args.command == "offer":
        result = OfferAgent().run(args.service, ai)
        data["offers"].append(result)
        save_data(data)
        print(json.dumps(result, indent=2))
    elif args.command == "content":
        result = ContentAgent().run(args.offer, ai)
        data["content"].extend(result)
        save_data(data)
        print(json.dumps(result, indent=2))
    elif args.command == "leads":
        result = LeadResearchAgent().run(parse_json(args.companies))
        data["leads"].extend(result)
        save_data(data)
        print(json.dumps(result, indent=2))
    elif args.command == "suppliers":
        result = SupplierAgent().run(parse_json(args.candidates))
        data["suppliers"].extend(result)
        save_data(data)
        print(json.dumps(result, indent=2))
    elif args.command == "delivery":
        result = DeliveryAgent().run(args.client, [item.strip() for item in args.items.split(",")], ai)
        print(json.dumps(result, indent=2))
    elif args.command == "analytics":
        print(json.dumps(AnalyticsAgent().run(data), indent=2))


if __name__ == "__main__":
    main()
