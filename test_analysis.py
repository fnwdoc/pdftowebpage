import pytest
from unittest.mock import MagicMock
from content_parser import parse_pdf_to_structured_content

# --- Mocking PyMuPDF's Data Structures ---

def create_mock_span(text, size, flags):
    """Creates a mock span dictionary."""
    return {"text": text, "size": size, "flags": flags}

def create_mock_line(spans):
    """Creates a mock line dictionary containing spans."""
    return {"spans": spans}

def create_mock_block(lines):
    """Creates a mock block dictionary containing lines."""
    return {"type": 0, "lines": lines}

def create_mock_page(blocks):
    """Creates a mock page object with a get_text method."""
    page = MagicMock()
    page.get_text.return_value = {"blocks": blocks}
    return page

def create_mock_doc(pages_content):
    """Creates a mock document object that can be iterated over."""
    doc = MagicMock()
    doc.__iter__.return_value = pages_content
    return doc

# --- New Tests Using Mocks ---

def test_empty_document():
    """Test that a document with no text blocks returns an empty list."""
    doc = create_mock_doc([])
    result = parse_pdf_to_structured_content(doc)
    assert result == []

def test_structure_and_analysis():
    """Test structural parsing and criteria analysis in one go."""
    # This mock data represents a two-page PDF
    mock_pages = [
        # Page 1: A heading and a paragraph with a scalability keyword
        create_mock_page([
            create_mock_block([create_mock_line([create_mock_span("Sobre nosso Produto", 16, 16)])]),
            create_mock_block([create_mock_line([create_mock_span("Nossa plataforma é inovadora.", 11, 4)])])
        ]),
        # Page 2: Another heading and a paragraph with a pricing keyword
        create_mock_page([
            create_mock_block([create_mock_line([create_mock_span("Nossos Preços", 16, 16)])]),
            create_mock_block([create_mock_line([create_mock_span("O custo-benefício é o melhor do mercado.", 11, 4)])])
        ])
    ]
    doc = create_mock_doc(mock_pages)
    result = parse_pdf_to_structured_content(doc)

    # Assertions for structure
    assert len(result) == 2
    assert result[0]['title'] == "Sobre nosso Produto"
    assert result[0]['page'] == 1
    assert "Nossa plataforma é inovadora" in result[0]['content_text']

    assert result[1]['title'] == "Nossos Preços"
    assert result[1]['page'] == 2
    assert "custo-benefício" in result[1]['content_text']

    # Assertions for analysis
    # Section 1 should be about scalability
    assert result[0]['analysis']['scalability']['found'] == True
    assert result[0]['analysis']['predictability']['found'] == False
    assert "<strong>plataforma</strong>" in result[0]['analysis']['scalability']['snippets'][0]

    # Section 2 should be about predictability (pricing)
    assert result[1]['analysis']['predictability']['found'] == True
    assert "<strong>custo-benefício</strong>" in result[1]['analysis']['predictability']['snippets'][0]

def test_no_headings_document():
    """Test a document with only paragraph-style text."""
    mock_pages = [
        create_mock_page([
            create_mock_block([create_mock_line([create_mock_span("Este é o primeiro parágrafo.", 12, 4)])]),
            create_mock_block([create_mock_line([create_mock_span("Este é o segundo parágrafo.", 12, 4)])])
        ])
    ]
    doc = create_mock_doc(mock_pages)
    result = parse_pdf_to_structured_content(doc)

    # Should be grouped into a single "Introduction" section
    assert len(result) == 1
    assert result[0]['title'] == "Introdução"
    assert "primeiro parágrafo" in result[0]['content_text']
