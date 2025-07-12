ARG PYTHON_VERSION_SHORT
ARG PYTHON_VERSION
ARG REPO_OWNER=python-mode
FROM ghcr.io/${REPO_OWNER}/python-mode-base:${PYTHON_VERSION_SHORT}-latest

ENV PYTHON_VERSION=${PYTHON_VERSION}
ENV PYTHONUNBUFFERED=1
ENV PYMODE_DIR="/workspace/python-mode"

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

# Create a script to run tests
RUN echo '#!/bin/bash\n\
# export PYENV_ROOT="/opt/pyenv"\n\
# export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"\n\
eval "$(pyenv init -)"\n\
eval "$(pyenv init --path)"\n\
# Use specified Python version\n\
pyenv shell ${PYTHON_VERSION}\n\
cd /workspace/python-mode\n\
echo "Using Python: $(python --version)"\n\
bash ./tests/test.sh\n\
rm -f tests/.swo tests/.swp 2>&1 >/dev/null \n\
' > /usr/local/bin/run-tests && \
    chmod +x /usr/local/bin/run-tests

# Default command
CMD ["/usr/local/bin/run-tests"]
