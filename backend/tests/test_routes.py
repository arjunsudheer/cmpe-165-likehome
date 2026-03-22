class TestRegistration:

    def test_accept_valid_registration(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'test@email.com',
            'password': 'password',
            'confirm_password': 'password'
        })
        assert response.status_code == 201
        assert response.get_json() == {"message": "user registered successfully"}

    def test_reject_missing_name(self, client):
        response = client.post('/auth/register', json={
            'email': 'test@email.com',
            'password': 'password',
        })
        assert response.status_code == 400

    def test_reject_empty_email_field(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': '',
            'password': 'password',
        })
        assert response.status_code == 400

    def test_reject_empty_password_field(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'test2@email.com',
            'password': '',
        })
        assert response.status_code == 400

    def test_reject_invalid_email_format(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'email.com',
            'password': 'password',
        })
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid email format"}

    def test_reject_under_minimum_password_length(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'short@email.com',
            'password': 'pass',
        })
        assert response.status_code == 400
        assert response.get_json() == {"error": "Password must be at least 6 characters"}

    def test_reject_duplicate_email(self, client):
        client.post('/auth/register', json={
            'name': 'User One',
            'email': 'duplicate@email.com',
            'password': 'password',
        })
        response = client.post('/auth/register', json={
            'name': 'User Two',
            'email': 'duplicate@email.com',
            'password': 'password',
        })
        assert response.status_code == 409
        assert response.get_json() == {"message": "email already exists"}

    def test_reject_different_case_duplicate_email(self, client):
        client.post('/auth/register', json={
            'name': 'User One',
            'email': 'dupcase@email.com',
            'password': 'password',
        })
        response = client.post('/auth/register', json={
            'name': 'User Two',
            'email': 'Dupcase@email.com',
            'password': 'password',
        })
        assert response.status_code == 409
        assert response.get_json() == {"message": "email already exists"}
