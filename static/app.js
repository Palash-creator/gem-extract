const state = {
  fields: [],
  result: null,
  progressTimer: null,
};

const fieldInput = document.getElementById('field-input');
const fieldList = document.getElementById('field-list');
const logs = document.getElementById('logs');
const jsonOutput = document.getElementById('json-output');
const tableWrap = document.getElementById('table-wrap');
const statusText = document.getElementById('status-text');
const progressLabel = document.getElementById('progress-label');
const progressFill = document.getElementById('progress-fill');

function appendLog(message) {
  const current = logs.textContent.trim();
  logs.textContent = `${current}\n[${new Date().toLocaleTimeString()}] ${message}`;
  logs.scrollTop = logs.scrollHeight;
}

function renderFields() {
  fieldList.innerHTML = '';
  state.fields.forEach((field) => {
    const li = document.createElement('li');
    li.textContent = field;
    fieldList.appendChild(li);
  });
}

function setProgress(value, status) {
  progressFill.style.width = `${value}%`;
  progressLabel.textContent = `${value}%`;
  statusText.textContent = status;
}

function renderTable(records) {
  if (!records.length) {
    tableWrap.innerHTML = '<p>No records yet.</p>';
    return;
  }

  const cols = Object.keys(records[0]);
  let html = '<table><thead><tr>';
  cols.forEach((col) => (html += `<th>${col}</th>`));
  html += '</tr></thead><tbody>';

  records.forEach((row) => {
    html += '<tr>';
    cols.forEach((col) => (html += `<td>${row[col] || ''}</td>`));
    html += '</tr>';
  });

  html += '</tbody></table>';
  tableWrap.innerHTML = html;
}

function startProgressAnimation() {
  let value = 8;
  setProgress(value, 'Running');
  clearInterval(state.progressTimer);

  state.progressTimer = setInterval(() => {
    value = Math.min(value + Math.floor(Math.random() * 8), 92);
    setProgress(value, 'Running');
  }, 350);
}

function stopProgressAnimation(done = true) {
  clearInterval(state.progressTimer);
  if (done) {
    setProgress(100, 'Completed');
  }
}

document.getElementById('add-field').addEventListener('click', () => {
  const value = fieldInput.value.trim();
  if (!value) return;
  if (!state.fields.includes(value)) {
    state.fields.push(value);
    renderFields();
    appendLog(`Added field "${value}".`);
  }
  fieldInput.value = '';
});

document.getElementById('run-btn').addEventListener('click', async () => {
  const docsInput = document.getElementById('documents');
  if (!docsInput.files.length) {
    appendLog('Please upload at least one document.');
    return;
  }
  if (!state.fields.length) {
    appendLog('Please add at least one extraction field.');
    return;
  }

  appendLog('Preparing extraction request...');
  startProgressAnimation();

  const formData = new FormData();
  [...docsInput.files].forEach((file) => formData.append('documents', file));
  formData.append('fields', JSON.stringify(state.fields));

  try {
    const res = await fetch('/api/extract', { method: 'POST', body: formData });
    const payload = await res.json();

    if (!res.ok) {
      throw new Error(payload.error || 'Extraction failed.');
    }

    stopProgressAnimation(true);
    appendLog(`Extraction completed successfully using: ${payload.engine}.`);
    payload.logs.forEach((entry) => appendLog(entry));

    state.result = payload;
    jsonOutput.textContent = JSON.stringify(payload, null, 2);
    renderTable(payload.records);
    document.getElementById('download-csv').disabled = false;
  } catch (err) {
    stopProgressAnimation(false);
    setProgress(0, 'Error');
    appendLog(`Error: ${err.message}`);
  }
});

document.getElementById('download-csv').addEventListener('click', async () => {
  if (!state.result) return;

  appendLog('Generating CSV download...');
  const res = await fetch('/api/export/csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ records: state.result.records }),
  });

  if (!res.ok) {
    appendLog('Failed to export CSV.');
    return;
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'extracted_entities.csv';
  a.click();
  URL.revokeObjectURL(url);
  appendLog('CSV download started.');
});

document.getElementById('clear-btn').addEventListener('click', () => {
  state.fields = [];
  state.result = null;
  renderFields();
  logs.textContent = 'System ready.';
  jsonOutput.textContent = '{}';
  tableWrap.innerHTML = '';
  document.getElementById('documents').value = '';
  document.getElementById('download-csv').disabled = true;
  setProgress(0, 'Idle');
});

setProgress(0, 'Idle');
