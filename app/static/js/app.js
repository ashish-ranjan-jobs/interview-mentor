// The Interview Mentor AI — Client Studio Engine (10 Resume Tracks + 45 Skills)
document.addEventListener('DOMContentLoaded', () => {
  const basePath = window.location.pathname.startsWith('/interview') ? '/interview' : '';

  // State
  let resumeData = null;
  let allResumeTracks = [];
  let currentResumeFilter = 'all';
  let allSkills = [];
  let currentCategory = 'all';
  let activeSession = null;
  let activeSkill = null;
  let activeTrack = null;
  let customGeminiKey = localStorage.getItem('custom_gemini_key') || '';
  let selectedModel = localStorage.getItem('selected_gemini_model') || 'gemini-pro-latest';

  // Views & Mode Switcher
  const viewModeResumes = document.getElementById('view-mode-resumes');
  const viewModeSkills = document.getElementById('view-mode-skills');
  const resumesHubView = document.getElementById('resumes-hub-view');
  const catalogView = document.getElementById('catalog-view');
  const interviewView = document.getElementById('interview-view');

  // Resume Track Elements
  const resumeTracksGrid = document.getElementById('resume-tracks-grid');
  const filterResumesAll = document.getElementById('filter-resumes-all');
  const filterResumesJava = document.getElementById('filter-resumes-java');
  const filterResumesPython = document.getElementById('filter-resumes-python');
  const javaTracksSidebar = document.getElementById('java-tracks-sidebar');
  const pythonTracksSidebar = document.getElementById('python-tracks-sidebar');

  // Resume Modal Elements
  const resumeDetailsModal = document.getElementById('resume-details-modal');
  const closeResumeModalBtn = document.getElementById('close-resume-modal-btn');
  const resumeModalIcon = document.getElementById('resume-modal-icon');
  const resumeModalTitle = document.getElementById('resume-modal-title');
  const resumeModalSubtitle = document.getElementById('resume-modal-subtitle');
  const resumeModalStack = document.getElementById('resume-modal-stack');
  const resumeModalMetrics = document.getElementById('resume-modal-metrics');
  const resumeModalBullets = document.getElementById('resume-modal-bullets');
  const resumeModalQuestions = document.getElementById('resume-modal-questions');
  const modalLaunchGrill = document.getElementById('modal-launch-grill');
  const modalLaunchFull = document.getElementById('modal-launch-full');

  // General Skill Elements
  const skillsGrid = document.getElementById('skills-grid');
  const dynamicCategories = document.getElementById('dynamic-categories');
  const skillSearch = document.getElementById('skill-search');
  const currentFilterTitle = document.getElementById('current-filter-title');
  const filteredCount = document.getElementById('filtered-count');
  const allCountBadge = document.getElementById('all-count-badge');
  const modelSelect = document.getElementById('model-select');
  const logoutBtn = document.getElementById('logout-btn');

  // Sidebar Nav Tabs
  const tabNavResumes = document.getElementById('tab-nav-resumes');
  const tabNavCategories = document.getElementById('tab-nav-categories');
  const tabNavHistory = document.getElementById('tab-nav-history');
  const resumeTrackListContainer = document.getElementById('resume-track-list-container');
  const categoryListContainer = document.getElementById('category-list-container');
  const sessionHistoryContainer = document.getElementById('session-history-container');
  const sessionsList = document.getElementById('sessions-list');

  // Studio Elements
  const exitInterviewBtn = document.getElementById('exit-interview-btn');
  const activeSkillTitle = document.getElementById('active-skill-title');
  const activeSkillDiff = document.getElementById('active-skill-diff');
  const activeSkillRole = document.getElementById('active-skill-role');
  const phaseSelect = document.getElementById('phase-select');
  const messagesContainer = document.getElementById('messages-container');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const hintDropdownBtn = document.getElementById('hint-dropdown-btn');
  const hintMenu = document.getElementById('hint-menu');
  const diagramBtn = document.getElementById('diagram-btn');
  const evaluateBtn = document.getElementById('evaluate-btn');
  const insertScratchpadBtn = document.getElementById('insert-scratchpad-btn');
  const scratchpadCode = document.getElementById('scratchpad-code');
  const scratchpadLang = document.getElementById('scratchpad-lang');
  const sendScratchpadDirectBtn = document.getElementById('send-scratchpad-direct-btn');

  // Settings Modal Elements
  const openSettingsBtn = document.getElementById('open-settings-btn');
  const settingsModal = document.getElementById('settings-modal');
  const closeSettingsBtn = document.getElementById('close-settings-btn');
  const saveSettingsBtn = document.getElementById('save-settings-btn');
  const testKeyBtn = document.getElementById('test-key-btn');
  const customKeyInput = document.getElementById('custom-key-input');
  const keyTestFeedback = document.getElementById('key-test-feedback');
  const serverKeyStatus = document.getElementById('server-key-status');

  // Scorecard Modal Elements
  const scorecardModal = document.getElementById('scorecard-modal');
  const closeScorecardBtn = document.getElementById('close-scorecard-btn');
  const closeScorecardFooterBtn = document.getElementById('close-scorecard-footer-btn');
  const scorecardSkillTitle = document.getElementById('scorecard-skill-title');
  const scorecardScore = document.getElementById('scorecard-score');
  const scorecardRecommendation = document.getElementById('scorecard-recommendation');
  const scorecardSummary = document.getElementById('scorecard-summary');
  const scorecardRubricContainer = document.getElementById('scorecard-rubric-container');
  const scorecardStrengths = document.getElementById('scorecard-strengths');
  const scorecardGrowth = document.getElementById('scorecard-growth');

  // Configure Markdown
  marked.setOptions({
    gfm: true,
    breaks: true,
    highlight: function(code, lang) {
      if (Prism.languages[lang]) {
        return Prism.highlight(code, Prism.languages[lang], lang);
      }
      return code;
    }
  });

  if (modelSelect) {
    modelSelect.value = selectedModel;
    modelSelect.addEventListener('change', (e) => {
      selectedModel = e.target.value;
      localStorage.setItem('selected_gemini_model', selectedModel);
    });
  }

  if (customKeyInput) {
    customKeyInput.value = customGeminiKey;
  }

  // --- Auth Fetch Helpers ---
  function getAuthHeaders() {
    const token = localStorage.getItem('interview_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  }

  async function apiFetch(endpoint, options = {}) {
    const headers = { ...getAuthHeaders(), ...(options.headers || {}) };
    const res = await fetch(`${basePath}${endpoint}`, { ...options, headers });
    if (res.status === 401) {
      window.location.href = `${basePath}/login`;
      throw new Error('Unauthorized');
    }
    return res;
  }

  // --- Initialize App ---
  async function init() {
    await checkStatus();
    await loadResumeTracks();
    await loadCategories();
    await loadSkills();
    await loadSessions();
  }

  async function checkStatus() {
    try {
      const res = await apiFetch('/api/system/status');
      if (res.ok) {
        const data = await res.json();
        if (serverKeyStatus) {
          serverKeyStatus.textContent = data.default_key_masked || 'Configured';
        }
      }
    } catch (e) {
      console.warn('Status check failed', e);
    }
  }

  // --- Mode Switching (Resumes vs Domain Skills) ---
  viewModeResumes.addEventListener('click', () => {
    viewModeResumes.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white shadow-sm flex items-center gap-1.5 transition-all';
    viewModeSkills.className = 'px-3 py-1.5 rounded-lg text-slate-400 hover:text-white flex items-center gap-1.5 transition-all';
    resumesHubView.classList.remove('hidden');
    catalogView.classList.add('hidden');
    interviewView.classList.add('hidden');
    switchSidebarTab('resumes');
  });

  viewModeSkills.addEventListener('click', () => {
    viewModeSkills.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white shadow-sm flex items-center gap-1.5 transition-all';
    viewModeResumes.className = 'px-3 py-1.5 rounded-lg text-slate-400 hover:text-white flex items-center gap-1.5 transition-all';
    catalogView.classList.remove('hidden');
    resumesHubView.classList.add('hidden');
    interviewView.classList.add('hidden');
    switchSidebarTab('categories');
  });

  // --- Load Resume Tracks ---
  async function loadResumeTracks() {
    try {
      const res = await apiFetch('/api/resumes');
      if (!res.ok) return;
      resumeData = await res.json();
      allResumeTracks = resumeData.all_tracks || [];

      renderResumeSidebar();
      renderResumeTracks();
    } catch (e) {
      console.error('Failed to load resume tracks', e);
    }
  }

  function renderResumeSidebar() {
    javaTracksSidebar.innerHTML = '';
    pythonTracksSidebar.innerHTML = '';

    (resumeData.java_tracks || []).forEach(track => {
      const btn = document.createElement('button');
      btn.className = 'w-full text-left px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-slate-800/80 hover:text-white flex items-center justify-between transition-colors group';
      btn.innerHTML = `
        <span class="flex items-center gap-1.5 truncate">
          <span class="w-5 h-5 rounded bg-amber-500/20 text-amber-400 font-bold text-[10px] flex items-center justify-center">${track.id}</span>
          <span class="truncate">${track.subtitle}</span>
        </span>
        <i class="fa-solid fa-chevron-right text-[9px] text-slate-600 group-hover:text-amber-400"></i>
      `;
      btn.addEventListener('click', () => openResumeModal(track));
      javaTracksSidebar.appendChild(btn);
    });

    (resumeData.python_tracks || []).forEach(track => {
      const btn = document.createElement('button');
      btn.className = 'w-full text-left px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-slate-800/80 hover:text-white flex items-center justify-between transition-colors group';
      btn.innerHTML = `
        <span class="flex items-center gap-1.5 truncate">
          <span class="w-5 h-5 rounded bg-emerald-500/20 text-emerald-400 font-bold text-[10px] flex items-center justify-center">${track.id}</span>
          <span class="truncate">${track.subtitle}</span>
        </span>
        <i class="fa-solid fa-chevron-right text-[9px] text-slate-600 group-hover:text-emerald-400"></i>
      `;
      btn.addEventListener('click', () => openResumeModal(track));
      pythonTracksSidebar.appendChild(btn);
    });
  }

  function renderResumeTracks() {
    const q = (skillSearch.value || '').toLowerCase().trim();
    let filtered = allResumeTracks;

    if (currentResumeFilter === 'java') {
      filtered = filtered.filter(t => t.category === 'java');
    } else if (currentResumeFilter === 'python') {
      filtered = filtered.filter(t => t.category === 'python');
    }

    if (q) {
      filtered = filtered.filter(t =>
        t.title.toLowerCase().includes(q) ||
        t.subtitle.toLowerCase().includes(q) ||
        (t.target_roles || []).some(r => r.toLowerCase().includes(q)) ||
        (t.core_stack || []).some(s => s.toLowerCase().includes(q)) ||
        (t.key_metrics || []).some(m => m.toLowerCase().includes(q))
      );
    }

    resumeTracksGrid.innerHTML = '';

    filtered.forEach(track => {
      const card = document.createElement('div');
      const isJava = track.category === 'java';
      const themeBorder = isJava ? 'border-amber-500/30 hover:border-amber-500/60' : 'border-emerald-500/30 hover:border-emerald-500/60';
      const badgeBg = isJava ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';

      card.className = `bg-slate-900/90 border ${themeBorder} rounded-2xl p-6 flex flex-col justify-between transition-all duration-200 shadow-xl group`;

      card.innerHTML = `
        <div>
          <!-- Track Header Badges -->
          <div class="flex items-center justify-between gap-2 mb-3">
            <span class="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border ${badgeBg}">
              ${track.code} • ${isJava ? 'Java 21 / Spring Boot 3' : 'Python 3.11 / FastAPI & GenAI'}
            </span>
            <span class="text-[11px] font-semibold text-slate-400">
              ${track.target_roles[0]}
            </span>
          </div>

          <!-- Title -->
          <h3 class="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors mb-1">
            ${track.title}
          </h3>
          <div class="text-xs text-indigo-400 font-semibold mb-4">
            ${track.subtitle}
          </div>

          <!-- Key Metrics Badges -->
          <div class="mb-4 space-y-1.5">
            ${(track.key_metrics || []).slice(0, 3).map(m => `
              <div class="text-xs text-slate-300 flex items-start gap-2 bg-slate-950/70 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
                <i class="fa-solid fa-circle-check ${isJava ? 'text-amber-400' : 'text-emerald-400'} text-xs mt-0.5"></i>
                <span class="line-clamp-1">${m}</span>
              </div>
            `).join('')}
          </div>

          <!-- Core Stack Tags -->
          <div class="flex flex-wrap gap-1.5 mb-6">
            ${(track.core_stack || []).slice(0, 6).map(s => `
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60">
                ${s}
              </span>
            `).join('')}
            ${track.core_stack.length > 6 ? `<span class="text-[10px] text-slate-500 self-center">+${track.core_stack.length - 6} more</span>` : ''}
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
          <button class="open-qbank-btn px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer">
            <i class="fa-solid fa-book-open text-indigo-400"></i>
            <span>Question Bank (${track.top_interview_questions.length})</span>
          </button>

          <div class="flex items-center gap-2">
            <button class="grill-track-btn px-3 py-1.5 rounded-lg bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/20 flex items-center gap-1.5 transition-all cursor-pointer">
              <i class="fa-solid fa-fire"></i>
              <span>Grill Resume</span>
            </button>
            <button class="full-mock-btn px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all cursor-pointer">
              <i class="fa-solid fa-play text-[10px]"></i>
              <span>Full Mock</span>
            </button>
          </div>
        </div>
      `;

      card.querySelector('.open-qbank-btn').addEventListener('click', () => openResumeModal(track));
      card.querySelector('.grill-track-btn').addEventListener('click', () => startResumeMockInterview(track, 'grill'));
      card.querySelector('.full-mock-btn').addEventListener('click', () => startResumeMockInterview(track, 'full'));

      resumeTracksGrid.appendChild(card);
    });
  }

  // Filter Buttons
  filterResumesAll.addEventListener('click', () => setResumeFilter('all'));
  filterResumesJava.addEventListener('click', () => setResumeFilter('java'));
  filterResumesPython.addEventListener('click', () => setResumeFilter('python'));

  function setResumeFilter(filter) {
    currentResumeFilter = filter;
    [filterResumesAll, filterResumesJava, filterResumesPython].forEach(btn => {
      btn.className = 'resume-cat-filter px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-300 hover:text-white border border-slate-800 cursor-pointer';
    });
    if (filter === 'all') {
      filterResumesAll.className = 'resume-cat-filter px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white shadow-sm cursor-pointer';
    } else if (filter === 'java') {
      filterResumesJava.className = 'resume-cat-filter px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 text-white shadow-sm cursor-pointer';
    } else if (filter === 'python') {
      filterResumesPython.className = 'resume-cat-filter px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white shadow-sm cursor-pointer';
    }
    renderResumeTracks();
  }

  // --- Resume Details & Question Bank Modal ---
  function openResumeModal(track) {
    activeTrack = track;
    const isJava = track.category === 'java';

    resumeModalIcon.textContent = track.id;
    resumeModalIcon.className = `w-10 h-10 rounded-xl ${isJava ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'} border flex items-center justify-center text-lg font-bold`;

    resumeModalTitle.textContent = `${track.title} (${track.code})`;
    resumeModalSubtitle.textContent = track.subtitle;

    // Stack
    resumeModalStack.innerHTML = (track.core_stack || []).map(s => `
      <span class="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 border border-slate-700">
        ${s}
      </span>
    `).join('');

    // Metrics
    resumeModalMetrics.innerHTML = (track.key_metrics || []).map(m => `
      <div class="flex items-start gap-2 bg-slate-950 p-2 rounded-lg border border-slate-800">
        <i class="fa-solid fa-chart-line text-indigo-400 mt-0.5 text-xs"></i>
        <span>${m}</span>
      </div>
    `).join('');

    // Bullets
    resumeModalBullets.innerHTML = (track.experience_bullets || []).map(b => `
      <li class="leading-relaxed mb-1.5">${b}</li>
    `).join('');

    // Questions
    resumeModalQuestions.innerHTML = (track.top_interview_questions || []).map((item, idx) => `
      <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2">
        <div class="font-bold text-white flex items-start gap-2">
          <span class="w-5 h-5 rounded bg-indigo-600/30 text-indigo-300 flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">Q${idx+1}</span>
          <span class="leading-snug">${item.q}</span>
        </div>
        <div class="text-slate-400 pl-7 leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
          <strong class="text-slate-200 block mb-1">Architectural Defense & Key Answer Points:</strong>
          ${item.ideal_answer}
        </div>
      </div>
    `).join('');

    resumeDetailsModal.classList.remove('hidden');
  }

  closeResumeModalBtn.addEventListener('click', () => resumeDetailsModal.classList.add('hidden'));

  modalLaunchGrill.addEventListener('click', () => {
    resumeDetailsModal.classList.add('hidden');
    if (activeTrack) startResumeMockInterview(activeTrack, 'grill');
  });

  modalLaunchFull.addEventListener('click', () => {
    resumeDetailsModal.classList.add('hidden');
    if (activeTrack) startResumeMockInterview(activeTrack, 'full');
  });

  // --- Start Resume-Based Mock Interview ---
  async function startResumeMockInterview(track, mode = 'full') {
    activeTrack = track;
    activeSkill = {
      id: `resume_${track.id}`,
      title: `${track.title} (${track.code})`,
      role: track.target_roles[0],
      difficulty: 'Senior / Staff Bar Raiser',
      topic: track.subtitle,
      category: track.category
    };

    resumesHubView.classList.add('hidden');
    catalogView.classList.add('hidden');
    interviewView.classList.remove('hidden');

    activeSkillTitle.textContent = `${track.title} (${track.code})`;
    activeSkillDiff.textContent = mode === 'grill' ? '🔥 Bar Raiser Grill' : 'Senior Technical Loop';
    activeSkillDiff.className = mode === 'grill' ? 'text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30';
    activeSkillRole.textContent = `Target Role: ${track.target_roles[0]}`;
    phaseSelect.value = 'Phase 1: Warm-up & Clarification';

    // Set scratchpad default language
    scratchpadLang.value = track.category === 'java' ? 'java' : 'python';

    messagesContainer.innerHTML = `
      <div class="flex items-center justify-center h-48 text-slate-500 text-sm gap-3">
        <i class="fa-solid fa-circle-notch fa-spin text-indigo-400 text-xl"></i>
        <span>Summoning your ${mode === 'grill' ? 'Bar Raiser Interviewer' : 'Technical Lead'} for ${track.code}...</span>
      </div>
    `;

    try {
      const res = await apiFetch(`/api/resumes/${track.id}/mock`, {
        method: 'POST',
        body: JSON.stringify({
          mode,
          model: selectedModel,
          custom_key: customGeminiKey || null
        })
      });

      if (!res.ok) throw new Error('Failed to launch resume mock session');
      const data = await res.json();
      activeSession = data.session;

      messagesContainer.innerHTML = '';
      if (data.initial_message) {
        appendMessage(data.initial_message);
      }

      await loadSessions();
    } catch (e) {
      messagesContainer.innerHTML = `
        <div class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          <p class="font-bold mb-1">Failed to launch interview session:</p>
          <p class="text-xs">${e.message}</p>
          <button id="retry-session-btn" class="mt-3 px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-semibold">Retry</button>
        </div>
      `;
      document.getElementById('retry-session-btn')?.addEventListener('click', () => startResumeMockInterview(track, mode));
    }
  }

  // --- Domain Categories & Skills (45 Skills) ---
  async function loadCategories() {
    try {
      const res = await apiFetch('/api/categories');
      if (!res.ok) return;
      const categories = await res.json();

      dynamicCategories.innerHTML = '';
      categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.dataset.cat = cat.id;
        btn.className = 'cat-filter-btn w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/80 hover:text-white flex items-center justify-between transition-colors cursor-pointer';
        btn.innerHTML = `
          <span class="flex items-center gap-2 truncate">
            <i class="fa-solid ${cat.icon} text-slate-400 w-4"></i>
            <span class="truncate">${cat.title}</span>
          </span>
          <span class="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400">${cat.count}</span>
        `;
        btn.addEventListener('click', () => {
          viewModeSkills.click();
          setCategory(cat.id, cat.title);
        });
        dynamicCategories.appendChild(btn);
      });

      document.querySelector('[data-cat="all"]').addEventListener('click', () => {
        viewModeSkills.click();
        setCategory('all', 'All Domains');
      });
    } catch (e) {
      console.error('Failed to load categories', e);
    }
  }

  function setCategory(catId, catTitle = 'All Topics') {
    currentCategory = catId;
    currentFilterTitle.textContent = catTitle;

    document.querySelectorAll('.cat-filter-btn').forEach(b => {
      if (b.dataset.cat === catId) {
        b.className = 'cat-filter-btn w-full text-left px-3 py-2 rounded-lg text-xs font-medium bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-between';
      } else {
        b.className = 'cat-filter-btn w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/80 hover:text-white flex items-center justify-between transition-colors';
      }
    });

    renderSkills();
  }

  async function loadSkills() {
    try {
      const res = await apiFetch('/api/skills');
      if (!res.ok) return;
      allSkills = await res.json();
      if (allCountBadge) allCountBadge.textContent = allSkills.length;
      renderSkills();
    } catch (e) {
      console.error('Failed to load skills', e);
    }
  }

  function renderSkills() {
    const q = (skillSearch.value || '').toLowerCase().trim();
    let filtered = allSkills;

    if (currentCategory !== 'all') {
      filtered = filtered.filter(s => s.category === currentCategory);
    }

    if (q) {
      filtered = filtered.filter(s =>
        s.title.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        s.role.toLowerCase().includes(q) ||
        s.topic.toLowerCase().includes(q)
      );
    }

    if (filteredCount) filteredCount.textContent = `${filtered.length} skills`;
    skillsGrid.innerHTML = '';

    filtered.forEach(skill => {
      const card = document.createElement('div');
      card.className = 'bg-slate-900/80 hover:bg-slate-900 border border-slate-800/80 hover:border-indigo-500/40 rounded-xl p-5 flex flex-col justify-between transition-all duration-200 shadow-lg group';

      let diffColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      if (skill.difficulty.toLowerCase().includes('hard')) {
        diffColor = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      } else if (skill.difficulty.toLowerCase().includes('medium')) {
        diffColor = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      }

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between gap-2 mb-3">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 truncate">
              ${skill.category_badge || skill.category}
            </span>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded border ${diffColor}">
              ${skill.difficulty}
            </span>
          </div>

          <h4 class="font-bold text-white text-base group-hover:text-indigo-300 transition-colors line-clamp-1 mb-1">
            ${skill.title}
          </h4>

          <div class="text-xs text-indigo-400/90 font-medium mb-2 flex items-center gap-1.5 truncate">
            <i class="fa-solid fa-user-tie text-[10px] text-slate-500"></i>
            <span class="truncate">${skill.role}</span>
          </div>

          <p class="text-xs text-slate-400 line-clamp-3 mb-4 leading-relaxed">
            ${skill.description || 'Practice problem solving and design tradeoffs.'}
          </p>
        </div>

        <div class="pt-3 border-t border-slate-800/60 flex items-center justify-between">
          <span class="text-[11px] text-slate-500 truncate">
            <i class="fa-solid fa-tag text-[9px] mr-1"></i>${skill.topic}
          </span>
          <button class="start-skill-btn px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5 cursor-pointer">
            <span>Interview</span>
            <i class="fa-solid fa-arrow-right text-[10px]"></i>
          </button>
        </div>
      `;

      card.querySelector('.start-skill-btn').addEventListener('click', () => startDomainSkillInterview(skill));
      skillsGrid.appendChild(card);
    });
  }

  skillSearch.addEventListener('input', () => {
    renderResumeTracks();
    renderSkills();
  });

  // --- Start Domain Skill Interview ---
  async function startDomainSkillInterview(skill) {
    activeSkill = skill;
    catalogView.classList.add('hidden');
    resumesHubView.classList.add('hidden');
    interviewView.classList.remove('hidden');

    activeSkillTitle.textContent = skill.title;
    activeSkillDiff.textContent = skill.difficulty;
    activeSkillRole.textContent = `Target Role: ${skill.role}`;
    phaseSelect.value = 'Phase 1: Warm-up & Clarification';

    messagesContainer.innerHTML = `
      <div class="flex items-center justify-center h-48 text-slate-500 text-sm gap-3">
        <i class="fa-solid fa-circle-notch fa-spin text-indigo-400 text-xl"></i>
        <span>Summoning your ${skill.role} AI Interviewer...</span>
      </div>
    `;

    try {
      const res = await apiFetch('/api/sessions', {
        method: 'POST',
        body: JSON.stringify({
          skill_id: skill.id,
          model: selectedModel,
          custom_key: customGeminiKey || null
        })
      });

      if (!res.ok) throw new Error('Failed to start interview session');
      const data = await res.json();
      activeSession = data.session;

      messagesContainer.innerHTML = '';
      if (data.initial_message) {
        appendMessage(data.initial_message);
      }

      await loadSessions();
    } catch (e) {
      messagesContainer.innerHTML = `
        <div class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          <p class="font-bold mb-1">Failed to launch interview session:</p>
          <p class="text-xs">${e.message}</p>
        </div>
      `;
    }
  }

  // --- Resume Past Session ---
  async function resumeSession(sessionId) {
    catalogView.classList.add('hidden');
    resumesHubView.classList.add('hidden');
    interviewView.classList.remove('hidden');

    messagesContainer.innerHTML = `
      <div class="flex items-center justify-center h-48 text-slate-500 text-sm gap-3">
        <i class="fa-solid fa-circle-notch fa-spin text-indigo-400 text-xl"></i>
        <span>Loading interview session...</span>
      </div>
    `;

    try {
      const res = await apiFetch(`/api/sessions/${sessionId}`);
      if (!res.ok) throw new Error('Session not found');
      const data = await res.json();
      activeSession = data.session;
      activeSkill = data.skill;

      activeSkillTitle.textContent = activeSkill.title;
      activeSkillDiff.textContent = activeSkill.difficulty || 'Technical Loop';
      activeSkillRole.textContent = `Target Role: ${activeSkill.role || 'Senior Engineer'}`;
      phaseSelect.value = activeSession.phase || 'Phase 1: Warm-up & Clarification';

      messagesContainer.innerHTML = '';
      data.messages.forEach(msg => appendMessage(msg));
      scrollToBottom();
    } catch (e) {
      alert(`Error loading session: ${e.message}`);
      resumesHubView.classList.remove('hidden');
      interviewView.classList.add('hidden');
    }
  }

  // --- Message Appending ---
  function appendMessage(msg) {
    const isUser = msg.role === 'user';
    const bubbleWrapper = document.createElement('div');
    bubbleWrapper.className = `flex gap-3 max-w-4xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`;

    const avatar = document.createElement('div');
    avatar.className = `w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold ${
      isUser ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' : 'bg-slate-800 text-indigo-400 border border-slate-700'
    }`;
    avatar.innerHTML = isUser ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

    const body = document.createElement('div');
    body.className = `rounded-2xl p-4 text-sm leading-relaxed max-w-[85%] ${
      isUser
        ? 'bg-indigo-600/20 border border-indigo-500/30 text-white'
        : 'bg-slate-900 border border-slate-800 text-slate-200'
    }`;

    if (msg.action_type && msg.action_type !== 'chat') {
      const badge = document.createElement('div');
      badge.className = 'text-[10px] font-semibold uppercase tracking-wider mb-2 inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700';
      if (msg.action_type === 'hint') badge.innerHTML = '<i class="fa-regular fa-lightbulb text-amber-400"></i> Hint Guidance';
      else if (msg.action_type === 'diagram') badge.innerHTML = '<i class="fa-solid fa-diagram-project text-indigo-400"></i> Visual Architecture';
      else if (msg.action_type === 'evaluate') badge.innerHTML = '<i class="fa-solid fa-award text-emerald-400"></i> Scorecard Evaluation';
      else if (msg.action_type === 'advance') badge.innerHTML = '<i class="fa-solid fa-forward text-indigo-400"></i> Phase Transition';
      body.appendChild(badge);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'prose-chat text-xs sm:text-sm text-slate-200';
    contentDiv.innerHTML = marked.parse(msg.content);
    body.appendChild(contentDiv);

    bubbleWrapper.appendChild(avatar);
    bubbleWrapper.appendChild(body);
    messagesContainer.appendChild(bubbleWrapper);
    scrollToBottom();
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // --- Send Message & Stream SSE ---
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text || !activeSession) return;

    chatInput.value = '';
    sendBtn.disabled = true;

    appendMessage({
      role: 'user',
      content: text,
      action_type: 'chat'
    });

    const streamWrapper = document.createElement('div');
    streamWrapper.className = 'flex gap-3 max-w-4xl';
    streamWrapper.innerHTML = `
      <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold bg-slate-800 text-indigo-400 border border-slate-700">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="rounded-2xl p-4 text-sm leading-relaxed max-w-[85%] bg-slate-900 border border-slate-800 text-slate-200">
        <div class="prose-chat text-xs sm:text-sm text-slate-200 stream-target typing-cursor"></div>
      </div>
    `;
    messagesContainer.appendChild(streamWrapper);
    const streamTarget = streamWrapper.querySelector('.stream-target');
    scrollToBottom();

    let fullText = '';

    try {
      const response = await fetch(`${basePath}/api/sessions/${activeSession.id}/message`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          content: text,
          model: selectedModel,
          custom_key: customGeminiKey || null
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.text) {
                fullText += parsed.text;
                streamTarget.innerHTML = marked.parse(fullText);
                scrollToBottom();
              }
              if (parsed.error) {
                fullText += `\n\n> ⚠️ *${parsed.error}*`;
                streamTarget.innerHTML = marked.parse(fullText);
              }
            } catch (err) {}
          }
        }
      }

      streamTarget.classList.remove('typing-cursor');
      Prism.highlightAllUnder(streamWrapper);
    } catch (err) {
      streamTarget.classList.remove('typing-cursor');
      streamTarget.innerHTML = `<span class="text-rose-400">Connection error: ${err.message}</span>`;
    } finally {
      sendBtn.disabled = false;
      chatInput.focus();
    }
  });

  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });

  // --- Hints, Diagram, Advance ---
  hintDropdownBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    hintMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', () => {
    hintMenu.classList.add('hidden');
  });

  document.querySelectorAll('.hint-option').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      hintMenu.classList.add('hidden');
      const level = parseInt(btn.dataset.hintLevel, 10);
      if (!activeSession) return;

      appendMessage({
        role: 'user',
        content: `💡 [Requested Level ${level} Hint]`,
        action_type: 'hint'
      });

      await streamEndpoint(`/api/sessions/${activeSession.id}/hint`, {
        level,
        model: selectedModel,
        custom_key: customGeminiKey || null
      });
    });
  });

  diagramBtn.addEventListener('click', async () => {
    if (!activeSession) return;
    appendMessage({
      role: 'user',
      content: '📐 [Requested Architecture / ASCII Diagram]',
      action_type: 'diagram'
    });

    await streamEndpoint(`/api/sessions/${activeSession.id}/diagram`, {
      content: 'Request ASCII diagram',
      model: selectedModel,
      custom_key: customGeminiKey || null
    });
  });

  phaseSelect.addEventListener('change', async (e) => {
    const newPhase = e.target.value;
    if (!activeSession) return;

    appendMessage({
      role: 'user',
      content: `⏭️ [Advanced to ${newPhase}]`,
      action_type: 'advance'
    });

    await streamEndpoint(`/api/sessions/${activeSession.id}/advance`, {
      phase: newPhase,
      model: selectedModel,
      custom_key: customGeminiKey || null
    });
  });

  async function streamEndpoint(endpoint, payload) {
    const streamWrapper = document.createElement('div');
    streamWrapper.className = 'flex gap-3 max-w-4xl';
    streamWrapper.innerHTML = `
      <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold bg-slate-800 text-indigo-400 border border-slate-700">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="rounded-2xl p-4 text-sm leading-relaxed max-w-[85%] bg-slate-900 border border-slate-800 text-slate-200">
        <div class="prose-chat text-xs sm:text-sm text-slate-200 stream-target typing-cursor"></div>
      </div>
    `;
    messagesContainer.appendChild(streamWrapper);
    const streamTarget = streamWrapper.querySelector('.stream-target');
    scrollToBottom();

    let fullText = '';
    try {
      const response = await fetch(`${basePath}${endpoint}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.text) {
                fullText += parsed.text;
                streamTarget.innerHTML = marked.parse(fullText);
                scrollToBottom();
              }
            } catch (err) {}
          }
        }
      }
      streamTarget.classList.remove('typing-cursor');
      Prism.highlightAllUnder(streamWrapper);
    } catch (err) {
      streamTarget.classList.remove('typing-cursor');
      streamTarget.innerHTML = `<span class="text-rose-400">Stream error: ${err.message}</span>`;
    }
  }

  // --- Scratchpad Integration ---
  insertScratchpadBtn.addEventListener('click', () => {
    const code = scratchpadCode.value.trim();
    if (!code) return;
    const lang = scratchpadLang.value;
    const formatted = `\`\`\`${lang}\n${code}\n\`\`\``;
    chatInput.value = chatInput.value ? `${chatInput.value}\n\n${formatted}` : formatted;
    chatInput.focus();
  });

  sendScratchpadDirectBtn.addEventListener('click', () => {
    const code = scratchpadCode.value.trim();
    if (!code || !activeSession) return;
    const lang = scratchpadLang.value;
    chatInput.value = `Here is my code implementation:\n\n\`\`\`${lang}\n${code}\n\`\`\``;
    chatForm.dispatchEvent(new Event('submit'));
  });

  // --- Scorecard & Evaluation Modal ---
  evaluateBtn.addEventListener('click', async () => {
    if (!activeSession) return;

    evaluateBtn.disabled = true;
    evaluateBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i> <span>Evaluating...</span>';

    try {
      const res = await apiFetch(`/api/sessions/${activeSession.id}/evaluate`, {
        method: 'POST',
        body: JSON.stringify({
          content: 'Generate final scorecard',
          custom_key: customGeminiKey || null
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Evaluation failed');
      }

      const data = await res.json();
      displayScorecard(data.evaluation);
    } catch (e) {
      alert(`Scorecard Error: ${e.message}`);
    } finally {
      evaluateBtn.disabled = false;
      evaluateBtn.innerHTML = '<i class="fa-solid fa-award"></i> <span>Scorecard</span>';
    }
  });

  function displayScorecard(evaluation) {
    scorecardSkillTitle.textContent = `${activeSkill.title} • ${activeSkill.role}`;
    scorecardScore.textContent = evaluation.score || 80;
    scorecardRecommendation.textContent = evaluation.recommendation || 'Hire';

    const rec = (evaluation.recommendation || '').toLowerCase();
    if (rec.includes('strong hire')) {
      scorecardRecommendation.className = 'text-xl font-bold text-emerald-400';
    } else if (rec.includes('hire')) {
      scorecardRecommendation.className = 'text-xl font-bold text-indigo-400';
    } else {
      scorecardRecommendation.className = 'text-xl font-bold text-rose-400';
    }

    scorecardSummary.textContent = evaluation.summary || 'Solid overall technical demonstration.';

    scorecardRubricContainer.innerHTML = '';
    const rubric = evaluation.rubric_breakdown || {};
    const labels = {
      problem_solving: 'Problem Solving & Fundamentals',
      technical_competence: 'Technical Competence & Architecture',
      communication_collaboration: 'Communication & Collaboration',
      edge_cases_and_scale: 'Edge Cases & Scalability'
    };

    for (const [key, val] of Object.entries(rubric)) {
      const item = document.createElement('div');
      item.className = 'p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs';
      const label = labels[key] || key.replace('_', ' ').toUpperCase();
      const score = val.score || 75;
      const feedback = val.feedback || '';

      item.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-bold text-slate-200">${label}</span>
          <span class="font-bold text-indigo-400">${score}/100</span>
        </div>
        <div class="w-full bg-slate-800 h-1.5 rounded-full mb-1.5 overflow-hidden">
          <div class="bg-indigo-500 h-1.5 rounded-full" style="width: ${score}%"></div>
        </div>
        <p class="text-slate-400 text-[11px]">${feedback}</p>
      `;
      scorecardRubricContainer.appendChild(item);
    }

    scorecardStrengths.innerHTML = '';
    (evaluation.strengths || []).forEach(s => {
      const li = document.createElement('li');
      li.textContent = s;
      scorecardStrengths.appendChild(li);
    });

    scorecardGrowth.innerHTML = '';
    (evaluation.areas_for_growth || []).forEach(g => {
      const li = document.createElement('li');
      li.textContent = g;
      scorecardGrowth.appendChild(li);
    });

    scorecardModal.classList.remove('hidden');
  }

  closeScorecardBtn.addEventListener('click', () => scorecardModal.classList.add('hidden'));
  closeScorecardFooterBtn.addEventListener('click', () => scorecardModal.classList.add('hidden'));

  // --- Sidebar Tabs Switcher ---
  tabNavResumes.addEventListener('click', () => switchSidebarTab('resumes'));
  tabNavCategories.addEventListener('click', () => switchSidebarTab('categories'));
  tabNavHistory.addEventListener('click', () => switchSidebarTab('history'));

  function switchSidebarTab(tab) {
    [tabNavResumes, tabNavCategories, tabNavHistory].forEach(t => {
      t.className = 'pb-2 px-2 font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex-1 text-center transition-colors cursor-pointer';
    });
    resumeTrackListContainer.classList.add('hidden');
    categoryListContainer.classList.add('hidden');
    sessionHistoryContainer.classList.add('hidden');

    if (tab === 'resumes') {
      tabNavResumes.className = 'pb-2 px-2 font-medium border-b-2 border-indigo-500 text-white flex-1 text-center transition-colors cursor-pointer';
      resumeTrackListContainer.classList.remove('hidden');
    } else if (tab === 'categories') {
      tabNavCategories.className = 'pb-2 px-2 font-medium border-b-2 border-indigo-500 text-white flex-1 text-center transition-colors cursor-pointer';
      categoryListContainer.classList.remove('hidden');
    } else if (tab === 'history') {
      tabNavHistory.className = 'pb-2 px-2 font-medium border-b-2 border-indigo-500 text-white flex-1 text-center transition-colors cursor-pointer';
      sessionHistoryContainer.classList.remove('hidden');
      loadSessions();
    }
  }

  async function loadSessions() {
    try {
      const res = await apiFetch('/api/sessions');
      if (!res.ok) return;
      const sessions = await res.json();
      sessionsList.innerHTML = '';

      if (sessions.length === 0) {
        sessionsList.innerHTML = '<div class="text-xs text-slate-500 p-3 text-center">No past sessions yet.</div>';
        return;
      }

      sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = 'p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-indigo-500/30 text-xs flex flex-col gap-1 transition-all group';
        const dateStr = new Date(s.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        item.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-200 truncate flex-1 group-hover:text-indigo-300 transition-colors cursor-pointer title-click">
              ${s.skill_title}
            </span>
            <button class="delete-session-btn text-slate-600 hover:text-rose-400 p-1 cursor-pointer">
              <i class="fa-regular fa-trash-can text-[10px]"></i>
            </button>
          </div>
          <div class="flex items-center justify-between text-[10px] text-slate-500">
            <span>${dateStr}</span>
            <span class="px-1.5 py-0.2 rounded bg-slate-800 text-indigo-400">${s.status}</span>
          </div>
        `;

        item.querySelector('.title-click').addEventListener('click', () => resumeSession(s.id));
        item.querySelector('.delete-session-btn').addEventListener('click', async (e) => {
          e.stopPropagation();
          if (confirm('Delete this interview session?')) {
            await apiFetch(`/api/sessions/${s.id}`, { method: 'DELETE' });
            await loadSessions();
            if (activeSession && activeSession.id === s.id) {
              resumesHubView.classList.remove('hidden');
              interviewView.classList.add('hidden');
              activeSession = null;
            }
          }
        });

        sessionsList.appendChild(item);
      });
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  }

  // --- Exit Interview Studio ---
  exitInterviewBtn.addEventListener('click', () => {
    resumesHubView.classList.remove('hidden');
    interviewView.classList.add('hidden');
    loadSessions();
  });

  // --- Settings Modal ---
  openSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  closeSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));

  saveSettingsBtn.addEventListener('click', () => {
    customGeminiKey = customKeyInput.value.trim();
    if (customGeminiKey) {
      localStorage.setItem('custom_gemini_key', customGeminiKey);
    } else {
      localStorage.removeItem('custom_gemini_key');
    }
    settingsModal.classList.add('hidden');
  });

  testKeyBtn.addEventListener('click', async () => {
    const keyToTest = customKeyInput.value.trim() || 'server_default';
    testKeyBtn.disabled = true;
    testKeyBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i> Testing...';
    keyTestFeedback.className = 'hidden';

    try {
      const res = await apiFetch('/api/system/test-key', {
        method: 'POST',
        body: JSON.stringify({ api_key: keyToTest })
      });
      const data = await res.json();

      keyTestFeedback.classList.remove('hidden');
      if (data.valid) {
        keyTestFeedback.className = 'p-3 rounded-xl text-xs flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400';
        keyTestFeedback.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${data.message}`;
      } else {
        keyTestFeedback.className = 'p-3 rounded-xl text-xs flex items-center gap-2 bg-rose-500/10 border border-rose-500/20 text-rose-400';
        keyTestFeedback.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.message}`;
      }
    } catch (err) {
      keyTestFeedback.classList.remove('hidden');
      keyTestFeedback.className = 'p-3 rounded-xl text-xs flex items-center gap-2 bg-rose-500/10 border border-rose-500/20 text-rose-400';
      keyTestFeedback.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Error: ${err.message}`;
    } finally {
      testKeyBtn.disabled = false;
      testKeyBtn.innerHTML = '<i class="fa-solid fa-vial"></i> Test Key';
    }
  });

  // --- Logout ---
  logoutBtn.addEventListener('click', async () => {
    if (confirm('Lock interview suite and return to login screen?')) {
      await apiFetch('/api/auth/logout', { method: 'POST' });
      localStorage.removeItem('interview_token');
      window.location.href = `${basePath}/login`;
    }
  });

  // Initialize
  init();
});
