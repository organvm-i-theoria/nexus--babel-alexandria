.PHONY: test lint openapi-snapshot certainty certainty-check evolution-contract-test verify db-upgrade db-downgrade run-api run-worker

test:
	@if [ -x .venv/bin/pytest ]; then \
		.venv/bin/pytest -q; \
	else \
		pytest -q; \
	fi

lint:
	@if [ -x .venv/bin/ruff ]; then \
		.venv/bin/ruff check --no-cache src tests scripts; \
	else \
		ruff check --no-cache src tests scripts; \
	fi

openapi-snapshot:
	@if [ -x .venv/bin/python ]; then \
		.venv/bin/python scripts/generate_openapi_contract_snapshot.py; \
	else \
		python scripts/generate_openapi_contract_snapshot.py; \
	fi

certainty:
	@if [ -x .venv/bin/python ]; then \
		.venv/bin/python scripts/repo_certainty_audit.py; \
	else \
		python scripts/repo_certainty_audit.py; \
	fi

certainty-check:
	@if [ -x .venv/bin/python ]; then \
		.venv/bin/python scripts/repo_certainty_audit.py --check; \
	else \
		python scripts/repo_certainty_audit.py --check; \
	fi

evolution-contract-test:
	@if [ -x .venv/bin/pytest ]; then \
		.venv/bin/pytest -q tests/test_evolution_api.py; \
	else \
		pytest -q tests/test_evolution_api.py; \
	fi

verify:
	$(MAKE) lint
	$(MAKE) certainty-check
	$(MAKE) test

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

run-api:
	uvicorn nexus_babel.main:app --reload

run-worker:
	python -m nexus_babel.worker
