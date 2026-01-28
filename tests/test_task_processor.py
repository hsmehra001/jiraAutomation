"""Unit tests for task processor service."""
import pytest
from unittest.mock import Mock, MagicMock
from jira import JIRAError
from services.task_processor import TaskProcessor


@pytest.fixture
def mock_jira_client():
    """Create a mock JiraClient."""
    return Mock()


@pytest.fixture
def task_processor(mock_jira_client):
    """Create a TaskProcessor instance with mocked client."""
    return TaskProcessor(mock_jira_client)


def create_mock_issue(key, status, assignee_name=None):
    """Helper to create a mock issue."""
    issue = Mock()
    issue.key = key
    issue.fields.status.name = status
    if assignee_name:
        issue.fields.assignee.name = assignee_name
    else:
        issue.fields.assignee = None
    return issue


class TestTaskProcessor:
    """Test cases for TaskProcessor class."""

    def test_process_story_subtasks_success(self, task_processor, mock_jira_client):
        """Test successful processing of subtasks."""
        # Setup mocks
        mock_jira_client.get_current_user.return_value = {'username': 'testuser'}

        subtask1 = Mock()
        subtask1.key = 'PROJ-124'
        subtask2 = Mock()
        subtask2.key = 'PROJ-125'
        mock_jira_client.get_subtasks.return_value = [subtask1, subtask2]

        issue1 = create_mock_issue('PROJ-124', 'Open', 'testuser')
        issue2 = create_mock_issue('PROJ-125', 'Completed', 'testuser')
        mock_jira_client.get_issue.side_effect = [issue1, issue1, issue2]

        mock_jira_client.transition_issue.return_value = True
        mock_jira_client.get_worklogs.return_value = []

        # Execute
        result = task_processor.process_story_subtasks('PROJ-123')

        # Verify
        assert result['summary']['total'] == 2
        assert result['summary']['processed'] == 1
        assert result['summary']['skipped'] == 1
        assert len(result['results']) == 2

    def test_process_story_subtasks_not_assigned(self, task_processor, mock_jira_client):
        """Test skipping subtasks not assigned to current user."""
        mock_jira_client.get_current_user.return_value = {'username': 'testuser'}

        subtask1 = Mock()
        subtask1.key = 'PROJ-124'
        mock_jira_client.get_subtasks.return_value = [subtask1]

        issue1 = create_mock_issue('PROJ-124', 'Open', 'otheruser')
        mock_jira_client.get_issue.return_value = issue1

        result = task_processor.process_story_subtasks('PROJ-123')

        assert result['summary']['skipped'] == 1
        assert result['results'][0]['status'] == 'skipped'
        assert 'Not assigned to me' in result['results'][0]['message']

    def test_process_single_subtask_open_to_completed(self, task_processor, mock_jira_client):
        """Test processing subtask from Open to Completed."""
        issue = create_mock_issue('PROJ-124', 'Open', 'testuser')

        # Mock transitions
        mock_jira_client.transition_issue.return_value = True
        mock_jira_client.get_issue.return_value = create_mock_issue('PROJ-124', 'In Progress.', 'testuser')
        mock_jira_client.get_worklogs.return_value = []

        result = task_processor._process_single_subtask(issue, 'testuser')

        assert result['status'] == 'success'
        assert 'Moved to In Progress' in result['actions']
        assert 'Logged 2h work' in result['actions']
        assert 'Moved to Completed' in result['actions']

    def test_process_single_subtask_already_completed(self, task_processor, mock_jira_client):
        """Test skipping already completed subtask."""
        issue = create_mock_issue('PROJ-124', 'Completed', 'testuser')

        result = task_processor._process_single_subtask(issue, 'testuser')

        assert result['status'] == 'skipped'
        assert result['message'] == 'Already Completed'
        assert len(result['actions']) == 0

    def test_process_single_subtask_work_already_logged(self, task_processor, mock_jira_client):
        """Test skipping worklog when already logged."""
        issue = create_mock_issue('PROJ-124', 'In Progress.', 'testuser')

        # Mock existing worklog
        mock_worklog = Mock()
        mock_worklog.author.name = 'testuser'
        mock_jira_client.get_worklogs.return_value = [mock_worklog]
        mock_jira_client.transition_issue.return_value = True

        result = task_processor._process_single_subtask(issue, 'testuser')

        assert result['status'] == 'success'
        assert 'Work already logged, skipped worklog' in result['actions']
        assert 'Logged 2h work' not in result['actions']

    def test_process_single_subtask_error(self, task_processor, mock_jira_client):
        """Test error handling during processing."""
        issue = create_mock_issue('PROJ-124', 'Open', 'testuser')

        # Mock error
        error = JIRAError(status_code=400, text='Bad Request')
        mock_jira_client.transition_issue.side_effect = error

        result = task_processor._process_single_subtask(issue, 'testuser')

        assert result['status'] == 'error'
        assert 'Error:' in result['message']

    def test_should_process_subtask_assigned(self, task_processor):
        """Test should process when assigned to user."""
        issue = create_mock_issue('PROJ-124', 'Open', 'testuser')

        result = task_processor._should_process_subtask(issue, 'testuser')

        assert result is True

    def test_should_process_subtask_not_assigned(self, task_processor):
        """Test should not process when assigned to different user."""
        issue = create_mock_issue('PROJ-124', 'Open', 'otheruser')

        result = task_processor._should_process_subtask(issue, 'testuser')

        assert result is False

    def test_should_process_subtask_no_assignee(self, task_processor):
        """Test should not process when no assignee."""
        issue = create_mock_issue('PROJ-124', 'Open', None)

        result = task_processor._should_process_subtask(issue, 'testuser')

        assert result is False

    def test_has_worklog_by_user_true(self, task_processor, mock_jira_client):
        """Test detecting existing worklog by user."""
        issue = Mock()

        mock_worklog1 = Mock()
        mock_worklog1.author.name = 'otheruser'
        mock_worklog2 = Mock()
        mock_worklog2.author.name = 'testuser'
        mock_jira_client.get_worklogs.return_value = [mock_worklog1, mock_worklog2]

        result = task_processor._has_worklog_by_user(issue, 'testuser')

        assert result is True

    def test_has_worklog_by_user_false(self, task_processor, mock_jira_client):
        """Test no worklog by user."""
        issue = Mock()

        mock_worklog = Mock()
        mock_worklog.author.name = 'otheruser'
        mock_jira_client.get_worklogs.return_value = [mock_worklog]

        result = task_processor._has_worklog_by_user(issue, 'testuser')

        assert result is False
