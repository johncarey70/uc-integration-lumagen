# Use a minimal Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy source and config files
COPY intg-lumagen/driver.py ./
COPY lumagen.json remote_ui_page.json ./

# Install ucapi from PyPI
RUN pip install --no-cache-dir ucapi

# Optional: set the port as an environment variable
ENV PORT=9084

# Run the integration
CMD ["python", "driver.py"]
