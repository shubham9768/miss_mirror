import multiprocessing
import os
import queue
import traceback

import face_recognition
import numpy
import requests
import time

import sys
from PIL import Image
from io import BytesIO

master = os.path.abspath(os.path.join(__file__, '..', '..'))
sys.path.append(master)

from sandbox import camera_ip


def load_faces_from_db():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    directory_string = dir_path + '/faces'
    directory = os.fsencode(directory_string)
    # Load the faces
    decoded_faces = {}
    print("Loading faces from database.")
    for file_ in os.listdir(directory):
        filename = os.fsdecode(file_)
        if filename.endswith(".jpg"):
            img_full_path = directory_string + '/' + filename
            # Load the jpg file into a numpy array
            image = face_recognition.load_image_file(img_full_path)
            image_face_encoding = face_recognition.face_encodings(image)[0]
            decoded_faces[filename[:-4]] = image_face_encoding
    print('>>>>{} faces from db loaded.'.format(len(decoded_faces)))
    face_names_local = decoded_faces.keys()
    return face_names_local, decoded_faces


def start_engine(names_queue, kill_queue):
    face_names, decoded_faces = load_faces_from_db()
    print("Recognise engine in.")
    url_text = camera_ip.get_url()
    count = 0
    t = 0
    while True:
        tm = time.time()
        if kill_queue.qsize():
            print("Recognise engine out.")
            break
        try:
            response = requests.get(url_text)
            img = Image.open(BytesIO(response.content))
            img = numpy.array(img)
            if img.any():
                face_encodings = face_recognition.face_encodings(img)
                for face_encoding in face_encodings:
                    res_raw = face_recognition.compare_faces(list(decoded_faces.values()), face_encoding)
                    if len(res_raw) > 0:
                        res = zip(res_raw, face_names)
                        for i, j in res:
                            if i:
                                print("Camera Engine : ", j)
                                names_queue.put(j)
                        if not any(res_raw):
                            print("Camera Engine : Unknown")
                            names_queue.put("Unknown")
        except:
            traceback.print_exc()
            print("Some problem in recognising process")
        t += (time.time() - tm)
        count += 1
        if count>3:
            break
        print("Count : {}".format(count))
    print("avg:{}".format(t / count))


if __name__ == '__main__':
    y=time.time()
    kq = multiprocessing.Queue()
    q = multiprocessing.Queue()
    print("{} going in".format(time.time()-y))
    start_engine(kq, q)