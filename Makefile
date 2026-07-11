.PHONY: run test lint clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Start the development server
	python api.py

test: ## Run all tests
	python -m pytest tests/ -v

lint: ## Run ruff linter
	ruff check .

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf htmlcov .coverage

cli: ## Run CLI pipeline (requires --jd and --resumes args)
	python main.py --jd samples/jd_ml_engineer.txt --resumes samples/resumes.txt
