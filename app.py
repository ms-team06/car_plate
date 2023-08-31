import cv2
from utils import *
import numpy as np
import os

# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/DETECTION',methods=['GET'])
def DETECTION():
    return render_template('detect.html')

@app.route('/upload',methods=['GET'])
def RECTANGLE():
    return render_template('upload.html')

@app.route('/file_upload', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        img_dir = './uploads/'
        files = request.files.getlist("files")
        for f in files:
            f.save(os.path.join(img_dir, secure_filename(f.filename)))
        return render_template('detect.html')

@app.route('/yolo', methods=['GET', 'POST'])
def yolo(): 
    if request.method == 'POST':
        img_dir = './uploads/'
        Plate_Detection('./uploads/')

@app.route('/color', methods=['GET', 'POST'])
def yolo(): 
    if request.method == 'POST':
        img_dir = './uploads/'
        Color_Detection('./uploads/plate')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)