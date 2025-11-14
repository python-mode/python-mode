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

# Install Python coverage tool for code coverage collection
RUN pip install --no-cache-dir coverage

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

# Install Vader.vim for Vader test framework
RUN mkdir -p /root/.vim/pack/vader/start && \
    git clone --depth 1 https://github.com/junegunn/vader.vim.git /root/.vim/pack/vader/start/vader.vim || \
    (cd /root/.vim/pack/vader/start && git clone --depth 1 https://github.com/junegunn/vader.vim.git vader.vim)

# Initialize git submodules
WORKDIR /workspace/python-mode

# Create a simplified script to run tests (no pyenv needed with official Python image)
RUN echo '#!/bin/bash\n\
cd /workspace/python-mode\n\
echo "Using Python: $(python3 --version)"\n\
echo "Using Vim: $(vim --version | head -1)"\n\
bash ./tests/test.sh\n\
EXIT_CODE=$?\n\
# Cleanup files that might be created during tests\n\
# Remove Vim swap files\n\
find . -type f -name "*.swp" -o -name "*.swo" -o -name ".*.swp" -o -name ".*.swo" 2>/dev/null | xargs rm -f 2>/dev/null || true\n\
# Remove temporary test scripts\n\
rm -f .tmp_run_test_*.sh 2>/dev/null || true\n\
# Remove Python cache files and directories\n\
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true\n\
find . -type f -name "*.pyc" -o -name "*.pyo" 2>/dev/null | xargs rm -f 2>/dev/null || true\n\
# Remove test artifacts\n\
rm -rf test-logs results 2>/dev/null || true\n\
rm -f test-results.json coverage.xml .coverage .coverage.* 2>/dev/null || true\n\
exit $EXIT_CODE\n\
' > /usr/local/bin/run-tests && \
    chmod +x /usr/local/bin/run-tests

# Default command
CMD ["/usr/local/bin/run-tests"]
