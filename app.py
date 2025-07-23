# app.py
import os
import base64
from flask import Flask, render_template, request, send_file, jsonify
from fpdf import FPDF
import csv
import io
import fitz  # PyMuPDF
import traceback

# --- Setup ---
app = Flask(__name__)
ALLOWED_FONTS = {
    "Arial": "Arial", "Times": "Times", "Courier": "Courier",
    "Roboto": "Roboto", "Bahnschrift": "Bahnschrift"
}
BLOCK_ROWS, BLOCK_COLS = 2, 8
ITEMS_PER_BLOCK = (BLOCK_ROWS * BLOCK_COLS) - 1 # 15

# --- Helper Functions ---
def wrap_text(pdf, text, max_width):
    # This function remains the same
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        if pdf.get_string_width(current_line + " " + word) < max_width:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

def draw_block(pdf, start_x, start_y, data_for_block, cell_width, cell_height, line_height):
    """Draws a single 2x8 block at a specific location with the given data."""
    data_iterator = iter(data_for_block)
    for r in range(BLOCK_ROWS):
        for c in range(BLOCK_COLS):
            # Check if this is the last cell in the block (which is always empty)
            if r == BLOCK_ROWS - 1 and c == BLOCK_COLS - 1:
                pdf.rect(start_x + c * cell_width, start_y + r * cell_height, cell_width, cell_height)
                continue

            # Try to get the next text item
            text = next(data_iterator, None)
            
            # --- Draw cell and content ---
            cell_x = start_x + c * cell_width
            cell_y = start_y + r * cell_height
            pdf.rect(cell_x, cell_y, cell_width, cell_height)

            if text:
                text = str(text)
                writable_width = cell_height * 0.8
                lines = wrap_text(pdf, text, writable_width)
                total_text_height = len(lines) * line_height
                center_x = cell_x + (cell_width / 2)
                center_y = cell_y + (cell_height / 2)

                with pdf.rotation(90, x=center_x, y=center_y):
                    current_y_text = center_y - (total_text_height / 2) + (line_height / 2)
                    for line in lines:
                        line_width = pdf.get_string_width(line)
                        current_x_text = center_x - (line_width / 2)
                        pdf.text(current_x_text, current_y_text, line)
                        current_y_text += line_height

# --- PDF Generation Logic ---
def generate_pdf_from_data(data_list, cell_width, cell_height, font_family, font_size, orientation):
    if orientation == 'L':
        page_width, page_height = 297, 210
    else:
        page_width, page_height = 210, 297

    pdf = FPDF(orientation=orientation, unit='mm', format='A4')
    
    if font_family == "Roboto":
        pdf.add_font('Roboto', '', 'fonts/roboto.ttf')
    elif font_family == "Bahnschrift":
        pdf.add_font('Bahnschrift', '', 'fonts/bahnschrift.ttf')
        
    pdf.set_font(font_family, size=font_size)
    line_height = pdf.font_size * 1.2
    
    data_idx = 0
    while data_idx < len(data_list):
        pdf.add_page()

        # --- Calculate positions for the two blocks ---
        block_width = BLOCK_COLS * cell_width
        block_height = BLOCK_ROWS * cell_height
        
        # Center the blocks horizontally
        x_centered = (page_width - block_width) / 2
        
        # Position blocks vertically with some space
        vertical_gap = page_height - (2 * block_height)
        y_top = vertical_gap / 3 # Position the top block 1/3 down the gap
        y_bottom = y_top + block_height + (vertical_gap / 3) # Position the bottom block

        # --- Populate and draw blocks ---
        # First block
        block1_data = data_list[data_idx : data_idx + ITEMS_PER_BLOCK]
        draw_block(pdf, x_centered, y_top, block1_data, cell_width, cell_height, line_height)
        data_idx += ITEMS_PER_BLOCK
        
        # Second block (only if there's still data)
        if data_idx < len(data_list):
            block2_data = data_list[data_idx : data_idx + ITEMS_PER_BLOCK]
            draw_block(pdf, x_centered, y_bottom, block2_data, cell_width, cell_height, line_height)
            data_idx += ITEMS_PER_BLOCK
            
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

def get_data_from_request(request):
    text_data = []
    if 'csv_file' in request.files and request.files['csv_file'].filename != '':
        file = request.files['csv_file']
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.reader(stream)
        text_data = [row[0] for row in reader if row]
    else:
        default_text = request.form.get('default_text', 'A. Student')
        # Generate enough default items to show 2 full blocks (30 items)
        text_data = [default_text] * 35 
    return text_data

def handle_request(request):
    form_data = request.form
    cell_width = float(form_data.get('cell_width', 29))
    cell_height = float(form_data.get('cell_height', 40))
    font_size = int(form_data.get('font_size', 10))
    orientation = form_data.get('orientation', 'L')
    font_family = form_data.get('font_family', 'Arial')
    
    if font_family not in ALLOWED_FONTS: font_family = 'Arial'
    
    text_data = get_data_from_request(request)
    
    # Pass only the relevant parameters
    pdf_buffer = generate_pdf_from_data(text_data, cell_width, cell_height, font_family, font_size, orientation)
    return pdf_buffer

# --- Flask Routes (remain the same) ---
@app.route('/')
def index():
    return render_template('index.html', fonts=ALLOWED_FONTS)

@app.route('/generate', methods=['POST'])
def generate():
    pdf_buffer = handle_request(request)
    return send_file(pdf_buffer, as_attachment=True, download_name='generated_layout.pdf', mimetype='application/pdf')

@app.route('/preview', methods=['POST'])
def preview():
    try:
        pdf_buffer = handle_request(request)
        doc = fitz.open(stream=pdf_buffer, filetype="pdf")
        
        image_data_urls = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            encoded_string = base64.b64encode(img_bytes).decode('utf-8')
            data_url = f"data:image/png;base64,{encoded_string}"
            image_data_urls.append(data_url)
        
        doc.close()
        return jsonify({"pages": image_data_urls})

    except Exception as e:
        print(f"Error during preview generation: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=35124, debug=True)