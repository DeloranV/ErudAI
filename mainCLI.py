from util import ImageEncoder, Snapshotter
from agent import ActionPerformer, Query
from rag import GraphRetriever

n4j_auth_data = open("n4j_auth_data", "r").read().split("\n")
hf_api_key = open("hf_api_key", "r").read()

graph = GraphRetriever(n4j_auth_data[0], (n4j_auth_data[1], n4j_auth_data[2]), "neo4j")
graph.test_connectivity()
context_var = graph.get_ui_context()

query = Query(api_key=hf_api_key,
              base_url="https://fn7lxcome3tixe20.us-east-1.aws.endpoints.huggingface.cloud/v1/",
              debug=True)

result = query.execute(prompt=f"Enter drafts in my gmail. For navigation use this map of UI elements [{context_var}]")
