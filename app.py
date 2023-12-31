import face_recognition
import os
import sys
import json
import requests
import cv2
import numpy as np
import math
import flask
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify


app = flask.Flask(__name__)
app.config["DEBUG"] = True


# Helper
def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) *
                 math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'


class FaceRecognition:
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []
    process_current_frame = True

    def __init__(self):
        self.encode_faces()

    def encode_faces(self):
        for image in os.listdir('static/know_faces'):
            face_image = face_recognition.load_image_file(
                f"static/know_faces/{image}")
            face_encoding = face_recognition.face_encodings(face_image)[0]
            name_without_extension = image.split('.')[0]
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(name_without_extension)
        return self.known_face_encodings, self.known_face_names

    def run_recognition(self, frame):

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        print(rgb_small_frame)
        # Find all the faces and face encodings in the current frame of video
        self.face_locations = face_recognition.face_locations(rgb_small_frame)
        self.face_encodings = face_recognition.face_encodings(
            rgb_small_frame, self.face_locations)

        print(self.face_encodings)
        self.face_names = []
        a = False
        for face_encoding in self.face_encodings:
            print("Encoding faces")
            a = True
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(
                self.known_face_encodings, face_encoding)
            name = "Unknown"
            confidence = '???'

            # Calculate the shortest distance to face
            face_distances = face_recognition.face_distance(
                self.known_face_encodings, face_encoding)

            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
                confidence = face_confidence(face_distances[best_match_index])

            self.face_names.append(f'{name} ({confidence})')


        resultApi = flask.jsonify(
            {"face_names": self.face_names, "face_locations": self.face_locations})
        print(a)
        return resultApi
    
faceApp = FaceRecognition()


@app.route('/face_recognition', methods=['POST'])
def recognize():
    if flask.request.method == 'POST':
        # Get the image from post request
        image = flask.request.files['image'].read()
        image = np.fromstring(image, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # Run face recognition
        resultApi = faceApp.run_recognition(image)

        return resultApi
    
##Make web page to upload image
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        img = request.files['image']
        img.save('static/know_faces/'+img.filename)
        return redirect(url_for('home'))






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
        

