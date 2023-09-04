import cv2
import mediapipe as mp
import numpy as np
import math

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

############################################################################################################################################
###################################################### COORDINATE SYSTEM COMPUTATION  ######################################################
############################################################################################################################################

POSE_ARTICULATIONS = {
    # Dictionary of pose articulations mapping to their indices.
    14:(12,14,16), 13:(11,13,15), 24:(12,24,26), 23:(11,23,25), 26:(24,26,28), 25:(23,25,27),
    28:(26,28,32), 27:(25,27,31), 12:(24,12,11)
}

def coordinate_system_initialisation(lmList,articulation):
    """
    Initialize the coordinate system for a specific articulation.

    Args:
        lmList (numpy.array): Landmark list.
        articulation (int): Index of the articulation.

    Returns:
        tuple: Tuple containing the coordinate system vectors.
    """   
    p1 = POSE_ARTICULATIONS[articulation][0]
    p2 = POSE_ARTICULATIONS[articulation][1]
    p3 = POSE_ARTICULATIONS[articulation][2]

    O = np.array([lmList[p2,0],lmList[p2,1],lmList[p2,2]])
    OY = np.array([lmList[p1,0],lmList[p1,1],lmList[p1,2]]) - O
    norm_OY = np.linalg.norm(OY)
    if np.linalg.norm(OY) !=0 : 
        OY = OY / norm_OY
    temp = O - np.array([lmList[p3,0],lmList[p3,1],lmList[p3,2]]) 
    
    OZ = np.cross(temp,OY)
    if np.linalg.norm(OZ) !=0 : 
        OZ = OZ / np.linalg.norm(OZ)
    
    OX = np.cross(OY,OZ)
    if np.linalg.norm(OZ) !=0 : 
        OX = OX / np.linalg.norm(OX)
    P = np.array([[OX[0],OY[0],OZ[0]],
                [OX[1],OY[1],OZ[1]],
                [OX[2],OY[2],OZ[2]]])

    newList = (P@(lmList.T-np.expand_dims(O,axis=1))).T
    newList = newList / norm_OY
    return newList,[O,OX,OY,OZ,P]  


############################################################################################################################################
################################################################ VIDEO PROCESSING  #########################################################
############################################################################################################################################

def process_image(image_path, all_poses, nompose):
    """
    Process a video to extract pose landmarks and angles.

    Args:
        image_path (str): Path to the video file.
        all_poses (dict): Dictionary to store pose angles for different poses.
        nompose (str): Name of the pose.

    Returns:
        dict: Updated dictionary containing pose angles.
    """
    process = True
    #Processing of the video 
    with mp_pose.Pose(min_detection_confidence=0.5,min_tracking_confidence=0.5) as pose:
        #import the video to process
        video = cv2.VideoCapture(image_path)
        width,height = video.get(cv2.CAP_PROP_FRAME_WIDTH),video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        n = 33
        frame = 0
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
                        lmList[i,2] = landmarks[i].z*10
                except : 
                    pass

                # render detection
                mp_drawing.draw_landmarks(img,results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                        mp_drawing.DrawingSpec(color=(245,117,66),thickness=2,circle_radius=2),
                                        mp_drawing.DrawingSpec(color=(245,66,230),thickness=2,circle_radius=2))


                new_lmList,coordinate_system = list(coordinate_system_initialisation(lmList,12))

                
                print(lmList)
                print("")
                print(new_lmList)

                #adding each angle of articulation to a dictionnary
                #print(new_lmList)
                img = cv2.resize(img, (960, 540)) 


                cv2.imshow('image',img)
            
                frame += 1 
                cv2.waitKey(1)  
            else : 
                process = False

    #free the windows
    cv2.destroyAllWindows()
    video.release()
    all_poses[nompose] = new_lmList
    return all_poses