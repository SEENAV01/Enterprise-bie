"""Publish a canonical checked synthetic Scene IR project for native CI.

No dependency installer, test renderer, injected paint witness or real-book claim.
The isolated CI job separately installs the project's unchanged declared pins.
"""
from pathlib import Path
import argparse
import json
import sys
from dataclasses import replace

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedSceneIRDocument
from bie.compiler.qa_scene_compile import CompilerQATarget

TARGET=replace(CompilerQATarget(),width=640,height=360,fps=12,compiler_version='1.3.0-comp-h3')


def synthetic_document():
    refs=('fixture:section18-native-preview',)
    reasons=('reasoning:technical-preview-only',)
    element=UnifiedElement('preview-text','text',{'text':'Synthetic preview'},refs,reasons,
                           {'alt':'Synthetic technical preview, not a lesson'},
                           {'x':.1,'y':.2,'width':.8,'height':.3})
    # Metadata is part of the governed fingerprint. Supply it at construction,
    # never mutate a fingerprinted serialized document afterward.
    document=UnifiedSceneIRDocument('section18-native-preview','1.0.0','Technical preview',500,
                                    (element,),(),refs,reasons,
                                    metadata={'fixture':'SYNTHETIC_TEST_NOT_REAL_BOOK'}).to_dict()
    return document


def prepare(destination):
    from bie.compiler.hardened_scene_compile import publish_h3_scene
    document=synthetic_document()
    receipt=publish_h3_scene(document,destination,target=TARGET)
    assert receipt.source_gate_passed and receipt.accepted is False
    return dict(project=str(destination),source_gate_passed=True,
                scene_fingerprint=receipt.scene_fingerprint,
                native_render_status='NOT_RUN',synthetic_source=True,product_accepted=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path)
    p.add_argument('--check-document-only',action='store_true')
    args=p.parse_args()
    if args.check_document_only:
        from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
        document=synthetic_document();decoded=decode_scene_ir(document)
        assert decoded.to_dict()==document
        print(json.dumps(dict(canonical_roundtrip_verified=True,scene_fingerprint=decoded.fingerprint,
                              native_render_status='NOT_RUN',synthetic_source=True,product_accepted=False)))
    else:
        if args.destination is None:p.error('--destination is required for native project preparation')
        print(json.dumps(prepare(args.destination),sort_keys=True))
