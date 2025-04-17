from util import ImageEncoder, Snapshotter
from agent import ActionPerformer, Query

snapshotter = Snapshotter()
image_encoder = ImageEncoder()
action_performer = ActionPerformer()

query = Query(prompt="Pause the running model",
              debug=True)

encoded = image_encoder.encode(snapshotter.snapshot())

result = query.send(encoded_image=encoded,
                    api_key="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",
                    base_url="https://fn7lxcome3tixe20.us-east-1.aws.endpoints.huggingface.cloud/v1/"
                    )

action_performer.perform(result)
