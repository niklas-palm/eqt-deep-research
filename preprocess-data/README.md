# PDF Processor with Bedrock Integration

Process PDF documents with Amazon Bedrock to extract structured content as markdown.

This ensure better handling of graphs and tables, which traditionally are difficult to embed with common text-based embedding models.

## Features

- Extracts PDF pages as images
- Processes images concurrently with Amazon Bedrock (Claude 3.5 Sonnet V2)
- Combines results into a clean markdown document
- New document then manually uploaded to S3, and indexed in Bedrock Knowledge base for retrieval

### Knowledgebase config

- Hierarchical chunking
  - Child chunks 350 tokens
  - Parent chunk 1750
- Titan Embeddings G1 - Text V1.2

## Usage

```bash
# Process a PDF with 10 concurrent workers
python pdf_processor_bedrock.py your_document.pdf --workers 10
```

## Requirements

- Python 3.8+
- AWS credentials configured for Bedrock
- Dependencies in requirements.txt
