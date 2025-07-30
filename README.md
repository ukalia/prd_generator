# PRD Generator – AI-powered Product Requirement Document Generator using Local LLMs

## Overview

This project leverages Retrieval-Augmented Generation (RAG) with a local Large Language Model (LLM) to automatically generate high-quality Product Requirement Documents (PRDs) from raw business input (BRDs, user stories, or simple textual descriptions).

The system supports `.docx` files as input (e.g., business requirement documents or meeting notes) and outputs structured, markdown-formatted PRDs that can also be saved as `.docx`.

---

## Tech Stack

- **Python** – Core language
- **Ollama** – Runs local LLMs like Mistral or LLaMA
- **ChromaDB** – Vector store for document retrieval in RAG
- **python-docx** – For `.docx` file parsing and output generation

---

## Features

-  **RAG-Powered Prompting**: Retrieves relevant past PRD examples from a vector store to guide generation  
-  **Local LLM Inference**: Uses Ollama to run models like `mistral`, no API keys or cloud access needed  
-  **Structured PRD Output**: Includes sections like Overview, Goals, Requirements, Use Cases, and more  
-  **`.docx` Output Support**: Formats output with real Word styling (headings, bullets, page breaks)  
-  **Extensible Input Support**: Currently supports `.docx` BRDs but easily extendable to `.pdf`, `.txt`, or web input  

---

##  Sample Use Case

> Input: `sample_brd.docx`  
> Output: `generated_prd.docx` with sections like Overview, Goals, Requirements, Acceptance Criteria

---

## Project Structure
.
├── README.md
├── documents/
│   ├── brds/                       # Input BRD
│   ├── confluence-downloads/       # Attachments downloaded from confluence Pages(PRDs) 
│   ├── prds/                       # Locally available PRDs
│   └── generated-prd/              # Output PRD
├── generation/
│   ├── generation.py               # Entry Point for the generation flow
│   └── utils.py 
├── ingestion/
│   ├── confluence.py               # Entry point for ingestion and embedding the PRDs from confluence
│   ├── prds.py                     # Entry point for ingestion and embedding local PRDs
│   ├── utils
│       ├── confluence_utils.py
│       └── docx_utils.py
├── requirements.txt
├── utils/
│   ├── db_utils.py                 # Chroma Db utils
│   ├── ollama_utils.py             # Utils for Embedding and Generation using Ollama
│   └── text_utils.py               
├── db/                             # Local vector db for embeddings
├── venv/
└── .env
    

## 🧰 How to Run

### 1. Start Ollama (and pull Mistral)
ollama pull mistral

### 2. Install dependencies
pip install -r requirements.txt

### 3. Run Ingestion scripts
python -m ingestion.confluence
python -m ingestion.prds

### 4. Run Generation script
python -m generation.generation

