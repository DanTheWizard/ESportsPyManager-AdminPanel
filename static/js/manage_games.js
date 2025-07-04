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
            statusMessage.textContent = 'Status updated successfully!';
        } else {
            statusMessage.textContent = 'Failed to update status.';
        }
    })
    .catch(() => {
        statusMessage.textContent = 'Error updating status.';
    });
});