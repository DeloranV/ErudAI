from util import ImageEncoder, Snapshotter
from agent import ActionPerformer, Query

snapshotter = Snapshotter()
image_encoder = ImageEncoder()
action_performer = ActionPerformer()

api_key = open("api_key", "r").read()

query = Query(prompt="Close browser window",
              debug=True)

encoded = image_encoder.encode(snapshotter.snapshot())

result = query.send(encoded_image=encoded,
                    api_key=api_key,
                    base_url="https://fn7lxcome3tixe20.us-east-1.aws.endpoints.huggingface.cloud/v1/"
                    )

action_performer.perform(result)
#testcomment