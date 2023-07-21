FROM python:3.9

WORKDIR /app
COPY poetry.lock pyproject.toml ./

RUN pip install poetry

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

COPY . .

CMD ["python", "./src/main.py"]