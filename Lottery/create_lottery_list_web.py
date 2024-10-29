import os
import re
import sys
import json
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory
import create_lottery_list

UPLOAD_FOLDER = './Upload/'
DOWNLOAD_FOLDER = './Download'
ALLOWED_EXTENSIONS = set(['.csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    if any([filename.endswith(i) for i in ALLOWED_EXTENSIONS]):
        return True
    else:
        return False

home_page = '''
    <!doctype html>
    <title>Generate Lottery List</title>
    <h1>Please Upload csv File</h1>
    <h2>How to use?</h2>
    <p>Step 1: 上傳csv檔案，並輸入機率欄位（欄位數字是多少該用戶就會有幾筆資料，等同於他被抽到的機率）。</p>
    <p>Step 2: 輸入抽獎條件的依據欄位還有次數，例如：至少要騎乘一次，那就輸入rent_ct, 1。（如果沒有條件就不需輸入，保留原本網頁上的文字）</p>
    <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file value="檔案"></p>
        <p><input type=text name="probability_column" value="輸入機率欄位名稱"></p>
        <p><input type=text name="filter_column" value="輸入篩選欄位名稱"></p>
        <p><input type=text name="filter_value" value="輸入篩選閾值(>=n次)"></p>
        <p><input type=submit name=send value="提交">
    </form>
    <p>感謝SRE的協助！</p>
'''

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file'] # get file
        tmp_json = dict()
        for key, val in request.form.items():
            tmp_json[key] = val
        submmited_file = secure_filename(file.filename)
        tmp_json['upload_path'] = os.path.join(app.config['UPLOAD_FOLDER'], submmited_file)
        tmp_json['download_path'] = os.path.join(app.config['DOWNLOAD_FOLDER'], 'completed_' + submmited_file)
        if file and allowed_file(file.filename): # check file form
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], submmited_file))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], re.sub('.csv', '.json', submmited_file)), 'w', encoding='utf-8') as f:
                json.dump(tmp_json, f, ensure_ascii=False, indent=4)
            sys.argv = [submmited_file]
            create_lottery_list.main(submmited_file)
            return redirect(url_for('download_file', filename=submmited_file))
    return home_page

@app.route('/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    downlaod_name = 'completed_' + filename
    return send_from_directory(directory=app.config['DOWNLOAD_FOLDER'], filename=downlaod_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0')