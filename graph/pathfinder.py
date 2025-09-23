import neo4j
import asyncio
from .planner import Planner

class Pathfinder:
    def __init__(self,
                 uri: str,
                 auth: tuple[str, str],
                 db_name: str,
                 openai_api,
                 logger = None):
        self.driver = neo4j.AsyncGraphDatabase.driver(uri, auth=auth)
        self.DB_NAME = db_name
        self.planner = Planner(openai_api)
        self.logger = logger

    async def test_connectivity(self) -> None:
        """
        Helper method which throws an exception if there is a problem with neo4j connection
        """
        await self.driver.verify_connectivity()

    async def get_all_nodes(self) -> str: # TODO tuple instead of str context var
        """
        Method responsible for extracting all nodes stored in a neo4j database and joining them to form a single comma separated string

        :return: String containing comma separated names of stored nodes
        """
        async with self.driver.session(database=self.DB_NAME) as session:
            result = await session.run("MATCH (n)-[r]->(v) RETURN n.name, type(r), v.name")
            result = await result.data()

            context_var = ""
            for record in result:
                context_var += " ".join([record.get('n.name'), record.get('type(r)'), record.get('v.name'), "\n"])
            return context_var

    @staticmethod
    def generate_path_query(start_node: str, end_node: str) -> str:
        """
        Method responsible for constructing a pathfinding Cypher query, based on given a start and end node

        :param start_node: Node from which the path originates, given as a string of its name
        :param end_node: Node to which the path will be found, given as a string of its name
        :return: A complete Cypher query for performing a path search, given in the form of a string
        """
        path_query = f"""
                MATCH p = SHORTEST 1 ({{name: '{start_node}'}})-->+({{name: '{end_node}'}})
                RETURN p
                """
        return path_query

    async def get_ui_path(self, user_prompt: str) -> str:
        """
        Method responsible for giving a complete path of UI elements and views through which to navigate, in order to complete a given action

        :param user_prompt: Action prompt given by the user in the form of a string
        :return: A path of elements to go through, in order to reach the goal, returned in the form of a string
        """
        start_end = self.planner.plan_route(user_prompt, await self.get_all_nodes())
        path_query = Pathfinder.generate_path_query(start_end['start_node'], start_end['end_node'])

        async with self.driver.session(database=self.DB_NAME) as session:
            record = await session.run(path_query)
            record = await record.single()
        if not record:
            return ""

        path = record['p']
        nodes = path.nodes
        rels = path.relationships

        lines = []
        for src, rel, dst in zip(nodes, rels, nodes[1:]):
            src_type = src.get('type', "")
            dst_type = dst.get('type', "")
            lines.append(f"{src['name']} {src_type} {rel.type} {dst['name']} {dst_type}")

        return "\n".join(lines)

