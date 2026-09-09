def coverage_report(blocks):
    required={"DEFINITION","INTUITION","MECHANISM","CHECKPOINT"}
    present={b["type"] for b in blocks}
    return {
      "required_blocks":sorted(required),
      "missing":sorted(required-present),
      "complete":required.issubset(present)
    }
