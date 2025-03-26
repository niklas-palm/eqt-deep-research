"""DynamoDB utility functions for research jobs"""

import boto3
import datetime
from typing import Dict, Any, Optional
from .types import JobProgress, JobStatus
from . import logger
from .config import get_config


def enum_to_str(enum_value) -> str:
    """
    Convert enum to string without class prefix

    Args:
        enum_value: Enum value to convert

    Returns:
        String representation without class prefix
    """
    return str(enum_value).split(".")[-1]


class DynamoDBManager:
    """Manager for DynamoDB operations related to research jobs"""

    def __init__(self, jobs_table_name: Optional[str] = None):
        """
        Initialize the DynamoDB manager

        Args:
            jobs_table_name: The name of the DynamoDB table for job progress (defaults to env variable)
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.jobs_table_name = jobs_table_name or get_config().get("JOBS_TABLE_NAME")
        if not self.jobs_table_name:
            raise ValueError("JOBS_TABLE_NAME environment variable is required")

        # Initialize table reference
        self.jobs_table = self.dynamodb.Table(self.jobs_table_name)
        logger.info(f"DynamoDB manager initialized with table: {self.jobs_table_name}")

    def create_job(
        self, job_id: str, session_id: str, user_id: str, query: str
    ) -> Optional[JobProgress]:
        """
        Create a new job in the jobs table

        Args:
            job_id: Unique ID for the job
            session_id: Associated chat session ID
            user_id: User who initiated the job
            query: The original query text

        Returns:
            JobProgress object or None if failed
        """
        now = datetime.datetime.now().isoformat()
        try:
            job = JobProgress(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=now,
                updated_at=now,
                message="Job created, waiting to start processing",
            )

            # Convert JobProgress to dict
            job_dict = job.model_dump() if hasattr(job, "model_dump") else job.dict()

            item = {
                "jobId": job_id,
                "sessionId": session_id,
                "userId": user_id,
                "query": query,
                "status": enum_to_str(job_dict["status"]),  # Convert enum to string
                "created_at": now,
                "updated_at": now,
                "message": job_dict["message"],
                "ttl": int(
                    (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
                ),
            }

            self.jobs_table.put_item(Item=item)
            logger.info(f"Created job {job_id} for user {user_id}")
            return job
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        message: Optional[str] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a job

        Args:
            job_id: The job ID to update
            status: New status
            message: Optional status message
            result: Optional final result (for completed jobs)
            error: Optional error message (for failed jobs)

        Returns:
            True if successful, False otherwise
        """
        now = datetime.datetime.now().isoformat()
        update_expression_parts = [
            "set updated_at = :updated_at",
            "#job_status = :status",
        ]
        expression_values = {
            ":updated_at": now,
            ":status": enum_to_str(status),  # Convert enum to string
        }
        expression_names = {"#job_status": "status"}

        if message is not None:
            update_expression_parts.append("#msg = :message")
            expression_values[":message"] = message
            expression_names["#msg"] = "message"

        if result is not None:
            update_expression_parts.append("#res = :result")
            expression_values[":result"] = result
            expression_names["#res"] = "result"

        if error is not None:
            update_expression_parts.append("#err = :error")
            expression_values[":error"] = error
            expression_names["#err"] = "error"

        update_expression = " , ".join(update_expression_parts)

        try:
            self.jobs_table.update_item(
                Key={"jobId": job_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names,
            )
            logger.info(f"Updated job {job_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job progress information

        Args:
            job_id: The job ID to retrieve

        Returns:
            Job information or None if not found
        """
        try:
            response = self.jobs_table.get_item(Key={"jobId": job_id})
            return response.get("Item")
        except Exception as e:
            logger.error(f"Error retrieving job: {e}")
            return None


# Convenience function to get a singleton instance
def get_db_manager() -> DynamoDBManager:
    """
    Get a DynamoDB manager instance

    Returns:
        A DynamoDB manager instance
    """
    return DynamoDBManager()
