from selenium import webdriver
import unittest
from app.models import Role, User
from app import create_app, db
from app import fake
import threading
import re

class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # start Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        try:
            cls.client = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=options)
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            print('browser has been started')
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # create the database and populate with some fake data
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            fake.posts(10)

            # add an administrator user
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='1558911620@qq.com', username='ml', password='cat', role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # start the Flask server in a thread 
            cls.server_thread = threading.Thread(
                    target=cls.app.run, kwargs={
                        'debug': 'false',
                        'use_reloader': False,
                        'use_debugger': False})
            cls.server_thread.start()


    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the Flask server and the browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # destroy the database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')


    def tearDown(self):
        pass

    def test_admin_home_page(self):
        # navigate to home page
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello,Stranger', self.client.page_source))
        
        # navigate to login page
        self.client.find_element_by_link_text('Log In').click()
        self.assertIn('<h1>Login</h1>', self.client.page_source)

        # log in
        self.client.find_element_by_name('email').\
                send_keys('1558911620@qq.com')
        self.client.find_element_by_name('password').\
                send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('Hello,ml', self.client.page_source))

        # navigate to the user's profile page
        self.client.find_element_by_link_text('Profile').click()
        self.assertIn('<h1>ml</h1>', self.client.page_source)
