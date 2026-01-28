// Subtask creator frontend logic
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createForm');
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
            const response = await fetch('/api/create-subtasks', {
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
                showError(data.error || 'An error occurred while creating subtasks');
                return;
            }

            // Display results
            displayResults(data.created, data.summary);
            showToast('Subtasks created successfully!', 'success');

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

    function displayResults(created, summary) {
        // Build summary HTML
        let html = `
            <div class="summary">
                <h3>Summary</h3>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <strong>${summary.total}</strong> Total Subtasks
                    </div>
                    <div class="summary-stat">
                        <strong>${summary.created}</strong> Created
                    </div>
                    ${summary.failed > 0 ? `
                        <div class="summary-stat">
                            <strong>${summary.failed}</strong> Failed
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        // Build results HTML
        html += '<h3>Created Subtasks</h3>';

        if (created.length === 0) {
            html += '<p>No subtasks were created.</p>';
        } else {
            created.forEach(item => {
                const statusClass = item.status;
                const statusIcon = item.status === 'success' ? '✓' : '✗';

                html += `
                    <div class="result-item ${statusClass}">
                        <h4>${statusIcon} ${item.summary}</h4>
                        ${item.key ? `<p><strong>Key:</strong> ${item.key}</p>` : ''}
                        <p><strong>Status:</strong> ${item.status}</p>
                        <p><strong>Message:</strong> ${item.message}</p>
                    </div>
                `;
            });
        }

        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
        errorDiv.style.display = 'none';
    }
});
