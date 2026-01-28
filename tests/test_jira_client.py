"""Unit tests for Jira client service."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from jira import JIRAError
from services.jira_client import JiraClient


@pytest.fixture
def mock_jira():
    """Create a mock JIRA instance."""
    with patch('services.jira_client.JIRA') as mock:
        yield mock


@pytest.fixture
def jira_client(mock_jira):
    """Create a JiraClient instance with mocked JIRA."""
    return JiraClient('https://jira.example.com', 'test-token')


class TestJiraClient:
    """Test cases for JiraClient class."""
    
    def test_init(self, mock_jira):
        """Test client initialization."""
        client = JiraClient('https://jira.example.com', 'test-token')
        mock_jira.assert_called_once_with(
            server='https://jira.example.com',
            token_auth='test-token'
        )
        assert client.server == 'https://jira.example.com'
    
    def test_get_current_user(self, jira_client, mock_jira):
        """Test getting current user info."""
        mock_jira.return_value.myself.return_value = {
            'name': 'testuser',
            'displayName': 'Test User',
            'emailAddress': 'test@example.com'
        }
        
        user = jira_client.get_current_user()
        
        assert user['username'] == 'testuser'
        assert user['display_name'] == 'Test User'
        assert user['email'] == 'test@example.com'
    
    def test_get_current_user_with_key(self, jira_client, mock_jira):
        """Test getting current user when 'key' is used instead of 'name'."""
        mock_jira.return_value.myself.return_value = {
            'key': 'testuser',
            'displayName': 'Test User'
        }
        
        user = jira_client.get_current_user()
        
        assert user['username'] == 'testuser'
    
    def test_get_issue(self, jira_client, mock_jira):
        """Test fetching an issue."""
        mock_issue = Mock()
        mock_issue.key = 'PROJ-123'
        mock_jira.return_value.issue.return_value = mock_issue
        
        issue = jira_client.get_issue('PROJ-123')
        
        assert issue.key == 'PROJ-123'
        mock_jira.return_value.issue.assert_called_once_with('PROJ-123')
    
    def test_get_subtasks(self, jira_client, mock_jira):
        """Test getting subtasks."""
        mock_subtask1 = Mock()
        mock_subtask1.key = 'PROJ-124'
        mock_subtask2 = Mock()
        mock_subtask2.key = 'PROJ-125'
        
        mock_parent = Mock()
        mock_parent.fields.subtasks = [mock_subtask1, mock_subtask2]
        mock_jira.return_value.issue.return_value = mock_parent
        
        subtasks = jira_client.get_subtasks('PROJ-123')
        
        assert len(subtasks) == 2
        assert subtasks[0].key == 'PROJ-124'
        assert subtasks[1].key == 'PROJ-125'
    
    def test_transition_issue_success(self, jira_client, mock_jira):
        """Test successful issue transition."""
        mock_issue = Mock()
        mock_issue.key = 'PROJ-123'
        
        mock_jira.return_value.transitions.return_value = [
            {'id': '1', 'to': {'name': 'In Progress'}},
            {'id': '2', 'to': {'name': 'Done'}}
        ]
        
        result = jira_client.transition_issue(mock_issue, 'In Progress')
        
        assert result is True
        mock_jira.return_value.transition_issue.assert_called_once_with(mock_issue, '1')
    
    def test_transition_issue_not_found(self, jira_client, mock_jira):
        """Test transition when target status not available."""
        mock_issue = Mock()
        mock_jira.return_value.transitions.return_value = [
            {'id': '1', 'to': {'name': 'In Progress'}}
        ]
        
        result = jira_client.transition_issue(mock_issue, 'Completed')
        
        assert result is False
        mock_jira.return_value.transition_issue.assert_not_called()
    
    def test_add_worklog(self, jira_client, mock_jira):
        """Test adding worklog."""
        mock_issue = Mock()
        mock_issue.key = 'PROJ-123'
        
        result = jira_client.add_worklog(mock_issue, '2h')
        
        assert result is True
        mock_jira.return_value.add_worklog.assert_called_once_with(
            mock_issue,
            timeSpent='2h'
        )
    
    def test_get_worklogs(self, jira_client, mock_jira):
        """Test getting worklogs."""
        mock_issue = Mock()
        mock_worklog1 = Mock()
        mock_worklog2 = Mock()
        mock_jira.return_value.worklogs.return_value = [mock_worklog1, mock_worklog2]
        
        worklogs = jira_client.get_worklogs(mock_issue)
        
        assert len(worklogs) == 2
        mock_jira.return_value.worklogs.assert_called_once_with(mock_issue)
    
    def test_create_subtask(self, jira_client, mock_jira):
        """Test creating a subtask."""
        mock_issue = Mock()
        mock_issue.key = 'PROJ-124'
        mock_jira.return_value.create_issue.return_value = mock_issue
        
        fields = {'summary': 'Test subtask'}
        result = jira_client.create_subtask('PROJ-123', fields)
        
        assert result.key == 'PROJ-124'
        mock_jira.return_value.create_issue.assert_called_once_with(fields=fields)
    
    def test_assign_issue(self, jira_client, mock_jira):
        """Test assigning an issue."""
        mock_issue = Mock()
        mock_issue.key = 'PROJ-123'
        
        result = jira_client.assign_issue(mock_issue, 'testuser')
        
        assert result is True
        mock_jira.return_value.assign_issue.assert_called_once_with(
            mock_issue,
            'testuser'
        )
    
    def test_get_issue_types(self, jira_client, mock_jira):
        """Test getting issue types."""
        mock_type1 = Mock()
        mock_type1.name = 'Story'
        mock_type2 = Mock()
        mock_type2.name = 'Sub-task'
        mock_jira.return_value.issue_types.return_value = [mock_type1, mock_type2]
        
        types = jira_client.get_issue_types()
        
        assert len(types) == 2
        assert types[0].name == 'Story'
        assert types[1].name == 'Sub-task'
    
    def test_get_project(self, jira_client, mock_jira):
        """Test getting project info."""
        mock_issue = Mock()
        mock_issue.fields.project.id = '10001'
        mock_issue.fields.project.key = 'PROJ'
        mock_issue.fields.project.name = 'Test Project'
        mock_jira.return_value.issue.return_value = mock_issue
        
        project = jira_client.get_project('PROJ-123')
        
        assert project['id'] == '10001'
        assert project['key'] == 'PROJ'
        assert project['name'] == 'Test Project'
