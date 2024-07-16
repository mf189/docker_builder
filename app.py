from flask import Flask, request, jsonify
import docker
import uuid
import os
from celery import Celery
from celery.exceptions import Ignore
import docker.errors

# Flask configuration
app = Flask(__name__)
client = docker.from_env()

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)


@celery.task(bind=True, track_started=True)
def build(self, file_path, username, password, registry, name, tag):
    """
    Asynchronous celery task to build and push the image in the background.
    :param self: Task
    :param file_path: Path to the uploaded file
    :param username: Docker username
    :param password: Docker password
    :param registry: Docker registry name
    :param name: Image name
    :param tag: Image tag
    """
    try:
        # Docker login
        client.login(username=username, password=password)
        # Build the Docker image
        with open(file_path, 'rb') as file:
            image, logs = client.images.build(fileobj=file, custom_context=file_path.endswith(".tar"), rm=True)

        # Print build logs
        for log in logs:
            if 'stream' in log:
                self.update_state(state='PROGRESS', meta={'message': log['stream']})

        # Tag the image
        repository = f"{registry}/{name}"
        image.tag(repository, tag=tag)

        # Push the image to the registry
        push_logs = client.images.push(repository, tag=tag, stream=True, decode=True)
        # Print push logs
        for log in push_logs:
            if 'status' in log:
                self.update_state(state='PROGRESS', meta={'message': log['status']})
            if 'error' in log:
                self.update_state(state='ERROR', meta={'message': 'Push failed with the following message: ' + log['error']})
                raise Ignore()

        # Return positive response when image was pushed successfully.
        self.update_state(state='SUCCESS', meta={'message': 'Image built and pushed successfully.'})
        raise Ignore()

    # Handle different errors
    except docker.errors.BuildError as e:
        if "parse error" in str(e) or "unexpected EOF" in str(e):
            self.update_state(state='ERROR', meta={'message': 'Not a Dockerfile or tar archive.'})
        elif "Cannot locate" in str(e):
            self.update_state(state='ERROR', meta={'message': 'Cannot locate Dockerfile in tar archive.'})
        else:
            self.update_state(state='ERROR', meta={'message': 'Build failed with the following message: ' + str(e)})
        raise Ignore()
    except docker.errors.APIError as e:
        if "unauthorized" in str(e):
            self.update_state(state='ERROR', meta={'message': 'Login failed, check credentials.'})
        else:
            self.update_state(state='ERROR', meta={'message': 'Docker error with the following message: ' + str(e)})
        raise Ignore()
    finally:
        os.remove(file_path)


@app.route('/build', methods=['POST'])
def build_image():
    """
    Endpoint to build and push a Docker image from a Dockerfile or tar archive.

    Supports uploading a Dockerfile or tar archive and optionally specifying
    registry credentials, image name, and tag as query parameters.

    Parameters:
    - file: Dockerfile or tar archive to build image from (required).
    - registry: Docker registry URL (required).
    - username: Username for registry authentication (required).
    - password: Password for registry authentication (required).
    - name: Name to tag the built image (optional).
    - tag: Tag for the built image (optional).

    :return: Task ID of the started Task.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Missing dockerfile or tar archive."}), 400

    file = request.files['file']
    if not file.filename == "Dockerfile" and not file.filename.endswith(".tar"):
        return jsonify({"error": f"Not a Dockerfile or tar archive.{file.filename}"}), 400

    file.save(f'/tmp/{file.filename}')

    registry = request.form.get('registry')
    username = request.form.get('username')
    password = request.form.get('password')

    if not (registry and username and password):
        return jsonify({"error": "Missing registry or credentials."}), 400

    name = request.args.get('name', str(uuid.uuid4()))
    tag = request.args.get('tag', 'latest')

    task = build.delay(f'/tmp/{file.filename}', username, password, registry, name, tag)
    return jsonify({"task_id": task.id}), 202


@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    """
    Retrieve status of a Task.
    :param task_id:
    :return: Status of the Task
    """
    task = build.AsyncResult(task_id)
    satus = task.info['message'] if 'message' in task.info else str(task.info)
    response = {
        'state': task.state,
        'status': satus
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
