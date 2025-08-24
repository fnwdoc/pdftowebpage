import pytest
import fitz  # PyMuPDF
from analysis import analyze_presentation

# Helper function to create a test PDF document in memory
def create_test_doc(text):
    """Creates an in-memory PDF with one page containing the given text."""
    doc = fitz.open()  # New, empty PDF
    page = doc.new_page()
    # Insert text into a rectangle on the page.
    # The point can be arbitrary, as we only care about the text content.
    point = fitz.Point(50, 70)
    page.insert_text(point, text)
    return doc

def test_no_criteria_found():
    """Test with a generic text that shouldn't trigger any criteria."""
    doc = create_test_doc("This is a generic document about our company.")
    result = analyze_presentation(doc)
    for criterion, data in result.items():
        assert not data['found']
        assert data['snippets'] == []

def test_recurrence_found():
    """Test that recurrence criteria is found and evidence is correct."""
    doc = create_test_doc("Nós oferecemos uma assinatura anual. A mensalidade é baixa.")
    result = analyze_presentation(doc)

    assert result['recurrence']['found']
    assert not result['predictability']['found'] # Ensure no other criteria are triggered

    snippets = result['recurrence']['snippets']
    assert len(snippets) == 2
    assert snippets[0]['page'] == 1
    assert '<strong>assinatura</strong>' in snippets[0]['sentence']
    assert '<strong>mensalidade</strong>' in snippets[1]['sentence']

def test_predictability_found():
    """Test that predictability (pricing) criteria is found."""
    doc = create_test_doc("O preço do plano básico é R$50.")
    result = analyze_presentation(doc)
    assert result['predictability']['found']
    snippets = result['predictability']['snippets']
    assert len(snippets) == 1
    assert '<strong>preço</strong>' in snippets[0]['sentence']
    assert '<strong>R$</strong>50' in snippets[0]['sentence']

def test_scalability_found():
    """Test that scalability criteria is found."""
    doc = create_test_doc("Nossa plataforma de software é robusta.")
    result = analyze_presentation(doc)
    assert result['scalability']['found']
    snippets = result['scalability']['snippets']
    assert '<strong>plataforma</strong>' in snippets[0]['sentence']
    assert '<strong>software</strong>' in snippets[0]['sentence']

def test_multiple_criteria_in_one_sentence():
    """Test a sentence that triggers multiple criteria."""
    doc = create_test_doc("O preço da nossa assinatura de software é competitivo.")
    result = analyze_presentation(doc)
    assert result['predictability']['found']
    assert result['recurrence']['found']
    assert result['scalability']['found']

    # The same sentence should be evidence for all three
    assert '<strong>preço</strong>' in result['predictability']['snippets'][0]['sentence']
    assert '<strong>assinatura</strong>' in result['recurrence']['snippets'][0]['sentence']
    assert '<strong>software</strong>' in result['scalability']['snippets'][0]['sentence']

def test_empty_document():
    """Test that an empty document doesn't cause errors."""
    doc = fitz.open() # Empty doc
    result = analyze_presentation(doc)
    for criterion, data in result.items():
        assert not data['found']
        assert data['snippets'] == []
