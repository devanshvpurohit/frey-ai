/**
 * FREY AI - Edge Agricultural Dashboard Client
 * High-frequency telemetry polling, dynamic UI updates, and REST API controller.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let streamPaused = false;
  let historyOffset = 0;
  const historyLimit = 15;
  let currentTotalHistory = 0;

  // DOM Elements - Metrics
  const metricCamBadge = document.getElementById("metric-cam-badge");
  const metricCamRes = document.getElementById("metric-cam-res");
  const metricCamDevice = document.getElementById("metric-cam-device");
  const metricModelBackend = document.getElementById("metric-model-backend");
  const metricFps = document.getElementById("metric-fps");
  const metricLatency = document.getElementById("metric-latency");
  const metricCpu = document.getElementById("metric-cpu");
  const metricCpuBadge = document.getElementById("metric-cpu-badge");
  const metricTemp = document.getElementById("metric-temp");
  const metricRam = document.getElementById("metric-ram");
  const metricRamMb = document.getElementById("metric-ram-mb");
  const metricTotalDet = document.getElementById("metric-total-det");
  const metricHealthyRatio = document.getElementById("metric-healthy-ratio");
  const globalStatusDot = document.getElementById("global-status-dot");

  // DOM Elements - Stream & Live
  const mjpegStream = document.getElementById("mjpeg-stream");
  const streamOverlayNotice = document.getElementById("stream-overlay-notice");
  const livePillsContainer = document.getElementById("live-pills-container");
  const btnOverlayToggle = document.getElementById("btn-overlay-toggle");
  const btnPauseStream = document.getElementById("btn-pause-stream");
  const btnFullscreen = document.getElementById("btn-fullscreen");
  const btnSnapshotTop = document.getElementById("btn-snapshot-top");
  const btnToggleCamera = document.getElementById("btn-toggle-camera");
  const camToggleText = document.getElementById("cam-toggle-text");

  // DOM Elements - Crop Analysis
  const healthBadgeStatus = document.getElementById("health-badge-status");
  const diagCropName = document.getElementById("diag-crop-name");
  const diagDiseaseName = document.getElementById("diag-disease-name");
  const diagConfValue = document.getElementById("diag-conf-value");
  const diagScientific = document.getElementById("diag-scientific");
  const diagRecommendation = document.getElementById("diag-recommendation");

  // DOM Elements - History
  const historyTableBody = document.getElementById("history-table-body");
  const filterCrop = document.getElementById("filter-crop");
  const filterStatus = document.getElementById("filter-status");
  const filterSearchInput = document.getElementById("filter-search-input");
  const btnRefreshHistory = document.getElementById("btn-refresh-history");
  const btnExportCsv = document.getElementById("btn-export-csv");
  const paginationInfo = document.getElementById("pagination-info");
  const btnPrevPage = document.getElementById("btn-prev-page");
  const btnNextPage = document.getElementById("btn-next-page");

  // DOM Elements - Settings & Telemetry
  const settingsForm = document.getElementById("settings-form");
  const confSlider = document.getElementById("conf-slider");
  const confVal = document.getElementById("conf-val");
  const rateSlider = document.getElementById("rate-slider");
  const rateVal = document.getElementById("rate-val");
  const cameraSelect = document.getElementById("camera-select");
  const resSelect = document.getElementById("res-select");
  const autoSaveCheck = document.getElementById("auto-save-check");

  const teleCpuVal = document.getElementById("tele-cpu-val");
  const teleCpuBar = document.getElementById("tele-cpu-bar");
  const teleRamVal = document.getElementById("tele-ram-val");
  const teleRamBar = document.getElementById("tele-ram-bar");
  const teleBackendVal = document.getElementById("tele-backend-val");
  const teleTempVal = document.getElementById("tele-temp-val");
  const teleReconnectsVal = document.getElementById("tele-reconnects-val");

  // DOM Elements - Modal
  const snapshotModal = document.getElementById("snapshot-modal");
  const modalImg = document.getElementById("modal-img");
  const modalTitle = document.getElementById("modal-title");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalDownloadLink = document.getElementById("modal-download-link");

  // ==========================================
  //            TELEMETRY POLLING
  // ==========================================

  async function pollStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) return;
      const data = await res.json();

      // Camera status
      if (data.camera) {
        if (data.camera.mock_mode) {
          metricCamBadge.textContent = "SIMULATED";
          metricCamBadge.className = "badge badge-lime";
        } else if (data.camera.connected) {
          metricCamBadge.textContent = "ACTIVE";
          metricCamBadge.className = "badge badge-lime";
        } else {
          metricCamBadge.textContent = "OFFLINE";
          metricCamBadge.className = "badge badge-danger";
        }
        metricCamRes.textContent = `${data.camera.width} × ${data.camera.height}`;
        metricCamDevice.textContent = `${data.camera.device} (${data.camera.fps_actual || 0} FPS)`;
        teleReconnectsVal.textContent = data.camera.reconnect_attempts || 0;
      }

      // Model & Inference
      if (data.model) {
        metricModelBackend.textContent = (data.model.backend || "ONNX").toUpperCase();
        metricFps.textContent = data.model.estimated_fps || "0.0";
        metricLatency.textContent = data.model.avg_latency_ms || "0.0";
        teleBackendVal.textContent = data.model.backend === "onnxruntime" ? "ONNX Runtime CPU" : "OpenCV DNN CPU";
      }

      // System Telemetry
      if (data.system) {
        const cpu = data.system.cpu_percent || 0;
        metricCpu.textContent = cpu;
        teleCpuVal.textContent = `${cpu}%`;
        teleCpuBar.style.width = `${Math.min(100, cpu)}%`;

        const ram = data.system.ram_percent || 0;
        metricRam.textContent = ram;
        metricRamMb.textContent = data.system.ram_used_mb || "--";
        teleRamVal.textContent = `${ram}% (${data.system.ram_used_mb || 0} MB)`;
        teleRamBar.style.width = `${Math.min(100, ram)}%`;

        const temp = data.system.temp_c;
        if (temp !== null && temp !== undefined) {
          metricTemp.textContent = temp;
          teleTempVal.innerHTML = `${temp} &deg;C`;
          if (temp > 70) {
            metricTemp.style.color = "var(--accent-red)";
          } else {
            metricTemp.style.color = "inherit";
          }
        } else {
          metricTemp.textContent = "N/A";
          teleTempVal.textContent = "N/A (Host Emulation)";
        }
      }

      // Aggregate Stats
      if (data.stats) {
        metricTotalDet.textContent = data.stats.total_detections || 0;
        metricHealthyRatio.textContent = `${data.stats.healthy_ratio || 0}%`;
      }

      // Global status indicator
      globalStatusDot.style.backgroundColor = data.status === "healthy" ? "var(--accent-lime)" : "var(--accent-yellow)";

    } catch (err) {
      console.warn("Status poll error:", err);
      globalStatusDot.style.backgroundColor = "var(--accent-red)";
    }
  }

  // ==========================================
  //          LIVE DETECTIONS POLLING
  // ==========================================

  async function pollLiveDetections() {
    try {
      const res = await fetch("/api/detections");
      if (!res.ok) return;
      const data = await res.json();
      const detections = data.detections || [];
      const meta = data.metadata || {};

      // 1. Update live pills on stream footer
      if (detections.length === 0) {
        livePillsContainer.innerHTML = '<span class="pill pill-neutral">Scanning camera view... (no disease symptoms detected)</span>';
      } else {
        livePillsContainer.innerHTML = detections.map(d => {
          const cls = d.is_healthy ? "pill-healthy" : "pill-disease";
          const icon = d.is_healthy ? "✓" : "⚠";
          return `<span class="pill ${cls}"><strong>${icon} ${d.crop}:</strong> ${d.disease} (${d.confidence_percent})</span>`;
        }).join("");
      }

      // 2. Update Crop Analysis section
      if (detections.length > 0) {
        // Pick highest confidence detection
        const primary = detections[0];
        diagCropName.textContent = primary.crop;
        diagDiseaseName.textContent = primary.disease;
        diagConfValue.textContent = primary.confidence_percent;
        diagScientific.textContent = primary.scientific_name ? `Pathogen / Species: ${primary.scientific_name}` : "";
        diagRecommendation.textContent = primary.recommendation || "Maintain routine canopy scouting.";

        if (meta.diseased_count > 0) {
          healthBadgeStatus.textContent = "DISEASE DETECTED";
          healthBadgeStatus.className = "panel-badge-health badge-danger";
        } else {
          healthBadgeStatus.textContent = "HEALTHY CANOPY";
          healthBadgeStatus.className = "panel-badge-health badge-lime";
        }
      } else {
        diagCropName.textContent = "No Canopy Identified";
        diagDiseaseName.textContent = "Awaiting foliage detection in camera frame";
        diagConfValue.textContent = "--%";
        diagScientific.textContent = "";
        diagRecommendation.textContent = meta.general_recommendation || "Position crop canopy within 30–50 cm of the camera lens under indirect natural illumination.";
        healthBadgeStatus.textContent = "SCANNING";
        healthBadgeStatus.className = "panel-badge-health";
      }

    } catch (err) {
      console.warn("Live detections poll error:", err);
    }
  }

  // ==========================================
  //             DETECTION HISTORY
  // ==========================================

  async function loadHistory() {
    try {
      const crop = filterCrop.value;
      const status = filterStatus.value;
      const search = filterSearchInput.value.trim();

      let url = `/api/history?limit=${historyLimit}&offset=${historyOffset}`;
      if (crop && crop !== "all") url += `&crop=${encodeURIComponent(crop)}`;
      if (status === "diseased") url += `&is_healthy=0`;
      if (status === "healthy") url += `&is_healthy=1`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      currentTotalHistory = data.total;

      // Render table rows
      if (!data.records || data.records.length === 0) {
        historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No matching detection logs found.</td></tr>';
      } else {
        historyTableBody.innerHTML = data.records.map(r => {
          const statusBadge = r.is_healthy
            ? '<span class="badge badge-lime">Healthy</span>'
            : '<span class="badge badge-danger">Diseased</span>';
          const conf = Math.round(r.confidence * 100);
          const bboxStr = r.bbox ? `[${r.bbox.join(", ")}]` : "N/A";

          const snapHtml = r.image_path
            ? `<img src="${r.image_path}" class="table-thumbnail" data-src="${r.image_path}" data-title="${r.crop} - ${r.disease} (${conf}%)" alt="Thumb">`
            : '<span class="text-dim">No image</span>';

          return `
            <tr>
              <td class="text-dim" style="font-family: var(--font-mono);">${r.timestamp || "--"}</td>
              <td><strong>${r.crop}</strong></td>
              <td>${r.disease}</td>
              <td>${statusBadge}</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">${conf}%</td>
              <td class="text-dim text-sm" style="font-family: var(--font-mono);">${bboxStr}</td>
              <td>${snapHtml}</td>
            </tr>
          `;
        }).join("");

        // Attach click listener to thumbnails for modal preview
        document.querySelectorAll(".table-thumbnail").forEach(img => {
          img.addEventListener("click", () => {
            modalImg.src = img.getAttribute("data-src");
            modalTitle.textContent = img.getAttribute("data-title") || "Detection Snapshot";
            modalDownloadLink.href = img.getAttribute("data-src");
            snapshotModal.style.display = "flex";
          });
        });
      }

      // Update Pagination
      const start = currentTotalHistory === 0 ? 0 : historyOffset + 1;
      const end = Math.min(historyOffset + historyLimit, currentTotalHistory);
      paginationInfo.textContent = `Showing ${start}–${end} of ${currentTotalHistory} records`;
      btnPrevPage.disabled = historyOffset === 0;
      btnNextPage.disabled = historyOffset + historyLimit >= currentTotalHistory;

    } catch (err) {
      console.error("Failed to load history:", err);
      historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Error loading historical records.</td></tr>';
    }
  }

  // ==========================================
  //          SETTINGS & CONTROLS
  // ==========================================

  // Confidence slider live display
  confSlider.addEventListener("input", (e) => {
    confVal.textContent = `${Math.round(e.target.value * 100)}%`;
  });

  // Rate slider live display
  rateSlider.addEventListener("input", (e) => {
    rateVal.textContent = `${parseFloat(e.target.value).toFixed(1)} Hz`;
  });

  // Settings form submission
  settingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      conf_threshold: parseFloat(confSlider.value),
      inference_rate_hz: parseFloat(rateSlider.value),
      camera_device: cameraSelect.value,
      camera_res: resSelect.value,
      auto_save_history: autoSaveCheck.checked,
    };

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        showToast("Settings applied successfully!");
      }
    } catch (err) {
      showToast("Error updating settings", true);
    }
  });

  // Overlay Toggle Button
  let overlayEnabled = true;
  btnOverlayToggle.addEventListener("click", async () => {
    overlayEnabled = !overlayEnabled;
    btnOverlayToggle.classList.toggle("active", overlayEnabled);
    btnOverlayToggle.textContent = overlayEnabled ? "Overlay: ON" : "Overlay: OFF";
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ overlay_boxes: overlayEnabled }),
    });
  });

  // Pause / Resume Stream
  btnPauseStream.addEventListener("click", () => {
    streamPaused = !streamPaused;
    if (streamPaused) {
      mjpegStream.src = "";
      streamOverlayNotice.style.display = "flex";
      btnPauseStream.textContent = "Resume";
    } else {
      mjpegStream.src = `/video_feed?t=${Date.now()}`;
      streamOverlayNotice.style.display = "none";
      btnPauseStream.textContent = "Pause";
    }
  });

  // Snapshot Trigger
  btnSnapshotTop.addEventListener("click", async () => {
    btnSnapshotTop.disabled = true;
    try {
      const res = await fetch("/api/snapshot", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        showToast(`Snapshot captured (${data.detections_count} detections recorded)!`);
        loadHistory();
      } else {
        showToast("Snapshot failed: " + (data.error || "No frame"), true);
      }
    } catch (err) {
      showToast("Snapshot network error", true);
    } finally {
      btnSnapshotTop.disabled = false;
    }
  });

  // Camera Power Toggle
  let cameraActive = true;
  btnToggleCamera.addEventListener("click", async () => {
    const endpoint = cameraActive ? "/api/camera/stop" : "/api/camera/start";
    try {
      const res = await fetch(endpoint, { method: "POST" });
      if (res.ok) {
        cameraActive = !cameraActive;
        camToggleText.textContent = cameraActive ? "Active" : "Stopped";
        btnToggleCamera.className = cameraActive ? "btn btn-primary" : "btn btn-outline";
        showToast(`Camera ${cameraActive ? "resumed" : "stopped"}.`);
      }
    } catch (err) {
      showToast("Camera toggle failed", true);
    }
  });

  // Fullscreen
  btnFullscreen.addEventListener("click", () => {
    const el = document.getElementById("stream-container");
    if (!document.fullscreenElement) {
      el.requestFullscreen().catch(err => alert(err.message));
    } else {
      document.exitFullscreen();
    }
  });

  // Filter Listeners
  filterCrop.addEventListener("change", () => { historyOffset = 0; loadHistory(); });
  filterStatus.addEventListener("change", () => { historyOffset = 0; loadHistory(); });
  filterSearchInput.addEventListener("input", debounce(() => { historyOffset = 0; loadHistory(); }, 350));
  btnRefreshHistory.addEventListener("click", () => loadHistory());

  // Pagination Listeners
  btnPrevPage.addEventListener("click", () => {
    if (historyOffset >= historyLimit) {
      historyOffset -= historyLimit;
      loadHistory();
    }
  });

  btnNextPage.addEventListener("click", () => {
    if (historyOffset + historyLimit < currentTotalHistory) {
      historyOffset += historyLimit;
      loadHistory();
    }
  });

  // Export CSV
  btnExportCsv.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/history?limit=1000");
      const data = await res.json();
      if (!data.records || data.records.length === 0) {
        showToast("No records to export", true);
        return;
      }
      const headers = ["ID", "Timestamp", "Crop", "Disease", "Status", "Confidence", "Recommendation", "Image"];
      const rows = data.records.map(r => [
        r.id,
        `"${r.timestamp}"`,
        `"${r.crop}"`,
        `"${r.disease}"`,
        r.is_healthy ? "Healthy" : "Diseased",
        r.confidence,
        `"${(r.recommendation || '').replace(/"/g, '""')}"`,
        `"${r.image_path || ''}"`,
      ]);
      const csvContent = [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `frey_ai_detections_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast("CSV export generated!");
    } catch (err) {
      showToast("CSV export failed", true);
    }
  });

  // Modal Close
  modalCloseBtn.addEventListener("click", () => { snapshotModal.style.display = "none"; });
  snapshotModal.addEventListener("click", (e) => {
    if (e.target === snapshotModal) snapshotModal.style.display = "none";
  });

  // Toast Notification Helper
  function showToast(msg, isError = false) {
    const existing = document.getElementById("frey-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "frey-toast";
    toast.style.position = "fixed";
    toast.style.bottom = "24px";
    toast.style.right = "24px";
    toast.style.backgroundColor = isError ? "#ef4444" : "#22c55e";
    toast.style.color = isError ? "#ffffff" : "#05140b";
    toast.style.padding = "10px 18px";
    toast.style.borderRadius = "8px";
    toast.style.fontWeight = "700";
    toast.style.fontSize = "0.85rem";
    toast.style.boxShadow = "0 4px 15px rgba(0,0,0,0.5)";
    toast.style.zIndex = "9999";
    toast.style.animation = "fadeIn 0.2s ease";
    toast.textContent = msg;

    document.body.appendChild(toast);
    setTimeout(() => {
      if (toast) toast.remove();
    }, 3000);
  }

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Populate Camera Device dropdown from backend
  async function loadDevices() {
    try {
      const res = await fetch("/api/settings");
      if (!res.ok) return;
      const data = await res.json();
      if (data.available_devices && data.available_devices.length > 0) {
        cameraSelect.innerHTML = data.available_devices.map(d => {
          const val = d.path.startsWith("/dev/video") ? d.path : d.id;
          return `<option value="${val}">${d.name}</option>`;
        }).join("");
        if (data.settings && data.settings.camera_device) {
          cameraSelect.value = data.settings.camera_device;
        }
      }
    } catch (err) {
      console.warn("Could not load camera devices:", err);
    }
  }

  // Initialize
  loadDevices();
  pollStatus();
  pollLiveDetections();
  loadHistory();

  // Polling intervals
  setInterval(pollStatus, 1500);
  setInterval(pollLiveDetections, 1000);
});
