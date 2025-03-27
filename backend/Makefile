.ONESHELL:
SHELL := /bin/bash

# Help function to display available commands
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Environment variables with default values
export STACKNAME ?= eqt
export REGION ?= eu-west-1
export COGNITO_USER_POOL_ARN ?= arn:aws:cognito-idp:eu-west-1:675385716628:userpool/eu-west-1_ZglCV4T4H 
export KNOWLEDGEBASE_ID ?= MOOFWQ2QDV # Bedrock knowledgebase ID
export RESEARCH_ROUNDS ?= 2
export STACK_OUTPUTS_FILE := $(shell mktemp -t stack_outputs.XXXXXX.json)

# Mark targets that don't create files as .PHONY
.PHONY: validate build deploy delete sync logs logs-filter logs-tail upload-frontend test

validate: ## Validates and lints the SAM template
	@echo "Validating SAM template..."
	sam validate --lint

build: ## Downloads all dependencies and builds resources
	@echo "Building SAM application..."
	sam build

deploy: ## Deploys the artifacts from the previous build
	@echo "Deploying stack $(STACKNAME) to region $(REGION)..."
	sam deploy \
		--stack-name $(STACKNAME) \
		--resolve-s3 \
		--capabilities CAPABILITY_IAM \
		--region $(REGION) \
		--parameter-overrides \
		CognitoUserPoolArn=$(COGNITO_USER_POOL_ARN) \
		KnowledgebaseId=$(KNOWLEDGEBASE_ID) \
		ResearchRounds=$(RESEARCH_ROUNDS) \
		--no-fail-on-empty-changeset

delete: ## Deletes the CloudFormation stack
	@echo "Deleting stack $(STACKNAME) from region $(REGION)..."
	sam delete \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--no-prompts

sync: ## Syncs local changes to AWS Lambda
	@echo "Syncing local changes to Lambda function..."
	sam sync \
		--stack-name $(STACKNAME) \
		--watch

logs: ## Show logs for the Lambda function
	@echo "Fetching logs for Lambda function..."
	sam logs \
		--stack-name $(STACKNAME) \
		--region $(REGION)

logs-tail: ## Tail logs for the Lambda function
	@echo "Tailing logs for Lambda function..."
	sam logs \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--tail

logs-filter: ## Filter logs for errors and warnings
	@echo "Filtering logs for errors and warnings..."
	sam logs \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--filter "ERROR"

upload-frontend: ## Upload frontend build to S3 bucket
	@echo "Fetching CloudFormation outputs..."
	@aws cloudformation describe-stacks \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--query "Stacks[0].Outputs" \
		--output json > $(STACK_OUTPUTS_FILE)

	@echo "Processing frontend deployment..."
	@BUCKET_NAME=$$(jq -r '.[] | select(.OutputKey=="FrontendBucketName") | .OutputValue' $(STACK_OUTPUTS_FILE)) && \
	DISTRIBUTION_ID=$$(jq -r '.[] | select(.OutputKey=="CloudFrontDistributionId") | .OutputValue' $(STACK_OUTPUTS_FILE)) && \
	CLOUDFRONT_URL=$$(jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue' $(STACK_OUTPUTS_FILE)) && \
	echo "S3 bucket name: $$BUCKET_NAME" && \
	echo "CloudFront distribution ID: $$DISTRIBUTION_ID" && \
	echo "Uploading to S3 bucket: $$BUCKET_NAME" && \
	aws s3 sync ../frontend/dist/ s3://$$BUCKET_NAME/ --delete && \
	echo "Invalidating CloudFront cache: $$DISTRIBUTION_ID" && \
	aws cloudfront create-invalidation --distribution-id $$DISTRIBUTION_ID --paths "/*" && \
	echo "Frontend deployment complete" && \
	echo "CloudFront URL: $$CLOUDFRONT_URL"
	
	# Clean up temporary file
	@rm $(STACK_OUTPUTS_FILE)

test: ## Run tests
	@echo "Running tests..."
	@python -m unittest discover tests

go: build deploy ## Build and deploys the stack