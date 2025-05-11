import base64
from io import BytesIO

class ImageEncoder:
    @staticmethod
    def encode(source: BytesIO, logger = None) -> str:
        """
        Method for encoding a given image

        Returns the encoded image in the form of a string

        Args:
            source - Source image contained in a BytesIO buffer
        """
        encoded = base64.b64encode(source.getvalue()).decode("utf-8")

        if logger and logger.log_encoded_image is True:
            logger.log_encoded_img_data(str(encoded))

        return encoded
