import neo4j
import json
from openai import OpenAI
DB_NAME = "neo4j"

# UNIFY INTO ONE PROMPT AND TELL IT TO CREATE TWO SEPARATE JSON'S ? (ONE FOR UI ONE FOR KNOWLEDGE)
# IF USING SPLIT PROMPTS - SEND BOTH ASYNCHRONOUSLY !!!

class KgExtractor:
    def __init__(self, openai_api, n4j_uri, n4j_auth):
        self.node_cache = {"response_json": None, "embedded_json": None}
        self.openai_api = openai_api
        self.driver = neo4j.GraphDatabase.driver(n4j_uri, auth=n4j_auth)

    def initialize_cache(self, encoded_image):
        response, embed = self.extract_view(encoded_image)
        self.cache_view(response, embed)

    def extract_gui_schema(self, clicked_button_text, encoded_image):
        response, embed = self.extract_view(encoded_image)
        self.gui_insertion(response, embed, clicked_button_text)

    def extract_view(self, encoded_image):
        print("GUI extraction started")
        PROMPT_GUI = """
        You are a GUI agent tasked with recognizing UI elements in a screenshot and giving a precise description of the gui according to the format below:
        [
          {
            "view_name": "<name_of_view_snake_case>",
            "view_url": "<url_of_view>",
            "elements": [
              {
                "text_in_element": "<...>",
                "element_type": "<...>"
              },
              {
                "text_in_element": "<...>",
                "element_type": "<...>"
              }
            ]
          }
        ]
        Possible element types:
        searchbar
        button
        slider
        input_line

        Do not ignore any UI elements. List everything visible.
        Ignore system tray.
        Replace any non-english characters with english alphabet.
        """
        messages = [
            {
                "role": "developer",
                "content": PROMPT_GUI
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

        client = OpenAI(api_key=self.openai_api)
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages
        )

        response = completion.choices[0].message.content
        responsejs = json.loads(response)[0]

        embed_response = client.embeddings.create(
            input=response,
            model="text-embedding-ada-002"
        )
        embedding = embed_response.data[0].embedding

        return responsejs, embedding

        # CREATE VECTOR INDEX viewEmbeddings IF NOT EXISTS
        # FOR (v:View)
        # ON v.embedding
        # OPTIONS { indexConfig: {
        #  `vector.dimensions`: 1536,
        #  `vector.similarity_function`: 'cosine'
        # }}

    def check_existing(self, embedding):
        with self.driver.session(database=DB_NAME) as session:
            query = f'''
            CALL {{
              CALL db.index.vector.queryNodes('viewEmbeddings', 1, {embedding})
              YIELD node, score
              WHERE score > 0.9
              RETURN node, node.name AS name, score
              UNION
              RETURN null AS node, null AS name, 0.0 AS score
              LIMIT 1
            }}
            RETURN node, name, score
            '''
            similar_view = session.run(query).fetch(1)
            print(similar_view[0]["score"])
            record = similar_view[0]

            if record["score"] > 0.98:
                print("View is already in database")
                node_data = record["node"]
                if node_data:
                    node_properties = dict(node_data.items())
                    normalized_properties = {
                        "view_name": node_properties.get("name"),
                        "view_url": node_properties.get("url"),
                        "elements": node_properties.get("elements", [])
                    }
                    json_format = json.dumps(normalized_properties)
                return json_format
            return None

    def cache_view(self, response, embed):
        if self.check_existing(embed):
            json_format = self.check_existing(embed)
            self.node_cache["response_json"] = json.loads(json_format)

        self.node_cache["response_json"] = response
        self.node_cache["embedded_json"] = embed

    def gui_insertion(self, node1, embed1, clicked_button):
        view_name1 = node1['view_name']
        view_url1 = node1['view_url']

        if self.check_existing(embed1):
            print("View already exists")
            return
        else:
            cached_json = self.node_cache["response_json"]
            cached_embed = self.node_cache["embedded_json"]
            cached_view_name = cached_json["view_name"]
            cached_view_url = cached_json["view_url"]

        with self.driver.session(database=DB_NAME) as session:
            for item in node1['elements']:
                query = f'''

                MERGE (v:View {{name: "{view_name1}", url: "{view_url1}" ,embedding: {embed1}, type: "view"}})
                MERGE (e:UIElement {{name: "{item['text_in_element']}", type: "{item['element_type']}"}})
                MERGE (v)-[:HAS]->(e)
                RETURN v
                '''
                session.run(query)

            for item in cached_json['elements']:
                query = f'''

                MERGE (v:View {{name: "{cached_view_name}", url: "{cached_view_url}" ,embedding: {cached_embed}, type: "view"}})
                MERGE (e:UIElement {{name: "{item['text_in_element']}", type: "{item['element_type']}"}})
                MERGE (v)-[:HAS]->(e)
                RETURN v.name
                '''
                record = session.run(query).fetch(1)[0]
                view2 = record["v.name"]

            query = f'''
            MATCH (v:View {{name: "{view_name1}"}})
            MATCH (e:UIElement {{name: "{clicked_button}"}})
            MERGE (e)-[:LEADS_TO]->(v)
            '''
            session.run(query)