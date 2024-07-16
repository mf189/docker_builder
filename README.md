# Image Builder Service

## Description
The service enables the user to upload a single Dockerfile or .tar archive, which is then used to construct a Docker image. Once completed, the image is pushed to a Docker registry.

**Note: This is an asynch implementation using Celery, a synchronous version can be found in the `synch` branch of this repository.**

## Requirements
- Python/ pip
- Running Docker deamon

## Setup
1. Clone the repository.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
    ```
3. Start App:
    ```bash
    docker-compose up --build
    ```
4. Use the `/build` endpoint to upload a Dockerfile and build the image.
   - Method: POST
   - Form Data: 
     - "file": Dockerfile or .tar archive 
     - "registry": Registry name
     - "username": username
     - "password": password
   - Request Parameters (optional):
     - name: Image name
     - tag: Image tag
5. Use the `/status` endpoint to retrieve the status


## Usage
#### Run Tests:
Set credentials in `/tests/test.py`
```bash
python -m unittest discover -s tests
```
#### Send Request:
```bash
curl -X POST -F "file=@tests\examples\single\Dockerfile" -F "registry=<registry>" -F "username=<username>" -F "password=<password>" "http://localhost:5000/build?name=my_image&tag=v1.0"
curl "http://localhost:5000/status/<task_id>" 
```