from openai import OpenAI

class HelperGPT:
    def __init__(self, openai_api: str, logger=None):
        self.openAI_api = openai_api
        self.logger = logger

    def _create_connection(self) -> OpenAI:
        client = OpenAI(
            api_key = f"{self.openAI_api}",
        )
        return client

    def plan_route(self, encoded_image: str, history: list[str]) -> str:
        computer_use_prompt = f"""
        You are a GUI scanning agent.
        Your task is to explore software on the screenshot breadth first.
        You are given a screenshot of current screen. 
        Your task is to click a button which could be a link to a next view. 
        Don't click buttons which are just utilities not leading to any view.
        Don't click buttons which consist of only an icon without text.
        If in doubt, go back to the homepage with the Comarch BSS button in top-left.
        Do not click the same element more than once unless it's the homepage button. 
        Ignore windows taskbar. 
        Ignore browser UI. 
        Focus only on the website in the browser.
        
        Output the Result as only the label string of the button to click. 
        Do not append any additional characters.

        Output format
        Reasoning:
        Result:
        
        Below is a list of what you have already clicked. Initially it will be empty, and will get filled overtime.
        You have already clicked: {history}
        
        Let's think step by step. 
        """
        messages = [
            {
                "role": "system",
                "content": computer_use_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

        client = self._create_connection()
        completion = client.chat.completions.create(
            extra_headers={},
            extra_body={},
            model="gpt-4o-mini",
            messages=messages
        )
        result = completion.choices[0].message.content
        print("-----GPT-----\n", result.strip())
        action = result.split("Result:")[-1]
        return action