FROM mcr.microsoft.com/devcontainers/python:3.14

RUN python -m pip install --upgrade pip \
    && python -m pip install 'flit>=3.8.0' pre-commit black

ENV FLIT_ROOT_INSTALL=1

COPY pyproject.toml .
RUN touch README.md \
    && mkdir -p src/sony_projector_protocol \
    && touch src/sony_projector_protocol/__init__.py \
    && python -m flit install --only-deps --deps develop \
    && rm -r pyproject.toml README.md src
