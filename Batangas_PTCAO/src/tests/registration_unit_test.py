import unittest
from flask import session
from Batangas_PTCAO.src.app import app, db
from Batangas_PTCAO.src.model import User, BusinessRegistration, SpecialServices, Room, EventFacility


class TestRegistrationRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_initial_registration_route(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertIn('registration_step', session)
            self.assertIn('registration_data', session)
            self.assertEqual(session['registration_data'], {})

    def test_business_registration_get(self):
        response = self.client.get('/business_registration')
        self.assertEqual(response.status_code, 200)

    def test_business_registration_post_success(self):
        data = {
            'business-registration': 'BR123',
            'business-name': 'Test Hotel',
            'official-contact': '1234567890',
            'business-address': '123 Test St',
            'taxpayer-name': 'John Doe',
            'total-employees': '50',
            'total-rooms': '20',
            'total-beds': '40'
        }
        response = self.client.post('/business_registration', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertIn('registration_data', session)
            self.assertIn('business', session['registration_data'])

    def test_business_registration_post_missing_fields(self):
        data = {
            'business-registration': 'BR123',
            'business-name': 'Test Hotel'
            # Missing other required fields
        }
        response = self.client.post('/business_registration', data=data)
        self.assertIn(b'All fields are required', response.data)

    def test_special_services_without_business_registration(self):
        response = self.client.get('/special_services')
        self.assertIn(b'Please complete business registration first', response.data)

    def test_special_services_post_success(self):
        # First complete business registration
        with self.client.session_transaction() as session:
            session['registration_data'] = {
                'business': {
                    'business_registration_no': 'BR123',
                    'business_name': 'Test Hotel',
                    'total_employees': 50,
                    'total_rooms': 20,
                    'total_beds': 40
                }
            }

        data = {
            'accreditation': 'DOT',
            'classification': '5-star',
            'room_type[]': ['Standard', 'Deluxe'],
            'room_number[]': ['10', '5'],
            'room_capacity[]': ['2', '3'],
            'facility_name[]': ['Conference Hall'],
            'facility_capacity[]': ['100'],
            'facility_amenities[]': ['Projector, Audio System'],
            'services': 'Additional services'
        }
        response = self.client.post('/special_services', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_credentials_without_previous_steps(self):
        response = self.client.get('/login_credentials')
        self.assertIn(b'Please complete special services first', response.data)

    def test_login_credentials_post_success(self):
        # Set up session data
        with self.client.session_transaction() as session:
            session['registration_data'] = {
                'business': {
                    'business_registration_no': 'BR123',
                    'business_name': 'Test Hotel',
                    'official_contact_no': '1234567890',
                    'business_address': '123 Test St',
                    'taxpayer_name': 'John Doe',
                    'total_employees': 50,
                    'total_rooms': 20,
                    'total_beds': 40
                },
                'services': {
                    'accreditation': 'DOT',
                    'classification': '5-star',
                    'rooms': [{'type': 'Standard', 'number': 10, 'capacity': 2}],
                    'facilities': [{'name': 'Conference Hall', 'capacity': 100, 'amenities': 'Projector'}],
                    'other_services': 'Additional services'
                }
            }

        data = {
            'username': 'test@example.com',
            'password': 'password123',
            'confirm-password': 'password123'
        }
        response = self.client.post('/login_credentials', data=data, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)

        # Verify database entries
        user = User.query.filter_by(user_email='test@example.com').first()
        self.assertIsNotNone(user)
        business = BusinessRegistration.query.filter_by(account_id=user.user_id).first()
        self.assertIsNotNone(business)
        services = SpecialServices.query.filter_by(business_id=business.business_id).first()
        self.assertIsNotNone(services)

    def test_login_credentials_password_mismatch(self):
        with self.client.session_transaction() as session:
            session['registration_data'] = {
                'business': {},
                'services': {}
            }

        data = {
            'username': 'test@example.com',
            'password': 'password123',
            'confirm-password': 'password456'
        }
        response = self.client.post('/login_credentials', data=data)
        self.assertIn(b'Passwords do not match', response.data)

    def test_login_credentials_duplicate_username(self):
        # Create an existing user
        user = User(user_email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        with self.client.session_transaction() as session:
            session['registration_data'] = {
                'business': {},
                'services': {}
            }

        data = {
            'username': 'test@example.com',
            'password': 'password123',
            'confirm-password': 'password123'
        }
        response = self.client.post('/login_credentials', data=data)
        self.assertIn(b'Username already exists', response.data)


