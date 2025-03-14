import os
import fitz  # PyMuPDF

UPLOAD_FOLDER = "uploads"
DOMAIN = "https://rbk.onspot.travel"  # Adicione seu domínio aqui

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

            # Retorna a URL completa da imagem
            image_urls.append(f"{DOMAIN}/uploads/{img_filename}")

    return image_urls