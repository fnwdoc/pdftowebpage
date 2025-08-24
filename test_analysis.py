import pytest
from analysis import analyze_text

def test_no_keywords():
    """Test with text that has no relevant keywords."""
    text = "This is a simple document about our company services."
    result = analyze_text(text)
    assert not result['has_recurrence']
    assert not result['has_pricing']

def test_recurrence_keywords_found():
    """Test with text containing recurrence keywords."""
    text = "Oferecemos um plano mensal com vantagens exclusivas. A assinatura é flexível."
    result = analyze_text(text)
    assert result['has_recurrence']
    assert not result['has_pricing']

def test_pricing_keywords_found():
    """Test with text containing pricing keywords."""
    text = "O valor do nosso serviço é de R$ 500. Veja a tabela de preços."
    result = analyze_text(text)
    assert not result['has_recurrence']
    assert result['has_pricing']

def test_both_keywords_found():
    """Test with text containing both recurrence and pricing keywords."""
    text = "Nosso plano mensal custa R$ 99,90. A assinatura anual tem desconto."
    result = analyze_text(text)
    assert result['has_recurrence']
    assert result['has_pricing']

def test_case_insensitivity():
    """Test if the analysis is case-insensitive."""
    text = "Nosso PLANO MENSAL tem o melhor PREÇO. O VALOR é R$ 100."
    result = analyze_text(text)
    assert result['has_recurrence']
    assert result['has_pricing']

def test_empty_string():
    """Test with an empty string to ensure it doesn't crash."""
    text = ""
    result = analyze_text(text)
    assert not result['has_recurrence']
    assert not result['has_pricing']
