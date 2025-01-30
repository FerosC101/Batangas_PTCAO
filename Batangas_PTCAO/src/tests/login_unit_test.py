import pytest
from Batangas_PTCAO.src.model import User, AccountStatus

def test_login_successful(client, app, db_session):
    # Create a test user
    test_user = User(
        user_email='test@example.com',
        account_status=AccountStatus.ACTIVE
    )
    test_user.set_password('testpassword')
    db_session.session.add(test_user)
    db_session.session.commit()

    # Attempt login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)

    # Check successful login
    assert response.status_code == 200
    assert b'dashboard' in response.data or b'Dashboard' in response.data

def test_login_invalid_password(client, app, db_session):
    # Create a test user
    test_user = User(
        user_email='test@example.com',
        account_status=AccountStatus.ACTIVE
    )
    test_user.set_password('testpassword')
    db_session.session.add(test_user)
    db_session.session.commit()

    # Attempt login with wrong password
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })

    # Check failed login
    assert b'Invalid email or password' in response.data