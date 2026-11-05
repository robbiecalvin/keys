# 1. Base Image
FROM python:3.9-slim

# 2. Set Working Directory
WORKDIR /app

# 3. Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the application code and templates
COPY . .

# 5. Expose the port Flask runs on
EXPOSE 80 

# 6. Command to run the application
CMD ["python", "server.py"]