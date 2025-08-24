import re

def analyze_text(text):
    """
    Analyzes the text extracted from a PDF to find business model insights,
    including snippets of text as evidence.
    """
    # Define keywords for each category
    recurrence_keywords = ["mensalidade", "assinatura", "plano mensal", "recorrente", "mensal", "anual"]
    pricing_keywords = ["preço", "valor", "r$", "reais", "dólares", "usd", "brl", "€", "eur"]

    # Split text into sentences. A simple split by '.' is used for simplicity.
    # A more robust solution would use NLP libraries like NLTK or spaCy.
    sentences = [s.strip() for s in text.split('.') if s.strip()]

    # --- Analysis ---
    recurrence_snippets = []
    pricing_snippets = []

    for sentence in sentences:
        lower_sentence = sentence.lower()
        # Check for recurrence keywords
        if any(keyword in lower_sentence for keyword in recurrence_keywords):
            if sentence not in recurrence_snippets:
                recurrence_snippets.append(sentence)

        # Check for pricing keywords
        if any(keyword in lower_sentence for keyword in pricing_keywords):
            if sentence not in pricing_snippets:
                pricing_snippets.append(sentence)

    # --- Return results ---
    analysis_results = {
        'has_recurrence': bool(recurrence_snippets),
        'recurrence_snippets': recurrence_snippets,
        'has_pricing': bool(pricing_snippets),
        'pricing_snippets': pricing_snippets,
    }

    return analysis_results
