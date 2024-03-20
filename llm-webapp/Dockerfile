FROM python:3.12-slim-bullseye

RUN pip install poetry==1.4.2

WORKDIR /llm-app

COPY pyproject.toml poetry.lock ./
COPY llm_webapp ./llm_webapp
RUN touch README.md

RUN poetry install --without dev
RUN poetry run flask --app llm_webapp init-db

ENTRYPOINT ["poetry", "run", "flask", "--app", "llm_webapp", "run", "--host=0.0.0.0"] 
