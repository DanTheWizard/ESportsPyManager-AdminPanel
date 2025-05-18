document.addEventListener("DOMContentLoaded", function () {
    const dropdowns = document.querySelectorAll('.action-dropdown');


    document.getElementById('select_all').addEventListener('change', function () {
      const isAll = this.checked;

      // Get ALL current checkboxes (including dynamically added ones)
      document.querySelectorAll('.device-checkbox').forEach(cb => {
        cb.checked = isAll;
      });
    });

    document.addEventListener('change', function (e) {
      if (e.target.classList.contains('device-checkbox')) {
        const all = document.querySelectorAll('.device-checkbox');
        const checked = document.querySelectorAll('.device-checkbox:checked');

        document.getElementById('select_all').checked = (all.length === checked.length);
      }
    });



    // Show/hide argument field based on selected action
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener("change", () => {
            const row = dropdown.closest("tr");
            const argBox = row.querySelector(".arg-box");
            const selected = dropdown.value;

            if (["shutdown", "say"].includes(selected) && !dropdown.disabled) {
                argBox.style.display = "inline-block";
            } else {
                argBox.style.display = "none";
                argBox.value = "";
            }
        });
    });

    // Bulk argument box visibility
    const bulkDropdown = document.getElementById("bulk_action");
    const bulkArg = document.getElementById("bulk_argument");
    bulkDropdown.addEventListener("change", () => {
        if (["shutdown", "say"].includes(bulkDropdown.value)) {
            bulkArg.style.display = "inline-block";
        } else {
            bulkArg.style.display = "none";
            bulkArg.value = "";
        }
    });

    // Fix individual dropdown behavior
    document.querySelectorAll(".action-dropdown").forEach(dropdown => {
        dropdown.addEventListener("change", () => {
            const row = dropdown.closest("tr");
            const argBox = row.querySelector(".arg-box");
            const selected = dropdown.value;
            if (["shutdown", "say"].includes(selected)) {
                argBox.style.display = "inline-block";
                argBox.setAttribute("name", "argument");
            } else {
                argBox.style.display = "none";
                argBox.removeAttribute("name");
            }
        });
    });


    function updateDeviceTable() {
      fetch(window.FLASK_ROUTES.api_device_statuses)
        .then(r => r.json())
        .then(data => {
          const tbody = document.getElementById('device-table-body');
          const currentRows = new Map();
          tbody.querySelectorAll('tr[data-machine-id]').forEach(row => {
            const id = row.getAttribute('data-machine-id');
            currentRows.set(id, row);
          });

          const seenOnline = new Set();
          const nowOnline = data.statuses.filter(d => d.online);
          const nowOffline = data.statuses.filter(d => !d.online);

          // Add missing online rows
          nowOnline.forEach(d => {
            seenOnline.add(d.machine_id);
            if (!currentRows.has(d.machine_id)) {
              const tr = document.createElement('tr');
              tr.setAttribute('data-machine-id', d.machine_id);
              tr.innerHTML = `
                <td><input type="checkbox" name="selected_devices" value="${d.machine_id}" class="device-checkbox"></td>
                <td>${d.nickname}</td>
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
                <td><input type="text" class="arg-box" style="display:none;"></td>
                <td>
                  <button type="button" class="execute-btn" data-machine-id="${d.machine_id}" data-nickname="${d.nickname}">Execute</button>
                </td>
              `;
              tbody.appendChild(tr);
            }
          });

          // Remove rows that are no longer online
          currentRows.forEach((row, id) => {
            if (!seenOnline.has(id)) {
              row.remove();
            }
          });

          // Rebind only if anything changed
          rebindActionDropdowns();
          rebindPerDeviceExecute();

          // Update offline list
          const ul = document.getElementById('offline-list');
          ul.innerHTML = '';
          if (nowOffline.length === 0) {
            ul.innerHTML = '<li>None — all registered devices are online.</li>';
          } else {
            nowOffline.forEach(d => {
              const li = document.createElement('li');
              const last = d.last_active
                ? new Date(d.last_active).toLocaleTimeString()
                : 'unknown';
              li.textContent = `${d.nickname} – last seen at ${last}`;
              ul.appendChild(li);
            });
          }
        });
    }


    function rebindActionDropdowns() {
      document.querySelectorAll('.action-dropdown').forEach(dropdown => {
        dropdown.addEventListener("change", () => {
          const row = dropdown.closest("tr");
          const argBox = row.querySelector(".arg-box");
          const selected = dropdown.value;

          if (["shutdown", "say"].includes(selected)) {
            argBox.style.display = "inline-block";
          } else {
            argBox.style.display = "none";
            argBox.value = "";
          }
        });
      });
    }

    function rebindPerDeviceExecute() {
      const tbody = document.getElementById('device-table-body');

      // Only bind once
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
          if (json.status === 'success') {
            alert(`✅ Sent "${json.sent}" to ${nickname}`);
          } else {
            alert(`⚠️ Error: ${json.message || 'unknown error'}`);
          }
        })
        .catch(err => {
          alert(`❌ Request failed: ${err}`);
        });
      });
    }


    setInterval(updateDeviceTable, 5000);
    updateDeviceTable();

});