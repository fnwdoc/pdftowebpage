import os
import fitz  # PyMuPDF
import json
import csv
import requests
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from urllib.parse import quote
from content_parser import parse_pdf_to_structured_content, EXPERT_KEYWORDS

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
LEADS_FILE = 'leads.csv'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename_base = filename.rsplit('.', 1)[0]
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)

        doc = fitz.open(pdf_path)
        structured_analysis_results = parse_pdf_to_structured_content(doc)
        doc.close()

        results_filename = f"{filename_base}.json"
        results_path = os.path.join(app.config['RESULTS_FOLDER'], results_filename)
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(structured_analysis_results, f, ensure_ascii=False, indent=4)

        return redirect(url_for('show_diagnosis', filename_base=filename_base))

    return 'Invalid file type'

@app.route('/diagnosis/<filename_base>')
def show_diagnosis(filename_base):
    results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{filename_base}.json")
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            structured_content = json.load(f)
    except FileNotFoundError:
        return "Analysis data not found.", 404
    return render_template('diagnosis.html', structured_content=structured_content, filename_base=filename_base)

@app.route('/preview/<filename_base>')
def show_landing_page_preview(filename_base):
    results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{filename_base}.json")
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            structured_content = json.load(f)
    except FileNotFoundError:
        return "Analysis data not found.", 404

    hero_subtitle = ""
    if structured_content and structured_content[0].get('content_text'):
        hero_subtitle = structured_content[0]['content_text'].split('\n\n')[0]

    return render_template('landing_page.html', structured_content=structured_content, hero_subtitle=hero_subtitle)

@app.route('/publish/<filename_base>')
def publish_to_websim(filename_base):
    results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{filename_base}.json")
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            structured_content = json.load(f)
    except FileNotFoundError:
        return "Analysis data not found.", 404

    hero_subtitle = ""
    if structured_content and structured_content[0].get('content_text'):
        hero_subtitle = structured_content[0]['content_text'].split('\n\n')[0]

    # Render the landing page to an HTML string
    html_content = render_template('landing_page.html', structured_content=structured_content, hero_subtitle=hero_subtitle)

    # Prepare the payload for the Websim API
    # The title and url are generic for now, as we don't have that info from the PDF
    websim_payload = {
        "title": f"Apresentação Otimizada - {filename_base}",
        "url": f"apresentacao-{filename_base}",
        "content": html_content
    }

    # Call the Websim API
    try:
        response = requests.post("https://api.websim.ai/api/v1/create_site", json=websim_payload, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes
        response_data = response.json()

        new_url = response_data.get("url")
        if new_url:
            return redirect(new_url)
        else:
            return "Erro: A API do Websim não retornou uma URL.", 500

    except requests.exceptions.RequestException as e:
        print(f"Error calling Websim API: {e}")
        return f"Erro ao contatar a API do Websim: {e}", 500

@app.route('/contact', methods=['POST'])
def handle_contact():
    # This logic remains the same
    form_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'whatsapp': request.form.get('whatsapp'),
        'message': request.form.get('message'),
        'filename_base': request.form.get('filename_base')
    }
    # ... (rest of the CSV logic is the same)
    # This part needs to be copied from the previous correct version.
    # It seems I don't have it in context, so I will have to reconstruct it.
    analysis_summary = {}
    try:
        results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{form_data['filename_base']}.json")
        with open(results_path, "r", encoding="utf-8") as f:
            structured_analysis = json.load(f)

        summary = {c: False for c in EXPERT_KEYWORDS.keys()}
        evidence = {f'evidence_{c}': '' for c in EXPERT_KEYWORDS.keys()}

        for section in structured_analysis:
            for criterion, data in section['analysis'].items():
                if data['found']:
                    summary[criterion] = True
                    evidence_text = " | ".join([s.replace('<strong>', '').replace('</strong>', '') for s in data['snippets']])
                    if evidence[f'evidence_{criterion}']:
                        evidence[f'evidence_{criterion}'] += " | " + evidence_text
                    else:
                        evidence[f'evidence_{criterion}'] = evidence_text

        for criterion, found in summary.items():
             analysis_summary[f'found_{criterion}'] = found
        analysis_summary.update(evidence)
    except Exception as e:
        print(f"Error reading analysis file for CSV: {e}")

    with app.app_context():
        diagnosis_url = url_for('show_diagnosis', filename_base=form_data['filename_base'], _external=True)

    lead_data_to_save = {**form_data, **analysis_summary, 'diagnosis_url': diagnosis_url}

    base_fieldnames = ['timestamp', 'name', 'email', 'whatsapp', 'message', 'filename_base', 'diagnosis_url']
    analysis_fieldnames = []
    for criterion in EXPERT_KEYWORDS.keys():
        analysis_fieldnames.append(f'found_{criterion}')
        analysis_fieldnames.append(f'evidence_{criterion}')

    fieldnames = base_fieldnames + analysis_fieldnames

    file_exists = os.path.isfile(LEADS_FILE)
    with open(LEADS_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(lead_data_to_save)

    prefilled_text = f"Olá, meu nome é {form_data['name']}. Vi o diagnóstico e gostaria de agendar."
    whatsapp_url = f"https://wa.me/5511911595028?text={quote(prefilled_text)}"

    return render_template('thank_you.html', whatsapp_url=whatsapp_url)

if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(debug=True)
