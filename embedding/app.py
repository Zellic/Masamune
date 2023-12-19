from flask import Flask, request, jsonify, redirect
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from flask_cors import CORS

# Create the Flask app
app = Flask(__name__)

# Enable CORS
CORS(app)

# `/` should redirect to https://masamune.app
@app.route('/')
def index():
    """
    This endpoint is used to redirect to https://masamune.app.

    :return: A redirect to https://masamune.app.
    """
    return redirect("https://masamune.app", code=302)

def load_embeddings():
    """
    Load the embeddings from the vectorstore.

    :return: The vectorstore.
    """
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("dec10_openai", embeddings)

def search(query, vectorstore):
    """
    The search function is used to search in the vectorstore.

    :param query: The query to search for.
    :param vectorstore: The vectorstore to search in.

    :return: The results of the search.
    """
    results = vectorstore.similarity_search_with_score(
        query, 
        k = 10
    )

    results = [result for result in results if result[1] < 0.4]

    return results

@app.route('/search', methods=['GET'])
def search_endpoint():
    """
    This endpoint is used to search in the vectorstore.

    :return: The results of the search, in JSON format.
    """

    # Get the query from the request
    query = request.args.get('query')

    # Load the embeddings
    vectorstore = load_embeddings()

    # Search the vectorstore
    results = search(query, vectorstore)

    # results is a tuple so we want to get the first element for the results
    results = [result[0] for result in results]
    
    # We want to return a list of the texts
    for result in results:
        result.page_content = result.page_content.split("\n\n")

    # Remove the empty strings
    for result in results:
        result.page_content = "".join(filter(None, result.page_content))

    # Build the JSON response
    to_jsonify = {
        'results': []
        }

    # Add the results to the JSON response
    for result in results:
        to_jsonify['results'].append({
            'content': result.page_content,
            'metadata': result.metadata
        })

    # Return the JSON response
    return jsonify(
        to_jsonify
    )

# Run the app
if __name__ == "__main__":
    app.run(
        debug = True
    )