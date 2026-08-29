.PHONY: setup ingest build test lint dashboard docs infra-up infra-down clean

setup:  ## Create venv and install deps
	uv venv && uv pip install -e ".[aws,quality,dev]"

ingest:  ## Run the ingestion script
	python scripts/ingest.py

build:  ## dbt build (run + test)
	cd dbt && dbt build --profiles-dir .

test:  ## Python unit tests
	pytest

lint:  ## ruff + sqlfluff
	ruff check .
	sqlfluff lint dbt/models || true

dashboard:  ## Launch Streamlit locally
	streamlit run dashboards/app.py

docs:  ## Generate + serve dbt docs
	cd dbt && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

infra-up:  ## terraform apply
	cd terraform && terraform init && terraform apply

infra-down:  ## terraform destroy (run when done every session)
	cd terraform && terraform destroy

clean:
	rm -rf dbt/target dbt/dbt_packages dbt/logs .pytest_cache .ruff_cache
