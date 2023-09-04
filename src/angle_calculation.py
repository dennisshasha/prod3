import cv2
import mediapipe as mp
import numpy as np
import math
from flask_socketio import SocketIO,emit
import ast

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

############################################################################################################################################
###################################################### COORDINATE SYSTEM COMPUTATION  ######################################################
############################################################################################################################################


POSE_ARTICULATIONS = {
    # Dictionary of pose articulations mapping to their indices.
    14:(12,14,16), 13:(11,13,15), 24:(12,24,26), 23:(11,23,25), 26:(24,26,28), 25:(23,25,27),
    28:(26,28,32), 27:(25,27,31)
}

COORDINATE_SYSTEM_INIT_DICT = {
    # Dictionary of coordinate system initializations.
    24:(12,24,23), 23:(11,23,24)
} 

# List of articulation indices.
ARTICULATIONS = set([13,14,24,23,26,25,28,27])

def coordinate_system_initialisation(lmList,articulation):
    """
    Initialize the coordinate system for a specific articulation.

    Args:
        lmList (numpy.array): Landmark list.
        articulation (int): Index of the articulation.

    Returns:
        tuple: Tuple containing the coordinate system vectors.
    """    
    if articulation == 24 or articulation ==23:
        p1 = COORDINATE_SYSTEM_INIT_DICT[articulation][0]
        p2 = COORDINATE_SYSTEM_INIT_DICT[articulation][1]
        p3 = COORDINATE_SYSTEM_INIT_DICT[articulation][2]

        O = np.array([lmList[p2,0],lmList[p2,1],lmList[p2,2]])
        OY = np.array([lmList[p1,0],lmList[p1,1],lmList[p1,2]]) - O

        if np.linalg.norm(OY) !=0 : 
            OY = OY / np.linalg.norm(OY)
        temp = O - np.array([lmList[p3,0],lmList[p3,1],lmList[p3,2]]) 
        
        OZ = np.cross(temp,OY)
        if np.linalg.norm(OZ) !=0 : 
            OZ = OZ / np.linalg.norm(OZ)
        
        OX = np.cross(OY,OZ)
        if np.linalg.norm(OX) !=0 : 
            OX = OX / np.linalg.norm(OX)
        P = np.array([[OX[0],OY[0],OZ[0]],
                    [OX[1],OY[1],OZ[1]],
                    [OX[2],OY[2],OZ[2]]])
    else:
        p1 = POSE_ARTICULATIONS[articulation][0]
        p2 = POSE_ARTICULATIONS[articulation][1]
        p3 = POSE_ARTICULATIONS[articulation][2]

        O = np.array([lmList[p2,0],lmList[p2,1],lmList[p2,2]])
        OY = np.array([lmList[p1,0],lmList[p1,1],lmList[p1,2]]) - O

        if np.linalg.norm(OY) !=0 : 
            OY = OY / np.linalg.norm(OY)
        temp = O - np.array([lmList[p3,0],lmList[p3,1],lmList[p3,2]]) 
        
        OX = np.cross(temp,OY)
        if np.linalg.norm(OX) !=0 : 
            OX = OX / np.linalg.norm(OX)
        
        OZ = np.cross(OX,OY)
        if np.linalg.norm(OZ) !=0 : 
            OZ = OZ / np.linalg.norm(OZ)
        P = np.array([[OX[0],OY[0],OZ[0]],
                    [OX[1],OY[1],OZ[1]],
                    [OX[2],OY[2],OZ[2]]])
    return O,OX,OY,OZ,P     
    
