# Makefile for YouTube Study Buddy Serverless Deployment
# Provides convenient commands for building, testing, and deploying

.PHONY: help build deploy test clean local seed rollback

# Default target
.DEFAULT_GOAL := help

# Environment variables (can be overridden)
ENVIRONMENT ?= dev
AWS_REGION ?= us-east-1
DEPLOY_TARGET ?= s3

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

##@ General

help: ## Display this help message
	@echo ""
	@echo "$(BLUE)YouTube Study Buddy - Serverless Deployment$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make [target] [ENVIRONMENT=dev|staging|production]"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make build                    # Build Lambda layer"
	@echo "  make deploy ENVIRONMENT=dev   # Deploy to dev environment"
	@echo "  make test                     # Run all tests"
	@echo "  make local                    # Start local development"
	@echo ""

##@ Build

build: build-layer package-lambdas ## Build Lambda layer and package functions

build-layer: ## Build Lambda layer with CLI and dependencies
	@echo "$(BLUE)Building Lambda layer...$(NC)"
	@cd lambda-layer && bash build.sh

package-lambdas: ## Package all Lambda functions
	@echo "$(BLUE)Packaging Lambda functions...$(NC)"
	@for dir in lambda/*/; do \
		if [ "$$(basename $$dir)" != "shared" ]; then \
			echo "Packaging $$(basename $$dir)..."; \
			cd $$dir && zip -r $$(basename $$dir).zip . -x "*.zip" -x "__pycache__/*" -q && cd ../..; \
		fi \
	done
	@echo "$(GREEN)All functions packaged$(NC)"

##@ Deploy

deploy: deploy-all ## Deploy complete stack (alias for deploy-all)

deploy-all: ## Deploy infrastructure, Lambda functions, and frontend
	@echo "$(BLUE)Deploying complete stack to $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) AWS_REGION=$(AWS_REGION) DEPLOY_TARGET=$(DEPLOY_TARGET) ./scripts/deploy-all.sh

deploy-infra: ## Deploy infrastructure only (Terraform)
	@echo "$(BLUE)Deploying infrastructure to $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) AWS_REGION=$(AWS_REGION) ./scripts/deploy-infrastructure.sh deploy

deploy-lambda: ## Deploy Lambda functions only
	@echo "$(BLUE)Deploying Lambda functions to $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) AWS_REGION=$(AWS_REGION) ./scripts/deploy-lambda.sh

deploy-frontend: ## Deploy frontend only
	@echo "$(BLUE)Deploying frontend to $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) DEPLOY_TARGET=$(DEPLOY_TARGET) ./scripts/deploy-frontend.sh

deploy-dev: ## Quick deploy to dev environment
	@$(MAKE) deploy ENVIRONMENT=dev

deploy-staging: ## Deploy to staging environment
	@$(MAKE) deploy ENVIRONMENT=staging

deploy-production: ## Deploy to production (requires confirmation)
	@$(MAKE) deploy ENVIRONMENT=production

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/test-lambda.sh

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@TEST_TYPE=unit ENVIRONMENT=$(ENVIRONMENT) ./scripts/test-lambda.sh

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@TEST_TYPE=integration ENVIRONMENT=$(ENVIRONMENT) ./scripts/test-lambda.sh

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests against $(ENVIRONMENT)...$(NC)"
	@TEST_TYPE=e2e ENVIRONMENT=$(ENVIRONMENT) ./scripts/test-lambda.sh

test-invoke: ## Test Lambda invocations
	@echo "$(BLUE)Testing Lambda invocations...$(NC)"
	@TEST_TYPE=invoke ENVIRONMENT=$(ENVIRONMENT) ./scripts/test-lambda.sh

coverage: ## Generate test coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/test-lambda.sh
	@echo "Coverage report: coverage/index.html"

##@ Local Development

local: ## Start local development environment
	@echo "$(BLUE)Starting local development environment...$(NC)"
	@./scripts/local-dev.sh start

local-stop: ## Stop local development services
	@echo "$(BLUE)Stopping local services...$(NC)"
	@./scripts/local-dev.sh stop

local-restart: ## Restart local development environment
	@echo "$(BLUE)Restarting local environment...$(NC)"
	@./scripts/local-dev.sh restart

local-logs: ## Show local service logs
	@./scripts/local-dev.sh logs

local-tables: ## Create local DynamoDB tables
	@echo "$(BLUE)Creating local DynamoDB tables...$(NC)"
	@./scripts/local-dev.sh tables

##@ Data Management

seed: ## Seed development data
	@echo "$(BLUE)Seeding development data for $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/seed-data.sh

seed-clean: ## Clean seed data
	@echo "$(BLUE)Cleaning seed data for $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/seed-data.sh clean

##@ Terraform

tf-init: ## Initialize Terraform
	@echo "$(BLUE)Initializing Terraform...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/deploy-infrastructure.sh init

tf-plan: ## Show Terraform plan
	@echo "$(BLUE)Planning Terraform changes for $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/deploy-infrastructure.sh plan

tf-validate: ## Validate Terraform configuration
	@echo "$(BLUE)Validating Terraform configuration...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/deploy-infrastructure.sh validate

tf-fmt: ## Format Terraform files
	@echo "$(BLUE)Formatting Terraform files...$(NC)"
	@cd terraform && terraform fmt -recursive

tf-state: ## Show Terraform state
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/deploy-infrastructure.sh state

tf-outputs: ## Save Terraform outputs to .env file
	@echo "$(BLUE)Saving Terraform outputs...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/deploy-infrastructure.sh outputs

tf-destroy: ## Destroy infrastructure (DANGEROUS)
	@echo "$(YELLOW)WARNING: This will destroy all infrastructure!$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/deploy-infrastructure.sh destroy

##@ Rollback

rollback: ## Interactive rollback menu
	@echo "$(BLUE)Starting rollback for $(ENVIRONMENT)...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/rollback.sh

rollback-lambda: ## Rollback Lambda functions
	@echo "$(BLUE)Rolling back Lambda functions...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/rollback.sh lambda

rollback-frontend: ## Rollback frontend deployment
	@echo "$(BLUE)Rolling back frontend...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/rollback.sh frontend

rollback-all: ## Rollback all components
	@echo "$(YELLOW)Rolling back all components...$(NC)"
	@ENVIRONMENT=$(ENVIRONMENT) ./scripts/rollback.sh all

##@ Monitoring

logs: ## Tail Lambda function logs (requires FUNCTION=name)
	@if [ -z "$(FUNCTION)" ]; then \
		echo "$(YELLOW)Usage: make logs FUNCTION=submit_video$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Tailing logs for ytstudy-$(ENVIRONMENT)-$(FUNCTION)...$(NC)"
	@aws logs tail /aws/lambda/ytstudy-$(ENVIRONMENT)-$(FUNCTION) --follow --region $(AWS_REGION)

logs-all: ## Show recent logs from all Lambda functions
	@echo "$(BLUE)Fetching recent logs from all functions...$(NC)"
	@for dir in lambda/*/; do \
		if [ "$$(basename $$dir)" != "shared" ]; then \
			func=$$(basename $$dir); \
			echo "\n$(GREEN)=== $$func ===$(NC)"; \
			aws logs tail /aws/lambda/ytstudy-$(ENVIRONMENT)-$$func --since 10m --region $(AWS_REGION) 2>/dev/null || echo "No logs"; \
		fi \
	done

