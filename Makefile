.PHONY: help format check test clean


help:
	@echo ""
	@echo "Usage: make <command>"
	@echo ""
	@echo "Available commands:"
	@echo "  - help     show help message"
	@echo "  - format   run formatting tools"
	@echo "  - check    run python linting tools"
	@echo "  - test     run pytest with coverage"
	@echo ""


format:
	ruff format app
	ruff check app --fix


check:
	ruff check app
	fawltydeps
	mypy app


test:
	pytest --cov=app --cov-branch --cov-report=xml

