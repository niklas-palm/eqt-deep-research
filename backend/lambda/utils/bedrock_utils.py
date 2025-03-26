"""Utility functions for interacting with Amazon Bedrock AI models"""

import json
import enum
from botocore.exceptions import ClientError, ParamValidationError
from typing import Dict, Any, Optional

import boto3

from . import logger
from .config import get_config


# Model size as an enum for better code readability
class ModelSize(enum.Enum):
    """Enum representing different model sizes for Bedrock models"""

    SMALL = "Nova Micro"
    MEDIUM = "Nova Lite"
    LARGE = "Claude 3.7"


# Map model sizes to actual Bedrock model IDs
MODEL_ID_MAPPING = {
    ModelSize.SMALL: "us.amazon.nova-micro-v1:0",
    ModelSize.MEDIUM: "us.amazon.nova-lite-v1:0",
    ModelSize.LARGE: "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
}

# Default model ID
DEFAULT_MODEL_SIZE = ModelSize.LARGE

# Default values for knowledge retrieval
DEFAULT_MAX_RESULTS = 5


def get_bedrock_response(
    prompt: str,
    temperature: float = 0.0,
    model_size: ModelSize = DEFAULT_MODEL_SIZE,
    max_tokens: int = 4000,
) -> Optional[str]:
    """
    Send a prompt to Amazon Bedrock and get a response using the converse API.

    Args:
        prompt: The prompt text to send to the model
        temperature: Controls randomness in the response (0.0 to 1.0)
        model_size: Size of the model to use (SMALL, MEDIUM, LARGE)
        max_tokens: Maximum number of tokens in the response

    Returns:
        The model's response text or None if failed
    """
    try:
        # Basic validation
        if not prompt or not prompt.strip():
            logger.error("Empty prompt provided to get_bedrock_response")
            return None

        # Get the model ID from the model size
        model_id = MODEL_ID_MAPPING.get(model_size)
        logger.info(f"Using model: {model_id} (size: {model_size.value})")

        # Create a bedrock runtime client
        region = get_config().get("REGION")
        if not region:
            raise ValueError("AWS_REGION environment variable is required")

        client = boto3.client(service_name="bedrock-runtime", region_name=region)

        # Format messages for the converse API
        messages = [{"role": "user", "content": [{"text": prompt}]}]

        # Call the converse API
        try:
            response = client.converse(
                modelId=model_id,
                messages=messages,
                inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
            )
        except client.exceptions.ModelTimeoutException as e:
            logger.error(f"Model timeout error: {str(e)}")
            # Try with reduced tokens if we're using a large model
            if model_size == ModelSize.LARGE and max_tokens > 2000:
                logger.info("Retrying with reduced max tokens")
                response = client.converse(
                    modelId=model_id,
                    messages=messages,
                    inferenceConfig={"temperature": temperature, "maxTokens": 2000},
                )
            else:
                raise

        # Extract the response text with better error handling
        try:
            output_message = response["output"]["message"]
            # The content could have different structures, so handle it carefully
            for content_item in output_message["content"]:
                if "text" in content_item:
                    return content_item["text"]

            # If we didn't find text content, log a warning and try to return something useful
            logger.warning("Could not find text content in response structure")
            logger.info(
                f"Response content structure: {json.dumps(output_message['content'])}"
            )
            return str(output_message["content"])
        except KeyError as e:
            logger.error(f"Unexpected response structure from Bedrock: {e}")
            logger.info(f"Response structure: {json.dumps(response)}")
            return None

    except client.exceptions.AccessDeniedException as e:
        logger.error(f"Access denied to Bedrock API: {str(e)}")
        logger.error(f"Check Lambda IAM role permissions for Bedrock")
        return None

    except client.exceptions.ResourceNotFoundException as e:
        logger.error(f"Resource not found in Bedrock API: {str(e)}")
        logger.error(f"Model ID '{model_id}' may be invalid or not available in region")
        return None

    except client.exceptions.ThrottlingException as e:
        logger.error(f"Bedrock API throttling error: {str(e)}")
        return None

    except ParamValidationError as e:
        logger.error(f"Parameter validation error with Bedrock API: {str(e)}")
        logger.error("Check the message format structure for the converse API")
        logger.exception("Parameter validation error details:")
        return None

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Bedrock API client error: {error_code} - {error_message}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error using Bedrock converse API: {str(e)}")
        logger.exception("Full exception details:")
        return None


def query_knowledge_base(
    query: str,
    knowledge_base_id: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    metadata_filter: Optional[Dict[str, Any]] = None,
    region_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Query the internal knowledge base using Bedrock Agent Runtime retrieve API

    Args:
        query: The query text to search the knowledge base with
        knowledge_base_id: The ID of the knowledge base to query
        max_results: Maximum number of retrieval results to return (default: 5)
        metadata_filter: Optional filter to apply to search based on metadata fields
        region_name: AWS region name (defaults to config region)

    Returns:
        Dictionary containing retrieval results or None if failed
    """
    # Basic validation
    if not query or not query.strip():
        logger.error("Empty query provided to query_knowledge_base")
        return None

    if not knowledge_base_id:
        logger.error("Empty knowledge_base_id provided to query_knowledge_base")
        return None

    try:
        logger.info(f"Querying knowledge base: {knowledge_base_id} with query: {query}")

        # Use region from config if not specified
        region = region_name or get_config().get("REGION")
        if not region:
            raise ValueError("AWS_REGION environment variable is required")

        # Create a bedrock agent runtime client
        client = boto3.client(service_name="bedrock-agent-runtime", region_name=region)

        # Build the retrieve API params
        retrieve_params = {
            "knowledgeBaseId": knowledge_base_id,
            "retrievalQuery": {"text": query},
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {"numberOfResults": max_results}
            },
        }

        # Add metadata filter if provided
        if metadata_filter:
            retrieve_params["retrievalConfiguration"][
                "metadataFilter"
            ] = metadata_filter

        # Call the retrieve API
        response = client.retrieve(**retrieve_params)

        # Extract and return the retrieval results
        results = response.get("retrievalResults", [])

        if not results:
            logger.info(f"No results found in knowledge base for query: {query}")
            return {"results": []}

        logger.info(f"Found {len(results)} results in knowledge base")
        return {"results": results}

    except client.exceptions.AccessDeniedException as e:
        logger.error(f"Access denied to Bedrock knowledge base: {str(e)}")
        logger.error(
            "AccessDeniedException: Check Lambda IAM role permissions for Bedrock Agent Runtime"
        )
        return None

    except client.exceptions.ResourceNotFoundException as e:
        logger.error(f"Knowledge base not found: {str(e)}")
        logger.error(
            f"ResourceNotFoundException: Knowledge base ID '{knowledge_base_id}' may be invalid or not available"
        )
        return None

    except client.exceptions.ThrottlingException as e:
        logger.error(f"Bedrock knowledge base API throttling error: {str(e)}")
        logger.error("ThrottlingException: Request rate exceeds service quota")
        return None

    except ParamValidationError as e:
        logger.error(
            f"Parameter validation error with Bedrock knowledge base API: {str(e)}"
        )
        logger.error("Check the query format structure for the retrieve API")
        logger.exception("Parameter validation error details:")
        return None

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(
            f"Bedrock knowledge base API client error: {error_code} - {error_message}"
        )
        return None

    except Exception as e:
        logger.error(f"Unexpected error using Bedrock knowledge base API: {str(e)}")
        logger.exception("Full exception details:")
        return None