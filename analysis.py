import re
import fitz  # PyMuPDF

# --- "Expert" Keyword Dictionary for 5 Criteria ---
# This dictionary is curated for high precision to avoid false positives.
EXPERT_KEYWORDS = {
    'recurrence': ['assinatura', 'mensalidade', 'recorrente', 'plano mensal', 'anual', 'pagamento mensal'],
    'predictability': ['preço', 'preços', 'custo', 'custos', 'custa', 'R$', '€', 'US$', 'investimento', 'custo-benefício'],
    'scalability': ['software', 'plataforma', 'automático', 'produto', 'API', 'escalar', 'sem limite'],
    'growth': ['expansão', 'crescer', 'crescimento', 'novo mercado', 'novos clientes', 'aumentar'],
    'profitability': ['lucro', 'lucratividade', 'margem', 'receita', 'EBITDA', 'ROI', 'retorno sobre o investimento']
}

def highlight_keywords(sentence, keywords):
    """Highlights all found keywords in a sentence with <strong> tags."""
    # Create a regex pattern that finds any of the keywords, case-insensitively.
    # The `\b` ensures we match whole words. The pattern is sorted by length
    # descending to match longer phrases first (e.g., "plano mensal" before "mensal").
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(k) for k in sorted_keywords) + r')\b'
    highlighted_sentence = re.sub(pattern, r'<strong>\1</strong>', sentence, flags=re.IGNORECASE)
    return highlighted_sentence

def analyze_presentation(doc):
    """
    Analyzes a PDF using a high-precision keyword dictionary to check against 5 business criteria.
    """
    results = {criterion: {'found': False, 'snippets': []} for criterion in EXPERT_KEYWORDS}

    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        # A more robust sentence split that handles more cases.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            found_keywords_in_sentence = {criterion: [] for criterion in EXPERT_KEYWORDS}

            # Check for keywords of each criterion in the sentence
            for criterion, keywords in EXPERT_KEYWORDS.items():
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', sentence, re.IGNORECASE):
                        found_keywords_in_sentence[criterion].append(keyword)

            # If any keywords were found, create and store the snippet
            for criterion, found_keywords in found_keywords_in_sentence.items():
                if found_keywords:
                    highlighted_sentence = highlight_keywords(sentence, found_keywords)

                    snippet = {
                        'page': page_num + 1,
                        'sentence': highlighted_sentence
                    }

                    # Avoid adding duplicate sentences for the same criterion
                    if not any(s['sentence'] == highlighted_sentence for s in results[criterion]['snippets']):
                         results[criterion]['snippets'].append(snippet)

    # Update the 'found' flag for each criterion
    for criterion, data in results.items():
        if data['snippets']:
            data['found'] = True

    return results
