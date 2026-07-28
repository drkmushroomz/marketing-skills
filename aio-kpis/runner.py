#!/usr/bin/env python3
"""
aio-kpis panel runner.

Queries whatever LLM APIs have credentials in the environment against a frozen prompt
panel, then computes the AI-visibility KPIs (1-4) in-process. Raw responses stay on disk;
only a compact results JSON is emitted. KPI 5 (AI-Referred Conversions) is GA4-based and
lives outside this runner (see SKILL.md).

Providers activate only when their key is present, so this never scans secrets:
  gemini      GEMINI_API_KEY or GOOGLE_API_KEY (google.genai, Google Search grounding),
              or Vertex via GOOGLE_GENAI_USE_VERTEXAI=true + GOOGLE_CLOUD_PROJECT + ADC
  perplexity  PERPLEXITY_API_KEY
  openai      OPENAI_API_KEY (Responses API web_search tool)

Usage:
  python runner.py --panel jinx --providers gemini,perplexity
  python runner.py --panel jinx --list-providers
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PANELS = BASE / "panels"
for sub in ("results", "history", "cache"):
    (BASE / sub).mkdir(exist_ok=True)


# ------------------------------------------------------------------ panel + helpers
def load_panel(name):
    path = PANELS / f"{name}.json"
    if not path.exists():
        sys.exit(f"panel not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def today():
    # Date is passed in from the caller in scheduled use; default to system date here.
    return _dt.date.today().isoformat()


def brand_terms(panel):
    """Word-boundary regex for the client's brand names."""
    names = {panel["meta"]["client"], "Jinx"}
    dom = panel["meta"].get("domain", "")
    pats = [re.escape(n) for n in names if n]
    return re.compile(r"\b(" + "|".join(pats) + r")\b", re.IGNORECASE), dom


COMP_ALIASES = {
    "Purina Pro Plan": ["purina pro plan", "pro plan", "purina"],
    "Blue Buffalo": ["blue buffalo", "blue wilderness", "bluebuffalo"],
    "Open Farm": ["open farm", "openfarm"],
    "Stella & Chewy's": ["stella & chewy", "stella and chewy", "stella chewy"],
    "Nulo": ["nulo"],
    "The Farmer's Dog": ["farmer's dog", "farmers dog", "the farmer's dog"],
    "Ollie": ["ollie"],
}


def competitor_matchers(panel):
    comp = panel["meta"].get("sov_competitor_set", {})
    names = list(comp.get("head_to_head", [])) + list(comp.get("fresh_benchmark_context_only", []))
    out = {}
    for n in names:
        aliases = COMP_ALIASES.get(n, [n.lower()])
        out[n] = re.compile(r"\b(" + "|".join(re.escape(a) for a in aliases) + r")\b", re.IGNORECASE)
    return out


REC_CUE = re.compile(
    r"\b(recommend|best|top pick|top choice|great option|solid option|worth|"
    r"i'd (go|suggest)|standout|excellent|favorite|go with|our pick)\b",
    re.IGNORECASE,
)


def classify(text, citations, brand_re, owned_domain, comp_res):
    text = text or ""
    hosts = " ".join(citations).lower()
    mention = bool(brand_re.search(text))
    # recommendation: brand named AND a recommendation cue within ~140 chars of a hit
    rec = False
    if mention:
        for m in brand_re.finditer(text):
            window = text[max(0, m.start() - 140): m.end() + 140]
            if REC_CUE.search(window):
                rec = True
                break
    owned_cited = bool(owned_domain) and (owned_domain.lower() in hosts or owned_domain.lower() in text.lower())
    any_citation = len(citations) > 0
    comps = [name for name, rx in comp_res.items() if rx.search(text)]
    return {
        "mention": mention,
        "recommend": rec,
        "owned_cited": owned_cited,
        "any_citation": any_citation,
        "competitor_mentions": comps,
    }


# ------------------------------------------------------------------ providers
def provider_gemini(prompt):
    from google import genai
    from google.genai import types

    client = genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY, or Vertex env + ADC
    resp = client.models.generate_content(
        model=os.environ.get("AIO_GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.0,
        ),
    )
    text = resp.text or ""
    cites = []
    try:
        gm = resp.candidates[0].grounding_metadata
        for ch in (gm.grounding_chunks or []):
            if ch.web:
                cites.append(ch.web.uri or "")
                if ch.web.title:
                    cites.append(ch.web.title)  # title is often the bare domain
    except Exception:
        pass
    return text, [c for c in cites if c]


def provider_perplexity(prompt):
    import httpx

    key = os.environ["PERPLEXITY_API_KEY"]
    r = httpx.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": os.environ.get("AIO_PPLX_MODEL", "sonar"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        },
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    cites = data.get("citations") or []
    if not cites:
        cites = [s.get("url", "") for s in data.get("search_results", []) if s.get("url")]
    return text, cites


def provider_openai(prompt):
    import httpx

    key = os.environ["OPENAI_API_KEY"]
    r = httpx.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": os.environ.get("AIO_OPENAI_MODEL", "gpt-4o"),
            "tools": [{"type": "web_search_preview"}],
            "input": prompt,
        },
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    text, cites = "", []
    for item in data.get("output", []):
        for c in item.get("content", []) or []:
            if c.get("type") in ("output_text", "text"):
                text += c.get("text", "")
                for ann in c.get("annotations", []) or []:
                    if ann.get("url"):
                        cites.append(ann["url"])
    if not text:
        text = data.get("output_text", "")
    return text, cites


