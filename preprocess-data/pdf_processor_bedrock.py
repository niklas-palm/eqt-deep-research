#!/usr/bin/env python3
"""
PDF Processor with Bedrock Integration

This script extracts PDF pages as images and processes them using Amazon Bedrock
with Claude 3 for content extraction, with support for concurrent processing.
"""

import argparse
import io
import json
import logging
import os
import re
import time
import concurrent.futures
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import tempfile

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Load prompt from file
with open(Path(__file__).parent / "prompt.txt", "r") as f:
    BEDROCK_PROMPT = f.read()


def extract_pdf_pages(pdf_path, zoom=2.0, max_pages=None):
    """Extract each page of a PDF as images"""
    import fitz  # PyMuPDF
    from PIL import Image

    pdf_path = Path(pdf_path)
    logger.info(f"Extracting pages from: {pdf_path}")

    # Open the PDF
    pdf = fitz.open(pdf_path)
    images = []

    # Determine number of pages to process
    total_pages = len(pdf)
    pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
    logger.info(f"PDF has {total_pages} pages, processing {pages_to_process}")

    # Process each page
    for i in range(pages_to_process):
        page = pdf[i]
        logger.info(f"Converting page {i+1}/{pages_to_process}")

        # Render page to an image with specified zoom factor
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))

        # Convert to PIL Image (in memory)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        images.append(img)

    logger.info(f"Successfully extracted {len(images)} pages")
    return images


