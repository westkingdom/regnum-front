# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes your main.py, pages/, utils/, credentials.json, etc.
COPY . .

# Make port 8080 available to the world outside this container
# Cloud Run expects containers to listen on port 8080 by default
EXPOSE 8080

# Define environment variable for the port Streamlit should listen on
ENV PORT=8080

# Run main.py when the container launches using Streamlit
# Use 0.0.0.0 to bind to all network interfaces
# Use --server.port $PORT to respect the Cloud Run environment variable
# Use --server.enableCORS=false and --server.enableXsrfProtection=false if needed,
# but be aware of security implications. Start without them.
# Ensure main.py is your intended entry point for the app.
CMD ["streamlit", "run", "main.py", "--server.port", "8080", "--server.address", "0.0.0.0"]