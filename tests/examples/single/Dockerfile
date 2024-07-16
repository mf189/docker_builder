# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Create a simple app.py directly in the Dockerfile
RUN echo "from flask import Flask\n\
\n\
app = Flask(__name__)\n\
\n\
@app.route('/')\n\
def hello():\n\
    return 'Hello World!'\n\
\n\
if __name__ == '__main__':\n\
    app.run(host='0.0.0.0', port=80)" > app.py

# Install Flask
RUN pip install Flask

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["python", "app.py"]