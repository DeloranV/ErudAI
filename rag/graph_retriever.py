import neo4j

class GraphRetriever:
    def __init__(self, uri: str, auth: tuple[str, str], db_name: str):
        self.driver = neo4j.GraphDatabase.driver(uri, auth=auth)
        self.DB_NAME = db_name

    def test_connectivity(self) -> bool:
        self.driver.verify_connectivity()

    def get_ui_context(self) -> str:
        context_var = ""
        with self.driver.session(database=self.DB_NAME) as session:
            result = session.run('MATCH (b)-[r]->(e) RETURN b.name, b.type, type(r), e.name, e.type')

            for record in result:
                begin_name = record.get('b.name')
                begin_type = record.get("b.type")
                relationship_type = record.get("type(r)")
                end_name = record.get("e.name")
                end_type = record.get("e.type")

                context_var += " ".join([begin_name, begin_type, relationship_type, end_name, end_type]) + "\n"

        return context_var