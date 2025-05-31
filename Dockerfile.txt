# Use a lightweight Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS dependencies
RUN apt update && apt install -y ffmpeg

# Set work directory
WORKDIR /app

# Copy project files into container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install yt-dlp whisper youtube-transcript-api googletrans==4.0.0-rc1 django

# Expose port
EXPOSE 8000

# Run migrations and start the Django dev server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
