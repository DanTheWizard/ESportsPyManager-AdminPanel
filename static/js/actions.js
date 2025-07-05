// Helpers

// Use the dynamically injected list of actions
const actionsWithArgument = window.ACTIONS_WITH_ARGUMENT || [];

// Update the shouldShowArgBox function
function shouldShowArgBox(action) {
  return actionsWithArgument.includes(action);
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
function createDeviceRow(device) {
  const tr = document.createElement('tr');
  tr.setAttribute('data-machine-id', device.machine_id);

  // Generate options dynamically from ACTIONS_LIST
  const actionOptions = window.ACTIONS_LIST.map(action =>
    `<option value="${action}">${action}</option>`
  ).join("");

  tr.innerHTML = `
    <td>
      <label class="container">
        <input type="checkbox" name="selected_devices" value="${device.machine_id}" class="device-checkbox">                              
          <svg viewBox="0 0 96 96" height="20px" width="20px">
            <path d="M 0 16 V 56 A 8 8 90 0 0 8 64 H 56 A 8 8 90 0 0 64 56 V 8 A 8 8 90 0 0 56 0 H 8 A 8 8 90 0 0 0 8 V 16 L 32 48 L 64 16 V 8 A 8 8 90 0 0 56 0 H 8 A 8 8 90 0 0 0 8 V 56 A 8 8 90 0 0 8 64 H 56 A 8 8 90 0 0 64 56 V 16" pathLength="575.0541381835938" class="path" transform="translate(10,10)"></path>
          </svg>
      </label></td>
    <td>${device.nickname}</td>
    <td>${device.tag}</td>
    <td>${device.machine_id}</td>
    <td>
      <select class="action-dropdown">
        ${actionOptions}
      </select>
    </td>
    <td><input type="text" class="arg-box" autocomplete="off" disabled placeholder="Optional Argument"></td>
    <td>
      <button type="button" class="execute-btn" data-machine-id="${device.machine_id}" data-nickname="${device.nickname}">Execute</button>
    </td>
  `;
  return tr;
}

function handleEmptyDeviceTable(tbody) {
  const existing = tbody.querySelectorAll('tr[data-machine-id]');
  const placeholder = tbody.querySelector('tr[data-empty-placeholder]');

  if (existing.length === 0 && !placeholder) {
    const tr = document.createElement("tr");
    tr.setAttribute("data-empty-placeholder", "true");
    tr.innerHTML = "<td colspan='7' style='text-align: center;'>No online registered devices found.</td>";
    tbody.appendChild(tr);
  } else if (existing.length > 0 && placeholder) {
    placeholder.remove();
  }
}


function updateDeviceTable() {
  fetch(window.FLASK_ROUTES.api_device_statuses)
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById('device-table-body');
      const currentRows = new Map();
      tbody.querySelectorAll('tr[data-machine-id]').forEach(row => {
        currentRows.set(row.getAttribute('data-machine-id'), row);
      });

      const seenOnline = new Set();
      const nowOnline = data.statuses.filter(d => d.online);
      const nowOffline = data.statuses.filter(d => !d.online);

      nowOnline.forEach(device => {
        seenOnline.add(device.machine_id);
        if (!currentRows.has(device.machine_id)) {
          const tr = createDeviceRow(device);
          tbody.appendChild(tr);
        }
      });

      // Remove rows that are no longer online
      currentRows.forEach((row, id) => {
        if (!seenOnline.has(id)) row.remove();
      });

      // Show "no online devices" message if applicable
      handleEmptyDeviceTable(tbody);

      // Offline list rendering
      const ul = document.getElementById('offline-list');
      ul.innerHTML = '';
      if (nowOffline.length === 0) {
        ul.innerHTML = '<li>None — all registered devices are online.</li>';
      } else {
        nowOffline.forEach(d => {
          const li = document.createElement('li');
          const lastSeen = d.last_active ? new Date(d.last_active).toLocaleString() : 'unknown';
          li.textContent = `${d.nickname} – last seen at ${lastSeen}`;
          ul.appendChild(li);
        });
      }

      rebindDropdowns();
      rebindPerDeviceExecute();
    })
    .catch(err => {
      alert(`❌ Failed to fetch device statuses: ${err}`);
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
