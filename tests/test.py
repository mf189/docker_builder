import unittest
import requests
import time


class TestBuildImage(unittest.TestCase):
    def setUp(self):
        self.url_build = 'http://localhost:5000/build'
        self.url_status = 'http://localhost:5000/status'
        self.data = {
            'registry': "",
            'username': "",
            'password': ""
        }

    def get_task_status(self, task_id):
        response = requests.get(f"{self.url_status}/{task_id}")
        return response.json()

    def wait_for_task_completion(self, task_id, timeout=300, interval=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if status['state'] in ['SUCCESS', 'FAILURE', 'ERROR']:
                return status
            time.sleep(interval)
        return {'state': 'TIMEOUT'}

    def test_no_file(self):
        response = requests.post(self.url_build, data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing dockerfile or tar archive.', response.json()['error'])

    def test_no_credentials(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing registry or credentials.', response.json()['error'])

    def test_wrong_credentials(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data={
                'registry': "mf189",
                'username': "wrong",
                'password': "wrong"
            })
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'ERROR')
        self.assertIn('Login failed, check credentials.', status['status'])

    def test_wrong_file_type(self):
        file_path = "tests/examples/error_files/wrong_file_type.txt"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data=self.data)
        self.assertEqual(400, response.status_code)
        self.assertIn('Not a Dockerfile or tar archive.', response.json()['error'])

    def test_invalid_tarfile(self):
        file_path = "tests/examples/error_files/invalid_tar.tar"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data=self.data)
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'ERROR')
        self.assertIn('Not a Dockerfile or tar archive.', status['status'])

    def test_no_dockerfile_in_tar(self):
        file_path = "tests/examples/error_files/without_docker_file.tar"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data=self.data)
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'ERROR')
        self.assertIn('Cannot locate Dockerfile in tar archive.', status['status'])

    def test_invalid_docker(self):
        file_path = "tests/examples/error_files/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data=self.data)
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'ERROR')
        self.assertIn('Build failed with the following message:', status['status'][:40])

    def test_failed_push(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = self.data
            data["registry"] = "wrong"
            response = requests.post(self.url_build, files=files, data=data)
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'ERROR')
        self.assertIn('Push failed with the following message:', status['status'][:39])

    def test_valid_tar(self):
        file_path = "tests/examples/complete/docker.tar"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data=self.data)
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'SUCCESS')
        self.assertIn('Image built and pushed successfully', status['status'])

    def test_valid_docker(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url_build, files=files, data=self.data)
        task_id = response.json()['task_id']
        status = self.wait_for_task_completion(task_id)
        self.assertEqual(status['state'], 'SUCCESS')
        self.assertIn('Image built and pushed successfully', status['status'])


if __name__ == '__main__':
    unittest.main()
