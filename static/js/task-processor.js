// Task processor frontend logic
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('processForm');
    const errorDiv = document.getElementById('error');
    const resultsDiv = document.getElementById('results');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Get form values
        const storyKey = document.getElementById('storyKey').value.trim();
        const jiraPat = document.getElementById('jiraPat').value.trim();

        // Validate story key format
        if (!storyKey || !storyKey.match(/^[A-Z]+-[0-9]+$/)) {
            showError('Invalid story key format. Expected format: PROJ-123');
            return;
        }

        if (!jiraPat) {
            showError('Jira Personal Access Token is required');
            return;
        }

        // Hide previous results/errors
        errorDiv.style.display = 'none';
        resultsDiv.style.display = 'none';

        // Show loading
        showLoading();

        try {
            const response = await fetch('/api/process-tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    story_key: storyKey,
                    jira_pat: jiraPat
                })
            });

            const data = await response.json();

            hideLoading();

            if (!response.ok || !data.success) {
                showError(data.error || 'An error occurred while processing tasks');
                return;
            }

            // Check if we have results or just a background processing message
            if (data.results && data.summary) {
                // Display results for synchronous processing
                displayResults(data.results, data.summary);
                showToast('Tasks processed successfully!', 'success');
            } else if (data.message) {
                // Display background processing message
                displayBackgroundProcessingMessage(storyKey);
                showToast('Tasks are being processed in the background!', 'success');
            }

        } catch (error) {
            hideLoading();
            showError(`Network error: ${error.message}`);
        }
    });

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        showToast(message, 'error');
    }

    function displayResults(results, summary) {
        // Build summary HTML
        let html = `
            <div class="summary">
                <h3>Summary</h3>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <strong>${summary.total}</strong> Total Subtasks
                    </div>
                    <div class="summary-stat">
                        <strong>${summary.processed}</strong> Processed
                    </div>
                    <div class="summary-stat">
                        <strong>${summary.skipped}</strong> Skipped
                    </div>
                </div>
            </div>
        `;

        // Build results HTML
        html += '<h3>Details</h3>';

        if (results.length === 0) {
            html += '<p>No subtasks found.</p>';
        } else {
            results.forEach(result => {
                const statusClass = result.status;
                const statusIcon = {
                    'success': '✓',
                    'skipped': '⊘',
                    'error': '✗'
                }[result.status] || '•';

                html += `
                    <div class="result-item ${statusClass}">
                        <h4>${statusIcon} ${result.subtask_key}</h4>
                        <p><strong>Status:</strong> ${result.current_status}</p>
                        ${result.assignee ? `<p><strong>Assignee:</strong> ${result.assignee}</p>` : ''}
                        <p><strong>Message:</strong> ${result.message}</p>
                        ${result.actions && result.actions.length > 0 ? `
                            <p><strong>Actions Taken:</strong></p>
                            <ul>
                                ${result.actions.map(action => `<li>${action}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                `;
            });
        }

        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
        errorDiv.style.display = 'none';
    }

    function displayBackgroundProcessingMessage(storyKey) {
        let html = `
            <div class="summary">
                <h3>Tasks Processing</h3>
                <div class="processing-message">
                    <p>Your tasks for story <strong>${storyKey}</strong> are being processed in the background.</p>
                    <p>You can safely navigate away from this page. The processing will continue on the server.</p>
                    <p>Check Jira for the latest status of your tasks.</p>
                </div>
            </div>
        `;

        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
        errorDiv.style.display = 'none';
    }
});
