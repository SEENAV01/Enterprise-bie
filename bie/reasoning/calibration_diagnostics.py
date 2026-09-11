from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import math

@dataclass(frozen=True)
class CalibrationSample:
    confidence: float
    correct: bool
    sample_id: str = ""

@dataclass(frozen=True)
class CalibrationBin:
    low: float
    high: float
    count: int
    mean_confidence: float
    accuracy: float
    gap: float

@dataclass(frozen=True)
class CalibrationReport:
    sample_count: int
    ece: float
    brier_score: float
    bins: tuple[CalibrationBin,...]
    calibration_version: str
    passed_data_validation: bool

def calibration_report(samples: Iterable[CalibrationSample], *, bin_count: int=10, calibration_version: str="v1") -> CalibrationReport:
    samples=tuple(samples)
    if not samples: raise ValueError("samples required")
    if bin_count < 2: raise ValueError("bin_count >= 2")
    if not calibration_version.strip(): raise ValueError("calibration_version required")
    for s in samples:
        if not isinstance(s.correct,bool) or not math.isfinite(s.confidence) or not 0<=s.confidence<=1:
            raise ValueError("invalid calibration sample")
    bins=[]
    for i in range(bin_count):
        low=i/bin_count; high=(i+1)/bin_count
        selected=[s for s in samples if (low<=s.confidence<high) or (i==bin_count-1 and s.confidence==1)]
        if not selected: continue
        mc=sum(s.confidence for s in selected)/len(selected)
        acc=sum(1.0 if s.correct else 0.0 for s in selected)/len(selected)
        bins.append(CalibrationBin(low,high,len(selected),mc,acc,abs(mc-acc)))
    n=len(samples)
    ece=sum(b.count/n*b.gap for b in bins)
    brier=sum((s.confidence-(1.0 if s.correct else 0.0))**2 for s in samples)/n
    return CalibrationReport(n,ece,brier,tuple(bins),calibration_version,True)
