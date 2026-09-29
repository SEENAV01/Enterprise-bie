"""HARD007: native PDF ingestion -> observed regions -> source QA records.

No OCR substitution for text PDFs. OCR is optional, bounded and performed only on
pages with no text layer. Scan text stays review-required. Page and region raster
identities are evidence of bytes, not proof of extraction/reading-order correctness.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
from io import BytesIO
from pathlib import Path
import csv,hashlib,math,subprocess,tempfile,os
from .common import *
from ...document_intelligence.pdf_ingest import ingest_pdf
from ...document_intelligence.pypdf_adapter import PyPdfAdapter
from ...document_intelligence.source_anchors import Anchor
from ...document_intelligence.text_blocks import TextBlock
from ..source_v2.adapters import block_from_bi
from ..source_v2.models import Source,Block

@dataclass(frozen=True,slots=True)
class DocumentPolicy:
    max_bytes: int = 16*1024*1024
    max_pages: int = 64
    max_regions: int = 4096
    max_pixels_per_page: int = 12_000_000
    max_total_pixels: int = 100_000_000
    max_text: int = 1_000_000
    dpi: int = 96
    def __post_init__(self):
        for name,hi in [('max_bytes',16*1024*1024),('max_pages',1024),('max_regions',4096),('max_pixels_per_page',40_000_000),('max_total_pixels',400_000_000),('max_text',1_000_000)]:
            integer(getattr(self,name),name,1,hi)
        integer(self.dpi,'dpi',72,300)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class OCRRunner:
    executable: str
    executable_sha256: str
    language: str = 'eng'
    timeout_seconds: int = 30
    def __post_init__(self):
        p=Path(self.executable)
        require(p.is_absolute() and p.is_file() and not p.is_symlink(),'OCR_EXECUTABLE')
        sha256(self.executable_sha256,'ocr.binary')
        require(self.language=='eng','OCR_LANGUAGE_NOT_VALIDATED')
        integer(self.timeout_seconds,'ocr.timeout',1,60)
    def run(self,png: bytes) -> tuple[list[dict],dict]:
        require(hashlib.sha256(Path(self.executable).read_bytes()).hexdigest()==self.executable_sha256,'OCR_TOOL_CHANGED')
        with tempfile.TemporaryDirectory(prefix='bie-qa-ocr-') as d:
            image=Path(d)/'page.png';image.write_bytes(png)
            command=[self.executable,str(image),str(Path(d)/'result'),'-l',self.language,'--psm','6','tsv']
            try:
                run=subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=self.timeout_seconds,
                    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','OMP_THREAD_LIMIT':'1'},check=False)
            except subprocess.TimeoutExpired as exc:raise ContractError('OCR_TIMEOUT') from exc
            require(run.returncode==0,'OCR_EXECUTION_FAILED')
            p=Path(d)/'result.tsv';require(p.exists() and p.stat().st_size<=4_000_000,'OCR_RESULT_LIMIT')
            raw=p.read_bytes();words=[]
            try:
                for row in csv.DictReader(raw.decode('utf-8').splitlines(),delimiter='\t'):
                    if row['level']!='5' or not row['text'].strip():continue
                    confidence=Fraction(row['conf']);require(0<=confidence<=100,'OCR_CONFIDENCE')
                    x,y,w,h=(int(row[k]) for k in ('left','top','width','height'))
                    require(x>=0 and y>=0 and w>0 and h>0,'OCR_BOX')
                    words.append(dict(text=row['text'],box=[x,y,x+w,y+h],confidence_ppm=int(confidence*10000)))
                    require(len(words)<=4096,'OCR_REGION_LIMIT')
            except (KeyError,ValueError,UnicodeError) as exc:raise ContractError('OCR_RESULT_INVALID') from exc
            return words,dict(engine='tesseract',executable_sha256=self.executable_sha256,language=self.language,
                 stderr_sha256=hashlib.sha256(run.stderr).hexdigest(),tsv_sha256=hashlib.sha256(raw).hexdigest(),exit_code=run.returncode,
                 source_png_sha256=hashlib.sha256(png).hexdigest(),phonetic_or_semantic_verification=False)


def _png(page, rect, dpi):
    import pymupdf
    pix=page.get_pixmap(matrix=pymupdf.Matrix(dpi/72,dpi/72),clip=rect,alpha=False)
    return pix.tobytes('png'),pix.width,pix.height


def _crop_png(png,box,width,height):
    """Crop the already rendered full page, avoiding renderer image-cache drift.

    Raster cells use outward rounding. Coordinates remain source page points;
    no crop metadata is trusted without rereading the complete page pixels.
    """
    from PIL import Image
    with Image.open(BytesIO(png)) as image:
        px=(math.floor(box[0]*image.width/width),math.floor(box[1]*image.height/height),
            math.ceil(box[2]*image.width/width),math.ceil(box[3]*image.height/height))
        require(0<=px[0]<px[2]<=image.width and 0<=px[1]<px[3]<=image.height,'RASTER_CROP_BOUNDS')
        cropped=image.crop(px);out=BytesIO();cropped.save(out,format='PNG');return out.getvalue()


def _box_ppm(box,width,height):
    require(len(box)==4 and all(math.isfinite(float(x)) for x in box),'DOCUMENT_BOX')
    x0,y0,x1,y1=box
    require(0<=x0<x1<=width and 0<=y0<y1<=height,'DOCUMENT_BOX_BOUNDS')
    return (max(0,math.floor(x0/width*1_000_000)),max(0,math.floor(y0/height*1_000_000)),
            min(1_000_000,math.ceil(x1/width*1_000_000)),min(1_000_000,math.ceil(y1/height*1_000_000)))


def inspect_pdf(source_ref: ArtifactRef, root: Path | str, binding: Binding, policy: DocumentPolicy,
                *, ocr: OCRRunner | None=None) -> dict:
    """Inspect every page, preserving native page IDs, text and raster provenance.

    Parser workers still need production isolation; this bounded adapter runs only
    operator-admitted documents. No executable JavaScript or embedded file is run.
    """
    require(type(policy) is DocumentPolicy and type(source_ref) is ArtifactRef and source_ref.role=='source','DOCUMENT_INPUT')
    require(binding.policy_digest==policy.content_digest,'DOCUMENT_POLICY_BINDING')
    require(source_ref.size<=policy.max_bytes,'DOCUMENT_BYTE_LIMIT')
    with SnapshotStore(root) as store:data=store.read(source_ref)
    import pymupdf
    try:doc=pymupdf.open(stream=data,filetype='pdf')
    except Exception as exc:raise ContractError('PDF_PARSE_FAILED') from exc
    with doc:
        require(not doc.needs_pass,'PDF_ENCRYPTED')
        require(1<=len(doc)<=policy.max_pages,'DOCUMENT_PAGE_LIMIT')
        # Native ingestion is actually called, not represented by a submitted flag.
        native=ingest_pdf(PyPdfAdapter(),data)
        require(native.page_count==len(doc),'NATIVE_PAGE_COUNT_MISMATCH')
        pages=[];regions=[];pixel_budget=0;char_budget=0
        for pi,page in enumerate(doc,1):
            rect=page.rect
            require(page.rotation==0 and rect.width>0 and rect.height>0,'PAGE_ROTATION_OR_GEOMETRY_REVIEW')
            pixels=math.ceil(rect.width*policy.dpi/72)*math.ceil(rect.height*policy.dpi/72)
            pixel_budget+=pixels
            require(pixels<=policy.max_pixels_per_page and pixel_budget<=policy.max_total_pixels,'DOCUMENT_PIXEL_LIMIT')
            png,pw,ph=_png(page,rect,policy.dpi)
            content=page.get_text('dict',sort=False);page_rows=[]
            for b in content.get('blocks',[]):
                if b.get('type')!=0:continue
                for line in b.get('lines',[]):
                    value=''.join(s['text'] for s in line['spans'])
                    if not value.strip():continue
                    box=list(line['bbox']);page_rows.append((value,box,'PDF_TEXT_LAYER',1_000_000))
            basis='PDF_TEXT_LAYER';ocr_receipt=None
            if not page_rows:
                basis='IMAGE_ONLY_UNREAD'
                if ocr is not None:
                    words,ocr_receipt=ocr.run(png);basis='OCR_UNVERIFIED'
                    for word in words:
                        x0,y0,x1,y1=word['box']
                        page_rows.append((word['text'],[x0/pw*rect.width,y0/ph*rect.height,x1/pw*rect.width,y1/ph*rect.height],basis,word['confidence_ppm']))
            ids=[]
            for text_value,box,kind,confidence in page_rows:
                require(len(regions)<policy.max_regions,'DOCUMENT_REGION_LIMIT')
                char_budget+=len(text_value);require(char_budget<=policy.max_text,'DOCUMENT_TEXT_LIMIT')
                pp=_box_ppm(box,rect.width,rect.height)
                region_id=f'p{pi:05d}-r{len(ids)+1:05d}';ids.append(region_id)
                crop=_crop_png(png,box,rect.width,rect.height)
                regions.append(dict(region_id=region_id,page=pi,box_points=[str(v) for v in box],box_ppm=list(pp),
                    text=text_value,normalized_text=text_value,normalization=[dict(raw_start=0,raw_end=len(text_value),out_start=0,out_end=len(text_value),operation='IDENTITY')],
                    text_sha256=hashlib.sha256(text_value.encode()).hexdigest(),raster_sha256=hashlib.sha256(crop).hexdigest(),basis=kind,confidence_ppm=confidence))
            pages.append(dict(page=pi,width_points=str(rect.width),height_points=str(rect.height),raster_sha256=hashlib.sha256(png).hexdigest(),
                pixels=[pw,ph],region_ids=ids,basis=basis,image_count=len(page.get_images()),drawing_count=len(page.get_drawings()),ocr_receipt=ocr_receipt))
        result=dict(schema_version='bie.qa.native-document/1',binding=asdict(binding),source=asdict(source_ref),policy_digest=policy.content_digest,
                    native_inventory=dict(page_count=native.page_count,text_pages=native.text_pages,encrypted=native.encrypted),
                    extractor=dict(pymupdf=pymupdf.VersionBind,geometry='page-points plus outward-rounded ppm',reading_order='EXTRACTION_ORDER_NOT_VERIFIED'),
                    pages=pages,regions=regions,semantic_correctness_verified=False)
        result['content_digest']=digest(result)
        return result


def verify_document(snapshot: dict, source_ref: ArtifactRef, root, binding: Binding, policy: DocumentPolicy,
                    *, required_fragments: tuple[tuple[int,str],...]=()) -> Report:
    """Re-read source and rendering. OCR isn't repeated or falsely authenticated."""
    fields(snapshot,('schema_version','binding','source','policy_digest','native_inventory','extractor','pages','regions','semantic_correctness_verified','content_digest'))
    require(snapshot['schema_version']=='bie.qa.native-document/1','DOCUMENT_SCHEMA')
    require(digest({k:v for k,v in snapshot.items() if k!='content_digest'})==snapshot['content_digest'],'DOCUMENT_RECEIPT_CHANGED')
    binding_matches(snapshot['binding'],binding)
    require(snapshot['source']==asdict(source_ref) and snapshot['policy_digest']==policy.content_digest,'DOCUMENT_SOURCE_OR_POLICY_BINDING')
    actual=inspect_pdf(source_ref,root,binding,policy)
    require(snapshot['native_inventory']==actual['native_inventory'],'NATIVE_INVENTORY_CHANGED')
    require(snapshot['extractor']==actual['extractor'] and snapshot['semantic_correctness_verified'] is False,'EXTRACTOR_IDENTITY_CHANGED')
    pages=items(snapshot['pages'],'PAGES',1,policy.max_pages);regions=items(snapshot['regions'],'REGIONS',0,policy.max_regions)
    require(len(pages)==len(actual['pages']),'PAGE_COVERAGE')
    by_id=unique(regions,'region_id','DUPLICATE_REGION');seen=[];findings=[]
    require(sum(len(text(r.get('text'),'region')) for r in regions)<=policy.max_text,'DOCUMENT_TEXT_LIMIT')
    for r in regions:
        fields(r,('region_id','page','box_points','box_ppm','text','normalized_text','normalization','text_sha256','raster_sha256','basis','confidence_ppm'),'REGION_FIELDS')
        integer(r['confidence_ppm'],'confidence',0,1000000)
    for page in pages:
        fields(page,('page','width_points','height_points','raster_sha256','pixels','region_ids','basis','image_count','drawing_count','ocr_receipt'),'PAGE_FIELDS')
    for saved,observed in zip(pages,actual['pages']):
        for key in ('page','width_points','height_points','pixels','raster_sha256','image_count','drawing_count'):
            require(saved.get(key)==observed[key],'PAGE_OBSERVATION_CHANGED')
        require(type(saved.get('region_ids')) is list,'PAGE_REGION_INVENTORY')
        seen.extend(saved['region_ids'])
        if observed['basis']=='PDF_TEXT_LAYER':
            expected=[x for x in actual['regions'] if x['page']==observed['page']]
            require(saved['basis']=='PDF_TEXT_LAYER' and saved['ocr_receipt'] is None and all(i in by_id for i in saved['region_ids']) and [by_id[i] for i in saved['region_ids']]==expected,'TEXT_REGION_CHANGED')
        else:
            require(saved.get('basis') in ('OCR_UNVERIFIED','IMAGE_ONLY_UNREAD'),'SCAN_BASIS')
            findings.append(Finding('OCR_OR_IMAGE_CONTENT_REQUIRES_REVIEW',str(saved['page'])))
            for ri in saved['region_ids']:
                r=by_id.get(ri);require(r is not None and r['page']==saved['page'],'REGION_PAGE')
                require(r['basis']=='OCR_UNVERIFIED' and r['normalized_text']==r['text'],'OCR_NORMALIZATION_REVIEW')
                require(r['normalization']==[dict(raw_start=0,raw_end=len(r['text']),out_start=0,out_end=len(r['text']),operation='IDENTITY')],'NORMALIZATION_MAP_CHANGED')
                require(hashlib.sha256(r['text'].encode()).hexdigest()==r['text_sha256'],'OCR_TEXT_IDENTITY')
                pp=_box_ppm([float(v) for v in r['box_points']],float(saved['width_points']),float(saved['height_points']))
                require(list(pp)==r['box_ppm'],'OCR_COORDINATE_MISMATCH')
            if saved['basis']=='IMAGE_ONLY_UNREAD':require(not saved['region_ids'] and saved['ocr_receipt'] is None,'UNREAD_PAGE_HAS_TEXT')
            if saved['basis']=='OCR_UNVERIFIED':
                rec=saved.get('ocr_receipt');require(type(rec) is dict and rec.get('source_png_sha256')==observed['raster_sha256'] and rec.get('exit_code')==0,'OCR_PAGE_BINDING')
        if saved['image_count'] or saved['drawing_count']:
            findings.append(Finding('FIGURE_TABLE_MEANING_REQUIRES_REVIEW',str(saved['page'])))
    require(len(seen)==len(set(seen)) and set(seen)==set(by_id),'REGION_COVERAGE')
    # Scan crops are derived from original page pixels, never submitted evidence.
    scan_regions=[r for r in regions if r['basis']=='OCR_UNVERIFIED']
    if scan_regions:
        import pymupdf
        with SnapshotStore(root) as store: original=store.read(source_ref)
        with pymupdf.open(stream=original,filetype='pdf') as doc:
            page_pixels={}
            for r in scan_regions:
                page=doc[r['page']-1]
                if r['page'] not in page_pixels:page_pixels[r['page']]=_png(page,page.rect,policy.dpi)[0]
                crop=_crop_png(page_pixels[r['page']],[float(v) for v in r['box_points']],page.rect.width,page.rect.height)
                require(hashlib.sha256(crop).hexdigest()==r['raster_sha256'],'OCR_CROP_CHANGED')
    for page,fragment in required_fragments:
        integer(page,'fragment.page',1,len(pages));text(fragment,'fragment')
        values=[r['text'] for r in regions if r['page']==page]
        if fragment not in '\n'.join(values):findings.append(Finding('REQUIRED_SOURCE_FRAGMENT_MISSING',fragment[:200],'BLOCKER'))
    findings.append(Finding('READING_ORDER_AND_EXTRACTION_ASSESSMENT_REQUIRED','document'))
    return report('BIE-QA-HARD-007',binding,findings,(source_ref,),snapshot)


