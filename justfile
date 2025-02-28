set dotenv-load := false

@_default:
    just --list

@deploy:
    flyctl deploy

@fmt:
    just --fmt --unstable

@lint *ARGS:
    uv --quiet run --with pre-commit-uv pre-commit run {{ ARGS }} --all-files

@up:
    python manage.py runserver

@update:
    pip install -U pip pip-tools uv
    pip install -U -r requirements.in
    pip-compile requirements.in
