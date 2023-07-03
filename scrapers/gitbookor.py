from langchain.document_loaders import GitbookLoader
import json

def query_data_sources(data_sources):
    """
    Scrape relevant gitbooks and return a list of dictionaries that's ready to be added to Masamune.
    """

    result = []

    for data_source in data_sources:

        gitbooker = GitbookLoader(data_source, load_all_paths=True)
        documents = gitbooker.load()

        for document in documents:
            # remove "\n" from the title
            document.metadata['title'] = document.metadata['title'].replace("\n", " ")

            # remove "\n" from the entire document
            document.page_content = document.page_content.replace("\n", " ")

            # strip all non-ascii characters
            document.page_content = document.page_content.encode("ascii", "ignore").decode()

            result.append(
                {
                    "title": document.metadata['title'],
                    "html_url": document.metadata['source'],
                    "body": document.page_content,
                    "labels": [
                        "Documentation",
                    ]
                }
            )

    # save to ../results/gitbook_docs.json
    with open("../results/gitbook_docs.json", "w") as f:
        json.dump(
            result,
            f
        )


if __name__ == "__main__":

    # Data sources:

    data_sources = [
        "https://uniswapv3book.com",
        "https://www.mev.wiki/",
        "https://kb.beaconcha.in/",
        "https://layerzero.gitbook.io",
        "https://resources.curve.fi/"
    ]

    query_data_sources(data_sources)