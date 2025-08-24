import os
import fitz  # PyMuPDF
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from urllib.parse import quote
from analysis import analyze_presentation

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
RESULTS_FOLDER = 'results'
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

        # --- PDF Processing and Analysis ---
        doc = fitz.open(pdf_path)

        # 1. Perform 5-criteria analysis
        analysis_results = analyze_presentation(doc)

        # 2. Generate basic HTML version for preview
        html_content = ""
        for page in doc:
            html_content += page.get_text("html")
        doc.close()

        # --- Save artifacts ---
        # 1. Save converted HTML
        html_filename = f"{filename_base}.html"
        html_path = os.path.join(app.config['CONVERTED_FOLDER'], html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 2. Save analysis results as JSON
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
    name = request.form.get('name')
    email = request.form.get('email')
    whatsapp = request.form.get('whatsapp')
    message = request.form.get('message')

    # Print lead data to console (server side)
    print(f"--- New Lead ---")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"WhatsApp: {whatsapp}")
    print(f"Message: {message}")
    print(f"----------------")

    # --- Prepare WhatsApp Click-to-Chat Link ---
    business_whatsapp_number = "5511911595028"
    prefilled_text = f"Olá, meu nome é {name}. Vi o diagnóstico do meu PDF e gostaria de agendar a sessão estratégica."
    encoded_text = quote(prefilled_text)
    whatsapp_url = f"https://wa.me/{business_whatsapp_number}?text={encoded_text}"

    return render_template('thank_you.html', whatsapp_url=whatsapp_url)

if __name__ == '__main__':
    for folder in [UPLOAD_FOLDER, CONVERTED_FOLDER, RESULTS_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(debug=True)
