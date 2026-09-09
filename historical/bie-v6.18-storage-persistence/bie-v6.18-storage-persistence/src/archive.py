def archive_policy(entity_name,
                  hot_until,
                  archive_after,
                  tier="COLD"):
    return {"entity":entity_name,
            "hot_until":hot_until,
            "archive_after":archive_after,
            "tier":tier}

def archival_due(record,now):
    return now >= record["archive_after"]
