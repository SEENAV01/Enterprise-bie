"""Independent hierarchical review aligned to persisted discourse scopes."""
from dataclasses import asdict,dataclass

from .annotation_review import AnnotationReviewPolicy,COMPLETENESS
from .annotation_window_context import ScopedAnnotationCall,WindowedAnnotationReviewPolicy,scene_payload,verify_call
from .director_artifacts import canonical,fingerprint,parse_json
from .director_model import DirectingFailure,invoke_structured,model_identity
from .hierarchical_annotations import HierarchicalAnnotationProduction,_contract,_scope_specs,verify_hierarchical_production
from .windowed_annotation_review import (GLOBAL_KEYS,GLOBAL_DIMENSIONS,PROMPT,SCHEMA,ReviewWindow,
    WindowedAnnotationReview,aggregate,subject_rows,validate_scoped_judgments)


@dataclass(frozen=True)
class HierarchicalAnnotationReviewPolicy(WindowedAnnotationReviewPolicy):
    window_version:str='bie-dir-hierarchical-review/1.0.0'
    maximum_windows:int=1024

    def validate(self):
        AnnotationReviewPolicy.validate(self)
        if self.window_version!='bie-dir-hierarchical-review/1.0.0':raise ValueError('unsupported hierarchical review policy')
        if type(self.maximum_windows) is not int or self.maximum_windows<1:raise ValueError('positive hierarchical review budget required')


@dataclass(frozen=True)
class HierarchicalAnnotationReview(WindowedAnnotationReview):
    discourse_schedule_fingerprint:str


HIERARCHICAL_PROMPT=PROMPT+'''
For HIERARCHICAL_DISCOURSE, inspect exactly the persisted leaf, boundary or retrieval scope supplied.
Leaf scopes collectively cover every utterance; boundary scopes collectively cover every inter-leaf edge;
retrieval scopes inspect deterministic non-adjacent candidates. No one local verdict implies global truth.
The host aggregates all observations conjunctively and reruns whole-result QA. Do not demand absent source
pages in discourse scopes or infer that lexical overlap proves a reference/repetition.'''


def _owner_scene(key,row,base):
    index={u.utterance_id:u for u in base.execution.snapshot.utterances};order=[s.scene_id for s in base.plan.scenes]
    if key=='discourse':return index[row['utterance_id']].scene_id
    if key=='transitions':return row['to_scene']
    if key=='terms':
        if row['definition'] is not None:return index[row['definition']['utterance_id']].scene_id
        return next(scene for scene in order if any(row['term'].casefold() in u.text.casefold() for u in index.values() if u.scene_id==scene))
    if key=='repetitions':return index[row['repeated']['utterance_id']].scene_id


def review_contracts(inputs,base,production,policy):
    annotations=production.annotations;rows=subject_rows(production,base);raw=parse_json(production.response_json)
    order=tuple(s.scene_id for s in base.plan.scenes)
    def contract(scope,scene_ids,selected,grounded,kind,dimensions):
        required=tuple(sorted([row[0] for row in selected]+['completeness:'+name for name in dimensions]))
        payload={'operation':'REVIEW_HIERARCHICAL_ANNOTATION','prompt_version':policy.prompt_version,
            'review_window_policy':asdict(policy),'review_kind':kind,'target_scope':scope,
            'grounded_narration':grounded,
            'annotations':{key:[row[2] for row in selected if row[1]==key] for key in raw if isinstance(raw[key],list)},
            'annotation_policy':asdict(annotations.policy),'annotation_fingerprint':annotations.fingerprint(),
            'input_fingerprint':inputs.fingerprint(),'snapshot_fingerprint':annotations.snapshot_fingerprint,
            'required_subject_ids':required}
        payload['review_scope_fingerprint']=fingerprint(payload)
        return scope,tuple(scene_ids),required,payload
    for scene in order:
        selected=[row for row in rows if scene in row[3]];support={scene}|{s for row in selected for s in row[3]}
        grounded=scene_payload(inputs,base,tuple(s for s in order if s in support),annotations.policy)[0]
        yield contract('source:'+scene,tuple(s for s in order if s in support),selected,grounded,'SOURCE_SCENES',COMPLETENESS)
    specs=_scope_specs(inputs,base,annotations.policy,production.identity)
    for index,(spec,executed) in enumerate(zip(specs,production.discourse_scopes),1):
        subject,payload,_,_=_contract(inputs,base,annotations.policy,spec,index);kind,scene_ids,_=spec;scene_set=set(scene_ids)
        if (kind,executed.call.scope_id)!=(executed.kind,subject):raise ValueError('annotation discourse schedule changed before review')
        if kind=='LEAF':
            selected=[row for row in rows if row[1] in GLOBAL_KEYS and _owner_scene(row[1],row[2],base) in scene_set]
            dimensions=tuple(name for name in GLOBAL_DIMENSIONS if name!='TRANSITIONS' or executed.boundary_edges)
        elif kind=='BOUNDARY':
            edge=executed.boundary_edges[0];selected=[row for row in rows if row[1]=='transitions' and (row[2]['from_scene'],row[2]['to_scene'])==edge]
            dimensions=('TRANSITIONS',)
        else:
            uids=set(executed.utterance_ids);selected=[]
            for row in rows:
                if row[1]=='discourse' and row[2]['utterance_id'] in uids:selected.append(row)
                elif row[1]=='repetitions' and {row[2]['first']['utterance_id'],row[2]['repeated']['utterance_id']}<=uids:selected.append(row)
            dimensions=('DISCOURSE','REPETITION')
        grounded={**payload,'operation':'REVIEW_GROUNDED_HIERARCHICAL_SCOPE'}
        yield contract('review:'+subject,scene_ids,selected,grounded,'HIERARCHICAL_DISCOURSE_'+kind,dimensions)


