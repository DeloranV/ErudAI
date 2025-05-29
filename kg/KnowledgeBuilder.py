import os, base64
import time

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import neo4j
import json
from openai import OpenAI, embeddings
import asyncio
DB_NAME = "neo4j"

# UNIFY INTO ONE PROMPT AND TELL IT TO CREATE TWO SEPARATE JSON'S ? (ONE FOR UI ONE FOR KNOWLEDGE)
# IF USING SPLIT PROMPTS - SEND BOTH ASYNCHRONOUSLY !!!

class kg_extractor:
    def __init__(self, openai_api, n4j_uri):
        self.node_cache = {"response_json": None, "embedded_json": None}
        self.openai_api = openai_api
        self.driver = neo4j.GraphDatabase.driver(n4j_uri)

    def initialize_cache(self, encoded_image):
        response, embed = self.extract_view(encoded_image)
        self.cache_view(response, embed)

    def extract_GUI_schema(self, clicked_button_text, encoded_image):
        response, embed = self.extract_view(encoded_image)
        self.GUI_insertion(response, embed, clicked_button_text)

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
        client = OpenAI(api_key=self.openai_api)
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "developer",
                    "content": f"{PROMPT_GUI}"
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

    def cache_view(self, responsejs, embedding):
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
                # Safely extract and serialize the node properties
                if node_data:
                    node_properties = dict(node_data.items())  # or node_data._properties
                    normalized_properties = {
                        "view_name": node_properties.get("name"),
                        "view_url": node_properties.get("url"),
                        "elements": node_properties.get("elements", [])  # Default to [] if missing
                    }
                    json_format = json.dumps(normalized_properties)
                    self.node_cache["response_json"] = json.loads(json_format)
                return

            self.node_cache["response_json"] = responsejs
            self.node_cache["embedded_json"] = embedding

    def GUI_insertion(self, node1, embed1, clicked_button):
        view_name1 = node1['view_name']
        view_url1 = node1['view_url']

        cached_json = self.node_cache["response_json"]
        cached_embed = self.node_cache["embedded_json"]
        cached_view_name = cached_json["view_name"]
        cached_view_url = cached_json["view_url"]

        # Insert new View with embedding
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

    def extract_knowledge_schema(self, encoded_image):
        print("knowledge extraction started")
        PROMPT_TEXT = """
        You are a knowledge builder agent, extracting useful information from screenshots of software.
        Useful information is anything that's not related to the software and GUI itself. In this case, it would be email contents.
        This knowledge will be used to build a concrete vector knowledge base.

        Respond in pure extracted text format, so that it can be inserted as a document into a vector database.

        Ignore the UI elements. Take into consideration only useful information.
        Replace any non-english characters with english alphabet.
        """
        client = OpenAI(api_key=self.openai_api)
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "developer",
                    "content": f"{PROMPT_TEXT}"
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
        )

        response = completion.choices[0].message.content

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )

        all_splits = text_splitter.split_text(response)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

        vector_store = Chroma(
            collection_name="knowledge_base",
            embedding_function=embeddings,
            persist_directory="./vector_knowledge_base"
        )

        ids = vector_store.add_texts(all_splits)

    # def vector_contents(self):
    #     embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    #
    #     vector_store = Chroma(
    #         collection_name="knowledge_base",
    #         embedding_function=embeddings,
    #         persist_directory="./vector_knowledge_base"
    #     )
    #
    #     results = vector_store.similarity_search(
    #         "When is my interview scheduled?"
    #     )
    #
    #     RAGContext = '\n'.join(result.page_content for result in results)  # CONTEXT READY TO PARSE TO THE MODEL
    #     print(RAGContext)


# async def main():
#     # CLEANER WAY THAN GATHER - USE asyncio ONLY IN THE IO-BLOCKING FRAGMENTS - OPENAI API CALLS
#     kg_build = kg_extractor()
#     await asyncio.gather(
#         asyncio.to_thread(kg_build.extract_GUI_schema),
#         asyncio.to_thread(kg_build.extract_knowledge_schema)
#     )
#     kg_build.vector_contents()


# asyncio.run(main())