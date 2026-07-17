const resumeText = document.getElementById('resumeText');
const jdText = document.getElementById('jdText');
const resumeFile = document.getElementById('resumeFile');
const jdFile = document.getElementById('jdFile');
const resumeFileName = document.getElementById('resumeFileName');
const jdFileName = document.getElementById('jdFileName');
const analyzeBtn = document.getElementById('analyzeBtn');
const statusMsg = document.getElementById('statusMsg');
const resultsSection = document.getElementById('resultsSection');

resumeFile.addEventListener('change', () => {
  resumeFileName.textContent = resumeFile.files[0] ? resumeFile.files[0].name : '';
});
jdFile.addEventListener('change', () => {
  jdFileName.textContent = jdFile.files[0] ? jdFile.files[0].name : '';
});

analyzeBtn.addEventListener('click', async () => {
  const hasResume = resumeText.value.trim() || resumeFile.files[0];
  const hasJd = jdText.value.trim() || jdFile.files[0];

  if (!hasResume || !hasJd) {
    setStatus('Please provide both a resume and a job description.', true);
    return;
  }

  const formData = new FormData();
  formData.append('resume_text', resumeText.value.trim());
  formData.append('jd_text', jdText.value.trim());
  if (resumeFile.files[0]) formData.append('resume_file', resumeFile.files[0]);
  if (jdFile.files[0]) formData.append('jd_file', jdFile.files[0]);

  setLoading(true);

  try {
    const res = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || 'Analysis failed.', true);
      setLoading(false);
      return;
    }

    renderResults(data);
    setStatus('Done.', false);
    loadHistory();
  } catch (err) {
    setStatus('Could not reach the server. Is the Flask app running?', true);
  }

  setLoading(false);
});

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.textContent = isLoading ? 'Analyzing...' : 'Analyze Skill Gap';
}

function setStatus(msg, isError) {
  statusMsg.textContent = msg;
  statusMsg.className = isError ? 'error' : '';
}

function renderResults(data) {
  resultsSection.classList.remove('hidden');

  // Percentage ring: circumference = 2 * pi * r (r=52) ≈ 326.7
  const circumference = 326.7;
  const offset = circumference - (data.match_percentage / 100) * circumference;
  const ringFill = document.getElementById('ringFill');
  ringFill.style.strokeDasharray = circumference;
  ringFill.style.strokeDashoffset = offset;
  document.getElementById('percentLabel').textContent = `${data.match_percentage}%`;

  const matchedList = document.getElementById('matchedList');
  const missingList = document.getElementById('missingList');
  matchedList.innerHTML = data.matched_skills.map(s => `<span class="tag">${escapeHtml(s)}</span>`).join('');
  missingList.innerHTML = data.missing_skills.map(s => `<span class="tag">${escapeHtml(s)}</span>`).join('');
}

async function loadHistory() {
  try {
    const res = await fetch('/history');
    const rows = await res.json();
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td>${r.matched_skills.length}</td>
        <td>${r.missing_skills.length}</td>
        <td class="pct">${r.match_percentage}%</td>
        <td>${r.created_at}</td>
      </tr>
    `).join('');
  } catch (err) {
    // history is a bonus feature; fail silently if backend/db isn't reachable yet
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Load history on page load
loadHistory();
