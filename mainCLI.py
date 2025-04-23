from util import ImageEncoder, Snapshotter
from agent import ActionPerformer, Query
from rag import GraphRetriever

snapshotter = Snapshotter()
image_encoder = ImageEncoder()
action_performer = ActionPerformer()

n4j_auth_data = open("n4j_auth_data", "r").read().split("\n")
hf_api_key = open("hf_api_key", "r").read()

graph = GraphRetriever(n4j_auth_data[0], (n4j_auth_data[1], n4j_auth_data[2]), "neo4j")
graph.test_connectivity()
context_var = graph.get_ui_context()

query = Query(prompt="Close browser window",
              debug=True)

encoded = image_encoder.encode(snapshotter.snapshot())

result = query.send(encoded_image=encoded,
                    api_key=hf_api_key,
                    base_url="https://fn7lxcome3tixe20.us-east-1.aws.endpoints.huggingface.cloud/v1/"
                    )

action_performer.perform(result)
