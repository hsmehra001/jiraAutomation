"""Unit tests for subtask creator service."""
import pytest
from unittest.mock import Mock, MagicMock
from jira import JIRAError
from services.subtask_creator import SubtaskCreator


@pytest.fixture
def mock_jira_client():
    """Create a mock JiraClient."""
    return Mock()


@pytest.fixture
def subtask_creator(mock_jira_client):
    """Create a SubtaskCreator instance with mocked client."""
    return SubtaskCreator(
        mock_jira_client,
        custom_field_id='customfield_10111',
        custom_field_value='Platform Comm Mgmt',
        default_estimate='2h'
    )


class TestSubtaskCreator:
    """Test cases for SubtaskCreator class."""
    
    def test_subtask_templates(self):
        """Test that subtask templates are defined correctly."""
        assert len(SubtaskCreator.SUBTASK_TEMPLATES) == 7
        assert "Unit Test Case Execution" in SubtaskCreator.SUBTASK_TEMPLATES
        assert "Peer Code Review" in SubtaskCreator.SUBTASK_TEMPLATES
    
    def test_create_subtasks_success(self, subtask_creator, mock_jira_client):
        """Test successful creation of all subtasks."""
        # Setup mocks
        mock_jira_client.get_current_user.return_value = {'username': 'testuser'}
        
        mock_issue_type = Mock()
        mock_issue_type.id = '5'
        mock_issue_type.name = 'Sub-task'
        mock_jira_client.get_issue_types.return_value = [mock_issue_type]
        
        mock_jira_client.get_project.return_value = {
            'id': '10001',
            'key': 'PROJ',
            'name': 'Test Project'
        }
        
        # Mock issue creation
        def create_mock_issue(parent_key, fields):
            issue = Mock()
            issue.key = f'PROJ-{len(mock_jira_client.create_subtask.mock_calls) + 100}'
            return issue
        
        mock_jira_client.create_subtask.side_effect = create_mock_issue
        
        # Execute
        result = subtask_creator.create_subtasks('PROJ-123')
        
        # Verify
        assert result['summary']['total'] == 7
        assert result['summary']['created'] == 7
        assert result['summary']['failed'] == 0
        assert len(result['created']) == 7
        assert all(item['status'] == 'success' for item in result['created'])
        
        # Verify all subtasks were created
        assert mock_jira_client.create_subtask.call_count == 7
        assert mock_jira_client.assign_issue.call_count == 7
    
    def test_create_subtasks_partial_failure(self, subtask_creator, mock_jira_client):
        """Test handling of partial failures during creation."""
        mock_jira_client.get_current_user.return_value = {'username': 'testuser'}
        
        mock_issue_type = Mock()
        mock_issue_type.id = '5'
        mock_issue_type.name = 'Sub-task'
        mock_jira_client.get_issue_types.return_value = [mock_issue_type]
        
        mock_jira_client.get_project.return_value = {'id': '10001'}
        
        # Mock first creation succeeds, second fails
        call_count = [0]
        def create_with_failure(parent_key, fields):
            call_count[0] += 1
            if call_count[0] == 2:
                raise JIRAError(status_code=400, text='Bad Request')
            issue = Mock()
            issue.key = f'PROJ-{call_count[0]}'
            return issue
        
        mock_jira_client.create_subtask.side_effect = create_with_failure
        
        result = subtask_creator.create_subtasks('PROJ-123')
        
        assert result['summary']['failed'] == 1
        assert result['summary']['created'] == 6
        assert any(item['status'] == 'error' for item in result['created'])
    
    def test_create_subtasks_no_subtask_type(self, subtask_creator, mock_jira_client):
        """Test error when Sub-task issue type not found."""
        mock_jira_client.get_current_user.return_value = {'username': 'testuser'}
        mock_jira_client.get_issue_types.return_value = []
        
        with pytest.raises(Exception, match="Sub-task issue type not found"):
            subtask_creator.create_subtasks('PROJ-123')
    
    def test_create_single_subtask(self, subtask_creator, mock_jira_client):
        """Test creating a single subtask."""
        mock_issue = Mock()
        mock_issue.key = 'PROJ-124'
        mock_jira_client.create_subtask.return_value = mock_issue
        
        result = subtask_creator._create_single_subtask(
            'PROJ-123',
            'Test Subtask',
            '10001',
            '5',
            'testuser'
        )
        
        assert result['key'] == 'PROJ-124'
        assert result['summary'] == 'Test Subtask'
        assert result['status'] == 'success'
        
        # Verify fields passed to create_subtask
        call_args = mock_jira_client.create_subtask.call_args
        fields = call_args[0][1]
        assert fields['project']['id'] == '10001'
        assert fields['parent']['key'] == 'PROJ-123'
        assert fields['summary'] == 'Test Subtask'
        assert fields['issuetype']['id'] == '5'
        assert fields['timetracking']['originalEstimate'] == '2h'
        assert fields['customfield_10111']['value'] == 'Platform Comm Mgmt'
        
        # Verify assignment
        mock_jira_client.assign_issue.assert_called_once_with(mock_issue, 'testuser')
    
    def test_get_subtask_issue_type_id_found(self, subtask_creator, mock_jira_client):
        """Test finding Sub-task issue type ID."""
        mock_type1 = Mock()
        mock_type1.id = '1'
        mock_type1.name = 'Story'
        
        mock_type2 = Mock()
        mock_type2.id = '5'
        mock_type2.name = 'Sub-task'
        
        mock_jira_client.get_issue_types.return_value = [mock_type1, mock_type2]
        
        result = subtask_creator._get_subtask_issue_type_id()
        
        assert result == '5'
    
    def test_get_subtask_issue_type_id_not_found(self, subtask_creator, mock_jira_client):
        """Test when Sub-task issue type not found."""
        mock_type = Mock()
        mock_type.id = '1'
        mock_type.name = 'Story'
        
        mock_jira_client.get_issue_types.return_value = [mock_type]
        
        result = subtask_creator._get_subtask_issue_type_id()
        
        assert result is None
    
    def test_get_subtask_issue_type_id_case_insensitive(self, subtask_creator, mock_jira_client):
        """Test case-insensitive matching for Sub-task type."""
        mock_type = Mock()
        mock_type.id = '5'
        mock_type.name = 'SUB-TASK'
        
        mock_jira_client.get_issue_types.return_value = [mock_type]
        
        result = subtask_creator._get_subtask_issue_type_id()
        
        assert result == '5'
