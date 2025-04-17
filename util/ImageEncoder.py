import base64
from io import BytesIO

class ImageEncoder:

    def encode(self, source: BytesIO) -> str:
        """
        Method for encoding a given image

        Returns the encoded image in the form of a string

        Args:
            source - Source image contained in a BytesIO buffer
        """
        encoded = base64.b64encode(source.getvalue()).decode("utf-8")
        return encoded
