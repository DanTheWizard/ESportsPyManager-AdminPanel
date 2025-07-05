const fields = ['enable', 'Epic', 'Steam', 'Battle', 'Riot'];
const statusMessage = document.getElementById('status-message');

// Fetch current status and set checkboxes
fetch('/api/games_status')
    .then(response => response.json())
    .then(data => {
        fields.forEach(field => {
            const checkbox = document.getElementById(field);
            if (checkbox) {
                checkbox.checked = !!data[field];
            }
        });
    })
    .catch(() => {
        statusMessage.textContent = 'Failed to load current status.';
    });

// Handle update button click
document.getElementById('update-status-btn').addEventListener('click', function () {
    const payload = {};
    fields.forEach(field => {
        const checkbox = document.getElementById(field);
        payload[field] = checkbox ? checkbox.checked : false;
    });

    fetch('/api/games_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showStatusMessage('Status updated successfully!');
        } else {
            showStatusMessage('Failed to update status.', true);
        }
    })
    .catch(() => {
        showStatusMessage('Error updating status.', true);
    });
});



function showStatusMessage(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.classList.remove('hidden', 'error', 'success');
    statusMessage.classList.add(isError ? 'error' : 'success');

    // Remove after 3 seconds
    setTimeout(() => {
        statusMessage.classList.add('hidden');
    }, 3000);
}

const newText = "Enable Kill Tool"; // Replace with desired text
document.querySelectorAll('.text-label-enable').forEach(element => {
    element.textContent = newText;
});
