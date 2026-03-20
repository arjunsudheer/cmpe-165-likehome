class TestRegistration:
    
    def test_reject_duplicate_email(self, client):
        client.post('/auth/register', json={'email': 'duplicate@email.com', 'password': 'password', 'confirm_password': 'password'})
        response = client.post('/auth/register', json={'email': 'duplicate@email.com', 'password': 'password', 'confirm_password': 'password'})
        assert response.status_code == 409
        assert response.get_json() == {"message": "email already exists"}

    def test_reject_different_case_duplicate_email(self, client):
        client.post('/auth/register', json={'email': 'duplicate@email.com', 'password': 'password', 'confirm_password': 'password'})
        response = client.post('/auth/register', json={'email': 'Duplicate@email.com', 'password': 'password', 'confirm_password': 'password'})
        assert response.status_code == 409
        assert response.get_json() == {"message": "email already exists"}

    def test_accept_non_duplicate_email(self, client):
        client.post('/auth/register', json={'email': 'new@email.com', 'password': 'password', 'confirm_password': 'password'})
        response = client.post('/auth/register', json={'email': 'newest@email.com', 'password': 'password', 'confirm_password': 'password'})
        assert response.status_code == 201
        assert response.get_json() == {"message": "user registered successfully"}
