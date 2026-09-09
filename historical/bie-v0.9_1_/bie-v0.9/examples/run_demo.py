
from bie_core.orchestrator import Pipeline
from bie_core.mock_pipeline import register_demo_handlers

p=Pipeline()
register_demo_handlers(p)
job, outputs=p.run("example-book.pdf", initial={"source_path":"example-book.pdf"})
print(job.job_id)
for k,v in job.stages.items(): print(k,v.status,v.attempts)
