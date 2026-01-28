"""Jira client service wrapper."""
import logging
from typing import List, Optional, Dict
from jira import JIRA, JIRAError, Issue

logger = logging.getLogger(__name__)


class JiraClient:
    """Wrapper around jira-python library for common operations."""
    
    def __init__(self, server: str, token: str):
        """
        Initialize Jira connection with PAT.
        
        Args:
            server: Jira server URL
            token: Personal Access Token
            
        Raises:
            JIRAError: If authentication fails
        """
        self.server = server
        self.jira = JIRA(server=server, token_auth=token)
        logger.info(f"Connected to Jira server: {server}")
    
    def get_current_user(self) -> Dict:
        """
        Get current authenticated user info.
        
        Returns:
            dict: User information including username/key
            
        Raises:
            JIRAError: If API call fails
        """
        myself = self.jira.myself()
        username = myself.get('name') or myself.get('key')
        logger.info(f"Current user: {username}")
        return {
            'username': username,
            'display_name': myself.get('displayName', username),
            'email': myself.get('emailAddress', '')
        }
    
    def get_issue(self, issue_key: str) -> Issue:
        """
        Fetch issue by key.
        
        Args:
            issue_key: Jira issue key (e.g., PROJ-123)
            
        Returns:
            Issue: Jira issue object
            
        Raises:
            JIRAError: If issue not found or API call fails
        """
        logger.debug(f"Fetching issue: {issue_key}")
        return self.jira.issue(issue_key)
    
    def get_subtasks(self, issue_key: str) -> List[Issue]:
        """
        Get all subtasks for a parent issue.
        
        Args:
            issue_key: Parent issue key
            
        Returns:
            List[Issue]: List of subtask issues
            
        Raises:
            JIRAError: If issue not found or API call fails
        """
        parent = self.get_issue(issue_key)
        subtasks = parent.fields.subtasks
        logger.info(f"Found {len(subtasks)} subtasks under {issue_key}")
        return subtasks
    
    def transition_issue(self, issue: Issue, transition_name: str) -> bool:
        """
        Move issue to specified status.
        
        Args:
            issue: Jira issue object
            transition_name: Name of the transition (e.g., "In Progress")
            
        Returns:
            bool: True if transition successful, False if transition not found
            
        Raises:
            JIRAError: If API call fails
        """
        transitions = self.jira.transitions(issue)
        for transition in transitions:
            if transition["to"]["name"] == transition_name:
                self.jira.transition_issue(issue, transition["id"])
                logger.info(f"Transitioned {issue.key} to {transition_name}")
                return True
        
        logger.warning(f"Transition '{transition_name}' not found for {issue.key}")
        return False
    
    def add_worklog(self, issue: Issue, time_spent: str) -> bool:
        """
        Log work on an issue.
        
        Args:
            issue: Jira issue object
            time_spent: Time to log (e.g., "2h", "30m")
            
        Returns:
            bool: True if worklog added successfully
            
        Raises:
            JIRAError: If API call fails
        """
        self.jira.add_worklog(issue, timeSpent=time_spent)
        logger.info(f"Logged {time_spent} work for {issue.key}")
        return True
    
    def get_worklogs(self, issue: Issue) -> List:
        """
        Get all worklogs for an issue.
        
        Args:
            issue: Jira issue object
            
        Returns:
            List: List of worklog objects
            
        Raises:
            JIRAError: If API call fails
        """
        return self.jira.worklogs(issue)
    
    def create_subtask(self, parent_key: str, fields: Dict) -> Issue:
        """
        Create a new subtask.
        
        Args:
            parent_key: Parent issue key
            fields: Dictionary of field values for the subtask
            
        Returns:
            Issue: Created subtask issue
            
        Raises:
            JIRAError: If creation fails
        """
        issue = self.jira.create_issue(fields=fields)
        logger.info(f"Created subtask {issue.key} under {parent_key}")
        return issue
    
    def assign_issue(self, issue: Issue, username: str) -> bool:
        """
        Assign issue to user.
        
        Args:
            issue: Jira issue object
            username: Username to assign to
            
        Returns:
            bool: True if assignment successful
            
        Raises:
            JIRAError: If API call fails
        """
        self.jira.assign_issue(issue, username)
        logger.info(f"Assigned {issue.key} to {username}")
        return True
    
    def get_issue_types(self) -> List:
        """
        Get all issue types.
        
        Returns:
            List: List of issue type objects
            
        Raises:
            JIRAError: If API call fails
        """
        return self.jira.issue_types()
    
    def get_project(self, issue_key: str) -> Dict:
        """
        Get project information from an issue.
        
        Args:
            issue_key: Any issue key in the project
            
        Returns:
            dict: Project information
            
        Raises:
            JIRAError: If API call fails
        """
        issue = self.get_issue(issue_key)
        return {
            'id': issue.fields.project.id,
            'key': issue.fields.project.key,
            'name': issue.fields.project.name
        }
