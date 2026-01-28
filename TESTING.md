# Testing Guide

## Running Tests

### Run All Tests

```bash
cd jira-automation-web-ui
pytest
```

### Run with Coverage

```bash
pytest --cov=services --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Run Specific Test Files

```bash
# Test configuration
pytest tests/test_config.py

# Test Jira client
pytest tests/test_jira_client.py

# Test task processor
pytest tests/test_task_processor.py

# Test subtask creator
pytest tests/test_subtask_creator.py

# Test Flask app
pytest tests/test_app.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test

```bash
pytest tests/test_config.py::TestConfig::test_validate_success
```

## Manual Testing Checklist

### Prerequisites

1. Have a valid Jira server accessible
2. Have a valid Personal Access Token
3. Have a test story with subtasks
4. Configure environment variables for testing

### Test Scenarios

#### 1. Application Startup

- [ ] Application starts without errors
- [ ] Configuration validation passes
- [ ] Access URL is logged
- [ ] Health endpoint returns 200

```bash
python app.py
curl http://localhost:5000/api/health
```

#### 2. Landing Page

- [ ] Navigate to http://localhost:5000
- [ ] Page loads correctly
- [ ] Navigation links work
- [ ] Both feature cards are displayed
- [ ] Responsive on mobile

#### 3. Process Tasks Feature

**Test Case 3.1: Valid Story with Assigned Subtasks**

- [ ] Navigate to "Process Tasks" page
- [ ] Enter valid story key (e.g., PROJ-123)
- [ ] Optionally enter PAT
- [ ] Click "Process Tasks"
- [ ] Loading spinner appears
- [ ] Results display correctly
- [ ] Summary shows correct counts
- [ ] Each subtask shows actions taken
- [ ] Success toast notification appears

**Test Case 3.2: Story with No Assigned Subtasks**

- [ ] Enter story key with no assigned subtasks
- [ ] Submit form
- [ ] Results show all subtasks skipped
- [ ] Message indicates "Not assigned to me"

**Test Case 3.3: Invalid Story Key**

- [ ] Enter invalid story key (e.g., "invalid")
- [ ] Submit form
- [ ] Validation error appears
- [ ] Form does not submit

**Test Case 3.4: Non-existent Story**

- [ ] Enter non-existent story key (e.g., PROJ-99999)
- [ ] Submit form
- [ ] Error message displays
- [ ] Error indicates story not found

**Test Case 3.5: Invalid PAT**

- [ ] Enter valid story key
- [ ] Enter invalid PAT
- [ ] Submit form
- [ ] Authentication error displays

**Test Case 3.6: Already Completed Subtasks**

- [ ] Enter story with completed subtasks
- [ ] Submit form
- [ ] Results show subtasks skipped
- [ ] Message indicates "Already Completed"

#### 4. Create Subtasks Feature

**Test Case 4.1: Valid Story**

- [ ] Navigate to "Create Subtasks" page
- [ ] Enter valid story key
- [ ] Optionally enter PAT
- [ ] Click "Create Subtasks"
- [ ] Loading spinner appears
- [ ] Results display 7 created subtasks
- [ ] Each subtask shows key and summary
- [ ] Summary shows 7 created, 0 failed
- [ ] Success toast notification appears

**Test Case 4.2: Invalid Story Key**

- [ ] Enter invalid story key
- [ ] Submit form
- [ ] Validation error appears

**Test Case 4.3: Non-existent Story**

- [ ] Enter non-existent story key
- [ ] Submit form
- [ ] Error message displays

**Test Case 4.4: Insufficient Permissions**

- [ ] Use PAT without create permission
- [ ] Submit form
- [ ] Permission error displays

#### 5. Error Handling

**Test Case 5.1: Network Error**

- [ ] Stop Jira server or disconnect network
- [ ] Try to process tasks
- [ ] Network error message displays

**Test Case 5.2: Server Error**

- [ ] Simulate server error (if possible)
- [ ] Error message displays clearly
- [ ] Application doesn't crash

#### 6. Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

#### 7. Mobile Responsiveness

Test on:
- [ ] iPhone (Safari)
- [ ] Android (Chrome)
- [ ] Tablet (iPad)

Check:
- [ ] Navigation menu works
- [ ] Forms are usable
- [ ] Results display correctly
- [ ] Toast notifications appear

#### 8. Concurrent Users

- [ ] Open application in multiple browsers
- [ ] Submit requests simultaneously
- [ ] Both requests complete successfully
- [ ] No conflicts or errors

## Performance Testing

### Load Test with Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 100 -c 10 http://localhost:5000/api/health

# Test with POST (create test.json first)
ab -n 10 -c 2 -p test.json -T application/json http://localhost:5000/api/process-tasks
```

### Expected Performance

- Health endpoint: < 50ms response time
- Process tasks: < 5s for 10 subtasks
- Create subtasks: < 10s for 7 subtasks

## Security Testing

### Test Cases

1. **SQL Injection** (N/A - no direct SQL)
2. **XSS Prevention**
   - [ ] Try entering `<script>alert('xss')</script>` in story key
   - [ ] Verify it's escaped in output

3. **CSRF** (Consider adding CSRF tokens for production)

4. **PAT Exposure**
   - [ ] Check that PAT never appears in logs
   - [ ] Check that PAT never appears in responses
   - [ ] Check browser dev tools for PAT in requests

5. **Input Validation**
   - [ ] Test with very long story keys
   - [ ] Test with special characters
   - [ ] Test with empty values

## Troubleshooting Test Failures

### Import Errors

```bash
# Ensure you're in the right directory
cd jira-automation-web-ui

# Install test dependencies
pip install -r requirements.txt
```

### Mock Errors

If mocks aren't working:
```bash
# Reinstall pytest and mock
pip install --upgrade pytest pytest-mock
```

### Coverage Not Working

```bash
# Install coverage plugin
pip install pytest-cov
```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest --cov=services --cov=app
```

## Test Data

### Sample Story Keys

For testing, create stories with:
- At least 3 subtasks
- Mix of Open, In Progress, and Completed statuses
- Some assigned to you, some to others

### Sample PAT

Generate a test PAT in Jira:
1. Go to Profile → Personal Access Tokens
2. Create new token with appropriate permissions
3. Use for testing (rotate regularly)
