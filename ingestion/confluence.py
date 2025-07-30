import logging
from ingestion.utils.confluence_utils import fetch_page_id_from_title, collect_subpages, get_page_content, process_and_store

logging.basicConfig(
    level=logging.INFO,  # Set the log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_and_store_historical_docs(pages):
    page_ids = []
    for space, title in pages:
        logger.info(f'Searching for title: "{title}" in space: "{space}"')
        try:
            p_id = fetch_page_id_from_title(title, space)
            if not p_id:
                logger.warning(f'Could not find page "{title}" in space "{space}"')
                continue
            page_ids.append(p_id)
            child_pages = collect_subpages(p_id)
            logger.info(f'Found {len(child_pages)} child pages under "{title}"')
            page_ids.extend(child_pages)
        except Exception as e:
            logger.exception(f'Error processing "{title}" in space "{space}": {e}')
    
    logger.info(f'Total pages to process: {len(page_ids)}')
    unique_page_ids = list(set(page_ids))
    logger.info(f'Unique pages to process: {len(unique_page_ids)}')

    pages_with_content = []
    for id in unique_page_ids:
        content = get_page_content(id)
        if not content:
            logger.warning(f'Could not fetch content for page ID: {id}')
            continue
        pages_with_content.append(content)
    logger.info(f'Successfully fetched content for {len(pages_with_content)} pages')

    if pages_with_content:
        try:
            process_and_store(pages_with_content)
        except Exception as e:
            logger.exception(f'Error processing pages: {e}')


if __name__ == '__main__':
    try:
        target_pages = [
            ('CAR', 'Product Documentation')
        ]
        fetch_and_store_historical_docs(target_pages)
    except KeyboardInterrupt:
        logger.exception('Interrupted by user.')