import os
import fitz  # PyMuPDF
import json
import csv
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from urllib.parse import quote
from analysis import analyze_presentation

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
RESULTS_FOLDER = 'results'
LEADS_FILE = 'leads.csv'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
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
        analysis_results = analyze_presentation(doc)

        html_content = ""
        for page in doc:
            html_content += page.get_text("html")
        doc.close()

        html_filename = f"{filename_base}.html"
        html_path = os.path.join(app.config['CONVERTED_FOLDER'], html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        results_filename = f"{filename_base}.json"
        results_path = os.path.join(app.config['RESULTS_FOLDER'], results_filename)
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=4)

        return redirect(url_for('show_diagnosis', filename_base=filename_base))

    return 'Invalid file type'

@app.route('/diagnosis/<filename_base>')
def show_diagnosis(filename_base):
    results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{filename_base}.json")
    html_filename = f"{filename_base}.html"

    try:
        with open(results_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
    except FileNotFoundError:
        return "Analysis data not found.", 404

    return render_template('diagnosis.html', analysis=analysis_data, html_filename=html_filename)

@app.route('/converted/<filename>')
def converted_file(filename):
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename)

@app.route('/contact', methods=['POST'])
def handle_contact():
    # --- Capture Lead Data ---
    form_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'whatsapp': request.form.get('whatsapp'),
        'message': request.form.get('message'),
        'filename_base': request.form.get('filename_base')
    }

    # --- Combine with Analysis Data ---
    analysis_summary = {}
    try:
        results_path = os.path.join(app.config['RESULTS_FOLDER'], f"{form_data['filename_base']}.json")
        with open(results_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        for criterion, data in analysis_data.items():
            analysis_summary[f'found_{criterion}'] = data['found']
    except Exception as e:
        print(f"Error reading analysis file: {e}")

    # --- Save to CSV File ---
    lead_data_to_save = {**form_data, **analysis_summary}
    fieldnames = ['timestamp', 'name', 'email', 'whatsapp', 'message', 'filename_base',
                  'found_recurrence', 'found_predictability', 'found_scalability',
                  'found_growth', 'found_profitability']

    file_exists = os.path.isfile(LEADS_FILE)
    with open(LEADS_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(lead_data_to_save)

    # --- Prepare for Thank You Page ---
    whatsapp_url = f"https://wa.me/5511911595028?text={quote(f'Olá, meu nome é {form_data["name"]}. Vi o diagnóstico e gostaria de agendar.')}"

    return render_template('thank_you.html', whatsapp_url=whatsapp_url)

if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER, CONVERTED_FOLDER, RESULTS_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(debug=True)
