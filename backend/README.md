# EQT Portfolio Research Backend

This backend service provides AI-powered research and analysis on EQT portfolio companies using data from the Stanford 2024 AI Index Report and optionally the web.

## Architecture Overview

The backend is built as an AWS Serverless application using AWS Lambda, API Gateway, and DynamoDB with the following components:

1. **API Gateway**: Entry point for all HTTP requests
2. **Lambda Functions**:
   - `api.py`: Main API handler for user requests
   - `research_processor.py`: Asynchronous research processing
3. **DynamoDB**: Stores job status and research results
4. **AWS Cognito**: Handles user authentication

## Research Pipeline

The research process follows a functional approach with these steps:

1. **Company Identification**: Analyzes user queries to determine which EQT portfolio company is being referenced
2. **Information Gathering**: Scrapes company websites and EQT portfolio data
3. **Knowledge Base Query**: Searches the Stanford AI Index report using query reformulation for improved vector search results
   - Uses LLM to reformulate the original query into multiple optimized search queries to increase search space.
4. **Analysis Generation**: Processes all gathered information to produce comprehensive answers
5. **Deep Research** (optional): Performs additional rounds of research to fill knowledge gaps using the Tavily Search API for internet search, enriching the analysis.

## Key Components

### Core Modules

- **research_processor.py**: The main orchestrator class that manages the research workflow
- **research_utils.py**: Core research functionality implemented as pure functions
- **config.py**: Centralized configuration management
- **bedrock_utils.py**: Interfaces with AWS Bedrock for AI processing
- **db_utils.py**: Database interactions for job tracking

### Utility Functions

- **portfolio_utils.py**: Handles EQT portfolio company data
- **web_utils.py**: Web scraping capabilities
- **ai_utils.py**: AI model interaction helpers and prompt templates
- **types.py**: Type definitions using Pydantic models

## Data Sources

1. **EQT Portfolio Data**: Stored in `assets/eqt_portfolio.json`
2. **Stanford AI Index Report**: Processed content from the AI Index 2024 report
3. **Company Websites**: Dynamically scraped during research
4. **Tavily Search API**: Third-party search API used for enhanced deep research capabilities

## Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.11+
- AWS SAM CLI
- AWS Systems Manager Parameter Store parameter: `/3p/keys/tavily` containing your Tavily API key

### Environment Variables

The following environment variables are required:

- `AWS_REGION`: AWS region for services
- `JOBS_TABLE_NAME`: DynamoDB table name for job tracking
- `RESEARCH_PROCESSOR_LAMBDA`: Name of the research processor Lambda
- `KB_ID`: Knowledge base ID for the Stanford AI Index data (optional, leave empty to disable knowledge base retrieval)
- `TAVILY_API_KEY`: API key for external research (automatically loaded from SSM parameter `/3p/keys/tavily`)
- `RESEARCH_ROUNDS`: Number of deep research rounds to perform (default: 1)

### Deployment

1. Build the SAM application:

   ```
   cd backend
   make build
   ```

2. Deploy to AWS:
   ```
   make deploy
   ```

### Running Tests

The project includes simple tests for key functionality:

1. Run tests (requires AWS credentials):
   ```
   make test
   ```

Note: Tests use actual AWS Bedrock services and require valid AWS credentials with Bedrock access.

## API Endpoints

### Public Endpoints

- `GET /api/public/health`: Health check endpoint

### Protected Endpoints (Require Authentication)

- `GET /api/auth/me`: Returns authenticated user information
- `POST /api/auth/research`: Creates a new research job
- `GET /api/auth/research/<job_id>`: Gets the status or result of a research job

## Error Handling and Logging

The application uses the AWS Lambda Powertools Logger for structured logging. Error handling is implemented at multiple levels:

- **API-level validation**: Validates requests before processing
- **Function-specific error handling**: Each function handles its own specific errors
- **Global exception handling**: Catches unexpected errors

## Future Improvements

- Additional test coverage including integration tests
- More comprehensive documentation and docstrings
- Enhanced exception handling across API calls
- Optimized content retrieval and caching
- User session persistence for chat history
