"""Versioned source/grammar-to-native catalog; never a second Visual planner."""
from dataclasses import asdict
from copy import deepcopy
from math import isfinite

from bie.scene_ir import chart_element, diagram_element, shape_element, text_element
from bie.compiler.chart_geometry import chart_geometry
from bie.compiler.diagram_compiler import diagram_geometry
from bie.compiler.shape_compiler import shape_geometry
from bie.compiler.governed_motion import plain
from bie.visual_intelligence.typography_metrics import measure, TypographyRequest
from .contracts import require, canonical, digest
from .scene_ir_contract import MAPPING_POLICY, finite_tree


def _box(primitive, target):
    box = deepcopy(primitive["layout"]["box"])
    require(type(box) is dict and set(box) == {"x", "y", "width", "height"}, "scene_ir_layout_fields")
    require(all(type(v) in (int, float) and isfinite(v) for v in box.values()), "scene_ir_layout_numeric")
    x, y, w, h = (box[k] for k in ("x", "y", "width", "height"))
    require(x >= 0 and y >= 0 and w > 0 and h > 0 and x+w <= 1+1e-9 and y+h <= 1+1e-9,
            "scene_ir_layout_bounds")
    width, height = w * target["viewport_width"], h * target["viewport_height"]
    require(width >= 48 and height >= 48, "scene_ir_presentation_bounds")
    return box, width, height


def _row(element, box):
    value = plain(asdict(element))
    return dict(value, normalized_box=box)


def _label(row, primitive):
    kind = row["semantic_kind"]
    items = {i["id"]: i for i in row["semantic_obligations"]["source_items"]}
    selected = [items[i] for i in primitive["source_item_ids"]]
    if kind == "sampled_chart":
        return primitive["element"]["label"]
    require(len(selected) == 1, "scene_ir_item_scope")
    item = selected[0]
    return item["label"] + (" | " + item["time_label"] +
        (" | uncertain" if item["uncertain"] else "") if kind == "timeline" else "")


def _access(row, primitive, detail, label):
    eid = primitive["element"]["id"]
    alts = [a for a in detail["alt_intents"] if a["intent_id"] == eid]
    require(len(alts) == 1 and alts[0]["mode"] == "long_description" and
            alts[0]["must_include"] == [primitive["element"]["label"]] and
            alts[0]["evidence_refs"] == row["evidence_refs"] and
            alts[0]["reasoning_refs"] == row["reasoning_refs"] and
            alts[0]["review_required"] is True and alts[0]["accepted"] is False and
            detail["accessibility"]["blocked"] is False,
            "scene_ir_accessibility_source")
    # Source-derived expansion (e.g. date uncertainty) adds no factual claim.
    required = primitive["element"]["label"]
    description = label if required in label else required + " | " + label
    return dict(alt=description, color_independent_encoding=True)


