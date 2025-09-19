include makefile.mk
include .env

SERVICE := $(word 2, $(MAKECMDGOALS))  # auth, ...
SERVICE_DIR := services/$(strip $(SERVICE))

ENV_STATE := $(word 3, $(MAKECMDGOALS))  # development, production


# --- Helm -------------------------------------------------------------------------------------------------------------
.PHONY: helm-deps helm-check helm-decrypt helm-encrypt helm-deploy helm-uninstall

NAME := $(strip $(SERVICE))-service
NAMESPACE := $(strip $(if $(word 3, $(MAKECMDGOALS)), $(word 3, $(MAKECMDGOALS)),development))

CHART_DIR := $(SERVICE_DIR)/helm

SECRETS_FILE := $(CHART_DIR)/secrets.yaml
SECRETS_ENC_FILE := $(CHART_DIR)/secrets.enc.yaml
VALUES_LOCAL_FILE := $(CHART_DIR)/values.local.yaml

helm-deps: ## helm-deps [SERVICE] — update helm dependencies for specified service.
	@helm dependency build $(CHART_DIR)

helm-check: ## helm-print [SERVICE] [NAMESPACE] — check and print helm template for specified service with specified namespace.
	@helm secrets template $(NAME) $(CHART_DIR) \
		$(if $(wildcard $(VALUES_LOCAL_FILE)), -f $(VALUES_LOCAL_FILE)) \
		$(if $(wildcard $(SECRETS_FILE)), -f $(SECRETS_FILE)) \
		--namespace $(NAMESPACE)

helm-decrypt: ## helm-decrypt [SERVICE] — decrypt helm secrets for specified service.
	@$(if $(wildcard $(SECRETS_ENC_FILE)), ( \
		helm secrets decrypt $(SECRETS_ENC_FILE) > $(SECRETS_FILE) \
	), exit 0)

helm-encrypt: ## helm-encrypt [SERVICE] — encrypt helm secrets for specified service.
	@$(if $(wildcard $(SECRETS_FILE)), ( \
		helm secrets encrypt $(SECRETS_FILE) > $(SECRETS_ENC_FILE) && git add $(SECRETS_ENC_FILE) \
	), exit 0)

helm-deploy: ## helm-deploy [SERVICE] [NAMESPACE] — deploy helm chart for specified service with specified namespace. Default namespace is `development`.
	@helm secrets upgrade --install $(NAME) $(CHART_DIR) \
	  $(if $(wildcard $(VALUES_LOCAL_FILE)), -f $(VALUES_LOCAL_FILE)) \
	  $(if $(wildcard $(SECRETS_ENC_FILE)), -f $(SECRETS_ENC_FILE)) \
	  --namespace $(NAMESPACE) \
	  --create-namespace \
	  --timeout 2m \
	  --atomic

helm-uninstall: ## helm-uninstall [SERVICE] [NAMESPACE] — uninstall helm chart for specified service with specified namespace.
	@helm uninstall $(NAME) --namespace $(NAMESPACE)

# --- Docker -----------------------------------------------------------------------------------------------------------
.PHONY: build rebuild up stop down down-v destroy tag-image

DOCKERHUB_USERNAME ?= mimspace
IMAGE_NAME := $(strip $(SERVICE))-service

REPOSITORY := $(DOCKERHUB_USERNAME)/$(IMAGE_NAME)
IMAGE_TAG := $(strip $(if $(word 3, $(MAKECMDGOALS)), $(word 3, $(MAKECMDGOALS)),develop))

DOCKER_COMPOSE_FLAGS := \
	--env-file $(SERVICE_DIR)/.env \
	-p $(IMAGE_NAME) \
	-f $(SERVICE_DIR)/docker/docker-compose.yml

build: ## build [SERVICE] — build docker image for specified service.
	$(call LOG_HEADER,build an image: $(REPOSITORY):$(IMAGE_TAG))
	@docker build \
	--build-arg POETRY_FLAGS="--only main,test" \
	--file $(SERVICE_DIR)/docker/Dockerfile \
	--tag $(REPOSITORY):$(IMAGE_TAG) \
	--target final \
	--secret id=github_token,src=$(GITHUB_ACCESS_TOKEN_FILE) \
	$(SERVICE_DIR)
	$(call LOG_HEADER,the image $(REPOSITORY):$(IMAGE_TAG) has been created!)

rebuild: down destroy build ## rebuild [SERVICE] — rebuild docker image for specified service.

up: ## up [SERVICE] — start docker container for specified service.
	$(call LOG_HEADER,starting $(REPOSITORY):$(IMAGE_TAG))
	@docker compose $(DOCKER_COMPOSE_FLAGS) up -d
	$(call LOG_HEADER,$(REPOSITORY):$(IMAGE_TAG) has been started!)

stop: ## stop [SERVICE] — stop docker container for specified service.
	$(call LOG_HEADER,stopping $(REPOSITORY):$(IMAGE_TAG))
	@docker compose $(DOCKER_COMPOSE_FLAGS) stop
	$(call LOG_HEADER,$(REPOSITORY):$(IMAGE_TAG) has been stopped!)

