from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from math import isfinite

@dataclass(frozen=True)
class SpatialFrame:
    frame_id: str
    dimension: int
    unit: str
    axis_names: tuple[str,...]

    def validate(self):
        if not self.frame_id.strip() or not self.unit.strip():
            raise ValueError("frame_id/unit required")
        if self.dimension < 1 or len(self.axis_names) != self.dimension:
            raise ValueError("dimension/axis mismatch")

@dataclass(frozen=True)
class SpatialPoint:
    frame: SpatialFrame
    coordinates: tuple[float,...]
    provenance_ids: tuple[str,...] = ()

    def validate(self):
        self.frame.validate()
        if len(self.coordinates) != self.frame.dimension:
            raise ValueError("coordinate dimension mismatch")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x)
               for x in self.coordinates):
            raise ValueError("coordinates must be finite numbers")

@dataclass(frozen=True)
class FrameTransform:
    source_frame_id: str
    target_frame_id: str
    transform_id: str
    provenance_ids: tuple[str,...] = ()

def assert_compatible(a: SpatialPoint, b: SpatialPoint) -> None:
    a.validate(); b.validate()
    if a.frame.frame_id != b.frame.frame_id:
        raise ValueError("incompatible spatial frames")
    if a.frame.unit != b.frame.unit:
        raise ValueError("incompatible units")
    if a.frame.axis_names != b.frame.axis_names:
        raise ValueError("incompatible axis conventions")

def transform_point(
    point: SpatialPoint,
    target_frame: SpatialFrame,
    transform: FrameTransform,
    fn: Callable[[tuple[float,...]], tuple[float,...]]
) -> SpatialPoint:
    point.validate(); target_frame.validate()
    if transform.source_frame_id != point.frame.frame_id or transform.target_frame_id != target_frame.frame_id:
        raise ValueError("transform frame mismatch")
    coords=tuple(fn(point.coordinates))
    out=SpatialPoint(target_frame,coords,tuple(sorted(set(point.provenance_ids+transform.provenance_ids+(transform.transform_id,)))))
    out.validate()
    return out
