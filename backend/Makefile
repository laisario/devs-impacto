.PHONY: test test-unit test-integration test-all coverage lint format

# Activate venv helper
ACTIVATE_VENV = @if [ -d "../.venv" ]; then source ../.venv/bin/activate && echo "✓ Venv ativado"; elif [ -d ".venv" ]; then source .venv/bin/activate && echo "✓ Venv ativado"; fi

# Run all tests
test:
	$(ACTIVATE_VENV) && python -m pytest tests/

# Run unit tests only
test-unit:
	$(ACTIVATE_VENV) && python -m pytest tests/ -m "not integration"

# Run integration tests only
test-integration:
	$(ACTIVATE_VENV) && python -m pytest tests/integration/ -v

# Run all tests with coverage
coverage:
	$(ACTIVATE_VENV) && python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	ruff check app/ tests/

# Format code
format:
	ruff format app/ tests/

# Type check
typecheck:
	mypy app/
