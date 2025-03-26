"""
Research processor Lambda function for handling asynchronous research jobs
"""

import json
from typing import Dict, Any

# Import local utility modules
from utils.types import JobStatus
from utils.db_utils import get_db_manager
from utils.portfolio_utils import fetch_portfolio_companies
from utils import logger
from utils.config import get_config
from utils.research_utils import (
    identify_company_in_query,
    gather_company_info,
    query_internal_knowledge_base,
    analyze_company_info,
    generate_fallback_response,
    perform_deep_research_rounds,
)


class ResearchPipeline:
    """Main orchestrator for the research pipeline"""

    def __init__(
        self, job_id: str, user_id: str, query: str, deep_research: bool = False
    ):
        """
        Initialize the research pipeline

        Args:
            job_id: The job ID to process
            user_id: The user ID who submitted the job
            query: The research query text
            deep_research: Whether to perform deeper, more thorough research
        """
        # Basic validation
        if not job_id:
            raise ValueError("Invalid job_id parameter")

        if not query or not query.strip():
            raise ValueError("Invalid or empty query parameter")

        logger.info(f"Initializing research pipeline for job {job_id}")
        logger.info(f"Query: '{query}', Deep research mode: {deep_research}")

        # Set core properties
        self.job_id = job_id
        self.user_id = user_id or "anonymous"
        self.query = query.strip()
        self.deep_research = bool(deep_research)

        # Get dependencies
        self.db_manager = get_db_manager()

        # Initialize state variables
        self.current_research = ""
        self.company_data = (
            None  # Will hold the identified company for the current query
        )

        # Get configuration
        config = get_config()
        self.research_rounds = config.get("RESEARCH_ROUNDS", 1)
        if self.research_rounds < 1:
            self.research_rounds = 1

    def _update_status(self, status: JobStatus, message: str) -> None:
        """Update job status in the database"""
        logger.info(f"Status update: {status} - {message}")
        self.db_manager.update_job_status(self.job_id, status, message=message)

    def _complete_job(self, result: str) -> None:
        """Mark job as completed with result"""
        # Basic validation
        if not result or not result.strip():
            logger.warning("Completing job with empty result")

        logger.info(f"Completing job with {len(result)} chars result")
        self.db_manager.update_job_status(
            self.job_id, JobStatus.COMPLETED, message="Research complete", result=result
        )

    def _fail_job(self, error_msg: str) -> None:
        """Mark job as failed with error"""
        logger.error(f"Job failed: {error_msg}")
        self.db_manager.update_job_status(
            self.job_id, JobStatus.FAILED, error=error_msg
        )

    def process(self) -> bool:
        """
        Run the full research pipeline

        Returns:
            True if job completed successfully, False otherwise
        """
        try:
            # Step 1: Fetch portfolio companies
            self._update_status(JobStatus.PROCESSING, "Retrieving EQT portfolio data")
            companies = fetch_portfolio_companies()
            if not companies:
                self._fail_job("Failed to access portfolio data")
                return False

            logger.info(f"Fetched {len(companies)} portfolio companies")

            # Step 2: Identify company in query
            self._update_status(JobStatus.PROCESSING, "Identifying company to research")
            self.company_data = identify_company_in_query(self.query, companies)

            # Handle case where no company is identified
            if not self.company_data:
                self._update_status(JobStatus.PROCESSING, "Generating general response")
                fallback_response = generate_fallback_response(self.query)
                if not fallback_response:
                    self._fail_job("Failed to generate response")
                    return False

                self._complete_job(fallback_response)
                return True

            # Company was identified
            company_name = self.company_data.get("name", "the company")

            # Step 3: Gather company information
            self._update_status(
                JobStatus.PROCESSING, f"Gathering information about {company_name}"
            )
            eqt_content, company_content = gather_company_info(
                self.company_data, self.deep_research
            )

            # NOTE: This condition can be met if company website blocks bots.
            if not eqt_content or not company_content:
                self._fail_job("Failed to gather company information")
                return False

            # Step 4: Query internal knowledge base if company was identified
            kb_data = query_internal_knowledge_base(self.query)

            # Step 5: Analyze information and generate initial response
            self._update_status(JobStatus.PROCESSING, "Analyzing collected information")
            analysis = analyze_company_info(
                self.query, eqt_content, company_content, kb_data, self.deep_research
            )

            if not analysis:
                self._fail_job("Failed to analyze company information")
                return False

            # Step 6: Perform deep research if enabled
            if self.deep_research and self.research_rounds > 0:
                self._update_status(
                    JobStatus.PROCESSING, f"Performing deep research on {company_name}"
                )
                enriched_analysis = perform_deep_research_rounds(
                    self.query, analysis, rounds=self.research_rounds
                )
                analysis = enriched_analysis

            # Complete the job with the final analysis
            self._complete_job(analysis)
            return True

        except Exception as e:
            logger.error(f"Unexpected error during research pipeline: {str(e)}")
            logger.exception("Full exception details:")
            self._fail_job(f"Research error: {str(e)}")
            return False


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for the research processor

    Args:
        event: The event data containing job info
        context: The Lambda context

    Returns:
        Response dictionary with status code and body
    """
    try:
        # Start processing with structured logging
        logger.info("Received research job processing request")

        # Extract job details from the event with validation
        job_id = event.get("job_id")
        user_id = event.get("user_id", "anonymous")
        query = event.get("query")
        deep_research = event.get("deep_research", False)

        # Log event information
        logger.info(
            {
                "message": "Processing research job",
                "job_id": job_id,
                "user_id": user_id,
                "query_length": len(query) if query else 0,
                "deep_research": deep_research,
            }
        )

        # Validate required parameters
        if not job_id or not query:
            logger.error(
                {
                    "message": "Missing required job parameters",
                    "job_id": job_id or "missing",
                    "has_query": bool(query),
                }
            )
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required job parameters"}),
            }

        # Create and run the research pipeline
        pipeline = ResearchPipeline(job_id, user_id, query, deep_research)
        success = pipeline.process()

        if success:
            logger.info(f"Successfully processed job {job_id}")
        else:
            logger.warning(f"Job processing completed with errors: {job_id}")

        # Return status
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Job processing completed",
                    "job_id": job_id,
                    "success": success,
                }
            ),
        }

    except Exception as e:
        # Log exception with details
        logger.error(f"Unhandled exception in research processor: {str(e)}")
        logger.exception("Full exception details:")

        # Return error response
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
