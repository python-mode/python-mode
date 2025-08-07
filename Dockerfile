ARG PYTHON_VERSION
# Use official Python slim image instead of non-existent base
# Note: For Python 3.13, use 3.13.0 if just "3.13" doesn't work
FROM python:${PYTHON_VERSION}-slim

ENV PYTHON_VERSION=${PYTHON_VERSION}
ENV PYTHONUNBUFFERED=1
ENV PYMODE_DIR="/workspace/python-mode"

# Install system dependencies required for testing
RUN apt-get update && apt-get install -y \
    vim-nox \
    git \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Copy the python-mode plugin
COPY . /workspace/python-mode

# Set up python-mode in the test environment
RUN mkdir -p /root/.vim/pack/foo/start/ && \
    ln -s ${PYMODE_DIR} /root/.vim/pack/foo/start/python-mode && \
    cp ${PYMODE_DIR}/tests/utils/pymoderc /root/.pymoderc && \
    cp ${PYMODE_DIR}/tests/utils/vimrc /root/.vimrc && \
    touch /root/.vimrc.before /root/.vimrc.after

# Initialize git submodules
WORKDIR /workspace/python-mode

# Create a simplified script to run tests (no pyenv needed with official Python image)
RUN echo '#!/bin/bash\n\
cd /workspace/python-mode\n\
echo "Using Python: $(python3 --version)"\n\
echo "Using Vim: $(vim --version | head -1)"\n\
bash ./tests/test.sh\n\
rm -f tests/.swo tests/.swp 2>&1 >/dev/null\n\
' > /usr/local/bin/run-tests && \
    chmod +x /usr/local/bin/run-tests

# Default command
CMD ["/usr/local/bin/run-tests"]
