def worked_example(example_id,title,problem=None,solution=None,
                  concept_refs=None,source_refs=None):
    return {"example_id":example_id,"title":title,"problem":problem,
            "solution":solution,"concept_refs":concept_refs or [],
            "source_refs":source_refs or []}
