import neo4j
from .planner import Planner

class Pathfinder:
    def __init__(self,
                 uri: str,
                 auth: tuple[str, str],
                 db_name: str,
                 openai_api,
                 logger = None):
        self.driver = neo4j.GraphDatabase.driver(uri, auth=auth)
        self.DB_NAME = db_name
        self.planner = Planner(openai_api)
        self.logger = logger

    def test_connectivity(self):
        self.driver.verify_connectivity()

    def get_all_nodes(self):
        with self.driver.session(database=self.DB_NAME) as session:
            result = session.run("MATCH (n)-[r]->(v) RETURN n.name, type(r), v.name")
            context_var = ""
            for record in result:
                context_var += " ".join([record.get('n.name'), record.get('type(r)'), record.get('v.name'), "\n"])
            return context_var

    @staticmethod
    def generate_path_query(start_node, end_node):
        path_query = f"""
                MATCH p = SHORTEST 1 ({{name: '{start_node}'}})-->+({{name: '{end_node}'}})
                RETURN p
                """
        return path_query

    def get_ui_path(self, user_prompt) -> str:
        context_var = ""
        start_end = self.planner.plan_route(user_prompt, self.get_all_nodes())
        path_query = Pathfinder.generate_path_query(start_end['start_node'], start_end['end_node'])

        with self.driver.session(database=self.DB_NAME) as session:
            result = session.run(path_query)
            for record in result:
                path = record['p']
                nodes = path.nodes
                relationships = path.relationships

            for i in range(len(relationships)):
                nodei = nodes[i]
                if 'type' not in nodei:
                    nodei_type = ""
                else:
                    nodei_type = nodei['type']
                # TODO REFACTOR THIS TRASH
                reli = relationships[i].type

                nodei1 = nodes[i + 1]
                if 'type' not in nodei1:
                    nodei1_type = ""
                else:
                    nodei1_type = nodei1['type']

                context_var += " ".join([nodei['name'], nodei_type, reli, nodei1['name'], nodei1_type, "\n"])

        return context_var

