"""Task processor service for processing assigned subtasks."""
import logging
from typing import Dict, List
from jira import Issue, JIRAError
from services.jira_client import JiraClient

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Service for processing subtasks through workflow states."""
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize with Jira client.
        
        Args:
            jira_client: JiraClient instance
        """
        self.jira_client = jira_client
    
    def process_story_subtasks(self, story_key: str) -> Dict:
        """
        Process all subtasks assigned to current user.
        
        Args:
            story_key: Parent story key
            
        Returns:
            dict: {
                'results': List of per-subtask results,
                'summary': Overall summary statistics
            }
            
        Raises:
            JIRAError: If Jira API calls fail
        """
        logger.info(f"Processing subtasks for story: {story_key}")
        
        # Get current user
        current_user = self.jira_client.get_current_user()
        username = current_user['username']
        
        # Get all subtasks
        subtasks = self.jira_client.get_subtasks(story_key)
        
        results = []
        processed_count = 0
        skipped_count = 0
        
        for subtask in subtasks:
            # Fetch full issue details
            issue = self.jira_client.get_issue(subtask.key)
            
            # Check if should process
            if not self._should_process_subtask(issue, username):
                assignee_name = issue.fields.assignee.name if issue.fields.assignee else None
                result = {
                    'subtask_key': issue.key,
                    'current_status': issue.fields.status.name,
                    'actions': [],
                    'status': 'skipped',
                    'message': f'Not assigned to me (assignee={assignee_name})',
                    'assignee': assignee_name
                }
                results.append(result)
                skipped_count += 1
                logger.info(f"Skipping {issue.key}: not assigned to current user")
                continue
            
            # Process the subtask
            result = self._process_single_subtask(issue, username)
            results.append(result)
            
            if result['status'] == 'success':
                processed_count += 1
            else:
                skipped_count += 1
        
        summary = {
            'total': len(subtasks),
            'processed': processed_count,
            'skipped': skipped_count
        }
        
        logger.info(f"Processing complete: {summary}")
        
        return {
            'results': results,
            'summary': summary
        }
    
    def _process_single_subtask(self, subtask: Issue, current_username: str) -> Dict:
        """
        Process individual subtask through workflow.
        
        Args:
            subtask: Jira issue object
            current_username: Current user's username
            
        Returns:
            dict: {
                'subtask_key': str,
                'current_status': str,
                'actions': List of actions taken,
                'status': 'success'|'skipped'|'error',
                'message': str,
                'assignee': str
            }
        """
        actions = []
        current_status = subtask.fields.status.name
        assignee = subtask.fields.assignee.name if subtask.fields.assignee else None
        
        logger.info(f"Processing {subtask.key} | Status: {current_status}")
        
        try:
            # Step 1: Move to In Progress if status is Open
            if current_status == "Open":
                if self.jira_client.transition_issue(subtask, "In Progress."):
                    actions.append("Moved to In Progress")
                    # Refresh issue to get updated status
                    subtask = self.jira_client.get_issue(subtask.key)
                    current_status = subtask.fields.status.name
                else:
                    logger.warning(f"Could not transition {subtask.key} to In Progress")
            
            # Step 2: Log work if status is In Progress and not already logged
            if current_status == "In Progress.":
                if not self._has_worklog_by_user(subtask, current_username):
                    self.jira_client.add_worklog(subtask, "2h")
                    actions.append("Logged 2h work")
                else:
                    actions.append("Work already logged, skipped worklog")
                    logger.info(f"Work already logged for {subtask.key}")
                
                # Step 3: Move to Completed
                if self.jira_client.transition_issue(subtask, "Completed"):
                    actions.append("Moved to Completed")
                else:
                    logger.warning(f"Could not transition {subtask.key} to Completed")
            
            # Step 4: Skip if already Completed
            elif current_status == "Completed":
                return {
                    'subtask_key': subtask.key,
                    'current_status': current_status,
                    'actions': actions,
                    'status': 'skipped',
                    'message': 'Already Completed',
                    'assignee': assignee
                }
            
            return {
                'subtask_key': subtask.key,
                'current_status': current_status,
                'actions': actions,
                'status': 'success',
                'message': 'Processed successfully',
                'assignee': assignee
            }
            
        except JIRAError as e:
            logger.error(f"Error processing {subtask.key}: {e.text}")
            return {
                'subtask_key': subtask.key,
                'current_status': current_status,
                'actions': actions,
                'status': 'error',
                'message': f'Error: {e.text}',
                'assignee': assignee
            }
    
    def _should_process_subtask(self, subtask: Issue, current_username: str) -> bool:
        """
        Check if subtask should be processed.
        
        Args:
            subtask: Jira issue object
            current_username: Current user's username
            
        Returns:
            bool: True if subtask should be processed
        """
        assignee = subtask.fields.assignee
        if not assignee:
            return False
        
        assignee_name = assignee.name if hasattr(assignee, 'name') else assignee.key
        return assignee_name == current_username
    
    def _has_worklog_by_user(self, subtask: Issue, username: str) -> bool:
        """
        Check if user already logged work on subtask.
        
        Args:
            subtask: Jira issue object
            username: Username to check
            
        Returns:
            bool: True if user has logged work
        """
        worklogs = self.jira_client.get_worklogs(subtask)
        for worklog in worklogs:
            worklog_author = worklog.author.name if hasattr(worklog.author, 'name') else worklog.author.key
            if worklog_author == username:
                return True
        return False
