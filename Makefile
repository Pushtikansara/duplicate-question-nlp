.PHONY: help install dev test lint format build serve docker-up docker-down clean

help:
	@echo "ARES API Development Commands"
	@echo "=============================="
	@echo "make install    - Install project dependencies"
	@echo "make dev        - Install dev dependencies"
	@echo "make test       - Run all tests"
	@echo "make test-api   - Run API tests only"
	@echo "make lint       - Run ruff check"
	@echo "make format     - Run ruff format"
	@echo "make typecheck  - Run mypy"
	@echo "make build      - Build package"
	@echo "make serve      - Start development server"
	@echo "make docker-up  - Start all Docker services"
	@echo "make docker-down- Stop all Docker services"
	@echo "make clean      - Clean build artifacts"

install:
	pip install -e .

dev:
	pip install -e ".[dev,test]"

test:
	python -m pytest tests/ -v --tb=short

test-api:
	python -m pytest tests/api/ tests/security/ -v --tb=short

test-grpc:
	python -m pytest tests/grpc/ -v --tb=short

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/ares/api/

build:
	python -m build

serve:
	ares-serve

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
