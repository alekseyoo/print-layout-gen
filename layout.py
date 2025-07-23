from fpdf import FPDF

def create_rotated_layout(output_filename, text, cell_width, cell_height, font_size, num_rows, num_cols):
    """
    Generates a printable PDF layout in landscape with rotated text in each cell.

    Args:
        output_filename (str): The name of the output PDF file.
        text (str): The text to be displayed in each cell.
        cell_width (int): The width of each cell in millimeters.
        cell_height (int): The height of each cell in millimeters.
        font_size (int): The font size of the text.
        num_rows (int): The number of rows in the layout.
        num_cols (int): The number of columns in the layout.
    """
    # Set orientation to 'L' for Landscape (297mm wide x 210mm tall)
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=font_size)

    # Calculate margins to center the entire grid on the page
    total_width = num_cols * cell_width
    total_height = num_rows * cell_height
    margin_x = (297 - total_width) / 2
    margin_y = (210 - total_height) / 2

    # Loop through each row and column to draw the cells
    for i in range(num_rows):
        for j in range(num_cols):
            # Calculate the top-left corner of the current cell
            cell_x = margin_x + (j * cell_width)
            cell_y = margin_y + (i * cell_height)

            # Draw the rectangular border for the cell
            pdf.rect(cell_x, cell_y, cell_width, cell_height)

            # Calculate the absolute center of the cell for rotation
            center_x = cell_x + (cell_width / 2)
            center_y = cell_y + (cell_height / 2)

            # Use the rotation context manager to rotate the text 90 degrees
            # The rotation happens around the center point of the cell.
            with pdf.rotation(90, x=center_x, y=center_y):
                # Place the text. We adjust its position to be perfectly centered.
                # `pdf.get_string_width(text) / 2` centers it horizontally.
                # `font_size / 3` is an approximate vertical adjustment for text alignment.
                pdf.text(
                    x=center_x - (pdf.get_string_width(text) / 2),
                    y=center_y + (font_size / 3),
                    txt=text
                )

    pdf.output(output_filename)
    print(f"Successfully created {output_filename}")

if __name__ == '__main__':
    # --- --- --- --- --- --- --- --- --- --- --- --- ---
    #           USER-ADJUSTABLE PARAMETERS
    # --- --- --- --- --- --- --- --- --- --- --- --- ---
    # Parameters are set exactly as you requested.
    output_pdf_name = "final_layout.pdf"
    cell_text = "A. Student"
    
    # Cell dimensions
    width_of_cell = 29  # 29mm wide
    height_of_cell = 40 # 40mm tall
    
    text_font_size = 18
    
    # Layout dimensions
    number_of_rows = 2
    number_of_columns = 8
    # --- --- --- --- --- --- --- --- --- --- --- --- ---

    create_rotated_layout(
        output_filename=output_pdf_name,
        text=cell_text,
        cell_width=width_of_cell,
        cell_height=height_of_cell,
        font_size=text_font_size,
        num_rows=number_of_rows,
        num_cols=number_of_columns
    )