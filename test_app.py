import unittest

import app as app_module


class AppFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_register_and_login_work(self):
        response = self.client.post('/register', data={
            'name': 'Tester',
            'email': 'tester@example.com',
            'password': 'secret123'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        response = self.client.post('/login', data={
            'email': 'tester@example.com',
            'password': 'secret123'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        dashboard_response = self.client.get('/dashboard')
        self.assertEqual(dashboard_response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
