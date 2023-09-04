"""
Title: VisualTango Web Application
Description: This Flask web application serves as a platform for processing and visualizing dance poses using computer vision techniques.
Author: [Your Name]
Date: [Date]

This module defines a Flask web application that provides functionalities for uploading dance videos, processing them using computer vision techniques, and visualizing the results.

Requirements:
- Flask: A micro web framework for Python.
- cloudinary: A cloud-based image and video management solution. // you can choose which external storage service you want, you just need to implement it.
- cv2: OpenCV library for computer vision tasks.
- redis: An in-memory data structure store used for caching. // Used with the worker as a broker between the web process and the worker process.
- celery: A distributed task queue for asynchronous processing. // Used to process the video and not overload the web process.
- Flask-SocketIO: Extension for WebSocket support in Flask applications. // Used for bi-directional communiation between client and server.
- apscheduler: A Python library for scheduling tasks.

"""

from flask import Flask, render_template,redirect,url_for,session,request,jsonify
import cloudinary,os

cloudinary.config(
    cloud_name= os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key= os.environ.get('CLOUDINARY_API_KEY'),
    api_secret= os.environ.get('CLOUDINARY_API_SECRET')
)

import cv2,json,cloudinary.uploader
from src.angle_calculation import process_image
from werkzeug.utils import secure_filename
from src.angle_classification import  angle_classification
from src.pose import Pose
from src.animation_creation import animation_creation
from datetime import datetime
import redis
import celery
from celery import Celery
from celery.schedules import crontab
from celery.result import AsyncResult
from config import Config
from flask_socketio import SocketIO,emit,join_room
from urllib import parse
import atexit
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
socketio = SocketIO(app)
app.config['UPLOAD_TIMEOUT'] = 300
celery = Celery(app.name)
celery.conf.update(broker_url = os.environ.get('REDIS_URL'),
                   result_backend= os.environ.get('REDIS_URL'))
app.secret_key = 'VISION'

# Set Redis connection:
redis_url = parse.urlparse(Config.REDIS_URL)
r = redis.StrictRedis(host=redis_url.hostname, port=redis_url.port, db=1, password=redis_url.password)


print(cloudinary.config)
UPLOAD_FOLDER = 'static/temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def generate_unique_filename(filename,id):
    """
    Generate a unique filename based on the given filename and ID.
    
    Args:
        filename (str): The original filename.
        id (str): The unique identifier.
        
    Returns:
        str: The generated unique filename.
    """
    base_filename, file_extension = os.path.splitext(filename)
    return f"{base_filename}_{id}{file_extension}"

def generate_unique_identifier():
    """
    Generate a unique identifier based on the current timestamp.
    
    Returns:
        str: The generated unique identifier.
    """
    return datetime.now().strftime('%Y%m%d%H%M%S%f')

def delete_temp():
    """
    Delete temporary files from the 'static/temp' folder.
    This function is scheduled to run at regular intervals.
    """
    folder_path = 'static/temp/'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier {file_path}: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_temp, trigger="interval", hours=12)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

celery.conf.beat_schedule = {
    'delete-temp': {
        'task': 'delete_temp',
        'schedule': crontab(hour=0, minute=0),  
    },
}

@celery.task
def process_video(filename,filename_save,id):
    """
    Celery task executed on a celery worker which rocess a video for pose analysis and classification.
    Need some modification to work with the external storage service. 
    You'll need to access the uploaded video on the storage service, then process it.

    Args:
        filename (str): The name of the uploaded video file.
        filename_save (str): The name to save the processed results.
        id (str): The unique identifier for the task.

    Returns:
        dict: The result of the pose analysis.
    """
    res = process_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    poses=[]
    to_save = angle_classification(poses,res)
    with open(f"static/temp/{filename_save}", "w") as output_file:
        output_file.write(to_save)
    os.remove(f'{app.config["UPLOAD_FOLDER"]}/{filename}')
    return res 

