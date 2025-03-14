from flask import Flask, request, jsonify
from extract_img_pdf import extract_images_from_stream
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/extract-images", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    pdf_file = request.files["pdf"]
    
    image_urls = extract_images_from_stream(pdf_file, pdf_file.filename)
    
    return jsonify({"images": image_urls})

@app.route("/")
def home():
    return "This is the API server"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)