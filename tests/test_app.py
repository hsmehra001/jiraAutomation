"""Integration tests for Flask application."""
import pytest
from unittest.mock import Mock, patch
from app import app


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRoutes:
    """Test Flask routes."""
    
    def test_index_page(self, client):
        """Test landing page loads."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Welcome to Jira Automation' in response.data
    
    def test_process_tasks_page(self, client):
        """Test process tasks page loads."""
        response = client.get('/process-tasks')
        assert response.status_code == 200
        assert b'Process Assigned Subtasks' in response.data
    
    def test_create_subtasks_page(self, client):
        """Test create subtasks page loads."""
        response = client.get('/create-subtasks')
        assert response.status_code == 200
        assert b'Create Standard Subtasks' in response.data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'config' in data


class TestProcessTasksAPI:
    """Test process tasks API endpoint."""
    
    @patch('app.JiraClient')
    @patch('app.TaskProcessor')
    def test_process_tasks_success(self, mock_processor_class, mock_client_class, client):
        """Test successful task processing."""
        # Setup mocks
        mock_processor = Mock()
        mock_processor.process_story_subtasks.return_value = {
            'results': [
                {
                    'subtask_key': 'PROJ-124',
                    'status': 'success',
                    'actions': ['Moved to In Progress', 'Logged 2h'],
                    'message': 'Processed successfully'
                }
            ],
            'summary': {
                'total': 1,
                'processed': 1,
                'skipped': 0
            }
        }
        mock_processor_class.return_value = mock_processor
        
        # Make request
        response = client.post('/api/process-tasks', json={
            'story_key': 'PROJ-123',
            'jira_pat': 'test-token'
        })
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['results']) == 1
        assert data['summary']['processed'] == 1
    
    def test_process_tasks_missing_story_key(self, client):
        """Test error when story key is missing."""
        response = client.post('/api/process-tasks', json={
            'jira_pat': 'test-token'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'story_key is required' in data['error']
    
    def test_process_tasks_missing_pat(self, client):
        """Test error when PAT is missing and not configured."""
        with patch('app.Config.JIRA_PAT', ''):
            response = client.post('/api/process-tasks', json={
                'story_key': 'PROJ-123'
            })
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'PAT is required' in data['error']
    
    def test_process_tasks_invalid_story_key(self, client):
        """Test error with invalid story key format."""
        response = client.post('/api/process-tasks', json={
            'story_key': 'invalid',
            'jira_pat': 'test-token'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid story key format' in data['error']
    
    @patch('app.JiraClient')
    def test_process_tasks_jira_error(self, mock_client_class, client):
        """Test handling of Jira API errors."""
        from jira import JIRAError
        
        mock_client_class.side_effect = JIRAError(
            status_code=401,
            text='Unauthorized'
        )
        
        response = client.post('/api/process-tasks', json={
            'story_key': 'PROJ-123',
            'jira_pat': 'invalid-token'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'Jira API Error' in data['error']


class TestCreateSubtasksAPI:
    """Test create subtasks API endpoint."""
    
    @patch('app.JiraClient')
    @patch('app.SubtaskCreator')
    def test_create_subtasks_success(self, mock_creator_class, mock_client_class, client):
        """Test successful subtask creation."""
        # Setup mocks
        mock_creator = Mock()
        mock_creator.create_subtasks.return_value = {
            'created': [
                {
                    'key': 'PROJ-124',
                    'summary': 'Unit Test Case Execution',
                    'status': 'success',
                    'message': 'Created and assigned'
                }
            ],
            'summary': {
                'total': 7,
                'created': 7,
                'failed': 0
            }
        }
        mock_creator_class.return_value = mock_creator
        
        # Make request
        response = client.post('/api/create-subtasks', json={
            'story_key': 'PROJ-123',
            'jira_pat': 'test-token'
        })
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['created']) == 1
        assert data['summary']['created'] == 7
    
    def test_create_subtasks_missing_story_key(self, client):
        """Test error when story key is missing."""
        response = client.post('/api/create-subtasks', json={
            'jira_pat': 'test-token'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'story_key is required' in data['error']
    
    def test_create_subtasks_invalid_story_key(self, client):
        """Test error with invalid story key format."""
        response = client.post('/api/create-subtasks', json={
            'story_key': 'invalid',
            'jira_pat': 'test-token'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid story key format' in data['error']
    
    @patch('app.JiraClient')
    def test_create_subtasks_jira_error(self, mock_client_class, client):
        """Test handling of Jira API errors."""
        from jira import JIRAError
        
        mock_client_class.side_effect = JIRAError(
            status_code=403,
            text='Forbidden'
        )
        
        response = client.post('/api/create-subtasks', json={
            'story_key': 'PROJ-123',
            'jira_pat': 'test-token'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'Jira API Error' in data['error']
