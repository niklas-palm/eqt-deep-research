"""
EQT Portfolio Research API Lambda handler
"""

import json
import uuid
import boto3
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.metrics import MetricUnit, Metrics
from typing import Dict, Any, Optional

# Import local utility modules
from utils.db_utils import get_db_manager
from utils import logger
from utils.config import get_config

# Initialize API Gateway resolver
cors_config = CORSConfig(allow_origin="*", max_age=300)
app = APIGatewayRestResolver(cors=cors_config)

# Initialize metrics
metrics = Metrics()


# Helper function to extract user information
def get_user_info(event: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extract user information from an API Gateway event

    Args:
        event: The API Gateway event

    Returns:
        User information dictionary or None if not available
    """
    try:
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            claims = event["requestContext"]["authorizer"].get("claims", {})
            if "sub" in claims:
                return {"userId": claims["sub"], "email": claims.get("email", "")}
    except Exception as e:
        logger.error(f"Error extracting user info: {str(e)}")

    return None


#######################
# Public API endpoints
#######################


@app.get("/api/public/health")
def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


#######################
# Protected API endpoints
#######################


@app.get("/api/auth/me")
def get_profile():
    """Return user profile information from Cognito"""
    # Get user from the event
    event = app.current_event.raw_event
    user = get_user_info(event) or {}

    # Return user info
    return {
        "userId": user.get("userId", ""),
        "email": user.get("email", ""),
        "message": "Authentication successful",
    }


@app.post("/api/auth/research")
def create_research_job():
    """Start an asynchronous portfolio research job"""
    # Extract request parameters
    body = app.current_event.json_body
    event = app.current_event.raw_event
    user = get_user_info(event) or {}
    query = body.get("query", "")
    deep_research = body.get("deep_research", False)
    job_id = f"job_{uuid.uuid4()}"
    user_id = user.get("userId", "anonymous")

    if not query:
        return {"error": "Missing query parameter", "status": "error"}

    # Log the incoming request
    logger.info(
        f"Creating research job for: {query}",
        extra={
            "jobId": job_id,
            "userId": user_id,
        },
    )
    
    # Record metric for job creation
    metrics.add_dimension(name="ResearchType", value="Deep" if deep_research else "Standard")
    metrics.add_metric(name="ResearchJobCreated", unit=MetricUnit.Count, value=1)

    # Create job in DynamoDB
    db_manager = get_db_manager()
    job = db_manager.create_job(job_id, "", user_id, query)

    if not job:
        return {"error": "Failed to create job", "status": "failed"}

    # Invoke the research processor Lambda asynchronously
    lambda_client = boto3.client("lambda")
    research_processor_name = get_config().get("RESEARCH_PROCESSOR_LAMBDA")
    if not research_processor_name:
        return {
            "error": "Missing RESEARCH_PROCESSOR_LAMBDA configuration",
            "status": "error",
        }

    logger.info(
        f"Invoking {research_processor_name} Lambda asynchronously for job {job_id}"
    )

    try:
        # Prepare the payload
        payload = {
            "job_id": job_id,
            "user_id": user_id,
            "query": query,
            "deep_research": deep_research,
        }

        # Invoke the Lambda function asynchronously
        lambda_client.invoke(
            FunctionName=research_processor_name,
            InvocationType="Event",  # Asynchronous invocation
            Payload=json.dumps(payload),
        )
        logger.info(f"Successfully invoked research processor for job {job_id}")
    except Exception as e:
        logger.error(f"Error invoking research processor Lambda: {str(e)}")
        # Don't fail the request, we already created the job record

    # Return immediately with job info
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Research job created and processing has started",
    }


@app.get("/api/auth/research/<job_id>")
def get_research_status(job_id):
    """Get the status of a research job"""

    if not job_id:
        return {"error": "Missing job ID", "status": "error"}

    # Get job status from DynamoDB
    db_manager = get_db_manager()
    job = db_manager.get_job(job_id)

    if not job:
        return {"error": f"Research job {job_id} not found", "status": "not_found"}

    # Return job status
    return job


# AWS Lambda handler
@logger.inject_lambda_context
@metrics.log_metrics  # This decorator will automatically flush metrics
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """AWS Lambda handler"""
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Unhandled exception")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
