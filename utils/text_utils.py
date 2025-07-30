import logging
import pymupdf
import re
from utils.db_utils import load_data_to_db
from utils.ollama_utils import get_embedding

logger = logging.getLogger(__name__)

def process_pdf(pdfs, page):
    from ingestion.utils.confluence_utils import download_attachment
    if not pdfs:
        logger.debug('No pdfs in this doc')
        return
    title = page.get('title', '')
    page_id = page.get('page_id', '')
    if title:
        safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()

    for pdf in pdfs:
        path = download_attachment(page_id, safe_title or 'Untitled', pdf)
        doc = pymupdf.open(path)
        all_text = []
        for p in doc:
            text = p.get_text()
            all_text.append(text)
        full_text = '\n'.join(all_text)
        process_text(full_text, page, pdf=pdf)


def process_text(text, page, pdf=''):
    if not text:
        logger.debug('No Text to process')
        return
    page_id = page.get('page_id', '')
    title = page.get('title')
    chunks = chunk_text(text, max_length=550, overlap=50)
    for chunk_idx, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)
            if embedding is None:
                logger.warning(f'Failed to generate embedding for chunk {chunk_idx} of page: {title}')
                continue
            if pdf:
                doc_id = f'{page_id}--pdf-{pdf}--chunk-{chunk_idx}'
            else:
                doc_id = f'{page_id}--chunk-{chunk_idx}'
            load_data_to_db(page, chunk_idx, chunk, doc_id, embedding, pdf)
        except Exception as e:
            logger.error(f'Error processing chunk {chunk_idx} for pdf {pdf} in page {title}, id {page_id}: {e}')
            
    logger.info(f'Successfully embedded doc: pdf {pdf} or page {title} in ({len(chunks)} chunks)')


def chunk_text(text, max_length=500, overlap=50):
    if not text or not text.strip():
        return []
    
    paragraphs = re.split(r'\n{2,}', text.strip())
    chunks = []
    current_chunk = ''
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if len(para) > max_length:
            sentences = split_into_sentences(para)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= max_length:
                    current_chunk += sentence + ' '
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ' '
            continue
        
        if len(current_chunk) + len(para) + 2 <= max_length:
            current_chunk += para + '\n\n'
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = para + '\n\n'
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    if overlap > 0 and len(chunks) > 1:
        chunks = add_overlap_to_chunks(chunks, overlap)
    
    validated_chunks = []
    embedding_max_length = 7000
    
    for chunk in chunks:
        if len(chunk) <= embedding_max_length:
            validated_chunks.append(chunk)
        else:
            logger.warning(f'Chunk still too long ({len(chunk)} chars), force splitting...')
            force_split_chunks = force_split_text(chunk, embedding_max_length - 100)
            validated_chunks.extend(force_split_chunks)
    return validated_chunks


def split_into_sentences(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def add_overlap_to_chunks(chunks, overlap):
    if len(chunks) <= 1:
        return chunks
    
    overlapped_chunks = [chunks[0]]
    
    for i in range(1, len(chunks)):
        prev_chunk = chunks[i-1]
        current_chunk = chunks[i]
        
        if len(prev_chunk) > overlap:
            overlap_text = prev_chunk[-overlap:].strip()
            space_index = overlap_text.find(' ')
            if space_index > 0:
                overlap_text = overlap_text[space_index:].strip()
            
            overlapped_chunk = overlap_text + '\n\n' + current_chunk
            overlapped_chunks.append(overlapped_chunk)
        else:
            overlapped_chunks.append(current_chunk)
    return overlapped_chunks


def force_split_text(text, max_length):
    chunks = []
    remaining_text = text
    
    while len(remaining_text) > max_length:
        split_point = max_length
        space_index = remaining_text.rfind(' ', 0, max_length)
        if space_index > max_length * 0.8:
            split_point = space_index
        
        chunk = remaining_text[:split_point].strip()
        if chunk:
            chunks.append(chunk)
        
        remaining_text = remaining_text[split_point:].strip()
    
    if remaining_text:
        chunks.append(remaining_text)
    return chunks


def validate_chunk_size(chunk, max_tokens=2000) -> bool:
    estimated_tokens = len(chunk) // 4
    return estimated_tokens <= max_tokens
