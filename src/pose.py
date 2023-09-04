class Pose:
    """
    Represents a pose with various attributes that describe its characteristics.

    Attributes:
        _name (list): List of pose names.
        _height (list): List of height variations.
        _leg (list): List of leg positions.
        _direction (list): List of directions.
        _angle (list): List of angle variations.
        _slider (list): List of slider values.
        _lean (list): List of leaning positions.

    Methods:
        __init__(name, height, leg, direction, slider, angle, lean):
            Initializes a Pose object with specified attributes.
        get_name():
            Returns the name of the pose.
        get_height():
            Returns the height variation of the pose.
        get_leg():
            Returns the leg position of the pose.
        get_direction():
            Returns the direction of the pose.
        get_angle():
            Returns the angle variation of the pose.
        get_slider():
            Returns the slider value of the pose.
        get_lean():
            Returns the leaning position of the pose.
        get_name_ind():
            Returns the index of the name attribute.
        get_height_ind():
            Returns the index of the height attribute.
        get_leg_ind():
            Returns the index of the leg attribute.
        get_direction_ind():
            Returns the index of the direction attribute.
        get_angle_ind():
            Returns the index of the angle attribute.
        get_slider_ind():
            Returns the index of the slider attribute.
        get_lean_ind():
            Returns the index of the lean attribute.
    """
    def __init__(self,name,height,leg,direction,slider,angle,lean):
        """
        Initializes a Pose object with specified attributes.

        Args:
            name (str): Name of the pose.
            height (str): Height variation of the pose.
            leg (str): Leg position of the pose.
            direction (str): Direction of the pose.
            slider (int): Slider value of the pose.
            angle (int): Angle variation of the pose.
            lean (str): Leaning position of the pose.
        """
        self._name = [ "Collected", "Corssed forward", "Forward", "Backward", "In air forward", "In air backward", "Slide outside", "Wrapped around", "Collected high", "Crossed backward" ]
        self._height = ["straight", "bent", "tiptoe"]
        self._leg = ["right", "left"]
        self._direction = ["north", "northwest", "northeast"]
        self._angle = [0, 30, 60, 90, 120, 150, 180, 270, 360]
        self._slider = [0,1,2,3,4,5,6,7]
        self._lean = ["straight","forward","backward"]
        self._p = self._name.index(name)
        self._h = self._height.index(height)
        self._w = self._leg.index(leg)
        self._d = self._direction.index(direction)
        self._r = self._angle.index(angle)
        self._t = self._slider.index(slider)
        self._l = self._lean.index(lean)

    @property
    def get_name(self):
        return self._name[self._p]
    
    @property
    def get_height(self):
        return self._height[self._h]
    
    @property
    def get_leg(self):
        return self._leg[self._w]
    
    @property
    def get_direction(self):
        return self._direction[self._d]
    
    @property
    def get_angle(self):
        return self._angle[self._r]
    
    @property
    def get_slider(self):
        return self._slider[self._t]
    
    @property
    def get_slider(self):
        return self._lean[self._l]
    
    @property
    def get_name_ind(self):
        return self._p
    
    @property
    def get_height_ind(self):
        return self._h
        
    @property
    def get_leg_ind(self):
        return self._w
    
    @property
    def get_direction_ind(self):
        return self._d
    
    @property
    def get_angle_ind(self):
        return self._r
    
    @property
    def get_slider_ind(self):
        return self._t
    
    @property
    def get_lean_ind(self):
        return self._l