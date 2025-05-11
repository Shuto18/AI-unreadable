from flask import Flask, request, render_template, send_file
import os
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import random
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LAParams
from io import BytesIO
import traceback

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def add_noise_to_text(text, noise_level=0.01):
    """テキストに微小なノイズを加える関数"""
    noisy_text = "".join(
        char + (chr(random.randint(0x3000, 0x30FF)) if random.random() < noise_level else "")
        for char in text
    )
    return noisy_text


def process_pdf_for_obfuscation(input_path, output_buffer):
    """PDFファイルを読み込み、テキストにノイズを加えてreportlabで再描画する関数"""

    try:
        c = canvas.Canvas(output_buffer, pagesize=letter)

        laparams = LAParams()  # layout analysis parameters
        pages = extract_pages(input_path, laparams=laparams)

        for page_layout in pages:
            print("Processing page...")
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        line_text = ""
                        char_info_list = []
                        for character in text_line:
                            if isinstance(character, LTChar):
                                line_text += character.get_text()
                                char_info_list.append({
                                    'x': character.x0,
                                    'y': page_layout.height - character.y1,
                                    'fontname': character.fontname,
                                    'fontsize': character.size
                                })

                        noisy_line_text = add_noise_to_text(line_text)
                        noisy_char_list = list(noisy_line_text)
                        current_char_index = 0

                        for original_char in text_line:
                            if isinstance(original_char, LTChar) and current_char_index < len(noisy_char_list):
                                try:
                                    x = original_char.x0
                                    y = page_layout.height - original_char.y1
                                    text_to_draw = noisy_char_list[current_char_index]
                                    font_name = original_char.fontname
                                    font_size = original_char.size

                                    # 文字コードを明示的に処理
                                    text_to_draw = text_to_draw.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

                                    c.setFont("Helvetica", 12)  # フォントとサイズを固定
                                    c.setFillColorRGB(0, 0, 0)  # テキストの色を黒に固定

                                    # 座標の安全性を確認
                                    if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                                        print(f"Warning: Invalid coordinates x={x}, y={y}")
                                        continue  # 描画をスキップ

                                    c.drawString(x, y, text_to_draw)
                                    current_char_index += 1

                                except Exception as draw_err:
                                    print(f"Error drawing text: {draw_err}")
                                    traceback.print_exc()  # 詳細なエラー情報をログに出力

            c.showPage()

        c.save()
        return True

    except FileNotFoundError:
        print("Error: Input file not found.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()  # 詳細なエラー情報をログに出力
        return False


@app.route('/', methods=['GET'])
def upload_form():
    """ファイルアップロードフォームを表示するルート"""
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """ファイルアップロードと処理を行うルート"""
    if 'pdf_file' not in request.files:
        return 'No file part'
    file = request.files['pdf_file']
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            file.save(filepath)

            output_buffer = BytesIO()
            if process_pdf_for_obfuscation(filepath, output_buffer):
                output_buffer.seek(0)
                return send_file(output_buffer, as_attachment=True, download_name='obfuscated_' + file.filename)
            else:
                return 'Error processing PDF.'

        except Exception as upload_err:
            print(f"File upload error: {upload_err}")
            traceback.print_exc()
            return 'File upload failed.'

        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

    return 'Only PDF files are allowed.'


if __name__ == '__main__':
    app.run(debug=True)