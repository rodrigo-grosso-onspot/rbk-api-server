import os
import io
import fitz  # PyMuPDF

UPLOAD_FOLDER = "uploads"
DOMAIN = "https://rbk.onspot.travel"

def extract_images_from_stream(pdf_stream, original_filename):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    pdf_bytes = pdf_stream.read()
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    image_urls = []
    
    for i, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            base_name = os.path.splitext(os.path.basename(original_filename))[0]
            img_filename = f"{base_name}_page{i}_img{img_index}.png"
            img_path = os.path.join(UPLOAD_FOLDER, img_filename)
            
            with open(img_path, "wb") as img_file:
                img_file.write(image_bytes)
            
            image_urls.append(f"{DOMAIN}/uploads/{img_filename}")
    
    return image_urls

def extract_images(pdf_path):
    doc = fitz.open(pdf_path)
    image_urls = []

    for i, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            img_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page{i}_img{img_index}.png"
            img_path = os.path.join(UPLOAD_FOLDER, img_filename)

            with open(img_path, "wb") as img_file:
                img_file.write(image_bytes)

            image_urls.append(f"{DOMAIN}/uploads/{img_filename}")

    return image_urls