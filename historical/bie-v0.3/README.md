# Book Intelligence Engine — v0.3

## M1–M3 foundation

`PDF → M2 provenance-preserving blocks → M3 source-grounded semantic UBR`

### M3 capabilities
- atomic information-unit extraction
- 24-class question taxonomy
- typed relation extraction
- strict JSON Structured Outputs
- mandatory provenance
- confidence scoring
- invalid-provenance filtering
- relation integrity checks
- CLI integration

### Live extraction
Set `OPENAI_API_KEY`, then run:

```bash
python -m backend.ingestion.cli input.pdf output.json
python -m backend.extraction.cli output.json m3.json
```

The API key is never stored in the repository. Use environment/secret management in production.

### Design rule
M3 is **semantic decomposition, not summarization**. Raw M2 blocks remain the immutable evidence layer.
M4 will consume M3 output to build the Knowledge Graph and Learning Graph.
