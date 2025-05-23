import json
from openai import OpenAI

class Planner:
    def __init__(self, openai_api: str, logger = None):
        self.openAI_api = openai_api
        self.logger = logger

    def plan_route(self, user_prompt, database_nodes):
        client = OpenAI(api_key=self.openAI_api)

        if self.logger is not None:
            self.logger.log_text_data("PLANNER-received-nodes", database_nodes)

        response = client.responses.create(
            model="gpt-4.1",
            input=f"""Given a list of node names, their types and their relationships to other nodes in a neo4j database and a user prompt, 
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
        if self.logger:
            self.logger.log_text_data("PLANNER-output-nodes", response.output_text)

        return json.loads(response.output_text)

