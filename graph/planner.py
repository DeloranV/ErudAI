import json

from openai import OpenAI

class Planner:
    def __init__(self, openAI_api: str):
        self.openAI_api = openAI_api

    def plan_route(self, user_prompt, database_nodes):
        client = OpenAI(api_key=self.openAI_api)

        response = client.responses.create(
            model="gpt-4.1",
            input=f"""Given a list of node names and their relationships in a neo4j database and a user prompt, 
            determine the starting node and ending node for traversing the graph, which will be used for path finding.
            Respond strictly according to the output format provided below.
        
            Output format:
            {{"start_node": "...",
            "end_node": "..."}}
        
            database:
            {database_nodes}
        
            prompt:
            {user_prompt}
            """
        )

        return json.loads(response.output_text)

