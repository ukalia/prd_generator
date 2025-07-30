from dotenv import load_dotenv
import logging
import os
from generation.utils import process_input_text
from ingestion.utils.docx_utils import extract_text_from_docx

logging.basicConfig(
    level=logging.INFO,  # Set the log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

BRD_PATH = os.getenv('BRD_LOC')


def process_input():
    try:
        files = [f for f in os.listdir(BRD_PATH) if not f.startswith('.') and os.path.isfile(os.path.join(BRD_PATH, f))]
        file = files[0]
        file_path = f'{BRD_PATH}/{file}'
        text = extract_text_from_docx(file_path)
        process_input_text(text)
        logger.info('PRD generated Successfully')
    except Exception as e:
        logger.exception(f'Error while processing input : {str(e)}')
    

if __name__ == '__main__':
    try:
        process_input()
    except KeyboardInterrupt:
        logger.exception('Keyboard Interrupt')