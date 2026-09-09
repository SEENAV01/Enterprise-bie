from dataclasses import dataclass, asdict, field

@dataclass
class Block:
    block_id: str
    page: int
    block_type: str          # heading, paragraph, table, figure, caption, list, equation
    text: str = ""
    bbox: list | None = None
    asset_ref: str | None = None
    parent_id: str | None = None
    order: int = 0

@dataclass
class Page:
    page: int
    width: float | None
    height: float | None
    blocks: list[Block] = field(default_factory=list)

def page_from_dict(p: dict) -> Page:
    return Page(
        page=p["page"],
        width=p.get("width"),
        height=p.get("height"),
        blocks=[Block(**b) for b in p.get("blocks",[])]
    )

def to_dict(page: Page):
    return asdict(page)
