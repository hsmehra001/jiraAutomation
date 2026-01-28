"""Configuration management for Jira Automation Web UI."""
import os
import sys

class Config:
    """Application configuration loaded from environment variables or command-line arguments."""

    # Jira Configuration
    JIRA_SERVER = os.getenv('JIRA_SERVER', 'https://jira.sirionlabs.tech')
    JIRA_PAT = None  # No default value, must be provided by user

    # Custom Field Configuration
    CUSTOM_FIELD_ID = os.getenv('CUSTOM_FIELD_ID', 'customfield_10111')
    CUSTOM_FIELD_VALUE = os.getenv('CUSTOM_FIELD_VALUE', 'Platform Comm Mgmt')
    DEFAULT_ESTIMATE = os.getenv('DEFAULT_ESTIMATE', '2h')

    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    @classmethod
    def validate(cls):
        """
        Validate required configuration parameters.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not cls.JIRA_SERVER:
            return False, "JIRA_SERVER is required"

        if not cls.JIRA_SERVER.startswith(('http://', 'https://')):
            return False, "JIRA_SERVER must start with http:// or https://"

        if cls.FLASK_PORT < 1 or cls.FLASK_PORT > 65535:
            return False, "FLASK_PORT must be between 1 and 65535"

        return True, None

    @classmethod
    def get_config_summary(cls):
        """
        Get a summary of current configuration (without sensitive data).

        Returns:
            dict: Configuration summary
        """
        return {
            'jira_server': cls.JIRA_SERVER,
            'jira_pat_configured': False,  # Always false as we're not using a default PAT
            'custom_field_id': cls.CUSTOM_FIELD_ID,
            'custom_field_value': cls.CUSTOM_FIELD_VALUE,
            'default_estimate': cls.DEFAULT_ESTIMATE,
            'flask_host': cls.FLASK_HOST,
            'flask_port': cls.FLASK_PORT,
            'debug': cls.DEBUG
        }
