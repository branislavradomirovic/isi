from pathlib import Path


def test_document_and_library_searches_have_explicit_text_labels():
    documents = Path("src/public/templates/documents.html").read_text()
    library = Path("src/public/templates/library.html").read_text()
    assert 'class="sr-only"' in documents
    assert 'class="sr-only"' in library
