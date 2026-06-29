# Use official Python lightweight image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for pdfkit/wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the API port
EXPOSE 8000

# Command to run the FastAPI server via Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]