FROM python:3.11-alpine

ENV POETRY_VERSION=1.7.1
RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

COPY . .

EXPOSE 8050

CMD ["gunicorn", "frontend.index:server", "-b", "0.0.0.0:8050"]
