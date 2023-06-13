import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
import json
from langchain.document_loaders import JSONLoader

    
def faiss_embed_with_metadata():

    # List all the files in the `json_results` folder
    json_results = os.listdir("../json_results")

    resulting_docs = []
    resulting_metadata = []

    # define the embeddings
    embeddings = OpenAIEmbeddings() 

    # for each file, load the json and add to the FAISS index
    for file in json_results:

        # load the json file, so that it's parsed and can be checked for the fields
        parsed_file = json.load(
            open("../json_results/" + file, "r")
            )
        
        to_be_schema = ""

        # TODO maybe replace the "body" with "title" where there's no body in the jsons

        if file == "hacklabs_findings.json" or file == "codearena_findings.json":
            to_be_schema = ".[].title"
        else:
            to_be_schema = ".[].body"

        # load the json to embed. ATM we're embedding the body of the json only
        loader = JSONLoader(
            file_path = "../json_results/" + file,
            jq_schema = to_be_schema
            )
        
        documents = loader.load()
        
        parsed_metadata = []
        for i in range(len(parsed_file)):
            parsed_metadata.append({
                # make a one-line if statement for each of the keys to check if they exist, otherwise they should not be added
                "title": parsed_file[i]["title"] if "title" in parsed_file[i] else None,
                "labels": parsed_file[i]["labels"] if "labels" in parsed_file[i] else None,
                "html_url": parsed_file[i]["html_url"] if "html_url" in parsed_file[i] else None,
                # "description": parsed_file[i]["description"] if "description" in parsed_file[i] else None, TODO: remove from index.   
                "target": parsed_file[i]["target"] if "target" in parsed_file[i] else None,
                "body": parsed_file[i]["body"] if "body" in parsed_file[i] else None
                }
            )
        
        resulting_docs += [doc.page_content for doc in documents]
        resulting_metadata += parsed_metadata

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.create_documents(
        resulting_docs,
        metadatas = resulting_metadata
        )

    # add the file to the index
    vectorstore = FAISS.from_documents(
        documents = docs,
        embedding = embeddings,
        )

    # save the index
    vectorstore.save_local("faiss_merged_extrametadata")


def query_stuff():

    # embeddings
    embeddings = OpenAIEmbeddings()
    
    # load the index
    vectorstore = FAISS.load_local("faiss_merged_extrametadata", embeddings)

    # query the index
    query = "impair a loan"

    results = vectorstore.similarity_search(query)

    print(results)

if __name__ == "__main__":
    # faiss_embed_with_metadata()
    query_stuff()
