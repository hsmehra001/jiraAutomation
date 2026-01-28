"""Flask application for Jira Automation Web UI."""
import logging
from flask import Flask, render_template, request, jsonify
from jira import JIRAError
from config import Config
from services.jira_client import JiraClient
from services.task_processor import TaskProcessor
from services.subtask_creator import SubtaskCreator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Validate configuration on startup
is_valid, error = Config.validate()
if not is_valid:
    logger.error(f"Configuration error: {error}")
    raise ValueError(f"Configuration error: {error}")

logger.info("Configuration validated successfully")
logger.info(f"Application starting on {Config.FLASK_HOST}:{Config.FLASK_PORT}")


@app.route('/')
def index():
    """Landing page with navigation."""
    return render_template('index.html')


@app.route('/process-tasks')
def process_tasks_page():
    """Task processing page."""
    return render_template('process-tasks.html')


@app.route('/create-subtasks')
def create_subtasks_page():
    """Subtask creation page."""
    return render_template('create-subtasks.html')


@app.route('/api/process-tasks', methods=['POST'])
def api_process_tasks():
    """
    API endpoint to process tasks.

    Request JSON:
        {
            "story_key": "PROJ-123",
            "jira_pat": "required_token"
        }

    Response JSON:
        {
            "success": true,
            "results": [...],
            "summary": {...}
        }
    """
    try:
        data = request.get_json()

        if not data or 'story_key' not in data:
            return jsonify({
                'success': False,
                'error': 'story_key is required'
            }), 400

        story_key = data['story_key'].strip()

        # Make jira_pat mandatory
        if 'jira_pat' not in data or not data['jira_pat'].strip():
            return jsonify({
                'success': False,
                'error': 'Jira PAT is required'
            }), 400

        jira_pat = data['jira_pat'].strip()

        # Validate story key format
        if not story_key or '-' not in story_key:
            return jsonify({
                'success': False,
                'error': 'Invalid story key format. Expected format: PROJ-123'
            }), 400

        logger.info(f"Processing tasks for story: {story_key}")

        # Initialize Jira client and processor
        jira_client = JiraClient(Config.JIRA_SERVER, jira_pat)
        processor = TaskProcessor(jira_client)

        # Process subtasks
        result = processor.process_story_subtasks(story_key)

        return jsonify({
            'success': True,
            'results': result['results'],
            'summary': result['summary']
        })

    except JIRAError as e:
        logger.error(f"Jira API error: {e.text}")
        return jsonify({
            'success': False,
            'error': f'Jira API Error: {e.text}',
            'error_code': e.status_code
        }), e.status_code if hasattr(e, 'status_code') else 500

    except Exception as e:
        logger.exception("Unexpected error processing tasks")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/create-subtasks', methods=['POST'])
def api_create_subtasks():
    """
    API endpoint to create subtasks.

    Request JSON:
        {
            "story_key": "PROJ-123",
            "jira_pat": "required_token"
        }

    Response JSON:
        {
            "success": true,
            "created": [...],
            "summary": {...}
        }
    """
    try:
        data = request.get_json()

        if not data or 'story_key' not in data:
            return jsonify({
                'success': False,
                'error': 'story_key is required'
            }), 400

        story_key = data['story_key'].strip()

        # Make jira_pat mandatory
        if 'jira_pat' not in data or not data['jira_pat'].strip():
            return jsonify({
                'success': False,
                'error': 'Jira PAT is required'
            }), 400

        jira_pat = data['jira_pat'].strip()

        # Validate story key format
        if not story_key or '-' not in story_key:
            return jsonify({
                'success': False,
                'error': 'Invalid story key format. Expected format: PROJ-123'
            }), 400

        logger.info(f"Creating subtasks for story: {story_key}")

        # Initialize Jira client and creator
        jira_client = JiraClient(Config.JIRA_SERVER, jira_pat)
        creator = SubtaskCreator(
            jira_client,
            Config.CUSTOM_FIELD_ID,
            Config.CUSTOM_FIELD_VALUE,
            Config.DEFAULT_ESTIMATE
        )

        # Create subtasks
        result = creator.create_subtasks(story_key)

        return jsonify({
            'success': True,
            'created': result['created'],
            'summary': result['summary']
        })

    except JIRAError as e:
        logger.error(f"Jira API error: {e.text}")
        return jsonify({
            'success': False,
            'error': f'Jira API Error: {e.text}',
            'error_code': e.status_code
        }), e.status_code if hasattr(e, 'status_code') else 500

    except Exception as e:
        logger.exception("Unexpected error creating subtasks")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'config': Config.get_config_summary()
    })


if __name__ == '__main__':
    logger.info(f"Starting Flask application...")
    logger.info(f"Access the application at: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")

    try:
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.DEBUG
        )
    except OSError as e:
        if 'Address already in use' in str(e):
            logger.error(f"Port {Config.FLASK_PORT} is already in use. Please choose a different port.")
        else:
            logger.error(f"Failed to start application: {e}")
        raise
