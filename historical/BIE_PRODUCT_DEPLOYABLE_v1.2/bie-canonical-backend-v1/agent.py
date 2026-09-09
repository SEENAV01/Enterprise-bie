from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

try:
    from agents import Agent, Runner, function_tool
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    Agent = Runner = None  # type: ignore
    function_tool = None  # type: ignore
    _AGENTS_IMPORT_ERROR = exc
else:
    _AGENTS_IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parent


def _require_agents_sdk() -> None:
    if _AGENTS_IMPORT_ERROR is not None:
        raise RuntimeError(
            "OpenAI Agents SDK is not installed. Install the project dependencies "
            "with `pip install -e .` or `pip install -r requirements.txt`."
        ) from _AGENTS_IMPORT_ERROR


def _run_bie(pdf_path: str) -> dict[str, Any]:
    from canonical_pipeline import CanonicalBIE

    path = Path(pdf_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("BIE Agent accepts PDF inputs only")

    output_dir = ROOT / "data" / "agent_runs" / path.stem
    provider = None
    if os.getenv("BIE_MOCK", "0") == "1":
        from providers.mock import MockProvider
        provider = MockProvider()

    ctx = CanonicalBIE(work_dir=output_dir, provider=provider).run(str(path))
    return {
        "run_id": ctx.run_id,
        "status": ctx.artifacts.get("manifest", {}).get("status", "COMPLETED"),
        "provider": ctx.artifacts.get("provider"),
        "artifacts": ctx.artifacts,
        "output_dir": str(output_dir),
    }


if function_tool is not None:
    @function_tool
    def run_bie_book_to_video(pdf_path: str, goal: str = "Transform the book into a grounded educational video project") -> str:
        """Run the canonical BIE M1-M300 pipeline on a PDF.

        Use this tool when the user provides a book/PDF and asks BIE to transform it
        into structured knowledge, course/lesson plans, scripts, scenes and a
        Remotion video-generation project. The pipeline preserves source provenance
        and applies its canonical validation stages.
        """
        result = _run_bie(pdf_path)
        result["goal"] = goal
        return json.dumps(result, ensure_ascii=False, default=str)
else:
    run_bie_book_to_video = None


def build_agent() -> Any:
    """Construct the BIE Agent SDK agent."""
    _require_agents_sdk()
    model = os.getenv("BIE_AGENT_MODEL", os.getenv("BIE_OPENAI_MODEL", "gpt-5.6-luna"))
    return Agent(
        name="BIE Book-to-Video Agent",
        model=model,
        instructions=(
            "You are the BIE orchestration agent. BIE is a specialized intelligence "
            "engine for transforming books into grounded educational video projects. "
            "Do not invent source content. When a PDF path is provided, call the BIE "
            "pipeline tool. Report the run status, provider, artifacts, unresolved "
            "items and output directory. BIE owns the canonical M1-M300 workflow; "
            "the agent coordinates and explains it rather than replacing it."
        ),
        tools=[run_bie_book_to_video],
    )


async def run_agent(message: str) -> Any:
    """Run the BIE Agent SDK workflow."""
    _require_agents_sdk()
    agent = build_agent()
    return await Runner.run(agent, message)


def run_agent_sync(message: str) -> Any:
    return asyncio.run(run_agent(message))
