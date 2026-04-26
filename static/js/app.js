(function () {
  const state = {
    profile: null,
    queries: [],
    recommendations: [],
    pipeline: null
  };

  const alertEl = document.getElementById("alert");
  const formEl = document.getElementById("profile-form");
  const queriesBodyEl = document.getElementById("queries-body");
  const recommendationsGridEl = document.getElementById("recommendations-grid");

  const statProfile = document.getElementById("stat-profile");
  const statQueries = document.getElementById("stat-queries");
  const statVisible = document.getElementById("stat-visible");
  const statAvg = document.getElementById("stat-avg");

  const pipelineId = document.getElementById("pipeline-id");
  const pipelineStatus = document.getElementById("pipeline-status");
  const pipelineDiscovered = document.getElementById("pipeline-discovered");
  const pipelineScored = document.getElementById("pipeline-scored");

  const minScoreEl = document.getElementById("min-score");
  const statusEl = document.getElementById("visibility-status");

  function showAlert(message, kind) {
    alertEl.className = `alert ${kind || "info"}`;
    alertEl.textContent = message;
  }

  function clearAlert() {
    alertEl.className = "alert hidden";
    alertEl.textContent = "";
  }

  async function request(url, options) {
    const response = await fetch(url, options);
    const payload = await response.json();

    if (!response.ok || payload.success === false) {
      throw new Error(payload?.error?.message || `Request failed: ${response.status}`);
    }
    return payload.data;
  }

  function profileUuid() {
    return state.profile && state.profile.profile_uuid;
  }

  function ensureProfile() {
    if (!profileUuid()) {
      throw new Error("Create a profile first.");
    }
  }

  function updateStats() {
    statProfile.textContent = profileUuid() || "-";
    statQueries.textContent = String(state.queries.length || state.profile?.stats?.total_queries || 0);
    statVisible.textContent = String(state.queries.filter((q) => q.domain_visible).length);
    statAvg.textContent = String(state.profile?.stats?.avg_opportunity_score ?? "N/A");
  }

  function updatePipeline() {
    pipelineId.textContent = state.pipeline?.pipeline_id || "-";
    pipelineStatus.textContent = state.pipeline?.status || "-";
    pipelineDiscovered.textContent = String(state.pipeline?.queries_discovered || 0);
    pipelineScored.textContent = String(state.pipeline?.queries_scored || 0);
  }

  function renderQueries() {
    if (!state.queries.length) {
      queriesBodyEl.innerHTML = '<tr><td colspan="6">No queries loaded.</td></tr>';
      return;
    }

    queriesBodyEl.innerHTML = state.queries
      .map(
        (q) => `
        <tr>
          <td>${q.query_text}</td>
          <td>${q.estimated_search_volume}</td>
          <td>${q.competitive_difficulty}</td>
          <td>${q.opportunity_score}</td>
          <td>${q.domain_visible ? "Yes" : "No"}</td>
          <td><button data-recheck="${q.query_uuid}">Recheck</button></td>
        </tr>
      `
      )
      .join("");
  }

  function renderRecommendations() {
    if (!state.recommendations.length) {
      recommendationsGridEl.innerHTML = "<p>No recommendations yet.</p>";
      return;
    }

    recommendationsGridEl.innerHTML = state.recommendations
      .map(
        (rec) => `
        <article class="recommendation-card">
          <h4>${rec.title}</h4>
          <p><strong>Type:</strong> ${rec.content_type}</p>
          <p><strong>Priority:</strong> ${rec.priority}</p>
          <p class="muted">Target Query: ${rec.target_query_uuid}</p>
        </article>
      `
      )
      .join("");
  }

  function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.tab === tabName);
    });
    document.getElementById("overview-panel").classList.toggle("hidden", tabName !== "overview");
    document.getElementById("queries-panel").classList.toggle("hidden", tabName !== "queries");
    document.getElementById("recommendations-panel").classList.toggle("hidden", tabName !== "recommendations");
  }

  async function fetchQueries() {
    ensureProfile();
    const params = new URLSearchParams();
    if (minScoreEl.value.trim()) params.set("min_score", minScoreEl.value.trim());
    if (statusEl.value) params.set("status", statusEl.value);
    const qs = params.toString();
    const data = await request(`/api/v1/profiles/${profileUuid()}/queries${qs ? `?${qs}` : ""}`);
    state.queries = data.items || [];
    renderQueries();
    updateStats();
  }

  async function fetchRecommendations() {
    ensureProfile();
    const data = await request(`/api/v1/profiles/${profileUuid()}/recommendations`);
    state.recommendations = data.items || [];
    renderRecommendations();
  }

  async function withLoading(fn) {
    showAlert("Working...", "info");
    try {
      await fn();
      clearAlert();
    } catch (err) {
      showAlert(err.message, "error");
    }
  }

  formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(formEl);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      domain: String(formData.get("domain") || "").trim(),
      industry: String(formData.get("industry") || "").trim(),
      description: String(formData.get("description") || "").trim(),
      competitors: String(formData.get("competitors") || "")
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean)
    };

    await withLoading(async () => {
      state.profile = await request("/api/v1/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      state.queries = [];
      state.recommendations = [];
      state.pipeline = null;
      updateStats();
      updatePipeline();
      renderQueries();
      renderRecommendations();
      switchTab("overview");
    });
  });

  document.getElementById("refresh-profile").addEventListener("click", () =>
    withLoading(async () => {
      ensureProfile();
      state.profile = await request(`/api/v1/profiles/${profileUuid()}`);
      updateStats();
    })
  );

  document.getElementById("run-pipeline").addEventListener("click", () =>
    withLoading(async () => {
      ensureProfile();
      state.pipeline = await request(`/api/v1/profiles/${profileUuid()}/run`, { method: "POST" });
      updatePipeline();
      await fetchQueries();
      await fetchRecommendations();
      switchTab("queries");
    })
  );

  document.getElementById("fetch-queries").addEventListener("click", () =>
    withLoading(async () => {
      await fetchQueries();
      switchTab("queries");
    })
  );

  document.getElementById("fetch-recommendations").addEventListener("click", () =>
    withLoading(async () => {
      await fetchRecommendations();
      switchTab("recommendations");
    })
  );

  document.getElementById("apply-filters").addEventListener("click", () =>
    withLoading(async () => {
      await fetchQueries();
    })
  );

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });

  queriesBodyEl.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-recheck]");
    if (!button) return;
    const queryUuid = button.getAttribute("data-recheck");
    withLoading(async () => {
      await request(`/api/v1/queries/${queryUuid}/recheck`, { method: "POST" });
      await fetchQueries();
    });
  });
})();
