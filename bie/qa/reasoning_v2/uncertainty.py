"""Check disclosure, action and empirical calibration without promoting uncertainty."""
from dataclasses import dataclass
from ..release_v2.contracts import ContractError
from ...reasoning.structured_uncertainty import UncertaintyComponent,assess_uncertainty
from .calibration import inspect_calibration

@dataclass(frozen=True, slots=True)
class DecisionWitness:
    argument_id: str
    declared_action: str
    required_action: str
    confidence_ppm: int
    observed_bin_accuracy_ppm: int
    calibration_samples: int
    ece_ppm: int
    brier_ppm: int
    canonical_requires_review: bool


def check_uncertainty(c,valid_args,invalid_args,sufficient_args,conflicted_args):
    r,p=c.request,c.policy;witnesses=[];calibrations={};dataset_ids=set()
    source_hashes=tuple(x.artifact.sha256 for x in r.source.sources)
    for cal in r.calibrations:
        if cal.domain!=p.domain or cal.language!=p.language:
            c.add('uncertainty','CALIBRATION_DOMAIN_MISMATCH',cal.calibration_id,'Calibration must match the operator domain and language.');continue
        if cal.issued_at>c.as_of or c.as_of-cal.issued_at>p.max_calibration_age_seconds:
            c.add('uncertainty','CALIBRATION_STALE',cal.calibration_id,'Calibration is future-dated or outside the policy age.');continue
        payload=c.payloads.get(cal.artifact.artifact_id)
        if payload is None:continue
        try:metrics=inspect_calibration(payload,cal,source_hashes)
        except ContractError as exc:
            c.add('uncertainty',exc.code,cal.calibration_id,'Calibration bytes/metadata/labels failed validation.');continue
        if metrics.dataset_id in dataset_ids:
            c.add('uncertainty','DUPLICATE_CALIBRATION_DATASET',cal.calibration_id,'One dataset cannot be submitted repeatedly as independent calibration.');continue
        dataset_ids.add(metrics.dataset_id)
        if metrics.samples<p.minimum_calibration_samples:
            c.add('uncertainty','CALIBRATION_SAMPLE_FLOOR',cal.calibration_id,'Too few distinct held-out sample groups for the operator floor.');continue
        if metrics.ece_ppm>p.maximum_ece_ppm or metrics.brier_ppm>p.maximum_brier_ppm:
            c.add('uncertainty','CALIBRATION_ERROR_FLOOR',cal.calibration_id,'Recomputed held-out calibration error exceeds a hard floor.');continue
        if ('calibration',cal.calibration_id) not in c.ready:
            c.add('uncertainty','CALIBRATION_AUTHORITY_MISSING',cal.calibration_id,'Sample labels, held-out provenance and applicability need authorized review.','REVIEW');continue
        calibrations[cal.calibration_id]=(cal,metrics)
    if {d.argument_id for d in r.decisions}!=set(c.arguments):
        c.add('uncertainty','CONFIDENCE_DECISION_INVENTORY_MISMATCH','reasoning-scope','Every argument requires exactly one uncertainty disposition.')
    used_calibrations=set()
    for d in sorted(r.decisions,key=lambda x:x.argument_id):
        a=c.arguments.get(d.argument_id)
        if a is None:
            c.add('uncertainty','CONFIDENCE_ARGUMENT_MISSING',d.argument_id,'Unknown argument cannot be assigned release confidence.');continue
        if (d.domain,d.language)!=(p.domain,p.language):c.add('uncertainty','DECISION_DOMAIN_MISMATCH',d.argument_id,'Decision domain/language differs from operator scope.')
        cal=None;metrics=None;observed=-1;bin_count=0
        if d.calibration_id:
            used_calibrations.add(d.calibration_id)
            pair=calibrations.get(d.calibration_id)
            if pair is not None:
                cal,metrics=pair
                if (cal.model_id,cal.model_version,cal.domain,cal.language)!=(d.model_id,d.model_version,d.domain,d.language):
                    c.add('uncertainty','CALIBRATION_MODEL_BINDING_MISMATCH',d.argument_id,'Another model/version/domain/language cannot calibrate this decision.');cal=None
                else:
                    b=min(d.confidence_ppm//100000,9)
                    row=next((x for x in metrics.bins if x[0]==b),None)
                    if row is not None:bin_count=row[1];observed=row[3]*1000000//row[1]
                    if bin_count<p.minimum_bin_samples:
                        c.add('uncertainty','CALIBRATION_CONFIDENCE_BIN_UNSUPPORTED',d.argument_id,'The reported confidence range lacks enough held-out examples.');cal=None
                    elif d.confidence_ppm>observed:
                        c.add('uncertainty','CONFIDENCE_EXCEEDS_OBSERVED_BIN_ACCURACY',d.argument_id,'The claimed confidence exceeds observed bin accuracy; this is a conservative diagnostic, not a population guarantee.');cal=None
        if cal is None:c.add('uncertainty','CALIBRATED_CONFIDENCE_UNESTABLISHED',d.argument_id,'No applicable, current, authorized calibration backs this confidence.','REVIEW')
        if d.confidence_ppm==1000000:
            c.add('uncertainty','ABSOLUTE_CERTAINTY_UNJUSTIFIED',d.argument_id,'Finite empirical calibration cannot establish certainty about arbitrary source-supported output.');cal=None
        fatal=(a.argument_id in invalid_args or a.argument_id in conflicted_args or
               c.source.grounding.status=='BLOCKED' or c.status('validity')=='BLOCKED' or c.status('evidence')=='BLOCKED')
        open_obligation=(a.argument_id not in valid_args or a.argument_id not in sufficient_args or cal is None or
                         c.status('validity')!='CHECKS_PASSED' or c.status('evidence')!='CHECKS_PASSED')
        required='abstain' if fatal or d.confidence_ppm<p.abstain_below_ppm else (
                 'review' if open_obligation or d.confidence_ppm<p.minimum_publish_confidence_ppm else 'publish')
        # Invoke the preserved canonical uncertainty contract as a compatibility
        # check. These weights are assurance flags, NOT joint probabilities.
        components=(UncertaintyComponent('qa-source','SOURCE','Source gate assurance',weight=int(c.source.grounding.status=='CHECKS_PASSED')),
                    UncertaintyComponent('qa-proof','INFERENCE','Formal/reviewed proof assurance',weight=int(a.argument_id in valid_args)),
                    UncertaintyComponent('qa-calibration','MODEL','Applicable calibration assurance',weight=int(cal is not None)))
        legacy=assess_uncertainty(components,review_threshold=p.minimum_publish_confidence_ppm/1000000)
        severity={'publish':0,'review':1,'abstain':2}
        if severity[d.disposition]<severity[required]:
            c.add('uncertainty','UNSAFE_UNCERTAINTY_DISPOSITION',d.argument_id,f'Declared {d.disposition}; required at least {required}. Confidence cannot override a failed or unverified obligation.')
        needs_disclosure=(required!='publish' or d.disposition!='publish' or bool(a.assumption_ids) or a.conclusion_mode=='conditional')
        if needs_disclosure and (not c.actual_claims(d.disclosure_claim_ids) or ('disclosure',d.argument_id) not in c.ready):
            c.add('uncertainty','UNCERTAINTY_DISCLOSURE_UNVERIFIED',d.argument_id,'Uncertainty/conditional assumptions must be visible in actual bound output, not only metadata.','REVIEW')
        if required!='publish' or d.disposition!='publish':
            c.add('uncertainty','REVIEW_OR_ABSTENTION_REMAINS_OPEN',d.argument_id,'Correct abstention or review handling is not a completed product release.','REVIEW')
        witnesses.append(DecisionWitness(d.argument_id,d.disposition,required,d.confidence_ppm,observed,
            metrics.samples if metrics else 0,metrics.ece_ppm if metrics else -1,metrics.brier_ppm if metrics else -1,legacy.requires_review))
    if used_calibrations!={x.calibration_id for x in r.calibrations}:
        c.add('uncertainty','CALIBRATION_INVENTORY_MISMATCH','reasoning-scope','No unknown or unused calibration record may be silently excluded.')
    c.metrics['uncertainty'].update(decisions=len(r.decisions),verified_calibration_sets=len(calibrations),
        publish_recommendations=sum(x.required_action=='publish' for x in witnesses),review_recommendations=sum(x.required_action=='review' for x in witnesses),
        abstain_recommendations=sum(x.required_action=='abstain' for x in witnesses))
    return tuple(witnesses)
