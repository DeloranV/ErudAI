from time import sleep
import pyautogui
from openai import OpenAI, APIStatusError
import re
import ast
from agent import ActionPerformer
from util import ImageEncoder, Snapshotter

class Query:
    def __init__(self,
                 api_key: str,
                 base_url: str,
                 multistep: bool=True,
                 logger = None):
        self.api_key = api_key
        self.base_url = base_url
        self.multistep = multistep
        self.logger = logger

    def execute(self, prompt: str):
        sleep(1)    # FOR HIDING CHAT WINDOW
        if self.multistep:
            while True: # DO-WHILE LOOP CONFORMING WITH PEP
                encoded = ImageEncoder.encode(Snapshotter.snapshot(self.logger), logger=self.logger)
                result = self._send(prompt=prompt, encoded_image=encoded)

                if result is None:
                    return

    def _create_connection(self) -> OpenAI:
        client = OpenAI(
            api_key = f"{self.api_key}",
            base_url = self.base_url,
        )
        return client

    @staticmethod
    def _escape_single_quotes(text):
        pattern = r"(?<!\\)'"
        return re.sub(pattern, r"\\'", text)

    @staticmethod
    def _parse_action(action_str):
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
    def _parse_to_pyautogui(response):
        try:
            action_dict = response
            action_type = action_dict.get("action_type")
            action_inputs = action_dict.get("action_inputs", {})

            if action_type in ["click"]:
                start_box = action_inputs.get("start_box")

                x2, y2 = 0, 0
                if len(start_box) == 2:
                    x1, y1 = start_box
                    #x2 = round(int(x1) * 1280 / 1000)
                    #y2 = round(int(y1) * 720 / 1000)

                ActionPerformer.perform_click([int(x1), int(y1)])
                return 1

            if action_type == "type":
                content = action_inputs.get("content", "")
                stripped_content = content

                if content.endswith("\n") or content.endswith("\\n"):
                    stripped_content = stripped_content.rstrip("\\n").rstrip("\n")

                if content:
                    ActionPerformer.perform_input(stripped_content)
                    return 1
                    # if content.endswith("\n") or content.endswith("\\n"):
                    #     pyautogui.press("enter")

            if action_type == "finished":
                return None

            return None

        except pyautogui.FailSafeException:
            print("Failsafe triggered")
            return None

    @staticmethod
    def _parse_to_structure_output(text):
        text = text.strip()

        assert "Action:" in text
        action_str = text.split("Action:")[-1]

        if "type(content" in action_str:
            def escape_quotes(match):
                content_ = match.group(1)
                return content_

            pattern = r"type\(content='(.*?)'\)"
            content = re.sub(pattern, escape_quotes, action_str)

            action_str = Query._escape_single_quotes(content)
            action_str = "type(content='" + action_str + "')"

        action_dict = Query._parse_action(action_str.replace("\n", "\\n").lstrip())

        action_type = action_dict["function"]
        params = action_dict["args"]

        action_inputs = {}
        for param_name, param in params.items():
            param = param.lstrip()
            action_inputs[param_name.strip()] = param

            if "start_box" in param_name or "end_box" in param_name:
                ori_box = param
                # Remove parentheses and split the string by commas
                numbers = ori_box.replace("(", "").replace(")", "").split(",")

                # Convert to float and scale by 1000
                action_inputs[param_name.strip()] = numbers

        action = {
            "action_type": action_type,
            "action_inputs": action_inputs
        }
        return action

    def _send(self, prompt: str, encoded_image: str):
        """
        Sends the request to the model on behalf of the user
        Returns the coordinates of the queried element
        Args:
            prompt - Prompt query to send to the model
            encoded_image - Encoded snapshot given in the form of a string
        """
        computer_use_prompt = f"""
        You are a GUI agent. You are given a task, with screenshots. You need to perform the next action to complete the task.
        
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
        finished(content='xxx') # When all steps are done and destination goal was reached. Use escape characters \\', \\", and \\n in content part to ensure we can parse the content in normal python string format.
        
        
        ## Note
        - Use English in `Thought` part.
        - Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.
        
        ## User Instruction
        {prompt}
        """

        try:
            client = self._create_connection()
            completion = client.chat.completions.create(
                extra_headers={},
                extra_body={},
                model="ByteDance-Seed/UI-TARS-1.5-7B",
                messages=[
                    {
                        "role": "user",
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

            if self.logger:
                self.logger.log_text_data("response", result)

            if "wait" in result:
                return "wait", None

            structured = Query._parse_to_structure_output(result)
            return Query._parse_to_pyautogui(structured)

        except APIStatusError as e:
            print("api error", e)
            return None

        finally:
            if self.logger:
                self.logger.log_text_data("prompt", prompt)
