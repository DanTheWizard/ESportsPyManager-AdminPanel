// Helpers
function shouldShowArgBox(action) {
  return ["shutdown", "say"].includes(action);
}

function toggleArgBox(argBox, action) {
  const visible = shouldShowArgBox(action);
  argBox.disabled = !visible;
  if (visible) {
    argBox.setAttribute("name", "argument");
  } else {
    argBox.value = "";
    argBox.removeAttribute("name");
  }
}

function getRowElements(dropdown) {
  const row = dropdown.closest("tr");
  return {
    row,
    argBox: row.querySelector(".arg-box"),
    action: dropdown.value
  };
}

// Checkbox: Select All Handler
document.getElementById('select_all').addEventListener('change', function () {
  const isChecked = this.checked;
  document.querySelectorAll('.device-checkbox').forEach(cb => cb.checked = isChecked);
});

// Checkbox: Sync 'Select All' checkbox
document.addEventListener('change', function (e) {
  if (e.target.classList.contains('device-checkbox')) {
    const all = document.querySelectorAll('.device-checkbox');
    const checked = document.querySelectorAll('.device-checkbox:checked');
    document.getElementById('select_all').checked = all.length === checked.length;
  }
});

// Dropdown: Single-device dropdown change
function bindActionDropdown(dropdown) {
  dropdown.addEventListener("change", () => {
    const { argBox, action } = getRowElements(dropdown);
    toggleArgBox(argBox, action);
  });
}

// Bulk Dropdown Handler
document.getElementById("bulk_action").addEventListener("change", function () {
  toggleArgBox(document.getElementById("bulk_argument"), this.value);
});

document.getElementById("bulk_execute").addEventListener("click", function () {
  const action = document.getElementById("bulk_action").value;
  const argument = document.getElementById("bulk_argument").value || "";
  const selectedDevices = Array.from(document.querySelectorAll(".device-checkbox:checked"))
    .map(cb => cb.value);

  if (selectedDevices.length === 0 || action === "none") {
    alert("⚠️ Please select at least one device and a valid action.");
    return;
  }

  const form = new URLSearchParams();
  selectedDevices.forEach(id => form.append("selected_devices", id));
  form.append("bulk_action", action);
  form.append("bulk_argument", argument);

  fetch(window.FLASK_ROUTES.send_action, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  })
  .then(response => {
    if (response.redirected) {
      // 🔁 Redirect manually to the Flask redirect URL
      window.location.href = response.url;
    } else {
      // You can parse text or add better fallback
      return response.text().then(text => {
        console.warn("Unexpected response:", text);
        alert("⚠️ Bulk action submitted, but server returned an unexpected response.");
      });
    }
  })
  .catch(err => {
    alert(`❌ Request failed: ${err}`);
  });
});




// Update Device Table
function updateDeviceTable() {
  fetch(window.FLASK_ROUTES.api_device_statuses)
    .then(r => r.json())
    .then(data => {
      const tbody = document.getElementById('device-table-body');
      const currentRows = new Map();
      tbody.querySelectorAll('tr[data-machine-id]').forEach(row => {
        currentRows.set(row.getAttribute('data-machine-id'), row);
      });

      const seenOnline = new Set();
      const nowOnline = data.statuses.filter(d => d.online);
      const nowOffline = data.statuses.filter(d => !d.online);

      nowOnline.forEach(d => {
        seenOnline.add(d.machine_id);
        if (!currentRows.has(d.machine_id)) {
          const tr = document.createElement('tr');
          tr.setAttribute('data-machine-id', d.machine_id);
          tr.innerHTML = `
            <td><input type="checkbox" name="selected_devices" value="${d.machine_id}" class="device-checkbox"></td>
            <td>${d.nickname}</td>
            <td>${d.tag}</td>
            <td>${d.machine_id}</td>
            <td>
              <select class="action-dropdown">
                <option value="none">none</option>
                <option value="test">test</option>
                <option value="shutdown">shutdown</option>
                <option value="say">say</option>
                <option value="MCEdu">MCEdu</option>
                <option value="ID">ID</option>
              </select>
            </td>
            <td><input type="text" class="arg-box" autocomplete="off" disabled placeholder="Optional Argument"></td>
            <td>
              <button type="button" class="execute-btn" data-machine-id="${d.machine_id}" data-nickname="${d.nickname}">Execute</button>
            </td>
          `;
          tbody.appendChild(tr);
        }
      });

      currentRows.forEach((row, id) => {
        if (!seenOnline.has(id)) row.remove();
      });

      rebindDropdowns();
      rebindPerDeviceExecute();

      const ul = document.getElementById('offline-list');
      ul.innerHTML = '';
      if (nowOffline.length === 0) {
        ul.innerHTML = '<li>None — all registered devices are online.</li>';
      } else {
        nowOffline.forEach(d => {
          const li = document.createElement('li');
          const last = d.last_active ? new Date(d.last_active).toLocaleTimeString() : 'unknown';
          li.textContent = `${d.nickname} – last seen at ${last}`;
          ul.appendChild(li);
        });
      }
    });
}

// Rebinding logic
function rebindDropdowns() {
  document.querySelectorAll('.action-dropdown').forEach(bindActionDropdown);
}

function rebindPerDeviceExecute() {
  const tbody = document.getElementById('device-table-body');
  if (tbody.dataset.bound === "true") return;
  tbody.dataset.bound = "true";

  tbody.addEventListener('click', function (e) {
    const btn = e.target.closest('.execute-btn');
    if (!btn) return;

    const row = btn.closest("tr");
    const machineId = btn.dataset.machineId;
    const nickname = btn.dataset.nickname || machineId;
    const action = row.querySelector('.action-dropdown').value;
    const argument = row.querySelector('.arg-box')?.value || "";

    const form = new URLSearchParams();
    form.append('machine_id', machineId);
    form.append('action', action);
    form.append('argument', argument);

    fetch(window.FLASK_ROUTES.send_action_device, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString()
    })
    .then(r => r.json())
    .then(json => {
      alert(json.status === 'success'
        ?`✅ Sent "${json.sent}" to ${nickname}`
        :`⚠️ Error: ${json.message || 'unknown error'}`
      );
    })
    .catch(err => alert(`❌ Request failed: ${err}`));
  });
}

// Init
setInterval(updateDeviceTable, window.REFRESH_TIMEOUT);
updateDeviceTable();