down: ## down [SERVICE] — shut down docker container for specified service.
	$(call LOG_HEADER,shutting down $(REPOSITORY):$(IMAGE_TAG))
	@docker compose $(DOCKER_COMPOSE_FLAGS) down $(DEV_NULL)
	$(call LOG_HEADER,$(REPOSITORY):$(IMAGE_TAG) has been shut down!)

down-v: ## down-v [SERVICE] — shut down docker containers and remove volumes for specified service.
	$(call LOG_HEADER,shutting down $(REPOSITORY):$(IMAGE_TAG) and removing volumes)
	@docker compose $(DOCKER_COMPOSE_FLAGS) down -v $(DEV_NULL)
	$(call LOG_HEADER,$(REPOSITORY):$(IMAGE_TAG) has been shut down!)

destroy: down ## Shut down docker containers and destroy image for specified service.
	@docker rmi -f $(REPOSITORY):$(IMAGE_TAG) $(DEV_NULL)
	$(call LOG_HEADER,image $(REPOSITORY):$(IMAGE_TAG) has been destroyed!)

tag-image: ## tag-image [SERVICE] [TAG] — tag specified service docker image with the specified version.
	docker tag $(REPOSITORY):develop $(REPOSITORY):$(IMAGE_TAG)

# --- Alembic ----------------------------------------------------------------------------------------------------------
.PHONY: revision upgrade downgrade

UPGRADE_REVISION := $(if $(word 2, $(MAKECMDGOALS)), $(word 2, $(MAKECMDGOALS)),head)
DOWNGRADE_REVISION := $(if $(word 2, $(MAKECMDGOALS)), $(word 2, $(MAKECMDGOALS)),-1)

revision: up ## revision msg="message" — create new autogenerated migration.
	@cd $(SERVICE_DIR) && poetry run python -m scripts.create_migration $(abspath $(SERVICE_DIR)) $(msg)

upgrade: up ## upgrade [head|REVISION|+N] — apply migrations (default: head).
	@cd $(SERVICE_DIR) && poetry run alembic upgrade $(UPGRADE_REVISION)

downgrade: up ## downgrade [base|REVISION|-N] — revert migrations (default: -1).
	@cd $(SERVICE_DIR) && poetry run alembic downgrade $(DOWNGRADE_REVISION)


# --- Code Linters -----------------------------------------------------------------------------------------------------
.PHONY: lint flake8

lint: flake8 ## lint [SERVICE] — lint code for specified service.

flake8: ## flake8 [SERVICE] — lint code for specified service.
	$(call LOG_HEADER,flake8)
	@cd $(SERVICE_DIR) && poetry run flake8 --toml-config=pyproject.toml .
	@echo All done! ✨ 🍰 ✨


# --- Code Formatters --------------------------------------------------------------------------------------------------
.PHONY: reformat isort black

reformat: isort black ## reformat [SERVICE] — format imports and code for specified service.

isort: ## isort [SERVICE] — format imports for specified service.
	$(call LOG_HEADER,isort)
	@cd $(SERVICE_DIR) && poetry run isort --settings=pyproject.toml .

black: ## black [SERVICE] — format code for specified service.
	$(call LOG_HEADER,black)
	@cd $(SERVICE_DIR) && poetry run black --config=pyproject.toml .


# --- Type Checking ----------------------------------------------------------------------------------------------------
.PHONY: mypy

mypy: ## mypy [SERVICE] — type check code for specified service.
	$(call LOG_HEADER,mypy)
	@cd $(SERVICE_DIR) && poetry run mypy --config-file=pyproject.toml .


# --- Testing ----------------------------------------------------------------------------------------------------------
.PHONY: pytest pytest-cov

DOCKER_COMPOSE_TESTING_FLAGS := \
	-p $(strip $(IMAGE_NAME))-test \
	-f $(SERVICE_DIR)/docker/docker-compose.testing.yml

pytest: ## pytest [SERVICE] — run tests for specified service.
	$(call LOG_HEADER,pytest)
	@docker compose $(DOCKER_COMPOSE_TESTING_FLAGS) run \
		--rm test-runner python /scripts/run_tests.py --pytest
	@docker compose $(DOCKER_COMPOSE_TESTING_FLAGS) down -v

pytest-cov: ## pytest-cov [SERVICE] — run tests for specified service and generate coverage report.
	$(call LOG_HEADER,pytest with coverage)
	@docker compose $(DOCKER_COMPOSE_TESTING_FLAGS) run \
		--rm test-runner python /scripts/run_tests.py --pytest-cov
	@docker compose $(DOCKER_COMPOSE_TESTING_FLAGS) down -v


# --- Code Checking ----------------------------------------------------------------------------------------------------
.PHONY: check

check: reformat lint mypy pytest helm-encrypt ## check [SERVICE] — full code check for specified service.