def build_catalog(rows, target, visual_details):
    """Consume authenticated actual current rows and exact Visual evidence only.

    The durable service grants currentness. This pure adapter additionally
    conserves the grammar/source/layout inventory. It never reads a PDF shortcut
    or imports a fixture catalog, performs provider calls, or creates motion.
    """
    finite_tree(rows); finite_tree(target); finite_tree(visual_details)
    details = {d["intent_id"]: d for d in visual_details}
    require(len(details) == len(visual_details), "scene_ir_visual_details_identity")
    catalog, mappings, seen = [], [], set()
    for row in rows:
        require(row["visual_intent_id"] in details, "scene_ir_visual_details_identity")
        detail = details[row["visual_intent_id"]]
        require(detail["scene_id"] == row["scene_id"], "scene_ir_foreign_scene")
        grammar = {e["id"]: e for e in detail["grammar"]["elements"]}
        layouts = {e["node_id"]: e for e in detail["layout"]["nodes"]}
        source = {i["id"]: i for i in row["semantic_obligations"]["source_items"]}
        require(len(source) == len(row["semantic_obligations"]["source_items"]), "scene_ir_source_items")
        for primitive in row["primitive_rows"]:
            pid, original = primitive["primitive_id"], primitive["element"]
            require(pid not in seen and original == grammar.get(original["id"]) and
                    primitive["layout"] == layouts.get(original["id"]), "scene_ir_primitive_identity")
            seen.add(pid)
            box, width, height = _box(primitive, target)
            refs, reasoning = primitive["source_refs"], primitive["reasoning_refs"]
            require(refs == original["source_ids"] and reasoning == row["reasoning_refs"], "scene_ir_catalog_lineage")
            ids = primitive["source_item_ids"]
            require(set(ids) <= set(source), "scene_ir_catalog_source")
            entries = []
            if primitive["semantic_role"] == "supporting_axis":
                require(not ids and original["role"] in ("chart_frame", "timeline_axis"), "scene_ir_static_context")
                label = original["label"]
                acc = _access(row, primitive, detail, label)
                points = [[8, 8], [8, height-8], [width-8, height-8]] if row["semantic_kind"] == "sampled_chart" else [[8, height/2], [width-8, height/2]]
                element = shape_element.build(pid, "polyline", refs, reasoning,
                    dict(points=points, view_box=[0, 0, width, height]),
                    dict(fill="none", stroke=target["foreground"], stroke_width=2, opacity=1), acc)
                entries.append(_row(element, box))
                text = text_element.build(pid + ":label", label, refs, reasoning,
                    role="label", accessibility=acc)
                require(text.props["text"] == label, "scene_ir_text_changed")
                entries.append(_row(text, box))
            elif row["semantic_kind"] == "sampled_chart":
                require(original["primitive"] == "bar" and original["role"] == "data_series" and
                        row["semantic_obligations"]["y_baseline"] == 0 and
                        row["semantic_obligations"]["exact_curve_claim"] is False,
                        "scene_ir_chart_unsupported")
                selected = [source[i] for i in ids]
                label = "; ".join(i["label"] + " " + i["value_text"] for i in selected)
                element = chart_element.build(pid, "bar", [i["label"] for i in selected],
                    [i["value"] for i in selected], refs, reasoning, _access(row, primitive, detail, label))
                value = _row(element, box)
                value["props"].update(row["semantic_obligations"]["axis"], units="")
                entries.append(value)
            else:
                require(row["semantic_kind"] in ("timeline", "cellular") and len(ids) == 1,
                        "scene_ir_domain_unsupported")
                item = source[ids[0]]
                if row["semantic_kind"] == "cellular":
                    require(not row["semantic_obligations"]["containments"] and
                            not row["semantic_obligations"]["transports"] and item["parent_id"] is None,
                            "scene_ir_structure_unsupported")
                    diagram_kind = "source-declared-" + item["kind"] + "-schematic-not-physical-scale"
                else:
                    diagram_kind = "source-declared-chronology-not-elapsed-time"
                label = _label(row, primitive)
                # The canonical SVG diagram emitter uses one text node, not the
                # Visual metrics helper's wrapping algorithm. Do not approve a
                # wrapped metric that the actual consumer cannot realize.
                metric = measure(TypographyRequest(label, target["font_px"], width-20, height-20,
                                                   mode="label", allow_wrap=False))
                require(not metric.overflow, "scene_ir_text_overflow")
                node = dict(node_id=item["id"], label=label, x=10, y=10, width=width-20,
                    height=height-20, font_size=target["font_px"], fill=target["background"],
                    stroke=target["foreground"], source_refs=refs, reasoning_refs=reasoning)
                element = diagram_element.build(pid, [node], [], refs, reasoning,
                    diagram_kind, _access(row, primitive, detail, label), view_box=[0, 0, width, height])
                entries.append(_row(element, box))
            catalog.extend(entries)
            mappings.append(dict(policy=MAPPING_POLICY, primitive_id=pid,
                grammar_element_id=original["id"], native_element_ids=[e["element_id"] for e in entries],
                semantic_kind=row["semantic_kind"], semantic_role=primitive["semantic_role"],
                source_item_ids=ids, source_refs=refs, reasoning_refs=reasoning,
                objective_ids=row["objective_ids"], concept_ids=row["concept_ids"],
                original_grammar=original, original_layout=primitive["layout"],
                coordinate_policy="normalized-box-to-current-canvas-local-pixels/1",
                source_obligations=row["semantic_obligations"], visual_revision=row["visual_revision"],
                narration_revision=row["narration_revision"], uncertainty=row["uncertainty"],
                original_alt_intent=next(a for a in detail["alt_intents"] if a["intent_id"] == original["id"]),
                rights="NATIVE_PROCEDURAL_PLAN_NO_EXTERNAL_MATERIAL",
                native_props_sha256={e["element_id"]: digest(e["props"]) for e in entries}))
    require(0 < len(catalog) <= 256 and len({e["element_id"] for e in catalog}) == len(catalog),
            "scene_ir_catalog_identity")
    verify_inventory(rows, catalog, mappings, target)
    return catalog, mappings


