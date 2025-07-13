/**
 * Fetch and refresh the list of unregistered devices.
 */
function refreshUnregisteredDevices() {
  fetch(window.FLASK_ROUTES.api_unregistered_devices)
    .then(res => res.json())
    .then(data => {
      const tbody = document.querySelector("table.unregistered_online tbody");

      const savedState = cacheInputState(tbody);
      const currentRows = getCurrentRows(tbody);
      const newIds = new Set();

      removePlaceholders(tbody);

      const elementToRemove = document.getElementById('loading_online_placeholder');
      if (elementToRemove) { // Check if the element exists before attempting to remove it
        elementToRemove.remove();
      }

      data.unregistered.forEach(device => {
        newIds.add(device.machine_id);
        const saved = savedState[device.machine_id] || {};
        const existingRow = currentRows.get(device.machine_id);
        const isFocused = existingRow?.querySelector('input[name="nickname"]') === document.activeElement;

        if (existingRow && isFocused) return; // Don't overwrite active user input

        const newRow = createUnregisteredRow(device, data.tags, saved);
        replaceOrInsertRow(tbody, newRow, existingRow);
      });

      removeStaleRows(currentRows, newIds);

      if (newIds.size === 0) {
        addEmptyUnregisteredPlaceholder(tbody);
      }

      bindRegisterButtons();
    })
    .catch(err => {
      console.error("Failed to fetch unregistered devices:", err);
      const tbody = document.querySelector("table.unregistered_online tbody");
      tbody.innerHTML = `<tr><td colspan="4">Error loading devices</td></tr>`;
    });
}

/**
 * Returns a map of machine_id to <tr> for the current unregistered device table.
 */
function getCurrentRows(tbody) {
  const map = new Map();
  tbody.querySelectorAll("tr[data-machine-id]").forEach(tr => {
    map.set(tr.getAttribute("data-machine-id"), tr);
  });
  return map;
}

/**
 * Saves the current input state of nickname and tag for each device row.
 */
function cacheInputState(tbody) {
  const state = {};
  tbody.querySelectorAll("tr[data-machine-id]").forEach(tr => {
    const id = tr.getAttribute("data-machine-id");
    state[id] = {
      nickname: tr.querySelector('input[name="nickname"]')?.value || "",
      tag: tr.querySelector('select[name="tag"]')?.value || ""
    };
  });
  return state;
}

/**
 * Removes rows no longer present in the updated device list.
 */
function removeStaleRows(currentRows, validIds) {
  currentRows.forEach((row, id) => {
    if (!validIds.has(id)) row.remove();
  });
}

/**
 * Removes any placeholder rows.
 */
function removePlaceholders(tbody) {
  tbody.querySelectorAll("tr[data-placeholder]").forEach(row => row.remove());
}

/**
 * Appends or replaces a row in the table depending on whether it already exists.
 */
function replaceOrInsertRow(tbody, newRow, existingRow) {
  if (existingRow) {
    tbody.replaceChild(newRow, existingRow);
  } else {
    tbody.appendChild(newRow);
  }
}

/**
 * Creates a table row for an unregistered device.
 */
function createUnregisteredRow(device, tags, saved) {
  const tr = document.createElement("tr");
  tr.setAttribute("data-machine-id", device.machine_id);

  const tagOptions = tags.map(tag => {
    const selected = tag === saved.tag ? "selected" : "";
    return `<option value="${tag}" ${selected}>${tag}</option>`;
  }).join("");

  tr.innerHTML = `
    <td>
      <button type="button" class="identify-btn"
          data-machine-id="${device.machine_id}"
          title="Make this PC identify itself">
          Identify
      </button>
      ${device.machine_id}
    </td>
    <td>${device.hostname}</td>
    <td>
      <select name="tag">${tagOptions}</select>
    </td>
    <td>
      <input type="text" name="nickname" placeholder="Enter nickname" value="${saved.nickname || ""}" required>
      <input type="hidden" name="machine_id" value="${device.machine_id}">
      <button class="register-btn" type="button">Register</button>
    </td>
  `;
  return tr;
}

/**
 * Shows a placeholder row if there are no unregistered devices.
 */
function addEmptyUnregisteredPlaceholder(tbody) {
  tbody.innerHTML = `<tr data-placeholder="true"><td colspan="4" style="text-align: center">No Unregistered Devices</td></tr>`;
}

/**
 * Attach click handlers to all "Register" buttons.
 */
function bindRegisterButtons() {
  document.querySelectorAll(".register-btn").forEach(button => {
    button.addEventListener("click", () => {
      const tr = button.closest("tr");
      const nickname = tr.querySelector('input[name="nickname"]').value.trim();
      const tag = tr.querySelector('select[name="tag"]').value;
      const machine_id = tr.querySelector('input[name="machine_id"]').value;

      if (!nickname) {
        alert("Please enter a nickname.");
        return;
      }

      const formData = new URLSearchParams();
      formData.append("machine_id", machine_id);
      formData.append("nickname", nickname);
      formData.append("tag", tag);

      fetch(window.FLASK_ROUTES.register_from_manage, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString()
      })
      .then(res => {
        if (!res.ok) throw new Error("Failed to register");
        refreshUnregisteredDevices(); // Refresh the table
        refreshRegisteredDevices();
      })
      .catch(err => {
        console.error("Registration failed:", err);
        alert("❌ Failed to register device.");
      });
    });
  });
}

/**
 * Refresh the list of registered devices and update the table.
 */
function refreshRegisteredDevices() {
  fetch("/api/registered_devices")
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById("registered-table-body");
      tbody.innerHTML = "";

      if (!data.registered || data.registered.length === 0) {
        tbody.innerHTML = `<tr><td style='text-align: center' colspan="5">No registered devices.</td></tr>`;
        return;
      }

      data.registered.forEach(device => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${device.nickname}</td>
          <td>${device.machine_id}</td>
          <td>${device.registered_at}</td>
          <td>${device.tag}</td>
          <td>
            <form method="POST" action="/api/deregister">
              <input type="hidden" name="machine_id" value="${device.machine_id}">
              <button type="submit">Remove (Unregister)</button>
            </form>
          </td>
        `;
        tbody.appendChild(tr);
      });
    })
    .catch(err => {
      console.error("Failed to refresh registered devices:", err);
    });
}

// === Auto-refresh loop ===
refreshUnregisteredDevices();
refreshRegisteredDevices();
setInterval(refreshUnregisteredDevices, window.REFRESH_TIMEOUT);
setInterval(refreshRegisteredDevices, window.REFRESH_TIMEOUT);

// Identify Button Handler
document.addEventListener("click", function (event) {
  if (!event.target.classList.contains("identify-btn")) return;

  const machineId = event.target.dataset.machineId;

  const form = new URLSearchParams();
  form.append("machine_id", machineId);
  form.append("action", "ID");
  form.append("argument", "");

  fetch(window.SEND_ACTION_DEVICE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: form.toString()
  })
  .then(r => r.json())
  .then(json => {
    if (json.status === "success") {
      alert(`✅ Identify signal sent to ${machineId}`);
    } else {
      alert(`⚠️ Error: ${json.message || 'Unknown error'}`);
    }
  })
  .catch(err => {
    alert(`❌ Request failed: ${err}`);
  });
});