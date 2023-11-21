import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
import json
import ijson
from langchain.document_loaders import JSONLoader


def faiss_embed_with_metadata_openai(file_name):


    print("ATTEMPTING TO EMBED: " + file_name)

    # List all the files in the `json_results` folder

    resulting_docs = []
    resulting_metadata = []

    # define the embeddings
    embeddings = OpenAIEmbeddings()     
    
    to_be_schema = ""

    # TODO maybe replace the "body" with "title" where there's no body in the jsons

    if file_name == "hacklabs_findings.json" or file_name == "codearena_findings.json":
        to_be_schema = ".[].title"
    else:
        to_be_schema = ".[].body"

    # load the json to embed. ATM we're embedding the body of the json only
    
    parsed_metadata = []

    with open ("../results/" + file_name, "r") as f:

        updated_json = []

        for parsed_file in ijson.items(f,"item"):

            try:

                if len(parsed_file["body"]) == 0:
                    parsed_file["body"] = parsed_file["title"]
                # if body is empty or very large, replace it with title
                if len(parsed_file["body"]) > 20000:
                    # get only first 20000 characters
                    parsed_file["body"] = parsed_file["body"][:20000]
            except:

                # means body doesn't exist for some reason, so what we want here is set the body to "title"
                parsed_file["body"] = parsed_file["title"]

            parsed_metadata.append({
                # make a one-line if statement for each of the keys to check if they exist, otherwise they should not be added
                "title": parsed_file["title"] if "title" in parsed_file else None,
                "labels": parsed_file["labels"] if "labels" in parsed_file else None,
                "html_url": parsed_file["html_url"] if "html_url" in parsed_file else None,
                # "description": parsed_file["description"] if "description" in parsed_file else None, TODO: remove from index.   
                "target": parsed_file["target"] if "target" in parsed_file else None,
                "body": parsed_file["body"] if "body" in parsed_file else None
                }
            )

            updated_json.append(parsed_file)

            # replace the json with the updated one
        json.dump(updated_json, open("../results/" + file_name, "w"))

    # TODO the changes need to be done by the loader, not by the parsed file, since that's 
    loader = JSONLoader(
        file_path = "../results/" + file_name,
        jq_schema = to_be_schema
        )
    
    documents = loader.load()
    
    resulting_docs += [doc.page_content for doc in documents]
    resulting_metadata += parsed_metadata

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.create_documents(
        resulting_docs,
        metadatas = resulting_metadata
        )
    
    try:

    # check if folder "file_name + _openai" exists
        if not os.path.exists("nov20_openai"):
            print("DOESN'T EXIST on: " + file_name)
            # add the file to the index
            vectorstore = FAISS.from_documents(
                documents = docs,
                embedding = embeddings,
                )
            
            vectorstore.save_local("nov20_openai")

        # else, we want to append to an already existing index
        else:

            # load the index
            vectorstore_existing = FAISS.load_local("nov20_openai", embeddings)
            # add the file to the index
            vectorstore_new = FAISS.from_documents(
                documents = docs,
                embedding = embeddings,
                )
            
            # merge the two indexes
            vectorstore_existing.merge_from(vectorstore_new)

            # save the index
            vectorstore_existing.save_local("nov20_openai")
    except Exception as e:
        print(e)
        print("ERROR ON: " + file_name)
        pass

    
def query_with_openai(query):

    # embeddings
    embeddings = OpenAIEmbeddings()
    
    # load the index
    vectorstore = FAISS.load_local("nov20_openai", embeddings)

    # query the index
    results = vectorstore.similarity_search_with_score(query, score_threshold=0.35, k = 10) # the lower the score, the "better" results we get
    # NOTE so basically the more issues we have in the repo the better we can match them;
    # before, the 0.8 threshold was needed for most findings, now 0.4(where lower is better) is needed for most findings;
    # this means that as time passes and we add more findings, we should theoretically lower the threshold to get the best results


    # print(results)
    return results


def json_splitter():

    # We want to list all the jsons in the json_results folder
    # and split them into jsons with 500 elements max each;
    # so for example if halborn has 1200 findings we split it in halborn_1(500), halborn_2(500), halborn_3(200)
    # and so on


    # List all the files in the `json_results` folder
    json_results = os.listdir("../results")

    # for each file, load the json and split it

    for file in json_results:

        json_file = json.load(open("../results/" + file, "r"))

        # check how many elements are in the json
        print(len(json_file))

        # if there are more than 500 elements, we want to split it
        if len(json_file) > 500:
            # split the json into chunks of 500 elements
            chunks = [json_file[i:i+500] for i in range(0, len(json_file), 500)]

            # save each chunk as a separate json file
            for i, chunk in enumerate(chunks):
                with open(f"../results/{file.split('.')[0]}_{i+1}.json", "w") as f:
                    json.dump(chunk, f)

            # remove the original file
            os.remove("../results/" + file)
        # else, we don't need to split it

if __name__ == "__main__":

    json_splitter()
    # List all the files in the `json_results` folder
    json_results = os.listdir("../results")

    for file in json_results:
        faiss_embed_with_metadata_openai(file)

    print("DONE")
