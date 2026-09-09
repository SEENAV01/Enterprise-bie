
class OCRSelectionError(ValueError):pass
def select(page):
 text_ratio=float(page.get("native_text_ratio",0));quality=float(page.get("native_text_quality",0))
 image=bool(page.get("has_page_image"))
 if text_ratio>=.85 and quality>=.9:return "NATIVE_TEXT"
 if image and (text_ratio<.25 or quality<.5):return "FULL_OCR"
 if image:return "HYBRID_RECONCILE"
 if text_ratio>0:return "NATIVE_TEXT"
 raise OCRSelectionError("no readable representation")
