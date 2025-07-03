import base64
from io import BytesIO

class ImageEncoder:
    @staticmethod
    def encode(source: BytesIO, logger = None) -> str:
        """
        Encodes a given BytesIO image with base64 encoding

        :param source: Image to encode given as a BytesIO object
        :param logger: Optional logger object to pass
        :return: B64 encoded image in the form of a string
        """
        encoded = base64.b64encode(source.getvalue()).decode("utf-8")

        if logger and logger.log_encoded_image is True:
            logger.log_encoded_img_data(str(encoded))

        return encoded