@celery.task
def process_animation(filename,filename_animation,public_id_video,id):
    """
    Process a video to create an animation of dance poses.
    Need some modification to work with the external storage service. 
    You'll need to access the uploaded video on the storage service, then process it.
    
    Args:
        filename (str): The name of the uploaded video file.
        filename_animation (str): The name to save the animation results.
        public_id_video (str): The public ID of the video in Cloudinary.
        id (str): The unique identifier for the task.

    Returns:
        dict: The result of the animation creation.
    """
    url_video = cloudinary.CloudinaryVideo(public_id_video)
    res = animation_creation(url_video)
    serialized_res = json.dumps(res)
    r.set(f"res_modelisation_{id}",serialized_res)
    r.set(f"filename_animation_{id}",filename_animation)
    r.set(f"filename_{id}",filename)
    r.set(f"public_key_{id}",public_id_video)
    # print(filename_animation)
    """with open(f"static/temp/{filename_animation}", "w") as f:
        f.writelines(["%s\n" % item for item in res])

    os.remove(f'{app.config["UPLOAD_FOLDER"]}/{filename}')"""
    return res 

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r   

@app.route('/')
def index():
    """
    Route: / (Root)

    Generates a unique identifier for the session, sets it in the session, and redirects to the 'menu' route.

    Returns:
        Response: Redirects to the 'menu' route.
    """
    identifier = generate_unique_identifier()
    session['id'] = identifier
    cloudinary.config(cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), api_key=os.getenv('CLOUDINARY_API_KEY'), 
    api_secret=os.getenv('API_SECRET'))
    return redirect(url_for('menu',id=identifier))

@app.route('/menu/<id>')
def menu(id):
    """
    Route: /menu/<id>

    Displays the menu page with the provided identifier.

    Args:
        id (str): The unique identifier.

    Returns:
        Response: Renders the 'index.html' template with the provided identifier.
    """
    return render_template('index.html',id=id)


@app.route('/visualtango/<id>', methods=['POST'])
def visualtango(id): 
    """
    Route: /visualtango/<id>

    Processes data and displays the 'visualtango.html' template.

    Args:
        id (str): The unique identifier.

    Returns:
        Response: Renders the 'visualtango.html' template with the provided identifier.
    """
    filename_save = generate_unique_filename("save.txt",id)
    with open(f"static/temp/{filename_save}", "w") as output_file:
            output_file.write("00003000")
    return render_template('visualtango.html',id=id)

@app.route('/processing_classification/<id>', methods=['POST'])
def classification(id):
    """
    Route: /processing_classification/<id>

    Processes an uploaded file for classification and initiates asynchronous processing.
    Redirects to the 'processing_classification.html' template.

    Args:
        id (str): The unique identifier.

    Returns:
        Response: Renders the 'processing_classification.html' template with the provided identifier.
    """
    if request.method == 'POST' and 'input_file1' in request.files:
        file = request.files['input_file1']
        if file.filename == '':
            return redirect(url_for('menu',id=id))
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename_save = generate_unique_filename("save.txt",id)
        all_poses = process_video.delay(filename,filename_save,id)
        session['task_id'] = all_poses.id	
    return render_template('processing_classification.html',id=id)

@app.route('/classification/<id>', methods=['POST'])
def result_classification(id):
    """
    Route: /classification/<id>

    Displays the result of the classification process.

    Args:
        id (str): The unique identifier.

    Returns:
        Response: Renders the "visualtango.html" template.
    """
    return render_template("visualtango.html")



