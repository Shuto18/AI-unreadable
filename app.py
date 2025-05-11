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



    