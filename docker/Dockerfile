# Playwright + Python test framework image.
# Uses the official Playwright Python base image which ships all browser
# dependencies pre-installed, then layers in project requirements.
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TEST_ENV=dev \
    HEADLESS=true

WORKDIR /app

# Install Python dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps

# Copy the rest of the framework.
COPY . .

# Default: run the full suite. Override at `docker run` time as needed.
ENTRYPOINT ["pytest"]
CMD ["-n", "4"]
