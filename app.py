import os
import PyPDF2
from flask import Flask, request, render_template, jsonify
import language_tool_python  # For grammar and style check

app = Flask(__name__)

# Set maximum file size (16MB for example)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Create the 'uploads' directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()  # Extract text from each page
    return text

# Initialize the LanguageTool client
tool = language_tool_python.LanguageTool('en-US')

# Function to analyze text for ambiguity and inconsistency
def analyze_text(text):
    analysis = {
        "is_ambiguous": False,
        "is_inconsistent": False,
        "suggestions": []
    }

    # Ambiguity check - looking for common ambiguous words
    ambiguous_words = ["may", "might", "could", "up to", "possibly"]
    for word in ambiguous_words:
        if word.lower() in text.lower():
            analysis["is_ambiguous"] = True
            analysis["suggestions"].append(f"Consider replacing ambiguous word: '{word}'")

    # Inconsistency check - looking for contradictory statements (simple example)
    if "cannot" in text and "handle" in text:
        analysis["is_inconsistent"] = True
        analysis["suggestions"].append("Potential contradiction found: 'cannot handle'")

    # Grammar and style check using LanguageTool
    matches = tool.check(text)
    for match in matches:
        analysis["suggestions"].append(f"Grammar/Style suggestion: {match.message} (at position {match.offset}-{match.offset+match.errorLength})")

    return analysis

# Endpoint for the root URL to render the upload form
@app.route('/')
def index():
    return render_template('index.html')  # Render the index.html page

# Endpoint to handle PDF file upload and display recommendations on the same page
@app.route('/analyze', methods=['POST'])
def analyze_pdf():
    if 'file' not in request.files:
        return render_template('index.html', error="No file part")
    
    file = request.files['file']
    
    if file.filename == '':
        return render_template('index.html', error="No selected file")
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        return render_template('index.html', error="Only PDF files are allowed")
    
    # Save the uploaded PDF file
    pdf_path = os.path.join('uploads', file.filename)
    file.save(pdf_path)
    
    # Extract text from the uploaded PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    
    # Perform the analysis on the extracted text
    analysis = analyze_text(extracted_text)
    
    # Render the analysis with the extracted text and recommendations
    return render_template('index.html', 
                           analysis=analysis, 
                           extracted_text=extracted_text[:1000])  # Show part of the text

if __name__ == '__main__':
    app.run(debug=True)
