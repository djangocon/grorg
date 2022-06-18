set dotenv-load := false

@_default:
    just --list

@deploy:
    flyctl deploy

@fmt:
    just --fmt --unstable

@pre-commit:
    git ls-files -- . | xargs pipx run pre-commit run --config=.pre-commit-config.yaml --files

@update:
    pip install -U pip pip-tools
    pip install -U -r ./requirements.in
    pip-compile ./requirements.in
