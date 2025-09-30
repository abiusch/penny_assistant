class ShapeFactory:
    @staticmethod
    def create_shape(shape_type):
        if shape_type == 'circle':
            return Circle()
        if shape_type == 'square':
            return Square()
        return None

class Circle:
    def draw(self):
        return 'circle'

class Square:
    def draw(self):
        return 'square'