def save_preview_images(images, output_dir="preview"):
    """Save images to disk for processing"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    logger.info(f"Saving images to {output_path}")

    image_paths = []
    # Save each image
    for i, img in enumerate(images):
        file_path = output_path / f"page_{i+1:03d}.png"
        img.save(file_path)
        image_paths.append(file_path)

    return image_paths


def process_image_with_bedrock(bedrock_client, image_path):
    """Process an image using Bedrock with retry logic for errors"""
    logger.info(f"Processing image: {image_path}")

    # Get image extension and read in image as bytes
    image_ext = str(image_path).split(".")[-1]
    with open(image_path, "rb") as f:
        image = f.read()

    # Create message with image and prompt
    message = {
        "role": "user",
        "content": [
            {"image": {"format": image_ext, "source": {"bytes": image}}},
            {"text": BEDROCK_PROMPT},
        ],
    }

    # Send the message to Bedrock with retries
    retry_attempts = 0
    max_retries = 3

    while retry_attempts < max_retries:
        try:
            response = bedrock_client.converse(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                messages=[message],
            )

            # Extract the response content
            output_message = response["output"]["message"]
            return {
                "page_path": str(image_path),
                "content": output_message["content"][0]["text"],
            }

        except ClientError as err:
            error_code = err.response.get("Error", {}).get("Code", "")
            error_message = err.response.get("Error", {}).get("Message", "")

            # Handle 503 Service Unavailable - retry immediately
            if error_code == "ServiceUnavailable" or "503" in error_message:
                retry_attempts += 1
                logger.warning(
                    f"Service unavailable (503). Retrying ({retry_attempts}/{max_retries})..."
                )
                continue

            # Handle 429 Too Many Requests - back off and retry
            elif error_code == "ThrottlingException" or "429" in error_message:
                retry_attempts += 1
                wait_time = 2 * retry_attempts  # Simple backoff
                logger.warning(
                    f"Rate limited (429). Waiting {wait_time}s before retry..."
                )
                time.sleep(wait_time)
                continue

            # Other errors - log and return error
            else:
                logger.error(f"Bedrock error: {error_message}")
                return {"page_path": str(image_path), "error": error_message}

    # If we reached here after retries, return error
    return {
        "page_path": str(image_path),
        "error": f"Failed after {max_retries} retries",
    }


def process_pdf_with_bedrock(pdf_path, output_file="results.json", max_concurrent=5, max_pages=None):
    """
    Main processing function that handles the entire PDF processing workflow
    
    Args:
        pdf_path: Path to the PDF file to process
        output_file: Path to save the JSON results
        max_concurrent: Maximum number of concurrent Bedrock requests
        max_pages: Maximum number of pages to process (None for all pages)
    
    Returns:
        Tuple of (json_output_path, markdown_output_path)
    """
    # Extract pages from PDF
    images = extract_pdf_pages(pdf_path, max_pages=max_pages)

    # Save images temporarily
    temp_dir = tempfile.TemporaryDirectory()
    image_paths = save_preview_images(images, temp_dir.name)

    # Initialize Bedrock client
    bedrock_client = boto3.client(
        service_name="bedrock-runtime", region_name="us-west-2"
    )

    # Process images concurrently
    logger.info(
        f"Processing {len(image_paths)} pages with {max_concurrent} concurrent workers"
    )
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all processing tasks
        futures = {
            executor.submit(process_image_with_bedrock, bedrock_client, img_path): img_path
            for img_path in image_paths
        }
        
        logger.info(f"Submitted {len(futures)} tasks to thread pool")
        
        # Process results as they complete (in any order)
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            img_path = futures[future]
            logger.info(f"Completed processing {i}/{len(futures)}: {img_path}")
            
            try:
                result = future.result()
                results.append(result)

                # Save incremental results
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)

            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
                results.append({"page_path": str(img_path), "error": str(e)})

    # Clean up
    temp_dir.cleanup()
    logger.info(f"Processing complete! Results saved to {output_file}")

    # Generate combined markdown
    markdown_file = output_file.replace(".json", ".md")
    create_combined_markdown(results, markdown_file)

    return output_file, markdown_file


def create_combined_markdown(results, output_file="combined.md"):
    """
    Create a combined markdown file from results, removing <markdown> tags
    
    Args:
        results: List of dictionaries containing page content
        output_file: Path to save the combined markdown output
    """
    logger.info(f"Creating combined markdown file: {output_file}")

    # Sort results by page path to maintain correct page order
    sorted_results = sorted(
        results, 
        key=lambda x: int(re.search(r'page_(\d+)', x.get("page_path", "0")).group(1))
    )

    # Extract and clean markdown content
    all_content = []
    markdown_pattern = r"<markdown>(.*?)</markdown>"

    for i, result in enumerate(sorted_results):
        # Skip pages with errors
        if "error" in result:
            logger.warning(f"Skipping page with error: {result.get('page_path')}")
            continue

        content = result.get("content", "")
        # Extract content between <markdown> tags
        matches = re.findall(markdown_pattern, content, re.DOTALL)

        if matches:
            # Join all matches and add to content
            clean_content = "\n\n".join(match.strip() for match in matches)
            all_content.append(clean_content)
        else:
            # If no tags found, use content as is
            logger.warning(f"No markdown tags found in page {i+1}, using raw content")
            all_content.append(content.strip())

    # Write combined markdown to output file
    with open(output_file, "w") as f:
        f.write("\n\n".join(all_content))

    logger.info(f"Combined markdown saved to {output_file} ({len(all_content)} pages)")
    return output_file


def main():
    """Main function to parse arguments and run the extraction"""
    parser = argparse.ArgumentParser(description="Process PDF with Bedrock")
    parser.add_argument("pdf_file", help="Path to the PDF file")
    parser.add_argument("--output", default="results.json", help="Output JSON file")
    parser.add_argument(
        "--workers", type=int, default=5, help="Number of concurrent Bedrock requests"
    )
    parser.add_argument(
        "--max-pages", type=int, default=None, help="Maximum number of pages to process"
    )

    args = parser.parse_args()

    try:
        # Process the PDF
        json_file, md_file = process_pdf_with_bedrock(
            args.pdf_file, 
            output_file=args.output, 
            max_concurrent=args.workers,
            max_pages=args.max_pages
        )
        logger.info(f"Results saved to {json_file} and {md_file}")

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
