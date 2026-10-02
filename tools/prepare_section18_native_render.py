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
from bie.compiler.hardened_scene_compile import publish_h3_scene

TARGET=replace(CompilerQATarget(),width=640,height=360,fps=12,compiler_version='1.3.0-comp-h3')


def prepare(destination):
    refs=('fixture:section18-native-preview',)
    reasons=('reasoning:technical-preview-only',)
    element=UnifiedElement('preview-text','text',{'text':'Synthetic preview'},refs,reasons,
                           {'alt':'Synthetic technical preview, not a lesson'},
                           {'x':.1,'y':.2,'width':.8,'height':.3})
    document=UnifiedSceneIRDocument('section18-native-preview','1.0.0','Technical preview',500,
                                    (element,),(),refs,reasons).to_dict()
    document['metadata']={'fixture':'SYNTHETIC_TEST_NOT_REAL_BOOK'}
    receipt=publish_h3_scene(document,destination,target=TARGET)
    assert receipt.source_gate_passed and receipt.accepted is False
    return dict(project=str(destination),source_gate_passed=True,
                scene_fingerprint=receipt.scene_fingerprint,
                native_render_status='NOT_RUN',synthetic_source=True,product_accepted=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().destination),sort_keys=True))
