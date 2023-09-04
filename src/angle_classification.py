import numpy as np
import ast
from src.pose import Pose
from src.tomatrix import pose_to_matrix

def frobenius(mat1,mat2):
	"""
    Calculate the Frobenius norm between two matrices.

    Args:
        mat1 (numpy.array): First matrix.
        mat2 (numpy.array): Second matrix.

    Returns:
        float: Frobenius norm between the matrices.
    """
	return np.linalg.norm(mat1-mat2,'fro')
	
def angle_classification(poses,all_poses):
	"""
    Classify angles based on Frobenius distance and select the best-matching pose.

    Args:
        poses (list): List to store the selected poses.
        all_poses (dict): Dictionary containing angles for each frame.

    Returns:
        str: Serialized representation of the selected pose.
    """
	print(f"all_poses = {all_poses}")
	with open("src/output/angle_for_classification.txt", 'r') as file:
		angle_for_classification = file.read()
		angle_for_classification = ast.literal_eval(angle_for_classification)
		file.close()
	for frame,value in all_poses.items() :
		L=[(i,frobenius(pose_to_matrix(all_poses[frame]),pose_to_matrix(angle_for_classification[i]))) for i in angle_for_classification.keys()]
		print("\n")
		print(L[0][0])
		# Code pour exécuter le programme Python avec le fichier d'entrée
		# Enregistrer le fichier de sortie
		s=""
		L.sort(key=lambda x: x[1])
		for item in L:
			s+=f'{item[0]}: {item[1]}\n'
		poses.append(eval(L[0][0]))
        
	to_save = ""
	for pose in poses:
		
		#Order in the saved file for 1 pose :
		#Direction
		#Height
		#Name
		#Rotation
		#Slider
		#Weighted leg
		#leaning

		to_save += str(pose._d)
		to_save += str(pose.get_height_ind)
		to_save += str(pose.get_name_ind)
		to_save += str(pose.get_angle_ind)
		to_save += str(pose.get_slider_ind) 
		to_save += str(pose.get_leg_ind)
		to_save += str(pose.get_lean_ind)

	return to_save
	
	
