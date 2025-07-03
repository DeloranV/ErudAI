from time import sleep
import pyautogui
from openai import OpenAI, APIStatusError
import re
import ast
from agent import ActionPerformer
from util import ImageEncoder, Snapshotter
from .helper_gpt import HelperGPT
from .helper_local import HelperEndpoint
from kg import KgExtractor

class AutonomyEmulator:
    def __init__(self,
                 helper_type: str,  # TODO ENUM HELPER TYPES
                 helper_auth: str,
                 connect_kg: bool = False,
                 kg_openai_api = None,
                 kg_n4j_uri = None,
                 kg_n4j_auth = None,
                 base_url: str = "http://127.0.0.1:8000/v1",
                 api_key: str = None,
                 multistep: bool = True,
                 logger = None):
        self.base_url = base_url
        self.api_key = api_key
        self.multistep = multistep
        self.logger = logger
        self.history = ["Customers", "Accounts"]

        if connect_kg:
            self.kg_extractor = KgExtractor(kg_openai_api, kg_n4j_uri, kg_n4j_auth)

        if helper_type == 'endpoint':
            self.helper_base_url = helper_auth[0]
            self.helper_api_key = helper_auth[1]
            self.helper_model_name = helper_auth[2]
            self.helper = HelperEndpoint(self.helper_base_url,
                                         self.helper_api_key,
                                         self.helper_model_name
                                         )

            #"http://127.0.0.1:8008/v1"
            #"OpenGVLab/InternVL3-38B"

        elif helper_type == 'gpt':
            self.helper_openai_api = helper_auth[0]
            self.helper = HelperGPT(openai_api=self.helper_openai_api)

    def execute(self) -> None:
        sleep(2)  # FOR HIDING CHAT WINDOW
        if self.multistep:
            while True:  # DO-WHILE LOOP CONFORMING WITH PEP
                encoded_1 = ImageEncoder.encode(Snapshotter.snapshot(self.logger), logger=self.logger)

                if self.kg_extractor: self.kg_extractor.initialize_cache(encoded_1)

                next_click = self.helper.plan_route(encoded_1, self.history)
                self.history.append(next_click.strip())
                result = self._send(prompt=next_click, encoded_image=encoded_1)

                if self.kg_extractor:
                    encoded_2 = ImageEncoder.encode(Snapshotter.snapshot(self.logger), logger=self.logger)
                    self.kg_extractor.extract_gui_schema(result[0], encoded_2)

                print(self.history)
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

                if result is None:
                    return

    def _create_connection(self) -> OpenAI:
        client = OpenAI(
            api_key=f"{self.api_key}",
            base_url=self.base_url,
        )
        return client

    @staticmethod
    def _escape_single_quotes(text: str) -> str:
        pattern = r"(?<!\\)'"
        return re.sub(pattern, r"\\'", text)

    @staticmethod
    def _parse_action(action_str: str) -> dict[str, str | None | dict] | None:
        try:
            node = ast.parse(action_str, mode='eval')

            if not isinstance(node, ast.Expression):
                raise ValueError("Not an expression")

            call = node.body

            if not isinstance(call, ast.Call):
                raise ValueError("Not a function call")

            if isinstance(call.func, ast.Name):
                func_name = call.func.id
            elif isinstance(call.func, ast.Attribute):
                func_name = call.func.attr
            else:
                func_name = None

            kwargs = {}
            for kw in call.keywords:
                key = kw.arg
                if isinstance(kw.value, ast.Constant):
                    value = kw.value.value
                elif isinstance(kw.value, ast.Str):
                    value = kw.value.s
                else:
                    value = None
                kwargs[key] = value

            return {
                'function': func_name,
                'args': kwargs
            }

        except Exception as e:
            print(f"Failed to parse action '{action_str}': {e}")
            return None

    @staticmethod
    def _parse_to_pyautogui(response: dict[str, str | None | dict]) -> dict[str, str | None | dict] | None:
        try:
            action_dict = response
            action_type = action_dict.get("action_type")
            action_inputs = action_dict.get("action_inputs", {})

            if action_type in ["click"]:
                start_box = action_inputs.get("start_box")
                x1, y1 = 0, 0
                if len(start_box) == 2:
                    x1, y1 = start_box

                ActionPerformer.perform_click([int(x1), int(y1)])
                return response

            if action_type == "type":
                content = action_inputs.get("content", "")
                stripped_content = content

                if content.endswith("\n") or content.endswith("\\n"):
                    stripped_content = stripped_content.rstrip("\\n").rstrip("\n")

                if content:
                    ActionPerformer.perform_input(stripped_content)
                    return response

            if action_type == "finished":
                return None
            return None

        except pyautogui.FailSafeException:
            print("Failsafe triggered")
            return None

    @staticmethod
    def _parse_to_structure_output(text: str) -> dict[str, str | None | dict | dict]:
        text = text.strip()

        assert "Action:" in text
        action_str = text.split("Action:")[-1]

        if "type(content" in action_str:
            def escape_quotes(match):
                content_ = match.group(1)
                return content_

            pattern = r"type\(content='(.*?)'\)"
            content = re.sub(pattern, escape_quotes, action_str)

            action_str = AutonomyEmulator._escape_single_quotes(content)
            action_str = "type(content='" + action_str + "')"

        action_dict = AutonomyEmulator._parse_action(action_str.replace("\n", "\\n").lstrip())

        action_type = action_dict["function"]
        params = action_dict["args"]

        action_inputs = {}
        for param_name, param in params.items():
            param = param.lstrip()
            action_inputs[param_name.strip()] = param

            if "start_box" in param_name or "end_box" in param_name:
                ori_box = param
                numbers = ori_box.replace("(", "").replace(")", "").split(",")

                action_inputs[param_name.strip()] = numbers

        action = {
            "action_type": action_type,
            "action_inputs": action_inputs
        }
        return action

    def _send(self, prompt: str, encoded_image: str) -> None | dict[str, str | None | dict] | tuple[str, None]:
        """
        Sends the request to the model on behalf of the user
        Returns the coordinates of the queried element
        Args:
            @arg prompt - Prompt query to send to the model
            @arg encoded_image - Encoded snapshot given in the form of a string
        """
        computer_use_prompt = f"""
        You need to click the button with the specified label to complete the task. 
        Do not click the same element more than once.
        Ignore windows taskbar. 
        Ignore browser UI.
        Focus only on the website in the browser.

        ## Output Format
        ```
        Thought: ...
        Action: ...
        ```

        ## Action Space

        click(start_box='(x1,y1)')
        left_double(start_box='<|box_start|>(x1,y1)<|box_end|>')
        type(content='xxx') # Use escape characters \\', \\\", and \\n in content part to ensure we can parse the content in normal python string format. If you want to submit your input, use \\n at the end of content. 
        scroll(start_box='<|box_start|>(x1,y1)<|box_end|>', direction='down or up or right or left')
        wait() #Sleep for 5s and take a screenshot to check for any changes.

        ## Note
        - Use English in `Thought` part.
        - Describe only the label of the element you've clicked in `Thought` part. Do not say anything else.

        ## User Instruction
        Click {prompt}
        """
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": computer_use_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

        try:
            client = self._create_connection()
            completion = client.chat.completions.create(
                extra_headers={},
                extra_body={},
                model="ByteDance-Seed/UI-TARS-1.5-7B",
                messages=messages,
                # top_p=None,
                # temperature=None,
                # max_tokens=150,
                # stream=False,
                # seed=None,
                # stop=None,
                # frequency_penalty=None,
                # presence_penalty=None
            )

            result = completion.choices[0].message.content
            print("-----TARS-----\n", result.strip(), "\n---------------HISTORY----------------")
            if self.logger:
                self.logger.log_text_data("response", result)

            if "wait" in result:
                return "wait", None

            structured = AutonomyEmulator._parse_to_structure_output(result)
            return AutonomyEmulator._parse_to_pyautogui(structured)

        except APIStatusError as e:
            print("api error", e)
            return None

        finally:
            if self.logger:
                self.logger.log_text_data("prompt", prompt)