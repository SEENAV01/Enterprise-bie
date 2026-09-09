def prompt(prompt_id, asset_id, prompt_text,
           negative_prompt=None, conditioning=None):
    if not prompt_text:
        raise ValueError("EMPTY_ASSET_PROMPT")
    return {
        "prompt_id": prompt_id, "asset_id": asset_id,
        "prompt": prompt_text,
        "negative_prompt": negative_prompt,
        "conditioning": conditioning or {}
    }

def valid(item):
    return bool(item["prompt_id"] and item["asset_id"] and item["prompt"])
