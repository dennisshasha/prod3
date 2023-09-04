import numpy as np



def pose_to_matrix(pose_data):
    """
    Convert pose data dictionary to a matrix representation.

    Args:
        pose_data (dict): Dictionary containing pose angle data for specific joints.

    Returns:
        numpy.ndarray: Matrix representation of pose data.
    """
    joints = ['RightHip', 'LeftHip', 'RightKnee', 'LeftKnee', 'RightAnkle', 'LeftAnkle']
    matrix = np.zeros((len(joints), 3))

    for i, joint in enumerate(joints):
        matrix[i, 0] = pose_data[joint]['x']
        matrix[i, 1] = pose_data[joint]['y']
        matrix[i, 2] = pose_data[joint]['z']

    return matrix

if __name__=='__main__':

    pose_data = {
        'RightHip': {'x': -19.233294798069664, 'y': -49.681944044371164, 'z': 0.9284795406641535},
        'LeftHip': {'x': -30.00493503652507, 'y': 134.76266254612622, 'z': 6.308758703299456},
        'RightKnee': {'x': 43.67645519097209, 'y': 34.66182394411719, 'z': -12.992847269141635},
        'LeftKnee': {'x': 75.8606986199378, 'y': -172.38526943163788, 'z': 2.7153772800777864},
        'RightAnkle': {'x': -44.34121419038945, 'y': -151.52502497124482, 'z': -60.808317541352835},
        'LeftAnkle': {'x': -59.44710330134808, 'y': 146.91755074558262, 'z': -63.76970978847453}
    }
    pose_matrix = pose_to_matrix(pose_data)
    print(pose_matrix)
