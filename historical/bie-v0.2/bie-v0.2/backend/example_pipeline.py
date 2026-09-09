from backend.ubr.models import Book, InformationUnit, Source, Relationship
from backend.graph.graph import KnowledgeGraph
from backend.lesson.planner import make_lesson
from backend.scene.planner import lesson_to_scenes
from backend.game.planner import knowledge_to_game
from backend.ubr.models import to_dict
import json

def main():
    units = [
        InformationUnit("IU_001", ["definition"], {"statement": "Electric charge is a physical property of matter."}, Source(1, "Ch1", "Charge"), questions=["WHAT"]),
        InformationUnit("IU_002", ["law"], {"statement": "Coulomb's law relates electrostatic force to charges and separation."}, Source(3, "Ch1", "Coulomb Law"), questions=["WHAT", "HOW_MUCH"], dependencies=["IU_001"]),
        InformationUnit("IU_003", ["definition", "explanation"], {"statement": "Electric field describes electric influence at a point."}, Source(6, "Ch1", "Electric Field"), questions=["WHAT", "WHY", "HOW"], dependencies=["IU_001", "IU_002"]),
        InformationUnit("IU_004", ["derivation"], {"statement": "Field due to a point charge follows from Coulomb's law and the definition of field."}, Source(8, "Ch1", "Electric Field"), questions=["HOW_DERIVED"], dependencies=["IU_002", "IU_003"])
    ]
    rels = [
        Relationship("IU_001", "PREREQUISITE_OF", "IU_002"),
        Relationship("IU_002", "PREREQUISITE_OF", "IU_003"),
        Relationship("IU_002", "PREREQUISITE_OF", "IU_004"),
        Relationship("IU_003", "PREREQUISITE_OF", "IU_004")
    ]
    book = Book("demo_physics", {"title": "BIE Demonstration Book", "subject": "Physics", "language": "en"}, {"chapters": []}, units, rels)
    g = KnowledgeGraph()
    for r in rels: g.add_edge(r.source, r.relation, r.target, r.confidence)
    ordered = g.topological_order([u.id for u in units])
    lookup = {u.id: u for u in units}
    lesson = make_lesson("L_001", "Understand electric field from prerequisite knowledge to derivation", ordered, lookup, 600)
    scenes = lesson_to_scenes(lesson, lookup)
    games = [knowledge_to_game(u, i+1) for i, u in enumerate(units)]
    print(json.dumps({"ubr": to_dict(book), "learning_order": ordered, "lesson": lesson, "scenes": scenes, "games": games}, indent=2))

if __name__ == "__main__": main()
