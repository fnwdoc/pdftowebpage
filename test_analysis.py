import pytest
import fitz  # PyMuPDF
from analysis import analyze_presentation, EXPERT_KEYWORDS

# Helper function to create a test PDF document in memory
def create_test_doc(text):
    """Creates an in-memory PDF with one page containing the given text."""
    doc = fitz.open()
    page = doc.new_page()
    point = fitz.Point(50, 70)
    page.insert_text(point, text)
    return doc

def test_no_criteria_found():
    """Test with a generic text that shouldn't trigger any criteria."""
    doc = create_test_doc("Este é um documento genérico sobre nossa empresa.")
    result = analyze_presentation(doc)
    for criterion, data in result.items():
        assert not data['found'], f"Criterion '{criterion}' should not have been found."

def test_keyword_found_and_highlighted():
    """Test that a single keyword is found and highlighted correctly."""
    doc = create_test_doc("Nossa solução de software é a melhor do mercado.")
    result = analyze_presentation(doc)

    assert result['scalability']['found']
    snippets = result['scalability']['snippets']
    assert len(snippets) == 1
    assert snippets[0]['page'] == 1
    assert '<strong>software</strong>' in snippets[0]['sentence']

def test_multiple_keywords_for_same_criterion():
    """Test that multiple keywords for the same criterion are found and highlighted."""
    doc = create_test_doc("O preço do nosso produto é competitivo.")
    result = analyze_presentation(doc)

    assert result['predictability']['found']
    snippets = result['predictability']['snippets']
    assert len(snippets) == 1
    # Check that both keywords are highlighted in the same sentence
    assert '<strong>preço</strong>' in snippets[0]['sentence']

    # The keyword 'produto' is for scalability, let's check that too
    assert result['scalability']['found']
    assert '<strong>produto</strong>' in result['scalability']['snippets'][0]['sentence']

def test_phrase_keyword_matching():
    """Test that multi-word phrases are matched correctly."""
    doc = create_test_doc("Oferecemos um plano mensal com bom custo-benefício.")
    result = analyze_presentation(doc)

    assert result['recurrence']['found']
    assert '<strong>plano mensal</strong>' in result['recurrence']['snippets'][0]['sentence']

    assert result['predictability']['found']
    assert '<strong>custo-benefício</strong>' in result['predictability']['snippets'][0]['sentence']

def test_case_insensitivity():
    """Test that keywords are found regardless of case."""
    doc = create_test_doc("Analisamos o ROI e a MARGEM de lucro.")
    result = analyze_presentation(doc)

    assert result['profitability']['found']
    assert '<strong>ROI</strong>' in result['profitability']['snippets'][0]['sentence']
    assert '<strong>MARGEM</strong>' in result['profitability']['snippets'][0]['sentence']

def test_empty_document():
    """Test that an empty document doesn't cause errors."""
    doc = fitz.open() # Empty doc
    result = analyze_presentation(doc)
    for criterion, data in result.items():
        assert not data['found']
