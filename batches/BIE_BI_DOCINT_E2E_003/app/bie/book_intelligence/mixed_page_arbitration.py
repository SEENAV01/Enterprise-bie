class E(ValueError):pass
def choose(native_conf,ocr_conf,has_math=False,has_visual=False):
 for x in (native_conf,ocr_conf):
  if not 0<=x<=1:raise E("confidence")
 if has_math or has_visual:return "HYBRID"
 if native_conf>=.9 and native_conf>=ocr_conf:return "NATIVE"
 if ocr_conf>=.85:return "OCR"
 return "REVIEW"