PROVIDERS = {
    "gemini": {"key_env": ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "fn": provider_gemini},
    "perplexity": {"key_env": ("PERPLEXITY_API_KEY",), "fn": provider_perplexity},
    "openai": {"key_env": ("OPENAI_API_KEY",), "fn": provider_openai},
}


def active_providers(requested):
    active = []
    for name in requested:
        spec = PROVIDERS.get(name)
        if not spec:
            print(f"  unknown provider: {name}", file=sys.stderr)
            continue
        vertex = name == "gemini" and os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
        has_key = any(os.environ.get(k) for k in spec["key_env"]) or vertex
        if has_key:
            active.append(name)
        else:
            print(f"  {name}: skipped (no credential in env: {', '.join(spec['key_env'])})", file=sys.stderr)
    return active


# ------------------------------------------------------------------ cache + KPIs
def cache_path(panel_name, provider, date):
    return BASE / "cache" / f"{panel_name}_{provider}_{date}.jsonl"


def load_cache(path):
    seen = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                seen[row["pid"]] = row
    return seen


def grade(n, providers):
    if n >= 300 and providers >= 3:
        return "A"
    if n >= 120 and providers >= 2:
        return "B"
    if n >= 40:
        return "C"
    return "D"


def run(panel_name, requested, date):
    panel = load_panel(panel_name)
    brand_re, owned = brand_terms(panel)
    comp_res = competitor_matchers(panel)
    qualified = [p for p in panel["prompts"] if p.get("qualified")]

    providers = active_providers(requested)
    if not providers:
        sys.exit("no active providers (set GEMINI_API_KEY / PERPLEXITY_API_KEY / OPENAI_API_KEY).")
    print(f"active providers: {', '.join(providers)}", file=sys.stderr)

    records = []
    for provider in providers:
        cpath = cache_path(panel_name, provider, date)
        cached = load_cache(cpath)
        with cpath.open("a", encoding="utf-8") as cf:
            for p in qualified:
                pid = p["id"]
                if pid in cached:
                    row = cached[pid]
                else:
                    try:
                        text, cites = PROVIDERS[provider]["fn"](p["prompt"])
                    except Exception as e:  # noqa: BLE001
                        print(f"  {provider}/{pid} failed: {e}", file=sys.stderr)
                        continue
                    cls = classify(text, cites, brand_re, owned, comp_res)
                    row = {"pid": pid, "provider": provider, "weight": p["weight"],
                           "bucket": p["intent_bucket"], **cls}
                    cf.write(json.dumps(row) + "\n")
                records.append(row)

    # aggregate
    n = len(records)
    wsum = sum(r["weight"] for r in records) or 1
    wmention = sum(r["weight"] for r in records if r["mention"])
    qav = 100 * wmention / wsum

    brand_mentions = sum(1 for r in records if r["mention"])
    comp_mentions = sum(len(r["competitor_mentions"]) for r in records)
    sov = 100 * brand_mentions / (brand_mentions + comp_mentions) if (brand_mentions + comp_mentions) else 0.0

    rec_rate = 100 * sum(1 for r in records if r["recommend"]) / n if n else 0.0

    cited_responses = [r for r in records if r["any_citation"]]
    owned_rate = 100 * sum(1 for r in cited_responses if r["owned_cited"]) / len(cited_responses) if cited_responses else 0.0

    g = grade(n, len(providers))
    result = {
        "client": panel["meta"]["client"],
        "domain": panel["meta"].get("domain"),
        "date": date,
        "panel_version": panel["meta"].get("panel_version"),
        "providers": providers,
        "sample_size": n,
        "reliability_grade": g,
        "modeled": True,
        "kpis": {
            "qualified_ai_visibility_pct": round(qav, 1),
            "competitive_share_of_voice_pct": round(sov, 1),
            "ai_recommendation_rate_pct": round(rec_rate, 1),
            "owned_citation_rate_pct": round(owned_rate, 1),
        },
        "detail": {
            "brand_mentions": brand_mentions,
            "competitor_mentions": comp_mentions,
            "cited_responses": len(cited_responses),
            "weighted_mentions": round(wmention, 1),
            "weighted_total": round(wsum, 1),
        },
        "note": "Modeled from our own panel run, not observed platform impressions. "
                "Recommendation Rate uses a heuristic classifier; treat as directional.",
    }

    out = BASE / "results" / f"{panel_name}_{date}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (BASE / "history" / f"{panel_name}.jsonl").open("a", encoding="utf-8") as hf:
        hf.write(json.dumps({"date": date, "grade": g, "n": n, **result["kpis"]}) + "\n")

    print(json.dumps(result, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="jinx")
    ap.add_argument("--providers", default="gemini,perplexity,openai")
    ap.add_argument("--date", default=today())
    ap.add_argument("--list-providers", action="store_true")
    args = ap.parse_args()

    requested = [p.strip() for p in args.providers.split(",") if p.strip()]
    if args.list_providers:
        act = active_providers(requested)
        print("active:", ", ".join(act) if act else "(none)")
        return
    run(args.panel, requested, args.date)


if __name__ == "__main__":
    main()
