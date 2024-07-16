import unittest
import requests


class TestBuildImage(unittest.TestCase):
    def setUp(self):
        self.url = 'http://localhost:5000/build'
        self.data = {
            'registry': "",
            'username': "",
            'password': ""
        }

    def test_no_file(self):
        response = requests.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing dockerfile or tar archive.', response.json()['error'])

    def test_no_credentials(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files)
            self.assertEqual(response.status_code, 400)
            self.assertIn('Missing registry or credentials.', response.json()['error'])

    def test_wrong_credentials(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data={
                'registry': "mf189",
                'username': "wrong",
                'password': "wrong"
            })
            self.assertEqual(response.status_code, 401)
            self.assertIn('Login failed, check credentials.', response.json()['error'])

    def test_wrong_file_type(self):
        file_path = "tests/examples/error_files/wrong_file_type.txt"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            self.assertEqual(415, response.status_code)
            self.assertIn('Not a Dockerfile or tar archive.', response.json()['error'])

    def test_invalid_tarfile(self):
        file_path = "tests/examples/error_files/invalid_tar.tar"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            self.assertEqual(500, response.status_code)
            self.assertIn('Build failed with the following message:', response.json()['error'][:40])

    def test_no_dockerfile_in_tar(self):
        file_path = "tests/examples/error_files/without_docker_file.tar"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            self.assertEqual(400, response.status_code)
            self.assertIn('Cannot locate Dockerfile in tar archive.', response.json()['error'])

    def test_invalid_docker(self):
        file_path = "tests/examples/error_files/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            self.assertEqual(response.status_code, 500)
            self.assertIn('Build failed with the following message:', response.json()['error'][:40])

    def test_failed_push(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = self.data
            data["registry"] = "wrong"
            response = requests.post(self.url, files=files, data=data)
            self.assertEqual(response.status_code, 500)
            self.assertIn('Push failed with the following message:', response.json()['error'][:39])

    def test_valid_tar(self):
        file_path = "tests/examples/complete/docker.tar"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Image built and pushed successfully', response.json()['message'])

    def test_valid_docker(self):
        file_path = "tests/examples/single/Dockerfile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Image built and pushed successfully', response.json()['message'])


if __name__ == '__main__':
    unittest.main()
