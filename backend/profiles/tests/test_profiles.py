import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", email="test@example.com", password="password123")

@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.mark.django_db
class TestProfileAPI:
    def test_get_profile(self, auth_client, user):
        url = reverse('profiles:account-me')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data['user']['username'] == user.username

    def test_update_profile(self, auth_client, user):
        url = reverse('profiles:account-me')
        data = {
            'user': {'first_name': 'NewName'},
            'profile': {'bio': 'Updated bio'}
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == 200
        assert response.data['user']['first_name'] == 'NewName'
        assert response.data['profile']['bio'] == 'Updated bio'

    def test_change_password(self, auth_client, user):
        url = reverse('profiles:account-change-password')
        data = {
            'current_password': 'password123',
            'new_password': 'newpassword123'
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == 200
        
        # Verify the password actually changed
        user.refresh_from_db()
        assert user.check_password('newpassword123')

@pytest.mark.django_db
class TestAPIToken:
    def test_create_and_list_token(self, auth_client):
        # Create
        url = reverse('profiles:api-token-list')
        response = auth_client.post(url, {'name': 'Test Token', 'scopes': ['read', 'write']}, format='json')
        assert response.status_code == 201
        assert 'raw_token' in response.data
        
        # List tokens
        list_response = auth_client.get(url)
        assert list_response.status_code == 200
        assert len(list_response.data) == 1
        assert list_response.data[0]['name'] == 'Test Token'
        assert 'raw_token' not in list_response.data[0] # List should not expose raw token

    def test_rotate_token(self, auth_client):
        url = reverse('profiles:api-token-list')
        response = auth_client.post(url, {'name': 'Rotate Me', 'scopes': ['read']}, format='json')
        token_id = response.data['id']
        old_raw = response.data['raw_token']

        rotate_url = reverse('profiles:api-token-rotate', args=[token_id])
        rotate_res = auth_client.post(rotate_url)
        
        assert rotate_res.status_code == 200
        new_raw = rotate_res.data['raw_token']
        assert old_raw != new_raw

@pytest.mark.django_db
class TestSessionHistory:
    def test_list_sessions(self, auth_client, user):
        # The SessionTrackingMiddleware would create a session in real life.
        # We manually create one here.
        from profiles.models import SessionHistory
        SessionHistory.objects.create(user=user, session_id='test-jti', device='TestDevice')
        
        url = reverse('profiles:session-history-list')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['device'] == 'TestDevice'
