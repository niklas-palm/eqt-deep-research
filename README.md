# EQT Portfolio Research

An AI-powered tool for analyzing EQT portfolio companies using the Stanford 2024 AI Index Report and optionally the web.

## Overview

This application provides a chat interface for users to ask questions about EQT portfolio companies in the context of AI trends and developments. It connects to AWS Bedrock AI services to analyze companies and generate insights.

Key features:

- **Company Identification**: Automatically identifies which EQT portfolio company is being asked about
- **Deep Research**: Option to perform deeper, more thorough research for comprehensive analysis
- **Asynchronous Processing**: Handles research requests in the background with status updates

## Architecture

The project follows a modern serverless architecture:

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: AWS Lambda functions with Python
- **Authentication**: AWS Cognito
- **AI Services**: AWS Bedrock with Claude models
- **Data Storage**: DynamoDB for job tracking

## Project Structure

```
eqt/
├── frontend/             # React frontend application
│   ├── public/           # Static assets
│   ├── src/              # Source code
│   │   ├── components/   # React components
│   │   ├── lib/          # Utility functions and hooks
│   │   └── pages/        # Page components
│   └── ...               # Config files
├── backend/              # AWS SAM backend application
│   ├── lambda/           # Lambda function code
│   │   ├── api.py        # API Gateway handler
│   │   ├── research_processor.py # Asynchronous research pipeline
│   │   └── utils/        # Utility modules
│   │       ├── ai_utils.py      # AI prompt helpers
│   │       ├── bedrock_utils.py # AWS Bedrock integration
│   │       ├── research_utils.py # Research functions
│   │       └── ...              # Other utilities
│   ├── tests/            # Backend tests
│   ├── template.yaml     # CloudFormation template
│   └── Makefile          # Commands for deployment
└── preprocess-data/      # Tools to process the Stanford AI Index Report
```

## Key Components

### Backend

The backend consists of two main Lambda functions:

1. **API Gateway Handler** (`api.py`): Handles HTTP requests and job creation
2. **Research Processor** (`research_processor.py`): Performs the actual research asynchronously

The research pipeline follows these steps:

1. Identify which EQT portfolio company is mentioned in the query
2. Gather information from company websites and EQT portfolio data
3. Query the Stanford AI Index report knowledge base
4. Analyze all collected information to generate a response
5. Optionally perform deep research for more comprehensive answers

### Frontend

The frontend provides a clean chat interface with:

- User authentication via AWS Cognito
- Research query submission
- Live status updates
- Research depth toggle
- Markdown rendering for formatted responses

## Getting Started

### Prerequisites

1. AWS CLI installed and configured
2. AWS SAM CLI installed
3. Node.js and npm/yarn
4. Python 3.11+
5. Access to AWS Bedrock Claude models
6. AWS Systems Manager Parameter Store parameter: `/3p/keys/tavily` containing your Tavily API key
7. Optional: Bedrock Knowledge Base ID for the Stanford AI Index data (leave empty to disable)

### Backend Deployment

1. Navigate to the backend directory:

   ```
   cd backend
   ```

2. Build the SAM application:

   ```
   make build
   ```

3. Deploy to AWS:
   ```
   make deploy
   ```

### Frontend Setup

1. Install dependencies:

   ```
   cd frontend
   npm install
   ```

2. Run locally:

   ```
   npm run dev
   ```

3. Access the application at `http://localhost:5173`

### Running Tests

The backend includes simple tests:

```
cd backend
make test
```

## Implementation Details

### AI Capabilities

- Uses AWS Bedrock models for natural language understanding and generation
- Employs different model sizes based on task complexity:
  - SMALL: Basic questions, fallback responses
  - MEDIUM: Company identification, knowledge gap detection
  - LARGE: In-depth analysis and research synthesis

### Data Sources

1. **EQT Portfolio Data**: Company information from EQT's portfolio
2. **Stanford AI Index Report**: Processed into a knowledge base
3. **Company Websites**: Dynamically scraped during research
4. **Tavily Search API**: Used for deep research capabilities
