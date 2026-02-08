.PHONY: help create-env activate-env install-requirements install-requirements-dev clean ruff deploy-dags git-push

MAKEFLAGS += --silent

PYTHON_VERSION := 3.10.14
PROJECT_NAME := velib-data-ingestion
VENV_NAME := $(PROJECT_NAME)-env
VENV_PATH := $(HOME)/.pyenv/versions/$(VENV_NAME)
DBT_VENV_PATH = $(VENV_PATH)/bin/dbt

MAKEFILE_DIR := $(dir $(realpath $(MAKEFILE_LIST)))
PROJECT_ROOT := $(MAKEFILE_DIR)
DAGS_DIR := dags
SRC_DIR := src
TESTS_DIR := tests
UTILS_DIR := utils


help:  ## Show the list of available commands
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


create-env:  ## Create pyenv virtual environment
	pyenv virtualenv $(PYTHON_VERSION) $(VENV_NAME) || true
	$(VENV_PATH)/bin/pip install --upgrade pip setuptools wheel
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - $(VENV_NAME) created successfully"

activate-env:  ## Command to copy paste in shell to activate the virtual environment
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - Run the following command:"
	echo "  pyenv shell $(VENV_NAME)"

dbt-env:
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - Run the following command:"
	echo "  source activate-dbt"

dbt-commands:
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S')"
	echo "Dev:"
	echo "  dbt run --select mart_station_status"
	echo "Prod:"
	echo "  dbt run --target prod --select mart_station_status"
	echo "Prod with full refresh:"
	echo "  dbt run --target prod --select mart_station_status --full-refresh"

refresh-mart:
	$(DBT_VENV_PATH) run --target prod --select mart_station_status
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - velib_data_ingestion.mart_station_status built successfully"


define update-basic-libraries
	$(VENV_PATH)/bin/pip install --upgrade pip setuptools wheel
endef

install-requirements:  ## Install main dependencies
	$(call update-basic-libraries)
	$(VENV_PATH)/bin/pip install -r requirements.txt
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - Main dependencies installed successfully"

install-requirements-dev:  ## Install development dependencies
	$(call update-basic-libraries)
	$(VENV_PATH)/bin/pip install -r requirements-dev.txt
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - Development dependencies installed successfully"

clean:  ## Remove temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "logs" -exec rm -rf {} +
	rm -rf .pytest_cache *.pyc
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - Temporary files removed successfully"

ruff:  ## Check and fix Python code with Ruff
	echo "Checking and fixing code with Ruff..."
	$(VENV_PATH)/bin/ruff check $(DAGS_DIR) $(SRC_DIR) $(TESTS_DIR) $(UTILS_DIR) --fix --no-cache
	$(VENV_PATH)/bin/ruff format $(DAGS_DIR) $(SRC_DIR) $(TESTS_DIR) $(UTILS_DIR) --no-cache
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - Code checked and fixed with Ruff"

upload-rarely-changing-files:
	./scripts/upload_to_s3.sh data/station_info/velib_station_info_enriched.csv station_info
	./scripts/upload_to_s3.sh data/others others
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - station_info/velib_station_info_enriched.csv and others/ uploaded to S3 successfully"

deploy-dags:  ## Deploy DAGs and data symlink to Airflow
	chmod +x $(PROJECT_ROOT)scripts/upload_to_s3.sh
	ln -sfn $(PROJECT_ROOT)$(DAGS_DIR) $(HOME)/airflow/dags/$(PROJECT_NAME)
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - DAGs successfully deployed in $(HOME)/airflow/dags/$(PROJECT_NAME)"

git-push:  ## Git pipeline
	git checkout --orphan tmp-first-push
	git add .
	git commit -m "[ADD] First push"
	git branch -M tmp-first-push main
	git push --force origin main

sort-requirements:  # Sort libraries in requirements files
	sort requirements.txt -o requirements.txt
	sort requirements-dev.txt -o requirements-dev.txt
	echo "[INFO] $$(date '+%Y-%m-%d %H:%M:%S') - requirements files sorted successfully"

