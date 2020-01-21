import unittest
from app.models import User, Role
from app import create_app, db
from base64 import b64encode
from flask import url_for, json

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization':
                'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_no_auth(self):
        with self.app.test_request_context(): # obtain request context for following assertion
            response = self.client.get(url_for('api.get_posts'),
                           content_type='application/json')
            self.assertEqual(response.status_code, 401)

    def test_posts(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='1558911620@qq.com', username='ml', password='cat', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        # write a post
        response = self.client.post(
            '/api/v1/posts/', 
            headers=self.get_api_headers('1558911620@qq.com', 'cat'),
            data=json.dumps({'body': 'body of the *blog* post'}))

        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get the new post
        response = self.client.get(
                url, 
                headers=self.get_api_headers('1558911620@qq.com', 'cat'))

        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))

        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *blog* post')
        self.assertEqual(json_response['body_html'], '<p>body of the <em>blog</em> post</p>')


        # get a page of existing blogs
        with self.app.test_request_context():
            response = self.client.get(
                url_for('api.get_posts', _external=True),
                headers=self.get_api_headers('1558911620@qq.com', 'cat'))
        self.assertEqual(response.status_code, 200)
    
        # get specific post using its id
        with self.app.test_request_context():
            response = self.client.get(
                url_for('api.get_post', id=1, _external=True),
                headers=self.get_api_headers('1558911620@qq.com', 'cat'))
        self.assertEqual(response.status_code, 200)

        # edit post
        response = self.client.put(
                '/api/v1/posts/1',
                headers=self.get_api_headers('1558911620@qq.com', 'cat'),
                data = json.dumps({'body': 'this post from test case has been modified.'}))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertTrue('modified' in json_response['body'])

