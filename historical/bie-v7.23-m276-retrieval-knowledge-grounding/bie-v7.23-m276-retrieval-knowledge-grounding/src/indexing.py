def lexical_terms(text):
    return set(text.lower().split())

def build_index(chunks):
    return [{"chunk":c,"terms":lexical_terms(c["text"])} for c in chunks]

def index_documents(chunks):
    return build_index(chunks)
