import json
from openai import OpenAI
from typing import Any

class Planner:
    def __init__(self, openai_api: str, logger = None):
        self.openAI_api = openai_api
        self.logger = logger

    def plan_route(self, user_prompt: str, database_nodes: str) -> Any:
        """
        Method responsible for sending a query to a helper model, which is given a list of nodes extracted from the
        graph database along with a user query and approximates which view will likely be the destination of a given action

        :param user_prompt: Action prompt given by the user in the form of a string
        :param database_nodes: All nodes - comma separated, extracted from a graph DB, given in the form of a string
        :return: A JSON deserialized into a python dictionary containing ['start_node'] and ['end_node'] keys with their respective values
        """
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