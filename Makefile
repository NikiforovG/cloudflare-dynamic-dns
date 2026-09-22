.PHONY: help format check test clean release

PART ?= patch


help:
	@echo ""
	@echo "Usage: make <command>"
	@echo ""
	@echo "Available commands:"
	@echo "  - help     show help message"
	@echo "  - format   run formatting tools"
	@echo "  - check    run python linting tools"
	@echo "  - test     run pytest with coverage"
	@echo "  - release  bump, commit, tag, and push from main (PART=patch, minor, or major)"
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


release: format
	@test "$$(git branch --show-current)" = main || { echo "Run release from main."; exit 1; }
	bumpversion "$(PART)"
	git -c push.followTags=false push --atomic origin main "refs/tags/v$$(poetry version --short)"