def verify_inventory(rows, catalog, mappings, target):
    """Inspect actual native props against independent upstream obligations.

    Generic schema PASS and a producer-authored passed flag are insufficient.
    Required static descendants, source values/time uncertainty, layout and all
    lineage are independently checked, including recomputed-fingerprint tamper.
    """
    finite_tree(catalog); finite_tree(mappings)
    by_id = {e["element_id"]: e for e in catalog}
    upstream = {p["primitive_id"]: (r, p) for r in rows for p in r["primitive_rows"]}
    by_map = {m["primitive_id"]: m for m in mappings}
    require(len(by_id) == len(catalog) and len(by_map) == len(mappings) and set(by_map) == set(upstream),
            "scene_ir_inventory_identity")
    descendants = [i for m in mappings for i in m["native_element_ids"]]
    require(len(set(descendants)) == len(descendants) and set(descendants) == set(by_id), "scene_ir_inventory_coverage")
    for pid, (row, primitive) in upstream.items():
        mapping = by_map[pid]
        require(mapping["policy"] == MAPPING_POLICY and mapping["primitive_id"] == pid and
                mapping["grammar_element_id"] == primitive["element"]["id"] and
                mapping["semantic_kind"] == row["semantic_kind"] and
                mapping["semantic_role"] == primitive["semantic_role"] and
                mapping["visual_revision"] == row["visual_revision"] and
                mapping["narration_revision"] == row["narration_revision"] and
                mapping["uncertainty"] == row["uncertainty"] and
                mapping["coordinate_policy"] == "normalized-box-to-current-canvas-local-pixels/1" and
                mapping["rights"] == "NATIVE_PROCEDURAL_PLAN_NO_EXTERNAL_MATERIAL",
                "scene_ir_mapping_policy")
        require(mapping["original_grammar"] == primitive["element"] and
                mapping["original_layout"] == primitive["layout"] and
                mapping["source_obligations"] == row["semantic_obligations"] and
                mapping["source_item_ids"] == primitive["source_item_ids"] and
                mapping["source_refs"] == primitive["source_refs"] and
                mapping["reasoning_refs"] == primitive["reasoning_refs"] and
                mapping["objective_ids"] == row["objective_ids"] and mapping["concept_ids"] == row["concept_ids"],
                "scene_ir_mapping_tampered")
        alt = mapping["original_alt_intent"]
        require(type(alt) is dict and alt["intent_id"] == primitive["element"]["id"] and
                alt["mode"] == "long_description" and alt["must_include"] == [primitive["element"]["label"]] and
                alt["evidence_refs"] == row["evidence_refs"] and alt["reasoning_refs"] == row["reasoning_refs"] and
                alt["review_required"] is True and alt["accepted"] is False, "scene_ir_alt_conservation")
        elements = [by_id[i] for i in mapping["native_element_ids"]]
        for element in elements:
            label = primitive["element"]["label"] if primitive["semantic_role"] == "supporting_axis" else (
                "; ".join(i["label"] + " " + i["value_text"] for i in row["semantic_obligations"]["source_items"]
                    if i["id"] in primitive["source_item_ids"]) if row["semantic_kind"] == "sampled_chart" else _label(row, primitive))
            required = primitive["element"]["label"]
            description = label if required in label else required + " | " + label
            expected_access = dict(alt=description, color_independent_encoding=True)
            if "reduced_motion_variant" in element["accessibility"]:
                require(primitive["semantic_role"] != "supporting_axis", "scene_ir_static_motion_invented")
                expected_access["reduced_motion_variant"] = "scene-ir-m1:" + pid
            require(element["accessibility"] == expected_access, "scene_ir_accessibility_conservation")
            require(element["normalized_box"] == primitive["layout"]["box"] and
                    element["source_refs"] == primitive["source_refs"] and
                    element["reasoning_refs"] == primitive["reasoning_refs"] and
                    digest(element["props"]) == mapping["native_props_sha256"][element["element_id"]],
                    "scene_ir_element_conservation")
        first = elements[0]
        box, width, height = _box(primitive, target)
        if primitive["semantic_role"] == "supporting_axis":
            require(len(elements) == 2 and [e["element_type"] for e in elements] == ["shape", "text"] and
                    [e["element_id"] for e in elements] == [pid, pid + ":label"] and
                    elements[1]["props"] == dict(text=primitive["element"]["label"], role="label"),
                    "scene_ir_static_context_lost")
            points = [[8, 8], [8, height-8], [width-8, height-8]] if row["semantic_kind"] == "sampled_chart" else [[8, height/2], [width-8, height/2]]
            require(first["props"] == dict(shape_kind="polyline", geometry=dict(points=points,
                view_box=[0, 0, width, height]), style=dict(fill="none", stroke=target["foreground"],
                stroke_width=2, opacity=1)), "scene_ir_static_geometry_changed")
            shape_geometry(first["props"])
        elif row["semantic_kind"] == "sampled_chart":
            require(len(elements) == 1 and first["element_type"] == "chart", "scene_ir_chart_type")
            geometry = chart_geometry(first["props"])
            source = {i["id"]: i for i in row["semantic_obligations"]["source_items"]}
            selected = [source[i] for i in primitive["source_item_ids"]]
            require(geometry["kind"] == "bar" and geometry["categories"] == [i["label"] for i in selected] and
                    geometry["values"] == [i["value"] for i in selected] and
                    all(first["props"][k] == row["semantic_obligations"]["axis"][k] for k in ("x_label", "y_label")) and
                    first["props"]["units"] == "", "scene_ir_chart_data_changed")
        else:
            require(len(elements) == 1 and first["element_type"] == "diagram", "scene_ir_item_type")
            geometry = diagram_geometry(first["props"], first["source_refs"], first["reasoning_refs"])
            source = {i["id"]: i for i in row["semantic_obligations"]["source_items"]}
            item = source[primitive["source_item_ids"][0]]
            kind = "source-declared-chronology-not-elapsed-time" if row["semantic_kind"] == "timeline" else "source-declared-" + item["kind"] + "-schematic-not-physical-scale"
            require(first["props"]["diagram_kind"] == kind and first["props"]["view_box"] == [0, 0, width, height] and
                first["props"]["nodes"] == [dict(node_id=item["id"], label=_label(row, primitive), x=10, y=10,
                    width=width-20, height=height-20, font_size=target["font_px"], fill=target["background"],
                    stroke=target["foreground"], source_refs=primitive["source_refs"], reasoning_refs=primitive["reasoning_refs"])],
                    "scene_ir_diagram_presentation_changed")
            require(len(geometry["nodes"]) == 1 and not geometry["edges"] and
                    geometry["nodes"][0]["node_id"] == primitive["source_item_ids"][0] and
                    geometry["nodes"][0]["label"] == _label(row, primitive), "scene_ir_item_semantics_changed")
    return dict(primitive_count=len(upstream), element_count=len(catalog), static_primitive_count=sum(
        p["semantic_role"] == "supporting_axis" for _, p in upstream.values()),
        source_item_count=sum(len(r["semantic_obligations"]["source_items"]) for r in rows),
        policy=MAPPING_POLICY, passed=True, accepted=False)
