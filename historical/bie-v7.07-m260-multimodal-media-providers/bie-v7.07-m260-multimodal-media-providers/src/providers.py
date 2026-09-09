def register_provider(registry, provider_id, media_kind, capabilities, priority=50):
    registry[provider_id]={"id":provider_id,"media_kind":media_kind,
                           "capabilities":capabilities,"priority":priority}
    return registry[provider_id]

def select_provider(registry, media_kind, capability):
    matches=[p for p in registry.values()
             if p["media_kind"]==media_kind and capability in p["capabilities"]]
    return sorted(matches,key=lambda p:-p["priority"])[0] if matches else None
