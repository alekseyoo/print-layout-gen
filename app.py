# app.py
import os
import base64
from flask import Flask, render_template, request, send_file, jsonify
from fpdf import FPDF
import csv
import io
import fitz  # PyMuPDF

# --- Setup ---
app = Flask(__name__)

# NEW: Update the font list with the new custom fonts.
# The key is the name we'll use in the code. The value is for display in the UI.
ALLOWED_FONTS = {
    "Arial": "Arial",
    "Times": "Times",
    "Courier": "Courier",
    "Roboto": "Roboto",
    "Bahnschrift": "Bahnschrift Semibold"
}

# --- Helper Functions ---
def wrap_text(pdf, text, max_width):
    """Wraps text to fit within a max_width. Returns a list of lines."""
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        # Check width with the next word added
        if pdf.get_string_width(current_line + " " + word) < max_width:
            current_line += " " + word if current_line else word
        else:
            # Add the current line to the list and start a new one
            lines.append(current_line)
            current_line = word
    # Add the last line
    lines.append(current_line)
    return lines

# --- PDF Generation Logic ---
def generate_pdf_from_data(data_list, cell_width, cell_height, font_family, font_size, num_rows, num_cols, orientation, skip_last_cell):
    """
    Generates a PDF from a list of strings, with each string in a rotated, wrapped, and centered cell.
    """
    if orientation == 'L':
        page_width, page_height = 297, 210
    else:
        page_width, page_height = 210, 297

    pdf = FPDF(orientation=orientation, unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    
    # --- NEW: Custom Font Registration ---
    # Register fonts if they are not the standard PDF types
    if font_family == "Roboto":
        pdf.add_font('Roboto', '', 'fonts/Roboto-Regular.ttf', uni=True)
    if font_family == "Bahnschrift":
        pdf.add_font('Bahnschrift', '', 'fonts/bahnschrift.ttf', uni=True)
        
    pdf.set_font(font_family, size=font_size)
    line_height = pdf.font_size * 1.2 # Standard line height

    data_index = 0
    while data_index < len(data_list):
        pdf.add_page()
        total_grid_width = num_cols * cell_width
        total_grid_height = num_rows * cell_height
        margin_x = (page_width - total_grid_width) / 2
        margin_y = (page_height - total_grid_height) / 2

        for i in range(num_rows):
            for j in range(num_cols):
                cell_x = margin_x + (j * cell_width)
                cell_y = margin_y + (i * cell_height)
                
                pdf.rect(cell_x, cell_y, cell_width, cell_height)

                is_last_cell_on_page = (i == num_rows - 1 and j == num_cols - 1)
                if skip_last_cell and is_last_cell_on_page:
                    continue

                if data_index < len(data_list):
                    text = str(data_list[data_index])
                    
                    # --- NEW: Margins and Wrapping Logic ---
                    # 10% margin means the writable area is 80% of the cell's dimension
                    # After rotation, the cell's height becomes our effective width for text.
                    writable_width = cell_height * 0.8
                    lines = wrap_text(pdf, text, writable_width)
                    total_text_height = len(lines) * line_height

                    center_x = cell_x + (cell_width / 2)
                    center_y = cell_y + (cell_height / 2)

                    with pdf.rotation(90, x=center_x, y=center_y):
                        # Calculate starting y to center the entire text BLOCK vertically
                        current_y = center_y - (total_text_height / 2) + (line_height / 2)
                        
                        for line in lines:
                            # Calculate starting x to center EACH LINE horizontally
                            line_width = pdf.get_string_width(line)
                            current_x = center_x - (line_width / 2)
                            pdf.text(current_x, current_y, line)
                            current_y += line_height # Move to the next line
                            
                    data_index += 1

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# (The get_data_from_request function remains the same)
def get_data_from_request(request):
    text_data = []
    if 'csv_file' in request.files and request.files['csv_file'].filename != '':
        file = request.files['csv_file']
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.reader(stream)
        text_data = [row[0] for row in reader if row]
    else:
        default_text = request.form.get('default_text', 'A. Student')
        num_rows = int(request.form.get('num_rows', 1))
        num_cols = int(request.form.get('num_cols', 1))
        text_data = [default_text] * (num_rows * num_cols)
    return text_data

def handle_request(request):
    form_data = request.form
    cell_width = float(form_data.get('cell_width', 29))
    cell_height = float(form_data.get('cell_height', 40))
    font_size = int(form_data.get('font_size', 12))
    num_rows = int(form_data.get('num_rows', 2))
    num_cols = int(form_data.get('num_cols', 8))
    orientation = form_data.get('orientation', 'L')
    font_family = form_data.get('font_family', 'Arial')
    skip_last_cell = 'skip_last' in form_data
    if font_family not in ALLOWED_FONTS: font_family = 'Arial'
    text_data = get_data_from_request(request)
    pdf_buffer = generate_pdf_from_data(text_data, cell_width, cell_height, font_family, font_size, num_rows, num_cols, orientation, skip_last_cell)
    return pdf_buffer

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html', fonts=ALLOWED_FONTS)

@app.route('/generate', methods=['POST'])
def generate():
    pdf_buffer = handle_request(request)
    return send_file(pdf_buffer, as_attachment=True, download_name='generated_layout.pdf', mimetype='application/pdf')

@app.route('/preview', methods=['POST'])
def preview():
    """NEW: Generates images for ALL pages and returns them as a JSON object."""
    try:
        pdf_buffer = handle_request(request)
        doc = fitz.open(stream=pdf_buffer, filetype="pdf")
        
        image_data_urls = []
        # Loop through every page in the generated PDF
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            # Encode image bytes to Base64 and create a data URL
            encoded_string = base64.b64encode(img_bytes).decode('utf-8')
            data_url = f"data:image/png;base64,{encoded_string}"
            image_data_urls.append(data_url)
        
        doc.close()
        # Return a JSON response containing a list of all page images
        return jsonify({"pages": image_data_urls})

    except Exception as e:
        print(f"Error during preview generation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)