set dotenv-load := false

@_default:
    just --list

@deploy:
    flyctl deploy

@fmt:
    just --fmt --unstable

# Run pre-commit hooks on all files
@lint *ARGS:
    uv --quiet tool run --with pre-commit-uv pre-commit run {{ ARGS }} --all-files

@pre-commit:
    pre-commit run --all-files

@up:
    python manage.py runserver

@update:
    pip install --upgrade pip uv
    uv pip install --upgrade -r requirements.in
    uv pip compile requirements.in --output-file requirements.txt
