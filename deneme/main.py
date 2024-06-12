from flask import Flask, request, send_file, render_template
import os
import PyPDF2
import pikepdf
import zipfile
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MERGED_FOLDER'] = 'merged'
app.config['COMPRESSED_FOLDER'] = 'compressed'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MERGED_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)

def merge_pdfs(pdf_list, output_path):
    merger = PyPDF2.PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_path)
    merger.close()

def compress_pdf(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        pdf.save(output_path, compress_streams=True)

def optimize_images_in_pdf(input_path, output_path, dpi=150, quality=85):
    # Convert PDF to images
    images = convert_from_path(input_path, dpi=dpi)
    
    # Save the images back to a PDF
    images[0].save(output_path, save_all=True, append_images=images[1:], quality=quality)

def zip_file(file_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, os.path.basename(file_path))

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    uploaded_files = request.files.getlist('pdf_files')
    filenames = []

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        filenames.append(file_path)

    merged_pdf_path = os.path.join(app.config['MERGED_FOLDER'], 'merged.pdf')
    optimized_pdf_path = os.path.join(app.config['MERGED_FOLDER'], 'optimized.pdf')
    compressed_pdf_path = os.path.join(app.config['COMPRESSED_FOLDER'], 'compressed.pdf')

    # Get the name of the first uploaded file without extension for zip file naming
    original_filename = secure_filename(uploaded_files[0].filename)
    zip_filename = f"{os.path.splitext(original_filename)[0]}.zip"
    zip_path = os.path.join(app.config['COMPRESSED_FOLDER'], zip_filename)

    # PDF dosyalarını birleştir
    merge_pdfs(filenames, merged_pdf_path)

    # Birleşik PDF dosyasındaki görüntüleri optimize et
    optimize_images_in_pdf(merged_pdf_path, optimized_pdf_path, dpi=150, quality=85)

    # Optimize edilmiş PDF dosyasını sıkıştır
    compress_pdf(optimized_pdf_path, compressed_pdf_path)

    # Sıkıştırılmış PDF dosyasını ZIP formatında sıkıştır
    zip_file(compressed_pdf_path, zip_path)

    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

if __name__ == '__main__':
    app.run(debug=True)
