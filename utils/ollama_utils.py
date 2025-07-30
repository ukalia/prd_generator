import logging
from ollama import embed, chat
import textwrap

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = 'nomic-embed-text'
GENERATION_MODEL = 'mistral:7b'

def get_embedding(text, model=EMBEDDING_MODEL):
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return None
        
    try:
        max_length = 7000
        if len(text) > max_length:
            logger.error(f'Text too long ({len(text)} chars) for embedding model context length. '
                        f'Consider re-chunking this text. Preview: {text[:100]}...')
            return None
            
        response = embed(model=model, input=text)
        embeddings = response.get('embeddings')
        
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        else:
            logger.error('No embeddings returned from Ollama')
            return None
            
    except Exception as e:
        logger.error(f'Embedding failed: {e}')
        logger.error(f'Text preview: {text[:100]}...')
        return None


def get_promt(input_text, context):
    prompt = f'''You are a product manager tasked with creating a detailed Product Requirement Document (PRD).
        Use the following input information to generate a clear, well-organized PRD that adheres to best practices. Leverage user requirements, input data, and relevant examples from previous PRDs to inform your writing.
        ---
        ### New Product Input
        {input_text}
        ### Reference PRD Examples
        {context}
        ---
        ### Instructions
        Generate a complete PRD by filling in the following sections using the input and reference material provided. The PRD must be clear, specific, and actionable, following standard industry formatting:
        1. **Overview** - Brief summary of the product or feature.  
        2. **Scope** - Objectives this product/feature aims to achieve.  
        3. **User Stories / Use Cases** - Realistic user scenarios demonstrating how the feature will be used.  
        4. **Requirements** - Specific, testable features and capabilities.  
        5. **Acceptance Criteria** - Clear pass/fail criteria for validating delivery.  
        6. **Out of Scope** - Features or elements not included in this release.  
        ---
        ### Additional Guidelines
        - Incorporate relevant details or phrasing from the Reference PRD Examples to improve consistency and quality.  
        - Avoid vague or generic language—be precise and practical.  
        - If any section lacks sufficient input, flag it clearly with a placeholder like `> TBD` or suggest reasonable defaults.  
        - Format the final PRD as a clean, well-formatted markdown document.
        '''
    return textwrap.dedent(prompt)


def generate_prd(input_text, context):
    prompt = get_promt(input_text, context)
    logger.debug(f'generated prompt : {prompt}')
    response = chat(
        model='mistral:7b',
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ]
    )
    return response['message']['content']
