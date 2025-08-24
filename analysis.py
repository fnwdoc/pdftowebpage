import re

def analyze_text(text):
    """
    Analyzes the text extracted from a PDF to find business model insights.
    """
    # Lowercase the text for case-insensitive search
    lower_text = text.lower()

    # Define keywords for each category
    recurrence_keywords = ["mensalidade", "assinatura", "plano mensal", "recorrente", "mensal", "anual"]
    pricing_keywords = ["preço", "valor", "r$", "reais", "dólares", "usd", "brl", "€", "eur"]

    # --- Analysis ---
    # 1. Check for recurrence model
    has_recurrence = any(keyword in lower_text for keyword in recurrence_keywords)

    # 2. Check for pricing information
    # We check for keywords or for tables that might contain pricing info.
    # A simple check for pricing keywords is a good start.
    has_pricing = any(keyword in lower_text for keyword in pricing_keywords)

    # A more advanced check could look for actual tables, but let's keep it simple for now.

    # --- Return results ---
    analysis_results = {
        'has_recurrence': has_recurrence,
        'has_pricing': has_pricing,
    }

    return analysis_results
