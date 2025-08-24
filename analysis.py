import re
import fitz # PyMuPDF

# --- Keyword Definitions for 5 Criteria ---
# Using lists of tuples to handle variations and provide a canonical name
KEYWORDS = {
    'recurrence': ['assinatura', 'mensalidade', 'recorrente', 'plano mensal', 'anual'],
    'predictability': ['preço', 'custo', 'custa', 'R$', '€', 'US$'],
    'scalability': ['software', 'plataforma', 'automático', 'produto', 'API'],
    'growth': ['expansão', 'crescer', 'novo mercado', 'clientes', 'usuários'],
    'profitability': ['lucro', 'lucratividade', 'margem', 'receita', 'EBITDA', 'ROI']
}

def highlight_keywords(sentence, keywords):
    """Highlights all found keywords in a sentence with <strong> tags."""
    # Create a regex pattern that finds any of the keywords, case-insensitively
    # The `\b` ensures we match whole words only.
    pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
    # Use a lambda function in re.sub to wrap the found word with <strong>
    highlighted_sentence = re.sub(pattern, r'<strong>\1</strong>', sentence, flags=re.IGNORECASE)
    return highlighted_sentence

def analyze_presentation(doc):
    """
    Analyzes a PDF presentation based on 5 business criteria.

    Args:
        doc: A fitz.Document object (from PyMuPDF).

    Returns:
        A dictionary containing the analysis results for each criterion.
    """

    results = {criterion: {'found': False, 'snippets': []} for criterion in KEYWORDS}

    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        # Split text into sentences. A simple split by '.' is used for simplicity.
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        for sentence in sentences:
            found_keywords_in_sentence = {criterion: [] for criterion in KEYWORDS}

            # Check for keywords of each criterion in the sentence
            for criterion, keywords in KEYWORDS.items():
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', sentence, re.IGNORECASE):
                        found_keywords_in_sentence[criterion].append(keyword)

            # If any keywords were found, create and store the snippet
            for criterion, found_keywords in found_keywords_in_sentence.items():
                if found_keywords:
                    # Highlight all found keywords in the sentence
                    highlighted_sentence = highlight_keywords(sentence, found_keywords)

                    snippet = {
                        'page': page_num + 1,
                        'sentence': highlighted_sentence
                    }

                    # Avoid adding duplicate sentences for the same criterion
                    # This check is on the original sentence, not the highlighted one
                    if not any(s['sentence'] == highlighted_sentence for s in results[criterion]['snippets']):
                         results[criterion]['snippets'].append(snippet)

    # Update the 'found' flag for each criterion
    for criterion, data in results.items():
        if data['snippets']:
            data['found'] = True

    return results
