from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DirectoryLoader
from langchain.vectorstores import FAISS
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["1000 per day"])

@app.route('/')
def index():
    return render_template('index.html')

def load_documents():
    loader = DirectoryLoader("data")
    return loader.load()

def split_documents(documents):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return text_splitter.split_documents(documents)

def save_embeddings(vectorstore):
    vectorstore.save_local("faiss_codearena")

def load_embeddings():
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("faiss_merged_extrametadata", embeddings)

@limiter.limit("10 per minute")
@app.route('/search', methods=['GET'])
def search_endpoint():
    query = request.args.get('query')
    vectorstore = load_embeddings()
    results = search(query, vectorstore)
    
    # We want to return a list of the texts
    for result in results:
        result.page_content = result.page_content.split("\n\n")
        # print(result)

    # remove empty strings
    for result in results:
        result.page_content = "".join(filter(None, result.page_content))

    # final formatting

    to_jsonify = {'results': []}

    for result in results:
        to_jsonify['results'].append({
            'content': result.page_content,
            'metadata': result.metadata
        })

    return jsonify(
        to_jsonify
    )
    # return render_template('index.html', results=results)

def search(query, vectorstore):
    results = vectorstore.similarity_search(query)
    return results
    
def main():
    documents = load_documents()
    docs = split_documents(documents)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    save_embeddings(vectorstore)

if __name__ == "__main__":
    # main()
    app.run()