def review_hierarchical_annotations(inputs,base,production,provider,identity,policy):
    if not isinstance(production,HierarchicalAnnotationProduction):raise ValueError('hierarchical production required')
    annotations=verify_hierarchical_production(production,inputs,base);policy.validate();model_identity(identity)
    if (identity.provider,identity.model)==(production.identity.provider,production.identity.model):raise ValueError('separate annotation reviewer required')
    contracts=tuple(review_contracts(inputs,base,production,policy))
    if len(contracts)>policy.maximum_windows:raise DirectingFailure('ANNOTATION_REVIEW_WINDOW_COUNT_EXCEEDED',owner='DIR_ANNOTATIONS')
    windows=[];attempts=()
    for scope,scene_ids,required,payload in contracts:
        def validate(raw,required=required,payload=payload):
            validate_scoped_judgments(raw,annotations,required,payload['review_scope_fingerprint']);return canonical(raw)
        try:response,trace=invoke_structured(provider,identity,policy.execution,'REVIEW_HIERARCHICAL_ANNOTATION',scope,
            HIERARCHICAL_PROMPT,payload,SCHEMA,validate);failure=None
        except DirectingFailure as error:response=None;trace=error.attempts;failure=error.code
        call=ScopedAnnotationCall(scope,scene_ids,fingerprint(payload),response,trace,failure)
        windows.append(ReviewWindow(call,required,payload['review_scope_fingerprint']));attempts+=trace
    judgments,failures,response=aggregate(annotations,windows)
    schedule=fingerprint([(scope.kind,scope.call.request_payload_fingerprint) for scope in production.discourse_scopes])
    return HierarchicalAnnotationReview(annotations.fingerprint(),annotations.snapshot_fingerprint,annotations.input_fingerprint,
        identity,policy,judgments,attempts,failures,response,tuple(windows),schedule)


def verify_hierarchical_review(inputs,base,production,review):
    if not isinstance(review,HierarchicalAnnotationReview) or not isinstance(review.policy,HierarchicalAnnotationReviewPolicy):
        raise ValueError('known hierarchical annotation review required')
    annotations=verify_hierarchical_production(production,inputs,base);review.policy.validate()
    expected_schedule=fingerprint([(scope.kind,scope.call.request_payload_fingerprint) for scope in production.discourse_scopes])
    if review.discourse_schedule_fingerprint!=expected_schedule:raise ValueError('review lost hierarchical annotation schedule')
    if (review.annotation_fingerprint,review.snapshot_fingerprint,review.input_fingerprint)!=(
            annotations.fingerprint(),annotations.snapshot_fingerprint,annotations.input_fingerprint):raise ValueError('stale hierarchical review')
    contracts=tuple(review_contracts(inputs,base,production,review.policy))
    if len(contracts)!=len(review.review_windows):raise ValueError('hierarchical review scope coverage changed')
    for (scope,scene_ids,required,payload),window in zip(contracts,review.review_windows):
        if (window.call.scene_ids,window.required_subject_ids,window.scope_fingerprint)!=(scene_ids,required,payload['review_scope_fingerprint']):
            raise ValueError('hierarchical review schedule changed')
        verify_call(window.call,review.identity,review.policy.execution,'REVIEW_HIERARCHICAL_ANNOTATION',scope,payload,SCHEMA,HIERARCHICAL_PROMPT,allow_failure=True)
    judgments,failures,response=aggregate(annotations,review.review_windows)
    if (judgments,failures,response)!=(review.judgments,review.failures,review.response_json):raise ValueError('hierarchical review aggregate changed')
    if tuple(a for w in review.review_windows for a in w.call.attempts)!=review.attempts:raise ValueError('hierarchical review attempts changed')
    return review
