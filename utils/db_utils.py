import chromadb
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)

load_dotenv()

DB_PATH = os.getenv('VECTOR_DB_DIRECTORY')

def get_collection(db_path=DB_PATH):
    db_client = chromadb.PersistentClient(path=db_path)
    collection = db_client.get_or_create_collection(name='prd_docs')
    return collection


def create_metadata_for_embedded_chunks(page, chunk_index, pdf=''):
    metadata = {
        'title': page.get('title', ''),
        'chunk_index': chunk_index,
    }
    created_at = page.get('created_at')
    updated_at = page.get('updated_at')
    if created_at:
        metadata['created_at'] = created_at
    if updated_at:
        metadata['updated_at'] = updated_at
    if page_id := page.get('page_id'):
        metadata['page_id'] = page_id
    if pdf:
        metadata['pdf'] = pdf

    return metadata


def load_data_to_db(page, chunk_idx, chunk, doc_id, embedding, pdf):
        metadata = create_metadata_for_embedded_chunks(page, chunk_idx, pdf=pdf)
        doc_collection = get_collection()
        doc_collection.add(
        documents=[chunk],
        metadatas=[metadata],
        ids=[doc_id],
        embeddings=[embedding]
    )


def perform_similarity_search(embedding):
    collection = get_collection()
    result = collection.query(
        query_embeddings=[embedding],
        n_results=10,
        include=['documents', 'metadatas', 'distances']
    )
    return result


def get_similar_docs(embedding):
    result = perform_similarity_search(embedding)
    try:
        filtered_docs = {}
        ids = result.get('ids')
        distances = result.get('distances')
        documents = result.get('documents')
        if documents:
            for id, doc, dist in zip(ids[0], documents[0], distances[0]):
                if dist < 0.5:
                    filtered_docs[id] = doc
        logger.info(f'Found {len(filtered_docs.keys())} similar docs')
    except Exception as e:
        logger.exception(f'Error while fetching similar docs : {str(e)}')
    return filtered_docs




