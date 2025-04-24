import openai
import datetime
import time
import keyboard
from openai import OpenAI

from agent import ActionPerformer
from util import ImageEncoder, Snapshotter

class Query:
    def __init__(self, api_key: str,
                 base_url: str = "https://openrouter.ai/api/v1",
                 multistep: bool=True,
                 debug: bool=False):

        self.api_key = api_key
        self.base_url = base_url
        self.multistep = multistep
        self.debug = debug

        self.image_encoder = ImageEncoder()
        self.snapshotter = Snapshotter()
        self.action_performer = ActionPerformer()

        if debug:
            self.log_name = f"logs/LOG_{time.time()}.txt"
            with open(self.log_name, "x") as log_file:
                log_file.write(f"LOG FILE FROM {datetime.datetime.now().isoformat()}\n")

    def _create_connection(self) -> OpenAI:
        client = OpenAI(
            api_key = f"{self.api_key}",
            base_url = self.base_url,
        )
        return client

    def _prepare_result(self, output: str) -> list:
        coordsStr = output[1:-1].split(',')

        coordsInt = []
        for coordinate in coordsStr:
            coordsInt.append(int(coordinate))

        coordsInt[0] = round(coordsInt[0] * 1280 / 1000)
        coordsInt[1] = round(coordsInt[1] * 720 / 1000)

        return coordsInt

    def execute(self, prompt: str):
        if self.multistep:
            while True: # DO-WHILE LOOP CONFORMING WITH PEP
                encoded = self.image_encoder.encode(self.snapshotter.snapshot())
                result = self._send(prompt=prompt, encoded_image=encoded)
                if result is None or keyboard.is_pressed("e"):
                    break
                self.action_performer.performClick(result)
                time.sleep(2)

    def _send(self, prompt: str, encoded_image: str) -> list | None:
        """
        Sends the request to the model on behalf of the user
        Returns the coordinates of the queried element
        Args:
            prompt - Prompt query to send to the model
            encoded_image - Encoded snapshot given in the form of a string
        """
        try:
            client = self._create_connection()
            completion = client.chat.completions.create(
                extra_headers={},
                extra_body={},
                model="bytedance-research/ui-tars-72b:free",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Give me coordinates in [x,y] to click for the following action: {prompt}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                # top_p = None,
                # temperature = None,
                # max_tokens = 150,
                # stream = False,
                # seed = None,
                # stop = None,
                # frequency_penalty = None,
                # presence_penalty = None
            )

            result = completion.choices[0].message.content

            if "finish" in result:
                return None

            coordinates = self._prepare_result(result)

            if self.debug:
                with open(self.log_name, 'a') as log_file:
                    log_file.write(f"<coordinates>: {coordinates}\n")
                    log_file.write(f"<response>: {result}\n")

            return coordinates

        except openai.APIStatusError as e:
            print(e)

        finally:
            if self.debug:
                with open(self.log_name, 'a') as log_file:
                    log_file.write(f"<prompt>: {prompt}\n")
                    #log_file.write(f"Encoded image: {encoded_image}\n")
