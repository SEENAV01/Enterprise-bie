"""Task 038 live AI runner: probe keys and models, smoke-test each provider, or run the blind test.

  --mode probe       list the models each configured key can use (no generation, no cost)
  --mode smoke       one tiny structured request per provider (proves key + model + schema path)
  --mode blind-test  one chapter PDF → lesson plan, narration script, 5 questions per provider

Keys come only from environment variables (GitHub Actions secrets in CI). Outputs go to --out:
SUMMARY.json (no generated content; also printed as ::notice annotations), LEDGER.jsonl, and for the
blind test REPORT.md, RESULTS.json (content by letter) and KEY.json (letter → provider, cost).
--fake runs everything offline through the deterministic fake provider.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.model_gateway.live import blind_test  # noqa: E402
from bie.model_gateway.live.config import PROVIDERS, build_routes, key_for, make_client, model_for  # noqa: E402
from bie.model_gateway.live.disk_cache import DiskCache  # noqa: E402
from bie.model_gateway.live.errors import ProviderError, redact  # noqa: E402
from bie.model_gateway.live.fake_client import FakeProviderClient  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.live.ledger import UsageLedger  # noqa: E402
from bie.model_gateway.model_interface import ModelRequest  # noqa: E402

MAX_PDF_BYTES = 50 * 1024 * 1024
SMOKE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["status", "language"],
                "properties": {"status": {"type": "string", "enum": ["ready"]}, "language": {"type": "string"}}}


def notice(title, message, level="notice"):
    clean = str(message).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    title = str(title).replace("%", "%25").replace(":", "%3A").replace(",", "%2C")
    print(f"::{level} title={title}::{clean[:3500]}", flush=True)


def secrets_in_env():
    return [key_for(p) for p in PROVIDERS if key_for(p)]


def read_source(source: str) -> bytes:
    if source.startswith("https://"):
        request = urllib.request.Request(source, headers={"user-agent": "bie-blind-test/1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read(MAX_PDF_BYTES + 1)
    elif "://" in source:
        raise SystemExit("SOURCE_URL_MUST_BE_HTTPS")
    else:
        path = (ROOT / source).resolve() if not Path(source).is_absolute() else Path(source)
        data = path.read_bytes()
    if len(data) > MAX_PDF_BYTES:
        raise SystemExit("SOURCE_TOO_LARGE")
    if not data.startswith(b"%PDF"):
        raise SystemExit("SOURCE_IS_NOT_A_PDF")
    return data


def probe(providers, fake):
    out = {}
    for provider in providers:
        key = key_for(provider)
        if fake:
            client = FakeProviderClient(provider)
        elif not key:
            out[provider] = {"status": "not_configured"}
            continue
        else:
            client = make_client(provider, key, timeout=60)
        try:
            models = client.list_models()
        except ProviderError as exc:
            out[provider] = {"status": "failed", "error_kind": exc.kind, "error": str(exc)[:300]}
            continue
        wanted = model_for(provider)
        out[provider] = {"status": "ok", "configured_model": wanted, "configured_model_available": wanted in models,
                         "model_count": len(models), "models": models}
    return out


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("probe", "smoke", "blind-test"), required=True)
    parser.add_argument("--providers", default=",".join(PROVIDERS))
    parser.add_argument("--out", required=True)
    parser.add_argument("--fake", action="store_true", help="offline deterministic fake providers")
    parser.add_argument("--source", help="chapter PDF: repository path or https URL")
    parser.add_argument("--pages", help="page range inside the PDF, for example 3-14")
    parser.add_argument("--class-level", default="Class 8")
    parser.add_argument("--language", default="English")
    parser.add_argument("--subject", default="")
    parser.add_argument("--cache-dir", help="optional response cache directory")
    parser.add_argument("--seed", type=int, help="fixed letter order (tests only)")
    args = parser.parse_args(argv)

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = sorted(set(providers) - set(PROVIDERS))
    if unknown:
        raise SystemExit("UNKNOWN_PROVIDERS:" + ",".join(unknown))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    keys = secrets_in_env()
    summary = {"mode": args.mode, "fake": args.fake, "providers": providers, "evidence_kind": "TECHNICAL_RUN",
               "product_accepted": False}
    try:
        if args.mode == "probe":
            result = probe(providers, args.fake)
            summary["probe"] = result
            write_json(out / "PROBE.json", result)
            for provider, item in result.items():
                if item["status"] == "ok":
                    names = [m for m in item["models"] if any(t in m for t in ("claude", "gpt", "o3", "o4", "gemini", "fake"))]
                    notice(f"probe {provider}", f"configured {item['configured_model']} available={item['configured_model_available']}; "
                                                 f"{item['model_count']} models: " + ", ".join(names[:120]))
                else:
                    notice(f"probe {provider}", json.dumps(item), "warning")
            ok = any(item["status"] == "ok" for item in result.values())
            summary["passed"] = ok
            return 0 if ok else 1

        routes, missing = build_routes(providers, fake=args.fake, timeout=600 if args.mode == "blind-test" else 120)
        summary["not_configured"] = missing
        for provider in missing:
            notice(f"{args.mode} {provider}", "no API key secret is set for this provider", "warning")
        if not routes:
            summary["passed"] = False
            notice(args.mode, "no provider is configured", "error")
            return 1
        ledger = UsageLedger(out / "LEDGER.jsonl")
        cache = DiskCache(args.cache_dir) if args.cache_dir else None
        gateway = LiveGateway(routes, ledger=ledger, cache=cache)

        if args.mode == "smoke":
            results = {}
            for route in routes:
                request = ModelRequest(request_id=f"smoke-{route}", messages=(
                    {"role": "system", "content": "You are a health check. Answer with JSON only."},
                    {"role": "user", "content": "Set status to ready and language to the name of the language of this sentence."}),
                    response_schema=SMOKE_SCHEMA)
                try:
                    response = gateway.complete(route, request, prompt_version="bie-smoke/1")
                    results[route] = {"status": "ok", "model": response.model,
                                      "returned_model": response.provenance.get("returned_model"), "content": response.content}
                except ProviderError as exc:
                    results[route] = {"status": "failed", "model": gateway.model_of(route), "error_kind": exc.kind, "error": str(exc)[:300]}
            summary["smoke"] = results
            summary["usage"] = ledger.summary()
            for route, item in results.items():
                notice(f"smoke {route}", json.dumps({**item, "usage": summary["usage"].get(route)}),
                       "notice" if item["status"] == "ok" else "error")
            summary["passed"] = all(item["status"] == "ok" for item in results.values()) and not missing
            return 0 if summary["passed"] else 1

        if not args.source:
            raise SystemExit("BLIND_TEST_NEEDS_SOURCE")
        chapter = blind_test.chapter_from_pdf(read_source(args.source), pages=args.pages)
        summary["chapter"] = {"source_sha256": chapter.source_sha256, "page_count": chapter.page_count,
                              "pages_used": [chapter.pages_used[0], chapter.pages_used[-1]], "chars": chapter.chars,
                              "text_sample": chapter.text[:240]}
        notice("blind-test chapter", json.dumps(summary["chapter"], ensure_ascii=False))
        results = blind_test.run(gateway, chapter, class_level=args.class_level, language=args.language, subject=args.subject)
        by_letter, key = blind_test.anonymise(results, seed=args.seed)
        report = blind_test.render_report(by_letter, chapter=chapter, class_level=args.class_level,
                                          language=args.language, subject=args.subject)
        (out / "REPORT.md").write_text(report, encoding="utf-8")
        write_json(out / "RESULTS.json", {"prompt_version": blind_test.PROMPT_VERSION, "class_level": args.class_level,
                                          "language": args.language, "subject": args.subject, "chapter": summary["chapter"],
                                          "options": by_letter})
        costs = blind_test.cost_summary(key, ledger.summary())
        write_json(out / "KEY.json", {"letters": key, "costs": costs})
        summary["providers_ok"] = sorted(p for p, r in results.items() if r["status"] == "ok")
        summary["providers_failed"] = {p: r["error_kind"] for p, r in results.items() if r["status"] != "ok"}
        summary["usage"] = ledger.summary()
        for provider, item in results.items():
            info = {"status": item["status"], "model": item["model"], "usage": summary["usage"].get(provider)}
            if item["status"] != "ok":
                info["error"] = item["error"]
            notice(f"blind-test {provider}", json.dumps(info), "notice" if item["status"] == "ok" else "error")
        summary["passed"] = not summary["providers_failed"] and not missing
        return 0 if summary["passed"] else 1
    except (ProviderError, ValueError, OSError) as exc:
        summary["passed"] = False
        summary["failure"] = redact(f"{type(exc).__name__}: {exc}", keys)[:600]
        notice(f"{args.mode} failure", summary["failure"], "error")
        return 1
    finally:
        write_json(out / "SUMMARY.json", json.loads(redact(json.dumps(summary, ensure_ascii=False), keys)))


if __name__ == "__main__":
    raise SystemExit(main())
