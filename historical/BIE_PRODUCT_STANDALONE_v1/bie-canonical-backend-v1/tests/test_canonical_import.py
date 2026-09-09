def test_canonical_imports():
    from canonical_pipeline import CanonicalBIE
    from ai.openai_provider import OpenAIProvider
    assert CanonicalBIE is not None
    assert OpenAIProvider is not None
