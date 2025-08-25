import os
import fitz  # PyMuPDF
import json
import csv
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
app.config['SERVER_NAME'] = 'localhost:5000' # Needed for url_for with _external=True
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

    return render_template('landing_page.html', structured_content=structured_content)


@app.route('/contact', methods=['POST'])
def handle_contact():
    form_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'whatsapp': request.form.get('whatsapp'),
        'message': request.form.get('message'),
        'filename_base': request.form.get('filename_base')
    }

    # --- Generate full context for the lead ---
    analysis_details = {}
    try:
        results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{form_data['filename_base']}.json")
        with open(results_path, "r", encoding="utf-8") as f:
            structured_analysis = json.load(f)

        # Initialize details for CSV
        for criterion in EXPERT_KEYWORDS.keys():
            analysis_details[f'found_{criterion}'] = False
            analysis_details[f'evidence_{criterion}'] = ''

        # Populate details from analysis
        for section in structured_analysis:
            for criterion, data in section['analysis'].items():
                if data['found']:
                    analysis_details[f'found_{criterion}'] = True
                    # Join snippets with a separator
                    evidence_text = " | ".join([s.replace('<strong>', '').replace('</strong>', '') for s in data['snippets']])
                    if analysis_details[f'evidence_{criterion}']:
                        analysis_details[f'evidence_{criterion}'] += " | " + evidence_text
                    else:
                        analysis_details[f'evidence_{criterion}'] = evidence_text

    except Exception as e:
        print(f"Error reading analysis file for CSV: {e}")

    # Generate the permanent link to the diagnosis page
    with app.app_context():
        diagnosis_url = url_for('show_diagnosis', filename_base=form_data['filename_base'], _external=True)

    # --- Save to CSV File ---
    lead_data_to_save = {**form_data, **analysis_details, 'diagnosis_url': diagnosis_url}

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

    whatsapp_url = f"https://wa.me/5511911595028?text={quote(f'Olá, meu nome é {form_data[\"name\"]}. Vi o diagnóstico e gostaria de agendar.')}"

    return render_template('thank_you.html', whatsapp_url=whatsapp_url)

if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(debug=True)
