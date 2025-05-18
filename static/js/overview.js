function refreshOverview() {
    fetch(window.FLASK_ROUTES.api_overview_data)
        .then(r => r.json())
        .then(data => {
            const onlineBody = document.getElementById("overview-online-body");
            const offlineList = document.getElementById("overview-offline-list");

            // Separate devices by online state
            const online = data.devices.filter(d => d.online);
            const offline = data.devices.filter(d => !d.online);

            // Update online table
            onlineBody.innerHTML = "";
            if (online.length === 0) {
                onlineBody.innerHTML = "<tr><td colspan='6'>No online registered devices found.</td></tr>";
            } else {
                online.forEach(d => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                    <td>${d.nickname}</td>
                    <td>${d.cpu}</td>
                    <td>${d.ram}</td>
                    <td>${d.user}</td>
                    <td>${d.app}</td>
                    `;
                    onlineBody.appendChild(tr);
                });
            }

            // Update offline list
            offlineList.innerHTML = "";
            if (offline.length === 0) {
                offlineList.innerHTML = "<li>None — all registered devices are online.</li>";
            } else {
                offline.forEach(d => {
                     const lastSeen = d.last_active
                        ? new Date(d.last_active).toLocaleTimeString()
                        : 'unknown';
                    const li = document.createElement("li");
                    li.textContent = `${d.nickname} – last seen at ${lastSeen}`;
                    offlineList.appendChild(li);
                });
            }
        })
    .catch(err => {
        console.error("Failed to fetch overview data:", err);
    });
}


refreshOverview();
setInterval(refreshOverview, window.REFRESH_TIMEOUT);