@app.route('/processing_modelisation/<id>', methods=['POST'])
def modelisation(id):
    """
    Route: /processing_modelisation/<id>

    Processes an uploaded file for modelization and initiates asynchronous processing.
    Redirects to the 'processing_modelisation.html' template.

    Args:
        id (str): The unique identifier.

    Returns:
        Response: Renders the 'processing_modelisation.html' template with the provided identifier.
    """
    if request.method == 'POST' and 'input_file2' in request.files:
        file = request.files['input_file2']
        if file.filename =='':
            return redirect(url_for('menu',id=id))
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        upload_result = None
        if file :
            print(file)
            
            with open(os.path.join(app.config['UPLOAD_FOLDER'],filename), 'rb') as video_file:
                upload_result = cloudinary.uploader.upload_large(video_file,
                                                                resource_type="video",
                                                                public_id=f"myfolder/mysubfolder/id_{filename}")
                app.logger.info(upload_result)
            
        
        #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename_animation = generate_unique_filename("AnimationFile.txt",id)
        
        results = process_animation.delay(filename,filename_animation,upload_result['public_id'],id)
        
        session['task_id'] = results.id
    return render_template('processing_modelisation.html',id=id)

@app.route('/modelisation/<id>', methods=['POST'])
def result_modelisation(id,):
    """
    Route: /modelisation/<id>

    Displays the result of the modelization process.

    Args:
        id (str): The unique identifier.

    Returns:
        Response: Renders the "modelisation.html" template.
    """
    poses=[]
    serialized_res = r.get(f"res_modelisation_{id}")
    if serialized_res is not None:
        res = json.loads(serialized_res)
    filename_animation = r.get(f"filename_animation_{id}")
    if filename_animation is not None:
        filename_animation = filename_animation.decode("utf-8")
    filename = r.get(f"filename_{id}")
    if filename is not None:
        filename = filename.decode("utf-8")
    public_id = r.get(f"public_key_{id}")
    if public_id is not None:
        public_id = public_id.decode("utf-8")
    cloudinary.api.delete_resources([public_id], resource_type="video")

    with open(f"static/temp/{filename_animation}", "w") as f:
        f.writelines(["%s\n" % item for item in res])
    os.remove(f'{app.config["UPLOAD_FOLDER"]}/{filename}')
    return render_template("modelisation.html")

@socketio.on('join')
def on_join(data):
    """
    SocketIO Event Handler: join

    Joins a room in SocketIO communication.

    Args:
        data (dict): Data containing the room information.
    """
    room = data['room']
    join_room(room)
    print(f"User joined room: {room}")

@socketio.on('connect')
def on_connect():
    """
    SocketIO Event Handler: connect

    Handles the connection of a SocketIO client.
    """
    print('Client connected')
    emit('status', {'msg': 'From the server : Connected'})

@socketio.on('request_modelisation_status')
def modelisation_status(data):
    """
    SocketIO Event Handler: request_modelisation_status

    Responds to the client's request for modelization status.
    Emits appropriate events indicating whether the task is completed or still processing.

    Args:
        data (dict): Data containing room information.

    Notes:
        The following events may be emitted:
        - If the task is completed: emit 'modelisation_completed'
        - If the task is still processing: emit 'modelisation_processing'
    """
    print('request received')
    room = data['room']
    task_id=session['task_id']
    task = celery.AsyncResult(task_id)
    if task.ready() :
        print('tache finie !')      
        emit('modelisation_completed',{'id': session['id'],'room':room},room=room)
    else :
        print('task not finished')
        emit('modelisation_processing',{'id': session['id'],'room':room},room=room)

@socketio.on('request_classification_status')
def classification_status(data):
    """
    SocketIO Event Handler: request_classification_status

    Responds to the client's request for classification status.
    Emits appropriate events indicating whether the task is completed or still processing.

    Args:
        data (dict): Data containing room information.

    Notes:
        The following events may be emitted:
        - If the task is completed: emit 'classification_completed'
        - If the task is still processing: emit 'classification_processing'
    """
    print('request received')
    room = data['room']
    task_id=session['task_id']
    task = celery.AsyncResult(task_id)
    if task.ready() :
        print('tache finie !')      
        emit('classification_completed',{'id': session['id'],'room':room},room=room)
    else :
        print('task not finished')
        emit('classification_processing',{'id': session['id'],'room':room},room=room)

if __name__ == '__main__':
    socketio.run(app,debug=True)
    
