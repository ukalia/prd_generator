from dotenv import load_dotenv
import logging
from ingestion.utils.docx_utils import get_prds, extract_date_from_document, extract_text_from_docx
from utils.text_utils import process_text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

load_dotenv()

def process_prds():
    files = get_prds()
    for f, p in files.items():
        if not f.lower().endswith('docx'):
            logger.warning(f'File {f} is not a .docx file')
            continue
        try:
            created_at, updated_at = extract_date_from_document(p)
            text = extract_text_from_docx(p)
            page = {
                'title': f,
                'page_id': f,
                'created_at': created_at,
                'updated_at': updated_at
            }
            process_text(text, page)
        except Exception as e:
            logger.error(f'Error processing doc {f}: {str(e)}')


if __name__ == '__main__':
    process_prds()