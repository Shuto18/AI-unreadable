from flask import Flask, request, render_template, send_file
import os
from PyPDF2 import PdfReader #PDF読み込み用ライブラリ
from reportlab.pdfgen import canvas #PDF描画用ライブラリ
from reportlab.lib.pagesizes import letter  # 用紙サイズ定義
from reportlab.pdfbase import pdfmetrics  # フォント登録用
from reportlab.pdfbase.ttfonts import TTFont  # TrueTypeフォント用
import random  # 乱数生成用
from pdfminer.high_level import extract_pages  # PDFレイアウト解析用
from pdfminer.layout import LTTextContainer, LTChar  # レイアウト要素
from io import BytesIO  # メモリ上のバイナリデータ操作用

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'   # アップロードファイルの保存先フォルダ
OUTPUT_FOLDER = 'outputs'   # 出力ファイルの保存先フォルダ
os.makedirs(UPLOAD_FOLDER, exist_ok=True)   # フォルダが存在しなければ作成
os.makedirs(OUTPUT_FOLDER, exist_ok=True)  # フォルダが存在しなければ作成


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
        c = canvas.Canvas(output_buffer, pagesize=letter)  # reportlabのCanvasオブジェクト作成

        for page_layout in extract_pages(input_path):  # pdfminerでページごとのレイアウトを解析
            print(f"Processing page...")
            text_elements = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):  # テキストコンテナの場合
                    for text_line in element:
                        for character in text_line:
                            if isinstance(character, LTChar):  # 個々の文字の場合
                                text_elements.append({
                                    'text': character.get_text(),
                                    'x': character.x0,
                                    'y': page_layout.height - character.y1,  # reportlabの座標系に合わせる
                                    'fontname': character.fontname,
                                    'fontsize': character.size
                                })

            for element in text_elements:
                noisy_text = add_noise_to_text(element['text'])  # テキストにノイズを追加
                try:
                    if element['fontname'] not in pdfmetrics.getFontNames():
                        try:
                            # より現実的なフォント登録処理は複雑になるため、ここでは省略
                            c.setFont("Helvetica", element['fontsize'])
                        except Exception as e:
                            c.setFont("Helvetica", element['fontsize'])
                    else:
                        c.setFont(element['fontname'], element['fontsize'])

                    c.drawString(element['x'], element['y'], noisy_text)  # ノイズ付きテキストを描画
                except Exception as e:
                    print(f"Error drawing text: {e}")

            c.showPage()  # ページを保存

        c.save()  # PDFを保存
        return True

    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません。")
        return False
    except Exception as e:
        print(f"予期せぬエラー: {e}")
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
        file.save(filepath)  # アップロードされたPDFを一時保存

        output_buffer = BytesIO()  # メモリ上のバッファ
        if process_pdf_for_obfuscation(filepath, output_buffer):
            output_buffer.seek(0)  # バッファの先頭に戻る
            # 処理済みPDFをダウンロードとして送信
            return send_file(output_buffer, as_attachment=True, download_name='obfuscated_' + file.filename)
        else:
            return 'PDF処理中にエラーが発生しました。'
    return 'PDFファイルのみアップロード可能です。'

if __name__ == '__main__':
    app.run(debug=True)