"""Subtask creator service for creating standard development subtasks."""
import logging
from typing import Dict, List
from jira import JIRAError
from services.jira_client import JiraClient

logger = logging.getLogger(__name__)


class SubtaskCreator:
    """Service for creating standard subtasks under a parent story."""
    
    SUBTASK_TEMPLATES = [
        "Unit Test Case Execution",
        "Peer Code Review",
        "Analysis & Understanding",
        "Internal Grooming among Team Members",
        "Dev Testing",
        "Unit Test Case Creation",
        "P0 Demo to QA and other stakeholders"
    ]
    
    def __init__(self, jira_client: JiraClient, custom_field_id: str, 
                 custom_field_value: str, default_estimate: str):
        """
        Initialize with Jira client and configuration.
        
        Args:
            jira_client: JiraClient instance
            custom_field_id: Custom field ID (e.g., customfield_10111)
            custom_field_value: Value for the custom field
            default_estimate: Default time estimate (e.g., "2h")
        """
        self.jira_client = jira_client
        self.custom_field_id = custom_field_id
        self.custom_field_value = custom_field_value
        self.default_estimate = default_estimate
    
    def create_subtasks(self, story_key: str) -> Dict:
        """
        Create all standard subtasks under story.
        
        Args:
            story_key: Parent story key
            
        Returns:
            dict: {
                'created': List of created subtask info,
                'summary': Overall summary statistics
            }
            
        Raises:
            JIRAError: If Jira API calls fail
        """
        logger.info(f"Creating subtasks under story: {story_key}")
        
        # Get current user
        current_user = self.jira_client.get_current_user()
        username = current_user['username']
        
        # Get subtask issue type ID
        subtask_issue_type_id = self._get_subtask_issue_type_id()
        if not subtask_issue_type_id:
            raise Exception("Sub-task issue type not found")
        
        # Get project info
        project = self.jira_client.get_project(story_key)
        
        created = []
        failed_count = 0
        
        for summary in self.SUBTASK_TEMPLATES:
            try:
                result = self._create_single_subtask(
                    story_key,
                    summary,
                    project['id'],
                    subtask_issue_type_id,
                    username
                )
                created.append(result)
                logger.info(f"Created {result['key']} - {summary}")
            except Exception as e:
                logger.error(f"Failed to create subtask '{summary}': {str(e)}")
                created.append({
                    'key': None,
                    'summary': summary,
                    'status': 'error',
                    'message': str(e)
                })
                failed_count += 1
        
        summary_stats = {
            'total': len(self.SUBTASK_TEMPLATES),
            'created': len(self.SUBTASK_TEMPLATES) - failed_count,
            'failed': failed_count
        }
        
        logger.info(f"Creation complete: {summary_stats}")
        
        return {
            'created': created,
            'summary': summary_stats
        }
    
    def _create_single_subtask(self, parent_key: str, summary: str, 
                               project_id: str, issue_type_id: str, 
                               username: str) -> Dict:
        """
        Create and assign single subtask.
        
        Args:
            parent_key: Parent story key
            summary: Subtask summary
            project_id: Project ID
            issue_type_id: Sub-task issue type ID
            username: Username to assign to
            
        Returns:
            dict: {
                'key': str,
                'summary': str,
                'status': 'success'|'error',
                'message': str
            }
            
        Raises:
            JIRAError: If creation or assignment fails
        """
        # Build fields dictionary
        fields = {
            "project": {"id": project_id},
            "parent": {"key": parent_key},
            "summary": summary,
            "description": summary,
            "issuetype": {"id": issue_type_id},
            "timetracking": {"originalEstimate": self.default_estimate},
            # Custom field must be sent as object
            self.custom_field_id: {"value": self.custom_field_value}
        }
        
        # Create subtask
        issue = self.jira_client.create_subtask(parent_key, fields)
        
        # Assign to current user
        self.jira_client.assign_issue(issue, username)
        
        return {
            'key': issue.key,
            'summary': summary,
            'status': 'success',
            'message': f'Created and assigned to {username}'
        }
    
    def _get_subtask_issue_type_id(self) -> str:
        """
        Find Sub-task issue type ID.
        
        Returns:
            str: Issue type ID or None if not found
        """
        issue_types = self.jira_client.get_issue_types()
        for issue_type in issue_types:
            if issue_type.name.lower() == "sub-task":
                logger.debug(f"Found Sub-task issue type ID: {issue_type.id}")
                return issue_type.id
        
        logger.error("Sub-task issue type not found")
        return None
