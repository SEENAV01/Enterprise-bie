def layout_region(region_id, source_id, page, region_type,
                  bbox, reading_order=0, parent_id=None):
    return {
        "region_id": region_id, "source_id": source_id, "page": page,
        "region_type": region_type, "bbox": bbox,
        "reading_order": reading_order, "parent_id": parent_id
    }

def ordered(regions):
    return sorted(regions, key=lambda x: (x["page"], x["reading_order"]))
