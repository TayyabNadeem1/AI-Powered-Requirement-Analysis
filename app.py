import os
import PyPDF2
from flask import Flask, request, render_template, jsonify
import language_tool_python  # For grammar and style check
from transformers import pipeline
from textstat import textstat  # For readability scores

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
            page_text = page.extract_text()
            if page_text:
                text += page_text
            else:
                print(f"Text not extracted from page {reader.pages.index(page)}")
    return text

# Initialize the LanguageTool client
tool = language_tool_python.LanguageTool('en-US')

# Initialize the Hugging Face pipelines
nli_model = pipeline("text-classification", model="ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli")
summarizer = pipeline("summarization")
emotion_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
sentiment_analyzer = pipeline("sentiment-analysis")
ner_model = pipeline("ner", aggregation_strategy="simple")

# Function to analyze semantic inconsistencies using an NLI model
def check_semantic_inconsistencies(text):
    sentences = text.split(".")  # Split text into sentences
    results = []
    for i in range(len(sentences) - 1):
        premise = sentences[i].strip()
        hypothesis = sentences[i + 1].strip()
        if premise and hypothesis:  # Ensure neither is empty
            result = nli_model(f"{premise} [SEP] {hypothesis}")
            if result[0]["label"] == "CONTRADICTION":
                results.append(f"Contradiction between: '{premise}' and '{hypothesis}'")
    return results

# Function to analyze text for ambiguity, inconsistency, and grammar issues
def analyze_text(text):
    analysis = {
        "is_ambiguous": False,
        "is_inconsistent": False,
        "suggestions": [],
        "sentiment": [],
        "entities": [],
        "summary": [],
        "emotions": {},
        "readability_scores": {},
        "grammar_issues": [],
        "extracted_text": text[:1000]  # Display only the first 1000 characters as preview
    }

    # Sentiment analysis
    sentiment = sentiment_analyzer(text)
    analysis["sentiment"] = sentiment

    # Named Entity Recognition (NER)
    entities = ner_model(text)
    analysis["entities"] = entities

    # Text summarization
    summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
    analysis["summary"] = summary

    # Emotion analysis
    emotions = emotion_analyzer(text)
    analysis["emotions"] = {
        'labels': [emotion['label'] for emotion in emotions],
        'scores': [emotion['score'] for emotion in emotions]
    }

    # Readability scores
    analysis["readability_scores"] = {
        "Flesch-Kincaid": textstat.flesch_kincaid_grade(text),
        "Gunning Fog": textstat.gunning_fog(text),
        "SMOG Index": textstat.smog_index(text),
        "Coleman-Liau": textstat.coleman_liau_index(text),
        "Automated Readability Index": textstat.automated_readability_index(text),
    }

    # Ambiguity check - looking for common ambiguous words
    ambiguous_words = [
        "may", "might", "could", "up to", "possibly", 
        "some", "several", "many", "few", "rarely", 
        "sometimes", "often", "frequently", "occasionally", "probably", 
        "approximately", "around", "about", "nearly", "almost", 
        "potentially", "likely", "unlikely", "depending", "various", 
        "certain", "generally", "typically", "normally", "usually", 
        "significant", "substantial", "minimal", "moderate", "enough", 
        "adequate", "sufficient", "effective", "efficient", "reasonable", 
        "relevant", "important", "necessary", "required", "expected", 
        "anticipated", "considerable", "relatively", "somewhat", "sort of", 
        "kind of", "partly", "slightly", "largely", "mostly"
    ]

    for word in ambiguous_words:
        if word.lower() in text.lower():
            analysis["is_ambiguous"] = True
            analysis["suggestions"].append(f"Consider replacing ambiguous word: '{word}'")

    # Semantic inconsistency detection
    contradictions = check_semantic_inconsistencies(text)
    if contradictions:
        analysis["is_inconsistent"] = True
        analysis["suggestions"].extend(contradictions)

    # Grammar and style check using LanguageTool
    matches = tool.check(text)
    for match in matches:
        analysis["grammar_issues"].append({
            'message': match.message,
            'context': match.context
        })

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
    
    # If no text is extracted, return an error message
    if not extracted_text:
        return render_template('index.html', error="Could not extract text from the PDF.")
    
    # Perform the analysis on the extracted text
    analysis = analyze_text(extracted_text)
    
    # Render the analysis with the extracted text and recommendations
    return render_template('index.html', 
                           analysis=analysis, 
                           error=None)  # Ensure no error is shown if everything is correct

if __name__ == '__main__':
    app.run(debug=True)
