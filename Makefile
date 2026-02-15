.PHONY: lint fmt check fix

run:
	@echo "\033[32mЗапуск приложения\033[0m"
	@echo "\033[35mДокументация API доступна по адресу: http://127.0.0.1:8000/docs\033[0m"
	poetry run uvicorn app.main:app --reload

check:
	@echo "\033[32mПроверка кода без исправлений\033[0m"
	poetry run ruff check .

fix:
	@echo "\033[32mАвтоисправление (ruff) + форматирование (ruff)\033[0m"
	poetry run ruff check . --fix
	poetry run ruff format .

lint:
	@echo "\033[32mТолько линтинг (ruff)\033[0m"
	poetry run ruff check .

fmt:
	@echo "\033[32mТолько форматирование (ruff)\033[0m"
	poetry run ruff format .

