def chart_plan(chart_type, data_ref, reveal_order=None):
    return {
        "type":chart_type,
        "data_ref":data_ref,
        "reveal_order":reveal_order or [],
        "actions":["draw_axes","reveal_data","highlight_pattern"],
        "sync_mode":"MARKER_DRIVEN"
    }

def table_plan(data_ref, rows):
    return {
        "data_ref":data_ref,
        "rows":rows,
        "actions":["reveal_row","highlight_cell","compare_rows"],
        "sync_mode":"MARKER_DRIVEN"
    }