def to_source_records(snapshot: dict, source_ref: ArtifactRef, *, verified_report: Report) -> tuple[Source,tuple[Block,...]]:
    require(type(verified_report) is Report and verified_report.binding==Binding(**snapshot['binding']) and verified_report.inspected==(source_ref,) and verified_report.task_id=='BIE-QA-HARD-007' and verified_report.status!='BLOCKED' and verified_report.details_digest==digest(snapshot),'UNVERIFIED_DOCUMENT_EXPORT')
    require(snapshot['source']==asdict(source_ref),'DOCUMENT_EXPORT_SOURCE')
    source=Source(source_ref.artifact_id,source_ref,'pdf',len(snapshot['pages']));blocks=[]
    for r in snapshot['regions']:
        # Outward-rounded geometry is explicit; native records preserve exact text.
        pp=r['box_ppm'];anchor=Anchor(source_ref.sha256,r['page'],r['region_id'],tuple(x/1_000_000 for x in pp))
        native=TextBlock(r['region_id'],r['text'],(r['region_id'],),r['page'],r['confidence_ppm']/1_000_000)
        blocks.append(block_from_bi(native,anchor,source,extractor_id='native-pdf-h3',extractor_version='1',))
    require(bool(blocks),'NO_EXTRACTED_TEXT')
    return source,tuple(blocks)
