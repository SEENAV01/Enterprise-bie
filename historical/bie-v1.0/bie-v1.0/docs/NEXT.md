# Next engineering stage

For the first real book run, use a short textbook chapter rather than a 500-page book. Validate M3/M4/M5 on 20–50 pages first.

Then scale with:
- page/chunk shards
- deterministic IDs
- cached API outputs keyed by content hash + model + prompt version
- parallel processing
- merge/evaluation
- human adjudication
- only then full-book processing

For high-volume offline processing, OpenAI's Batch API supports `/v1/responses` jobs and can reduce cost versus synchronous processing; design the orchestrator so the transport can later switch between synchronous and batch execution.
