import fitz  # PyMuPDF
import re
from collections import Counter

# --- "Expert" Keyword Dictionary for 5 Criteria ---
EXPERT_KEYWORDS = {
    'recurrence': ['assinatura', 'mensalidade', 'recorrente', 'plano mensal', 'anual', 'pagamento mensal'],
    'predictability': ['preço', 'preços', 'custa', 'R$', '€', 'US$', 'custo-benefício'],
    'scalability': ['software', 'plataforma', 'automático', 'produto', 'API', 'escalar', 'sem limite'],
    'growth': ['expansão', 'crescer', 'crescimento', 'novo mercado', 'novos clientes', 'aumentar'],
    'profitability': ['lucro', 'lucratividade', 'margem', 'receita', 'EBITDA', 'ROI', 'retorno sobre o investimento']
}

def highlight_keywords(sentence, keywords):
    """Highlights all found keywords in a sentence with <strong> tags."""
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(k) for k in sorted_keywords) + r')\b'
    return re.sub(pattern, r'<strong>\1</strong>', sentence, flags=re.IGNORECASE)

def analyze_text_for_criteria(text_block):
    """Analyzes a block of text against the 5 criteria."""
    analysis = {criterion: {'found': False, 'snippets': []} for criterion in EXPERT_KEYWORDS}
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text_block)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue

        for criterion, keywords in EXPERT_KEYWORDS.items():
            found_in_sentence = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', sentence, re.IGNORECASE)]
            if found_in_sentence:
                highlighted = highlight_keywords(sentence, found_in_sentence)
                analysis[criterion]['found'] = True
                analysis[criterion]['snippets'].append(highlighted)
    return analysis

def parse_pdf_to_structured_content(doc):
    """
    Parses a PDF document to identify structural elements (headings, paragraphs)
    and analyzes each section against the 5 criteria.
    """
    structured_content = []

    # First pass: determine the most common font size for paragraphs
    font_sizes = []
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(round(span["size"]))

    if not font_sizes:
        # If no text found, return empty structure
        return []

    # Determine the most common font size to use as the base paragraph size.
    # In case of a tie, the smallest size is chosen.
    counts = Counter(font_sizes)
    max_count = max(counts.values())
    most_common_sizes = [size for size, count in counts.items() if count == max_count]
    base_font_size = min(most_common_sizes)

    # Second pass: build structured content
    current_section = None

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
        for block in blocks:
            if block["type"] == 0: # Text block
                # Consolidate all text from the block
                block_text = ""
                is_heading = False
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Check if any span is significantly larger than base size
                        if round(span["size"]) > base_font_size + 2 and span["flags"] & 16: # Bold flag
                            is_heading = True
                        block_text += span["text"] + " "

                block_text = block_text.strip()
                if not block_text:
                    continue

                if is_heading:
                    # If we find a new heading, save the previous section
                    if current_section:
                        # Analyze the collected content of the previous section
                        current_section['analysis'] = analyze_text_for_criteria(current_section['content_text'])
                        structured_content.append(current_section)

                    # Start a new section
                    current_section = {
                        "type": "section",
                        "title": block_text,
                        "content_text": "",
                        "page": page_num + 1,
                        "analysis": {}
                    }
                elif current_section:
                    # If we are inside a section, add this block as content
                    current_section["content_text"] += block_text + "\n\n"
                else:
                    # Content before the first heading (could be a hero/intro)
                    current_section = {
                        "type": "section",
                        "title": "Introdução",
                        "content_text": block_text + "\n\n",
                        "page": page_num + 1,
                        "analysis": {}
                    }

    # Add the last processed section
    if current_section:
        current_section['analysis'] = analyze_text_for_criteria(current_section['content_text'])
        structured_content.append(current_section)

    # Second pass to determine dominant criterion for each section
    for section in structured_content:
        dominant_criterion = 'scalability' # Default icon
        max_snippets = -1
        for criterion, data in section['analysis'].items():
            if data['found'] and len(data['snippets']) > max_snippets:
                max_snippets = len(data['snippets'])
                dominant_criterion = criterion
        section['dominant_criterion'] = dominant_criterion

    return structured_content
