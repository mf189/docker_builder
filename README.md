# Image Builder Service

## Description
The service enables the user to upload a single Dockerfile or .tar archive, which is then used to construct a Docker image. Once completed, the image is pushed to a Docker registry.

## Requirements
- Python/ pip
- Running Docker deamon

## Setup
1. Clone the repository.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
    ```
3. Build docker image:
    ```bash
    docker build -t image_builder .
    ```
4. Run the Flask app in container:
    ```bash
    docker run -d -p 5000:5000 -v /var/run/docker.sock:/var/run/docker.sock image_builder
    ```
5. Use the `/build` endpoint to upload a Dockerfile and build the image.
   - Method: POST
   - Form Data: 
     - "file": Dockerfile or .tar archive 
     - "registry": Registry name
     - "username": username
     - "password": password
   - Request Parameters (optional):
     - name: Image name
     - tag: Image tag

## Usage
#### Run Tests:
Set credentials in `/tests/test.py`
```bash
python -m unittest discover -s tests
```
#### Send Request:
```bash
curl -X POST -F "file=@tests\examples\single\Dockerfile" -F "registry=<registry>" -F "username=<username>" -F "password=<password>" "http://localhost:5000/build?name=my_image&tag=v1.0"
```