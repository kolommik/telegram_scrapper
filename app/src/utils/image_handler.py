import os


class ImageHandler:
    def __init__(self, directory):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save_image(self, image, filename):
        path = os.path.join(self.directory, filename)
        image.save(path)

    def resize_image(self, image, size):
        return image.resize(size)
