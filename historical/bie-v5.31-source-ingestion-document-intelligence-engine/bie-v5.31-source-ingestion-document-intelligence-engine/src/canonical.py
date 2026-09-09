def canonical_source(document, pages, regions, blocks,
                      tables=None, figures=None, formulas=None):
    return {"schema_version":"5.31","document":document,
            "pages":pages,"regions":regions,"blocks":blocks,
            "tables":tables or [],"figures":figures or [],
            "formulas":formulas or []}
