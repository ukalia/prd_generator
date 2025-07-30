from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
import os
from pathlib import Path
import requests
from utils.text_utils import process_pdf, process_text


logger = logging.getLogger(__name__)

load_dotenv()

BASE_URL = os.getenv('CONFLUENCE_BASE_URL')
USERNAME = os.getenv('CONFLUENCE_USERNAME')
API_KEY = os.getenv('CONFLUENCE_API_KEY')
BASE_DOWNLOAD_PATH = os.getenv('DOWNLOADS_BASE_URL')
CONF_AUTH_CREDS = (USERNAME, API_KEY)
HEADERS = {
    'Accept': 'application/json'
}


def fetch_page_id_from_title(title, space_key):
    url = f'{BASE_URL}/rest/api/content'
    params = {
        'spaceKey': space_key,
        'title': title,
        'expand': 'ancestors'
    }

    try:
        response = requests.get(url, auth=CONF_AUTH_CREDS, headers=HEADERS, params=params)
        response.raise_for_status()
        result = response.json().get('results', [])

        if not result:
            logger.warning(f'Page "{title}" not found in space "{space_key}"')
            return None
        return result[0].get('id')
    except Exception as e:
        logger.exception(f'Error fetching page "{title}".\n {str(e)}')
        

def collect_subpages(page_id):
    all_pages = []

    def recurse(pid):
        child_pages = get_child_pages(pid)
        for page in child_pages:
            id = page.get('id')
            if id:
                all_pages.append(id)
                recurse(id)
    recurse(page_id)
    return all_pages


def get_child_pages(page_id):
    url = f'{BASE_URL}/rest/api/content/{page_id}/child/page'
    all_children = []
    start = 0
    limit = 100

    while True:
        params = {
            'start': start,
            'limit': limit,
            'expand': 'body.storage, version, history'
        }
        try:
            response = requests.get(url, auth=CONF_AUTH_CREDS, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()

            children = data.get('results', [])
            all_children.extend(children)

            if len(children) < limit:
                break
            start += limit
        except Exception as e:
            logger.exception(f'Error fetching child pages for {page_id}:\n {str(e)}')
            break

    return all_children


def get_page_content(page_id):
    url = f'{BASE_URL}/rest/api/content/{page_id}'
    params = {
        'expand': 'body.storage,version,history'
    }   
    try:
        response = requests.get(url, auth=CONF_AUTH_CREDS, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.exception(f'Error fetching page content for {page_id}: {e}')
        return None


def process_and_store(pages):
    if not pages:
        logger.warning(f'No Pages to Process')

    for page in pages:
        try:
            page_data = get_page_details(page)
            body = page_data.get('body')
            title = page_data.get('title')

            if not body:
                logger.warning(f'No content found for page {title}')
                continue

            parsed_page = parse_confluence_page(body)

            if not parsed_page:
                logger.warning(f'No content found after cleaning page "{title}"')
                continue

            parsed_page.update(page_data)
            process_parsed_page(parsed_page)
        except Exception as e:
            logger.exception(f'Error while processing page "{title}": {str(e)}')


def get_page_details(page):
        if not page:
            return {}

        version_info = page.get('version', {})
        history_info = page.get('history', {})
        return {
            'page_id': page.get('id'),
            'title': page.get('title', 'Untitled'),
            'body': page.get('body', {}).get('storage', {}).get('value', ''),
            'created_at': history_info.get('createdDate', ''),
            'updated_at': version_info.get('when', '')
        }


def parse_confluence_page(body):
    page = {}
    if not body:
        return page

    soup = BeautifulSoup(body, 'html.parser')
    attachments = extract_attachments_and_links(soup)
    page.update(attachments)
    text = soup.get_text(separator='\n').strip()
    if text:
        page['text'] = text
    return page


def extract_attachments_and_links(soup):
    if not soup:
        return {}

    attachments = {}
    attachments['pdfs'] = extract_pdfs(soup)
    linked_pages = extract_linked_pages(soup)

    if linked_pages:
        attachments['linked_pages'] = linked_pages  
    return attachments


def extract_pdfs(soup):
    pdfs = []
    embedded_attachments = soup.find_all('ri:attachment')

    for attachment in embedded_attachments:
        if attachment.has_attr('ri:filename'):
            filename = attachment['ri:filename'].lower()
            if filename.endswith('.pdf'):
                pdfs.append(filename)
    return pdfs


def extract_linked_pages(soup):
    linked_pages = []
    links = soup.find_all('ri:page')  

    for link in links:
        title = link.get('ri:content-title') or link.get('ri:page-id') or 'Untitled'
        space = link.get('ri:space-key')
        if title:
            linked_pages.append((space or 'Unknown', title))
    return linked_pages


def process_parsed_page(page):
    from ingestion.confluence import fetch_and_store_historical_docs

    pdfs = page.get('pdfs', [])
    text = page.get('text', '')
    linked_pages = page.get('linked_pages', [])
    process_pdf(pdfs, page)
    process_text(text, page)

    if linked_pages:
        fetch_and_store_historical_docs(linked_pages)


def download_attachment(page_id, safe_title, target_filename):
    url = f'{BASE_URL}/rest/api/content/{page_id}/child/attachment'
    
    try:
        response = requests.get(url, auth=CONF_AUTH_CREDS, headers=HEADERS)
        response.raise_for_status()

        attachments = response.json().get('results', [])
        for file in attachments:
            if file.get('title').lower() == target_filename.lower():
                download_link = file.get('_links', {}).get('download', '')
                if not download_link:
                    continue
                  
                download_url = f'{BASE_URL}{download_link}'
                res = requests.get(download_url, auth=CONF_AUTH_CREDS, headers=HEADERS)
                res.raise_for_status()

                path = Path(f'{BASE_DOWNLOAD_PATH}/{safe_title}/pdfs/{target_filename}')
                path.parent.mkdir(parents=True, exist_ok=True)

                with open(path, 'wb') as f:
                    f.write(res.content)
                logger.info(f'Downloaded attachment: {path}')
                return str(path)
                
    except requests.exceptions.RequestException as e:
        logger.exception(f'Error downloading attachment {target_filename} from page {page_id}: {e}')
    
    return None
