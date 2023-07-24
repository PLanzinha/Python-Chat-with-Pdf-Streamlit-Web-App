from chains import load_vector, create_embeddings


def main():
    embeddings = create_embeddings()

    vector_db = load_vector(embeddings)

    query = "Nature of this Guide"

    results = vector_db.similarity_search(query)

    print("Results for query:", query)
    for result in results:
        print(result.page_content)


if __name__ == "__main__":
    main()
