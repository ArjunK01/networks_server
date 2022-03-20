# You need to implement the "get" and "head" functions.
import os 

class FileReader:
    def __init__(self):
        pass

    def get(self, filepath, cookies):
        """
        Returns a binary string of the file contents, or None.
        """
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                data = f.read()
        else:
            data = None

        return data

    def head(self, filepath, cookies):
        """
        Returns the size to be returned, or None.
        """
        try:
            size = os.path.getsize(filepath)
        except:
            size = None

        return size