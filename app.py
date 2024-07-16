from flask import Flask, request, jsonify
import docker
import uuid
from docker import errors

app = Flask(__name__)
client = docker.from_env()


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

   Returns:
   - JSON response indicating success or failure.
   """
    # Get file
    if 'file' not in request.files:
        return jsonify({"error": "Missing dockerfile or tar archive."}), 400
    file = request.files.get("file")

    # Get docker registry and credentials
    registry = request.form.get('registry')
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if docker registry and credentials are set
    if not (registry and username and password):
        return jsonify({"error": f"Missing registry or credentials."}), 400

    # Retrieve optional query parameters
    name = request.args.get('name', str(uuid.uuid4()))
    tag = request.args.get('tag', 'latest')

    try:
        # Docker login
        client.login(username=username, password=password)
        # Build the Docker image
        image, logs = client.images.build(fileobj=file, custom_context=file.filename.endswith(".tar"), rm=True)
        # Print build logs
        for log in logs:
            if 'stream' in log:
                print(log['stream'].strip())

        # Tag the image
        repository = f"{registry}/{name}"
        image.tag(repository, tag=tag)

        # Push the image to the registry
        push_logs = client.images.push(repository, tag=tag, stream=True, decode=True)
        # Print push logs
        for log in push_logs:
            if 'status' in log:
                print(log['status'].strip())
            if 'error' in log:
                return jsonify({"error": "Push failed with the following message: " + log['error']}), 500

        # Return positive response when image was pushed successfully.
        return jsonify({"message": "Image built and pushed successfully", "repository": repository, "tag": tag}), 200

    # Handle different errors
    except docker.errors.BuildError as e:
        if "parse error" in str(e):
            return jsonify({"error": "Not a Dockerfile or tar archive."}), 415
        elif "Cannot locate" in str(e):
            return jsonify({"error": "Cannot locate Dockerfile in tar archive."}), 400
        else:
            return jsonify({"error": "Build failed with the following message: " + str(e)}), 500
    except docker.errors.APIError as e:
        if "unauthorized" in str(e):
            return jsonify({"error": f"Login failed, check credentials."}), 401
        else:
            return jsonify({"error": "Docker error with the following message: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