metrics: ## Show CloudWatch metrics (requires FUNCTION=name)
	@if [ -z "$(FUNCTION)" ]; then \
		echo "$(YELLOW)Usage: make metrics FUNCTION=submit_video$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Fetching metrics for ytstudy-$(ENVIRONMENT)-$(FUNCTION)...$(NC)"
	@aws cloudwatch get-metric-statistics \
		--namespace AWS/Lambda \
		--metric-name Invocations \
		--dimensions Name=FunctionName,Value=ytstudy-$(ENVIRONMENT)-$(FUNCTION) \
		--start-time $$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
		--end-time $$(date -u +%Y-%m-%dT%H:%M:%S) \
		--period 300 \
		--statistics Sum \
		--region $(AWS_REGION)

##@ Utilities

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf lambda/**/*.zip
	@rm -rf lambda-layer/cli-layer.zip
	@rm -rf lambda-layer/build
	@rm -f terraform/tfplan-*
	@rm -rf coverage
	@rm -rf .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete$(NC)"

status: ## Show deployment status
	@echo "$(BLUE)Deployment Status for $(ENVIRONMENT)$(NC)"
	@echo ""
	@if [ -f .env.$(ENVIRONMENT).terraform ]; then \
		echo "$(GREEN)Infrastructure Outputs:$(NC)"; \
		cat .env.$(ENVIRONMENT).terraform | grep -v "^#" | head -10; \
	else \
		echo "$(YELLOW)No infrastructure deployed$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)Lambda Functions:$(NC)"
	@aws lambda list-functions \
		--query "Functions[?starts_with(FunctionName, 'ytstudy-$(ENVIRONMENT)')].FunctionName" \
		--output table \
		--region $(AWS_REGION) 2>/dev/null || echo "  None found"

version: ## Show versions of tools
	@echo "$(BLUE)Tool Versions:$(NC)"
	@echo "  AWS CLI:    $$(aws --version 2>&1 | head -1)"
	@echo "  Terraform:  $$(terraform version | head -1)"
	@echo "  Node:       $$(node --version)"
	@echo "  npm:        $$(npm --version)"
	@echo "  Python:     $$(python3 --version)"
	@echo "  Make:       $$(make --version | head -1)"

docs: ## Open documentation
	@echo "$(BLUE)Opening documentation...$(NC)"
	@if [ -f docs/SERVERLESS-QUICKSTART.md ]; then \
		cat docs/SERVERLESS-QUICKSTART.md; \
	else \
		echo "Documentation not found"; \
	fi

validate-env: ## Validate environment configuration
	@echo "$(BLUE)Validating environment: $(ENVIRONMENT)$(NC)"
	@if [ "$(ENVIRONMENT)" != "dev" ] && [ "$(ENVIRONMENT)" != "staging" ] && [ "$(ENVIRONMENT)" != "production" ]; then \
		echo "$(YELLOW)Warning: Unknown environment '$(ENVIRONMENT)'$(NC)"; \
		echo "Valid environments: dev, staging, production"; \
	fi
	@if [ ! -f .env.$(ENVIRONMENT) ]; then \
		echo "$(YELLOW)Warning: .env.$(ENVIRONMENT) not found$(NC)"; \
	fi
	@echo "$(GREEN)Environment: $(ENVIRONMENT)$(NC)"
	@echo "$(GREEN)Region: $(AWS_REGION)$(NC)"
	@echo "$(GREEN)Deploy Target: $(DEPLOY_TARGET)$(NC)"

##@ CI/CD

ci-test: ## CI/CD test step
	@echo "$(BLUE)Running CI tests...$(NC)"
	@$(MAKE) test-unit
	@$(MAKE) test-integration

ci-deploy: ## CI/CD deploy step
	@echo "$(BLUE)Running CI deployment...$(NC)"
	@$(MAKE) build
	@$(MAKE) deploy-all

ci-validate: ## CI/CD validation step
	@echo "$(BLUE)Running CI validation...$(NC)"
	@$(MAKE) tf-validate
	@$(MAKE) validate-env