def angle(lmList,articulation,coordinate_system):
    """
    Calculate angles for a specific articulation.

    Args:
        lmList (numpy.array): Landmark list.
        articulation (int): Index of the articulation.
        coordinate_system (dict): Dictionary containing the coordinate system for each articulation.

    Returns:
        dict: Dictionary containing angles in degrees.
    """
    p1 = POSE_ARTICULATIONS[articulation][0]
    p2 = POSE_ARTICULATIONS[articulation][1]
    p3 = POSE_ARTICULATIONS[articulation][2]

    # Définition des points
    A = lmList[p1,:]
    B = lmList[p2,:]
    C = lmList[p3,:]
    P = coordinate_system[articulation][4]


    new_A = P@(A-coordinate_system[articulation][0])
    new_B = P@(B-coordinate_system[articulation][0])
    new_C = P@(C-coordinate_system[articulation][0])
    
    # Calcul des vecteurs
    AB = new_A - new_B
    BC = new_B - new_C
    # Normalisation des vecteurs
    if np.linalg.norm(AB) != 0:
        AB = AB / np.linalg.norm(AB) 
    if np.linalg.norm(BC) != 0:   
        BC = BC / np.linalg.norm(BC) 
    
    # Calcul de l'angle d'Euler dans le plan XY
    angle_xy = np.arctan2(BC[1], BC[0]) - np.arctan2(AB[1], AB[0])
    # Calcul de l'angle d'Euler dans le plan XZ
    angle_xz = np.arctan2(BC[2], BC[0]) - np.arctan2(AB[2], AB[0])

    # Calcul de l'angle d'Euler dans le plan YZ
    angle_yz = np.arctan2(BC[2], BC[1]) - np.arctan2(AB[2], AB[1])
    
    # Conversion des angles en degrés
    angle_xy = np.degrees(angle_xy)
    if angle_xy < 0:
        angle_xy += 360 
    if angle_xy >= 180:
        angle_xy -= 360
    angle_xz = np.degrees(angle_xz)
    if angle_xz < 0:
        angle_xz += 360 
    if angle_xz >= 180:
        angle_xz-= 360
    angle_yz = np.degrees(angle_yz)
    if angle_yz < 0:
        angle_yz += 360 
    if angle_yz >= 180:
        angle_yz -= 360
    #print(f"Angle Z: {int(angle_xy)} degrees")
    #print(f"Angle Y: {int(angle_xz)} degrees")
    #print(f"Angle X: {int(angle_yz)} degrees")
    
    return {"x":angle_yz,"y":angle_xz,"z":angle_xy}


############################################################################################################################################
################################################################ VIDEO PROCESSING  #########################################################
############################################################################################################################################

def process_image(file):
    """
    Process a video file and calculate angles for each frame.

    Args:
        file (str): Path to the video file.

    Returns:
        dict: Dictionary containing angles for each frame.
    """
    # Processing code goes here.
    process = True
        #Processing of the video 
    with mp_pose.Pose(min_detection_confidence=0.5,min_tracking_confidence=0.5) as pose:
        
        #import the video to process
        video = cv2.VideoCapture(file)
        width,height = video.get(cv2.CAP_PROP_FRAME_WIDTH),video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        n = 33
        all_poses = {}
        frame = 0
        coordinate_system = {}

        while process:
            success,img = video.read()
            if success:

                #recolor the image
                img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                img.flags.writeable = False

                #detect the pose
                results = pose.process(img)

                #recolor the image
                img.flags.writeable = True
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                lmList = np.zeros((n,3))

                #landmark extraction
                try :
                    landmarks = results.pose_landmarks.landmark
                    for i in range(len(landmarks)):
                        lmList[i,0] = landmarks[i].x*10
                        lmList[i,1] = landmarks[i].y*10
                        lmList[i,2] = landmarks[i].z*10/3
                except : 
                    pass

                # render detection
                mp_drawing.draw_landmarks(img,results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                        mp_drawing.DrawingSpec(color=(245,117,66),thickness=2,circle_radius=2),
                                        mp_drawing.DrawingSpec(color=(245,66,230),thickness=2,circle_radius=2))

                
                for articulation in ARTICULATIONS:
                    coordinate_system[articulation] = list(coordinate_system_initialisation(lmList,articulation))
                #print(frame)
                #adding each angle of articulation to a dictionnary
                angle_dict = {}
                if len(lmList)!=0 :
                    angle_dict["RightHip"]= angle(lmList,24,coordinate_system)
                    angle_dict["LeftHip"] = angle(lmList,23,coordinate_system)
                    angle_dict["RightKnee"] =  angle(lmList,26,coordinate_system)
                    angle_dict["LeftKnee"] = angle(lmList,25,coordinate_system)
                    angle_dict["RightAnkle"] = angle(lmList,28,coordinate_system)
                    angle_dict["LeftAnkle"] = angle(lmList,27,coordinate_system)
                all_poses[frame] = angle_dict
                #print(new_lmList)
                frame += 1
            else : 
                process = False
            #free the windows
    cv2.destroyAllWindows()
    video.release()
    return all_poses
