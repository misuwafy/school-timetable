// ===== School Timetable Management System =====
// Data stored in Python backend with SQLite

// ===== DATA LAYER =====
const API_BASE = '/api';
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const PERIODS = [1, 2, 3, 4, 5, 6, 7];
const PERIOD_TIMES = [
    '9:00 - 9:45', '9:45 - 10:30', '10:30 - 11:15', '11:15 - 12:00',
    '12:45 - 1:30', '1:30 - 2:15', '2:15 - 3:00'
];

const ALL_SUBJECTS_8_9 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT',
    'PET', 'Music', 'Work Education', 'Art'
];

const ALL_SUBJECTS_10 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT'
];

// Special subjects with fixed 1 period/week for class 8 and 9
const SPECIAL_SUBJECTS = ['PET', 'Music', 'Work Education', 'Art'];

// Cache
let _cache = { classes: [], teachers: [], blocks: [], timetable: {} };

async function fetchData() {
    try {
        const [teachers, blocks, classes, timetable] = await Promise.all([
            fetch(`${API_BASE}/teachers`).then(r => r.json()),
            fetch(`${API_BASE}/blocks`).then(r => r.json()),
            fetch(`${API_BASE}/classes`).then(r => r.json()),
            fetch(`${API_BASE}/timetable`).then(r => r.json())
        ]);
        _cache = { teachers, blocks, classes, timetable: timetable || {} };
        // Rebuild teacher subjects from class assignments
        const map = {};
        _cache.teachers.forEach(t => { map[t.name] = new Set(); });
        _cache.classes.forEach(cls => {
            (cls.subjects || []).forEach(sub => {
                if (sub.teacher && map[sub.teacher]) map[sub.teacher].add(sub.name);
            });
        });
        _cache.teachers.forEach(t => { t.subjects = [...(map[t.name] || [])]; });
    } catch (e) {
        console.error('API fetch failed:', e);
    }
    return _cache;
}

function getData() {
    return _cache;
}

function saveData(data) {
    _cache = data;
}

async function apiPost(endpoint, body) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    return res.json();
}

async function apiPut(endpoint, body) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    return res.json();
}

async function apiDelete(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
    return res.json();
}

// ===== NAVIGATION =====
let currentPage = 'dashboard';

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        navigateTo(page);
    });
});

document.getElementById('menuToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

    const titles = {
        'dashboard': 'Dashboard',
        'classes': 'Class Management',
        'teachers': 'Teacher Management',
        'blocks': 'Block Management',
        'timetable': 'Timetable'
    };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';
    document.getElementById('sidebar').classList.remove('open');
    renderPage(page);
}

function renderPage(page) {
    const content = document.getElementById('contentArea');
    switch (page) {
        case 'dashboard': content.innerHTML = renderDashboard(); break;
        case 'classes': content.innerHTML = renderClasses(); break;
        case 'teachers': content.innerHTML = renderTeachers(); break;
        case 'blocks': content.innerHTML = renderBlocks(); break;
        case 'timetable': content.innerHTML = renderTimetablePage(); break;
        default: content.innerHTML = renderDashboard();
    }
}

// ===== DASHBOARD =====
function renderDashboard() {
    const data = getData();
    const totalDivisions = data.classes.reduce((sum, c) => sum + c.divisions.length, 0);
    const hasTimeTable = Object.keys(data.timetable).length > 0;

    return `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon blue"><i class="fas fa-chalkboard"></i></div>
                <div class="stat-info">
                    <h3>${data.classes.length}</h3>
                    <p>Classes</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon green"><i class="fas fa-users"></i></div>
                <div class="stat-info">
                    <h3>${totalDivisions}</h3>
                    <p>Total Divisions</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon yellow"><i class="fas fa-user-tie"></i></div>
                <div class="stat-info">
                    <h3>${data.teachers.length}</h3>
                    <p>Teachers</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon cyan"><i class="fas fa-building"></i></div>
                <div class="stat-info">
                    <h3>${data.blocks.length}</h3>
                    <p>Blocks</p>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon ${hasTimeTable ? 'green' : 'yellow'}">
                    <i class="fas ${hasTimeTable ? 'fa-check-circle' : 'fa-clock'}"></i>
                </div>
                <div class="stat-info">
                    <h3>${hasTimeTable ? 'Generated' : 'Pending'}</h3>
                    <p>Timetable Status</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon blue"><i class="fas fa-calendar-day"></i></div>
                <div class="stat-info">
                    <h3>5 × 7</h3>
                    <p>Days × Periods</p>
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <h2><i class="fas fa-shoe-prints"></i> Setup Guide — Follow These Steps</h2>
            </div>
            <div class="panel-body">
                <div class="setup-steps">
                    <div class="setup-step ${data.blocks.length > 0 ? 'completed' : 'active'}">
                        <div class="step-number">${data.blocks.length > 0 ? '<i class="fas fa-check"></i>' : '1'}</div>
                        <div class="step-content">
                            <h4>Step 1: Create Blocks</h4>
                            <p>Add your school's physical blocks/buildings first. You can also assign Block Heads here.</p>
                            <button class="btn btn-sm ${data.blocks.length > 0 ? 'btn-outline' : 'btn-primary'}" onclick="navigateTo('blocks')">
                                <i class="fas fa-building"></i> ${data.blocks.length > 0 ? 'Manage Blocks' : 'Add Blocks'}
                            </button>
                            ${data.blocks.length > 0 ? `<span class="badge badge-success" style="margin-left:8px;">${data.blocks.length} block(s) added</span>` : ''}
                        </div>
                    </div>
                    <div class="setup-step ${data.teachers.length > 0 ? 'completed' : (data.blocks.length > 0 ? 'active' : '')}">
                        <div class="step-number">${data.teachers.length > 0 ? '<i class="fas fa-check"></i>' : '2'}</div>
                        <div class="step-content">
                            <h4>Step 2: Add Teachers</h4>
                            <p>Add all teachers, assign their subjects, and mark Block Heads.</p>
                            <button class="btn btn-sm ${data.teachers.length > 0 ? 'btn-outline' : 'btn-primary'}" onclick="navigateTo('teachers')">
                                <i class="fas fa-user-tie"></i> ${data.teachers.length > 0 ? 'Manage Teachers' : 'Add Teachers'}
                            </button>
                            ${data.teachers.length > 0 ? `<span class="badge badge-success" style="margin-left:8px;">${data.teachers.length} teacher(s) added</span>` : ''}
                        </div>
                    </div>
                    <div class="setup-step ${data.classes.length > 0 ? 'completed' : (data.teachers.length > 0 ? 'active' : '')}">
                        <div class="step-number">${data.classes.length > 0 ? '<i class="fas fa-check"></i>' : '3'}</div>
                        <div class="step-content">
                            <h4>Step 3: Create Classes</h4>
                            <p>Add classes (8, 9, 10) with divisions (A, B, C...), assign to blocks, and set periods per subject.</p>
                            <button class="btn btn-sm ${data.classes.length > 0 ? 'btn-outline' : 'btn-primary'}" onclick="navigateTo('classes')">
                                <i class="fas fa-chalkboard"></i> ${data.classes.length > 0 ? 'Manage Classes' : 'Add Classes'}
                            </button>
                            ${data.classes.length > 0 ? `<span class="badge badge-success" style="margin-left:8px;">${data.classes.length} class(es) added</span>` : ''}
                        </div>
                    </div>
                    <div class="setup-step ${hasTimeTable ? 'completed' : (data.classes.length > 0 ? 'active' : '')}">
                        <div class="step-number">${hasTimeTable ? '<i class="fas fa-check"></i>' : '4'}</div>
                        <div class="step-content">
                            <h4>Step 4: Generate Timetable</h4>
                            <p>Auto-generate a conflict-free timetable for the entire school.</p>
                            <button class="btn btn-sm ${hasTimeTable ? 'btn-outline' : 'btn-success'}" onclick="navigateTo('timetable')">
                                <i class="fas fa-magic"></i> ${hasTimeTable ? 'Regenerate' : 'Generate Timetable'}
                            </button>
                            ${hasTimeTable ? `<span class="badge badge-success" style="margin-left:8px;">Generated ✓</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        ${data.classes.length > 0 ? `
        <div class="panel">
            <div class="panel-header">
                <h2><i class="fas fa-chart-bar"></i> Classes Overview</h2>
            </div>
            <div class="panel-body">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr><th>Class</th><th>Divisions</th><th>Block</th><th>Subjects</th></tr>
                        </thead>
                        <tbody>
                            ${data.classes.map(c => `
                                <tr>
                                    <td><strong>Class ${c.name}</strong></td>
                                    <td>${c.divisions.map(d => `<span class="chip">${d}</span>`).join('')}</td>
                                    <td>${c.block || '-'}</td>
                                    <td>${c.subjects.length} subjects</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>` : ''}
    `;
}

// ===== CLASS MANAGEMENT =====
function renderClasses() {
    const data = getData();
    return `
        <div class="panel">
            <div class="panel-header">
                <h2>Create New Class</h2>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-outline" onclick="document.getElementById('excelUpload').click()"><i class="fas fa-file-excel"></i> Upload Excel</button>
                    <button class="btn btn-primary" onclick="showAddClassModal()"><i class="fas fa-plus"></i> Add Class</button>
                </div>
                <input type="file" id="excelUpload" style="display:none" accept=".xlsx,.xls" onchange="handleExcelUpload(event)">
            </div>
            <div class="panel-body">
                ${data.classes.length === 0 ? `
                    <div class="empty-state">
                        <i class="fas fa-chalkboard"></i>
                        <h3>No Classes Yet</h3>
                        <p>Create your first class to get started with the timetable.</p>
                    </div>
                ` : `
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Class</th>
                                    <th>Divisions</th>
                                    <th>Block</th>
                                    <th>Subjects</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.classes.map((c, idx) => `
                                    <tr>
                                        <td><strong>Class ${c.name}</strong></td>
                                        <td>${c.divisions.map(d => `<span class="chip">${d}</span>`).join('')}</td>
                                        <td><span class="badge badge-primary">${c.block || 'Not assigned'}</span></td>
                                        <td>
                                            ${c.subjects.slice(0, 3).map(s => `<span class="chip">${s.name}</span>`).join('')}
                                            ${c.subjects.length > 3 ? `<span class="chip">+${c.subjects.length - 3} more</span>` : ''}
                                        </td>
                                        <td>
                                            <button class="btn btn-sm btn-outline" onclick="viewClass(${idx})"><i class="fas fa-eye"></i></button>
                                            <button class="btn btn-sm btn-outline" onclick="editClass(${idx})"><i class="fas fa-edit"></i></button>
                                            <button class="btn btn-sm btn-danger" onclick="deleteClass(${idx})"><i class="fas fa-trash"></i></button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `}
            </div>
        </div>
    `;
}

function showAddClassModal(editIdx = null) {
    const data = getData();
    const isEdit = editIdx !== null;
    const cls = isEdit ? data.classes[editIdx] : null;
    const className = cls ? cls.name : '';
    const classNum = parseInt(className) || 8;

    // Determine subjects based on class number
    const availableSubjects = classNum === 10 ? ALL_SUBJECTS_10 : ALL_SUBJECTS_8_9;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'classModal';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>${isEdit ? 'Edit' : 'Add New'} Class</h3>
                <button class="modal-close" onclick="closeModal('classModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <div class="form-group">
                        <label>Class Name (e.g., 8, 9, 10)</label>
                        <select class="form-control" id="className" onchange="updateSubjectsForClass()">
                            <option value="8" ${className === '8' ? 'selected' : ''}>Class 8</option>
                            <option value="9" ${className === '9' ? 'selected' : ''}>Class 9</option>
                            <option value="10" ${className === '10' ? 'selected' : ''}>Class 10</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Divisions (e.g., A, B, C)</label>
                        <input type="text" class="form-control" id="classDivisions"
                            value="${cls ? cls.divisions.join(', ') : ''}" placeholder="A, B, C or A,B,C,D">
                        <small style="color:var(--text-light);margin-top:4px;display:block;">Enter division letters separated by commas</small>
                    </div>
                </div>
                <div class="form-group">
                    <label>Block</label>
                    <select class="form-control" id="classBlock">
                        <option value="">Select Block</option>
                        ${data.blocks.map(b => `<option value="${b.name}" ${cls && cls.block === b.name ? 'selected' : ''}>${b.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <select class="form-control" id="classType">
                        <option value="">Select Type</option>
                        <option value="Arabic" ${cls && cls.classType === 'Arabic' ? 'selected' : ''}>Arabic</option>
                        <option value="Malayalam" ${cls && cls.classType === 'Malayalam' ? 'selected' : ''}>Malayalam</option>
                        <option value="Urdu/Sanskrit" ${cls && cls.classType === 'Urdu/Sanskrit' ? 'selected' : ''}>Urdu/Sanskrit</option>
                        <option value="Sanskrit/Urdu/Arabic" ${cls && cls.classType === 'Sanskrit/Urdu/Arabic' ? 'selected' : ''}>Sanskrit/Urdu/Arabic</option>
                        <option value="Malayalam/Arabic" ${cls && cls.classType === 'Malayalam/Arabic' ? 'selected' : ''}>Malayalam/Arabic</option>
                        <option value="Sanskrit/Arabic/Urdu/Malayalam" ${cls && cls.classType === 'Sanskrit/Arabic/Urdu/Malayalam' ? 'selected' : ''}>Sanskrit/Arabic/Urdu/Malayalam</option>
                        <option value="Sanskrit/Arabic" ${cls && cls.classType === 'Sanskrit/Arabic' ? 'selected' : ''}>Sanskrit/Arabic</option>
                        <option value="Urdu/Arabic" ${cls && cls.classType === 'Urdu/Arabic' ? 'selected' : ''}>Urdu/Arabic</option>
                        <option value="Sanskrit" ${cls && cls.classType === 'Sanskrit' ? 'selected' : ''}>Sanskrit</option>
                        <option value="Urdu" ${cls && cls.classType === 'Urdu' ? 'selected' : ''}>Urdu</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Class Teacher</label>
                    <select class="form-control" id="classTeacher">
                        <option value="">Select Class Teacher</option>
                        ${data.teachers.map(t => `<option value="${t.name}" ${cls && cls.classTeacher === t.name ? 'selected' : ''}>${t.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Subjects & Periods per Week</label>
                    <div id="subjectsList">
                        ${renderSubjectEntries(cls, classNum)}
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="closeModal('classModal')">Cancel</button>
                <button class="btn btn-primary" onclick="saveClass(${editIdx})">${isEdit ? 'Update' : 'Save'} Class</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function renderSubjectEntries(cls, classNum) {
    const subjects = classNum === 10 ? ALL_SUBJECTS_10 : ALL_SUBJECTS_8_9;
    const defaultPeriods = {
        'PET': 1, 'Music': 1, 'Work Education': 1, 'Art': 1
    };
    const data = getData();
    const teachers = data.teachers;

    return `
        <div style="overflow-x:auto;">
            <table style="width:100%;font-size:13px;">
                <thead>
                    <tr>
                        <th style="text-align:left;padding:8px;">Subject</th>
                        <th style="text-align:left;padding:8px;">Teacher</th>
                        <th style="text-align:center;padding:8px;width:90px;">Periods/Week</th>
                    </tr>
                </thead>
                <tbody>
                    ${subjects.map(sub => {
                        const existing = cls ? cls.subjects.find(s => s.name === sub) : null;
                        const periods = existing ? existing.periodsPerWeek : (defaultPeriods[sub] || '');
                        const assignedTeacher = existing ? (existing.teacher || '') : '';
                        const isSpecial = SPECIAL_SUBJECTS.includes(sub);
                        return `
                            <tr style="border-bottom:1px solid var(--border);">
                                <td style="padding:8px;font-weight:500;">
                                    ${sub}
                                    ${isSpecial ? '<span class="badge badge-warning" style="margin-left:4px;">Fixed</span>' : ''}
                                </td>
                                <td style="padding:8px;">
                                    <select class="form-control" data-teacher-for="${sub}" style="padding:6px 10px;font-size:13px;">
                                        <option value="">-- Select Teacher --</option>
                                        ${teachers.map(t => `<option value="${t.name}" ${assignedTeacher === t.name ? 'selected' : ''}>${t.name}</option>`).join('')}
                                    </select>
                                </td>
                                <td style="padding:8px;text-align:center;">
                                    <input type="number" class="form-control" data-subject="${sub}" 
                                        value="${periods}" min="1" max="10" ${isSpecial ? 'readonly' : ''}
                                        style="max-width:70px;text-align:center;margin:0 auto;" placeholder="0">
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
        <div style="margin-top:12px;padding:10px;background:var(--bg);border-radius:var(--radius);font-size:13px;color:var(--text-light);">
            <strong>Total:</strong> <span id="totalPeriodsCount">0</span> / 35 periods
            <small style="display:block;margin-top:4px;">Must equal 35 (5 days × 7 periods per day)</small>
        </div>
        <script>
            setTimeout(() => {
                const inputs = document.querySelectorAll('[data-subject]');
                const updateTotal = () => {
                    let total = 0;
                    inputs.forEach(inp => { total += parseInt(inp.value) || 0; });
                    const el = document.getElementById('totalPeriodsCount');
                    if (el) {
                        el.textContent = total;
                        el.style.color = total === 35 ? 'var(--success)' : (total > 35 ? 'var(--danger)' : 'var(--text)');
                    }
                };
                inputs.forEach(inp => inp.addEventListener('input', updateTotal));
                updateTotal();
            }, 100);
        </script>
    `;
}

function updateSubjectsForClass() {
    const classNum = parseInt(document.getElementById('className').value);
    document.getElementById('subjectsList').innerHTML = renderSubjectEntries(null, classNum);
}

function saveClass(editIdx) {
    const data = getData();
    const className = document.getElementById('className').value;
    const divisionsInput = document.getElementById('classDivisions').value.trim();
    const block = document.getElementById('classBlock').value;
    const classType = document.getElementById('classType').value;
    const classTeacher = document.getElementById('classTeacher').value;

    // Check if class already exists (when adding new)
    if (editIdx === null && data.classes.find(c => c.name === className)) {
        showToast('Class ' + className + ' already exists!', 'error');
        return;
    }

    // Parse divisions from text input
    const divisions = divisionsInput
        .split(',')
        .map(d => d.trim().toUpperCase())
        .filter(d => d.length > 0);

    if (divisions.length === 0) {
        showToast('Please enter at least one division (e.g., A, B, C)', 'error');
        return;
    }

    // Check for duplicates
    const uniqueDivisions = [...new Set(divisions)];
    if (uniqueDivisions.length !== divisions.length) {
        showToast('Duplicate division names found. Please use unique names.', 'error');
        return;
    }

    // Collect subjects with teacher assignments
    const subjectInputs = document.querySelectorAll('[data-subject]');
    const subjects = [];
    let missingTeacher = false;
    subjectInputs.forEach(input => {
        const subName = input.dataset.subject;
        const periods = parseInt(input.value) || 0;
        const teacherSelect = document.querySelector(`[data-teacher-for="${subName}"]`);
        const teacher = teacherSelect ? teacherSelect.value : '';

        if (periods > 0 && !teacher) {
            missingTeacher = true;
        }

        subjects.push({
            name: subName,
            periodsPerWeek: periods,
            teacher: teacher
        });
    });

    if (missingTeacher) {
        showToast('Please assign a teacher for all subjects with periods > 0', 'error');
        return;
    }

    // Validate total periods
    const totalPeriods = subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0);
    if (totalPeriods !== 35) {
        showToast(`Total periods must be 35 (5 days × 7 periods). Current: ${totalPeriods}`, 'warning');
        return;
    }

    const classObj = {
        name: className,
        divisions: uniqueDivisions,
        block: block,
        classTeacher: classTeacher,
        subjects: subjects
    };

    const doSave = async () => {
        try {
            const classData = { name: className, divisions: uniqueDivisions, block, classType, classTeacher, subjects };
            if (editIdx !== null) {
                await apiPut(`/classes/${data.classes[editIdx].id}`, classData);
            } else {
                await apiPost('/classes', classData);
            }
            await fetchData();
            closeModal('classModal');
            showToast(`Class ${className} ${editIdx !== null ? 'updated' : 'created'}!`, 'success');
            renderPage('classes');
        } catch (e) { showToast('Error saving class', 'error'); }
    };
    doSave();
}

function updateTeacherSubjects(data) {
    // Rebuild each teacher's subject list from all class assignments
    const teacherSubjectsMap = {};
    data.teachers.forEach(t => { teacherSubjectsMap[t.name] = new Set(); });

    data.classes.forEach(cls => {
        cls.subjects.forEach(sub => {
            if (sub.teacher && teacherSubjectsMap[sub.teacher] !== undefined) {
                teacherSubjectsMap[sub.teacher].add(sub.name);
            }
        });
    });

    data.teachers.forEach(t => {
        t.subjects = [...(teacherSubjectsMap[t.name] || [])];
    });
}

function editClass(idx) {
    showAddClassModal(idx);
}

function viewClass(idx) {
    const data = getData();
    const cls = data.classes[idx];
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'viewClassModal';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>Class ${cls.name} Details</h3>
                <button class="modal-close" onclick="closeModal('viewClassModal')">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Divisions:</strong> ${cls.divisions.join(', ')}</p>
                <p><strong>Type:</strong> ${cls.classType || '-'}</p>
                <p><strong>Block:</strong> ${cls.block || 'Not assigned'}</p>
                <p><strong>Class Teacher:</strong> ${cls.classTeacher || 'Not assigned'}</p>
                <br>
                <table>
                    <thead><tr><th>Subject</th><th>Teacher</th><th>Periods/Week</th></tr></thead>
                    <tbody>
                        ${cls.subjects.filter(s => s.periodsPerWeek > 0).map(s => `<tr><td>${s.name}</td><td>${s.teacher || '-'}</td><td>${s.periodsPerWeek}</td></tr>`).join('')}
                    </tbody>
                </table>
                <br>
                <p><strong>Total Periods/Week:</strong> ${cls.subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0)}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="closeModal('viewClassModal')">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function deleteClass(idx) {
    if (!confirm('Are you sure you want to delete this class?')) return;
    const data = getData();
    apiDelete(`/classes/${data.classes[idx].id}`).then(() => fetchData()).then(() => {
        showToast('Class deleted', 'success');
        renderPage('classes');
    });
}

// ===== TEACHER MANAGEMENT =====
function renderTeachers() {
    const data = getData();

    // Calculate total periods per teacher from all class assignments
    const teacherTotalPeriods = {};
    data.teachers.forEach(t => { teacherTotalPeriods[t.name] = 0; });
    data.classes.forEach(cls => {
        const numDivisions = cls.divisions.length;
        cls.subjects.forEach(sub => {
            if (sub.teacher && teacherTotalPeriods[sub.teacher] !== undefined) {
                teacherTotalPeriods[sub.teacher] += sub.periodsPerWeek * numDivisions;
            }
        });
    });

    return `
        <div class="panel">
            <div class="panel-header">
                <h2>Teachers</h2>
                <button class="btn btn-primary" onclick="showAddTeacherModal()"><i class="fas fa-plus"></i> Add Teacher</button>
            </div>
            <div class="panel-body">
                ${data.teachers.length === 0 ? `
                    <div class="empty-state">
                        <i class="fas fa-user-tie"></i>
                        <h3>No Teachers Yet</h3>
                        <p>Add teachers with their name and settings.</p>
                    </div>
                ` : `
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Assigned Subjects</th>
                                    <th>Total Periods/Week</th>
                                    <th>Block Head</th>
                                    <th>Max/Day</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.teachers.map((t, idx) => {
                                    const total = teacherTotalPeriods[t.name] || 0;
                                    const maxWeek = (t.maxPeriodsPerDay || 7) * 5;
                                    const overloaded = total > maxWeek;
                                    return `
                                    <tr>
                                        <td><strong>${t.name}</strong></td>
                                        <td>${t.subjects && t.subjects.length > 0 ? t.subjects.map(s => `<span class="chip">${s}</span>`).join('') : '<span style="color:var(--text-light);font-size:12px;">Not yet assigned</span>'}</td>
                                        <td>
                                            <strong style="color:${overloaded ? 'var(--danger)' : 'var(--text)'};">${total}</strong>
                                            <span style="color:var(--text-light);font-size:11px;">/ ${maxWeek} max</span>
                                            ${overloaded ? '<span class="badge badge-danger" style="margin-left:4px;">Overloaded</span>' : ''}
                                        </td>
                                        <td>${t.isBlockHead ? `<span class="badge badge-warning">${t.headOfBlock}</span>` : '-'}</td>
                                        <td>${t.maxPeriodsPerDay || 7}</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline" onclick="editTeacher(${idx})"><i class="fas fa-edit"></i></button>
                                            <button class="btn btn-sm btn-danger" onclick="deleteTeacher(${idx})"><i class="fas fa-trash"></i></button>
                                        </td>
                                    </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                    <div style="margin-top:16px;padding:12px;background:var(--bg);border-radius:var(--radius);font-size:13px;">
                        <strong>Note:</strong> Total Periods/Week = sum of all periods assigned across all classes × divisions. 
                        Max/Week = Max Periods/Day × 5 days.
                    </div>
                `}
            </div>
        </div>
    `;
}

function showAddTeacherModal(editIdx = null) {
    const data = getData();
    const isEdit = editIdx !== null;
    const teacher = isEdit ? data.teachers[editIdx] : null;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'teacherModal';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>${isEdit ? 'Edit' : 'Add New'} Teacher</h3>
                <button class="modal-close" onclick="closeModal('teacherModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Teacher Name</label>
                    <input type="text" class="form-control" id="teacherName" 
                        value="${teacher ? teacher.name : ''}" placeholder="Enter teacher name">
                </div>
                <div class="form-group">
                    <label>Max Periods per Day</label>
                    <input type="number" class="form-control" id="maxPeriodsDay" 
                        min="1" max="8" value="${teacher ? (teacher.maxPeriodsPerDay || 7) : 7}">
                </div>
                <div class="form-group">
                    <label style="display:flex;align-items:center;gap:8px;">
                        <input type="checkbox" id="isBlockHead" ${teacher && teacher.isBlockHead ? 'checked' : ''} onchange="toggleBlockHeadSelect()">
                        <span>This teacher is a Block Head</span>
                    </label>
                    <div id="blockHeadSelectWrapper" style="margin-top:8px;${teacher && teacher.isBlockHead ? '' : 'display:none;'}">
                        <select class="form-control" id="headOfBlock">
                            <option value="">Select Block</option>
                            ${data.blocks.map(b => `<option value="${b.name}" ${teacher && teacher.headOfBlock === b.name ? 'selected' : ''}>${b.name}</option>`).join('')}
                        </select>
                        <small style="color:var(--text-light);margin-top:4px;display:block;">Block Heads will not have any classes during Period 1.</small>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="closeModal('teacherModal')">Cancel</button>
                <button class="btn btn-primary" onclick="saveTeacher(${editIdx})">${isEdit ? 'Update' : 'Save'} Teacher</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function toggleBlockHeadSelect() {
    const checked = document.getElementById('isBlockHead').checked;
    document.getElementById('blockHeadSelectWrapper').style.display = checked ? 'block' : 'none';
}

function saveTeacher(editIdx) {
    const data = getData();
    const name = document.getElementById('teacherName').value.trim();
    const maxPeriodsPerDay = parseInt(document.getElementById('maxPeriodsDay').value) || 7;
    const isBlockHead = document.getElementById('isBlockHead').checked;
    const headOfBlock = isBlockHead ? document.getElementById('headOfBlock').value : '';

    if (!name) { showToast('Please enter teacher name', 'error'); return; }
    if (isBlockHead && !headOfBlock) { showToast('Please select the block this teacher heads', 'error'); return; }

    const body = { name, maxPeriodsPerDay, isBlockHead, headOfBlock };

    const doSave = async () => {
        try {
            if (editIdx !== null) {
                await apiPut(`/teachers/${data.teachers[editIdx].id}`, body);
            } else {
                await apiPost('/teachers', body);
            }
            if (isBlockHead && headOfBlock) {
                const block = data.blocks.find(b => b.name === headOfBlock);
                if (block) await apiPut(`/blocks/${block.id}`, { head: name });
            }
            await fetchData();
            closeModal('teacherModal');
            showToast(`Teacher ${name} ${editIdx !== null ? 'updated' : 'added'}!`, 'success');
            renderPage('teachers');
        } catch (e) { showToast('Error saving teacher', 'error'); }
    };
    doSave();
}

function editTeacher(idx) {
    showAddTeacherModal(idx);
}

function deleteTeacher(idx) {
    if (!confirm('Are you sure you want to delete this teacher?')) return;
    const data = getData();
    apiDelete(`/teachers/${data.teachers[idx].id}`).then(() => fetchData()).then(() => {
        showToast('Teacher deleted', 'success');
        renderPage('teachers');
    });
}

// ===== BLOCK MANAGEMENT =====
function renderBlocks() {
    const data = getData();
    return `
        <div class="panel">
            <div class="panel-header">
                <h2>Blocks</h2>
                <button class="btn btn-primary" onclick="showAddBlockModal()"><i class="fas fa-plus"></i> Add Block</button>
            </div>
            <div class="panel-body">
                ${data.blocks.length === 0 ? `
                    <div class="empty-state">
                        <i class="fas fa-building"></i>
                        <h3>No Blocks Yet</h3>
                        <p>Add physical blocks/buildings of your school.</p>
                    </div>
                ` : `
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr><th>Block Name</th><th>Head</th><th>Description</th><th>Classes Assigned</th><th>Actions</th></tr>
                            </thead>
                            <tbody>
                                ${data.blocks.map((b, idx) => {
                                    const assignedClasses = data.classes.filter(c => c.block === b.name);
                                    return `
                                        <tr>
                                            <td><strong>${b.name}</strong></td>
                                            <td>${b.head ? `<span class="badge badge-warning"><i class="fas fa-crown"></i> ${b.head}</span>` : '<span style="color:var(--text-light);">Not assigned</span>'}</td>
                                            <td>${b.description || '-'}</td>
                                            <td>${assignedClasses.map(c => `<span class="chip">Class ${c.name}</span>`).join('') || 'None'}</td>
                                            <td>
                                                <button class="btn btn-sm btn-outline" onclick="editBlock(${idx})"><i class="fas fa-edit"></i></button>
                                                <button class="btn btn-sm btn-danger" onclick="deleteBlock(${idx})"><i class="fas fa-trash"></i></button>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                `}
            </div>
        </div>
    `;
}

function showAddBlockModal(editIdx = null) {
    const data = getData();
    const isEdit = editIdx !== null;
    const block = isEdit ? data.blocks[editIdx] : null;

    // Get teachers that can be heads
    const availableTeachers = data.teachers.filter(t => {
        // If editing, allow current head or teachers not heading other blocks
        if (block && t.headOfBlock === block.name) return true;
        return !t.isBlockHead || !t.headOfBlock;
    });

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'blockModal';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>${isEdit ? 'Edit' : 'Add New'} Block</h3>
                <button class="modal-close" onclick="closeModal('blockModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Block Name</label>
                    <input type="text" class="form-control" id="blockName" 
                        value="${block ? block.name : ''}" placeholder="e.g., Block A, Main Building">
                </div>
                <div class="form-group">
                    <label>Description (optional)</label>
                    <input type="text" class="form-control" id="blockDesc" 
                        value="${block ? (block.description || '') : ''}" placeholder="Brief description">
                </div>
                <div class="form-group">
                    <label>Block Head (Teacher)</label>
                    <select class="form-control" id="blockHead">
                        <option value="">Select Head (optional)</option>
                        ${data.teachers.map(t => `<option value="${t.name}" ${block && block.head === t.name ? 'selected' : ''}>${t.name}</option>`).join('')}
                    </select>
                    <small style="color:var(--text-light);margin-top:4px;display:block;">The Block Head will have no classes during Period 1 (administrative duties).</small>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="closeModal('blockModal')">Cancel</button>
                <button class="btn btn-primary" onclick="saveBlock(${editIdx})">${isEdit ? 'Update' : 'Save'} Block</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function saveBlock(editIdx) {
    const data = getData();
    const name = document.getElementById('blockName').value.trim();
    const description = document.getElementById('blockDesc').value.trim();
    const head = document.getElementById('blockHead').value;

    if (!name) {
        showToast('Please enter block name', 'error');
        return;
    }

    const doSave = async () => {
        try {
            if (editIdx !== null) {
                const block = data.blocks[editIdx];
                const oldHead = block.head;
                await apiPut(`/blocks/${block.id}`, { name, description, head });
                if (oldHead && oldHead !== head) {
                    const oht = data.teachers.find(t => t.name === oldHead);
                    if (oht) await apiPut(`/teachers/${oht.id}`, { isBlockHead: false, headOfBlock: '' });
                }
            } else {
                await apiPost('/blocks', { name, description, head });
            }
            if (head) {
                const ht = data.teachers.find(t => t.name === head);
                if (ht) await apiPut(`/teachers/${ht.id}`, { isBlockHead: true, headOfBlock: name });
            }
            await fetchData();
            closeModal('blockModal');
            showToast(`Block ${name} ${editIdx !== null ? 'updated' : 'added'}!`, 'success');
            renderPage('blocks');
        } catch (e) { showToast('Error saving block', 'error'); }
    };
    doSave();
}

function editBlock(idx) {
    showAddBlockModal(idx);
}

function deleteBlock(idx) {
    if (!confirm('Are you sure you want to delete this block?')) return;
    const data = getData();
    apiDelete(`/blocks/${data.blocks[idx].id}`).then(() => fetchData()).then(() => {
        showToast('Block deleted', 'success');
        renderPage('blocks');
    });
}

// ===== TIMETABLE PAGE (Tabbed) =====
let currentTimetableTab = 'generate';

function renderTimetablePage() {
    const data = getData();
    const hasTimeTable = Object.keys(data.timetable).length > 0;

    return `
        <div class="timetable-tabs">
            <button class="tab-btn ${currentTimetableTab === 'generate' ? 'active' : ''}" onclick="switchTimetableTab('generate')">
                <i class="fas fa-magic"></i> Generate
            </button>
            <button class="tab-btn ${currentTimetableTab === 'class' ? 'active' : ''}" onclick="switchTimetableTab('class')" ${!hasTimeTable ? 'disabled' : ''}>
                <i class="fas fa-chalkboard"></i> Class Wise
            </button>
            <button class="tab-btn ${currentTimetableTab === 'teacher' ? 'active' : ''}" onclick="switchTimetableTab('teacher')" ${!hasTimeTable ? 'disabled' : ''}>
                <i class="fas fa-user-tie"></i> Teacher Wise
            </button>
            <button class="tab-btn ${currentTimetableTab === 'block' ? 'active' : ''}" onclick="switchTimetableTab('block')" ${!hasTimeTable ? 'disabled' : ''}>
                <i class="fas fa-building"></i> Block Wise
            </button>
            <button class="tab-btn ${currentTimetableTab === 'school' ? 'active' : ''}" onclick="switchTimetableTab('school')" ${!hasTimeTable ? 'disabled' : ''}>
                <i class="fas fa-calendar-alt"></i> School Wise
            </button>
        </div>
        <div id="timetableTabContent">
            ${renderTimetableTabContent()}
        </div>
    `;
}

function switchTimetableTab(tab) {
    currentTimetableTab = tab;
    document.getElementById('contentArea').innerHTML = renderTimetablePage();
}

function renderTimetableTabContent() {
    switch (currentTimetableTab) {
        case 'generate': return renderGenerate();
        case 'class': return renderViewClass();
        case 'teacher': return renderViewTeacher();
        case 'block': return renderViewBlock();
        case 'school': return renderViewSchool();
        default: return renderGenerate();
    }
}

// ===== TIMETABLE GENERATION =====
function renderGenerate() {
    const data = getData();
    const hasData = data.classes.length > 0 && data.teachers.length > 0;
    const hasTimeTable = Object.keys(data.timetable).length > 0;

    return `
        <div class="panel">
            <div class="panel-header">
                <h2><i class="fas fa-magic"></i> Auto-Generate Timetable</h2>
            </div>
            <div class="panel-body">
                ${!hasData ? `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Setup Required</h3>
                        <p>Please add classes, teachers, and blocks before generating a timetable.</p>
                        <div style="display:flex;gap:12px;justify-content:center;">
                            <button class="btn btn-primary" onclick="navigateTo('classes')">Add Classes</button>
                            <button class="btn btn-primary" onclick="navigateTo('teachers')">Add Teachers</button>
                        </div>
                    </div>
                ` : `
                    <div style="margin-bottom:24px;">
                        <h3 style="margin-bottom:8px;">Pre-generation Check</h3>
                        <div id="preCheckResults"></div>
                    </div>

                    ${hasTimeTable ? `
                        <div style="background:#fffbeb; padding:16px; border-radius:var(--radius); margin-bottom:20px; border:1px solid #f59e0b;">
                            <strong><i class="fas fa-exclamation-triangle"></i> Warning:</strong> A timetable already exists. Generating a new one will overwrite it.
                        </div>
                    ` : ''}

                    <button class="btn btn-success btn-lg" onclick="generateTimetable()" style="padding:14px 32px;font-size:16px;">
                        <i class="fas fa-magic"></i> Generate Conflict-Free Timetable
                    </button>

                    <div id="generationProgress" style="display:none;margin-top:24px;">
                        <p id="genStatus">Generating...</p>
                        <div class="progress-bar"><div class="progress-fill" id="genProgress" style="width:0%"></div></div>
                    </div>

                    <div id="generationResult" style="margin-top:24px;"></div>
                `}
            </div>
        </div>
    `;
}

function generateTimetable() {
    const data = getData();

    // Validation
    if (data.classes.length === 0) {
        showToast('No classes defined!', 'error');
        return;
    }
    if (data.teachers.length === 0) {
        showToast('No teachers defined!', 'error');
        return;
    }

    // Check that all subjects have teachers assigned
    const missingTeachers = [];
    data.classes.forEach(cls => {
        cls.subjects.forEach(sub => {
            if (sub.periodsPerWeek > 0 && !sub.teacher) {
                missingTeachers.push(`${sub.name} (Class ${cls.name})`);
            }
        });
    });

    if (missingTeachers.length > 0) {
        const unique = [...new Set(missingTeachers)];
        showToast(`No teacher assigned for: ${unique.slice(0, 3).join(', ')}${unique.length > 3 ? '...' : ''}`, 'error');
        document.getElementById('generationResult').innerHTML = `
            <div style="background:#fef2f2;padding:16px;border-radius:var(--radius);border:1px solid var(--danger);">
                <h4 style="color:var(--danger);margin-bottom:8px;"><i class="fas fa-times-circle"></i> Missing Teacher Assignments</h4>
                <ul style="margin-left:20px;">${unique.map(m => `<li>${m}</li>`).join('')}</ul>
            </div>
        `;
        return;
    }

    // Show progress
    document.getElementById('generationProgress').style.display = 'block';
    document.getElementById('genProgress').style.width = '10%';
    document.getElementById('genStatus').textContent = 'Initializing...';

    setTimeout(() => {
        document.getElementById('genProgress').style.width = '30%';
        document.getElementById('genStatus').textContent = 'Assigning teachers to classes...';

        setTimeout(() => {
            document.getElementById('genProgress').style.width = '60%';
            document.getElementById('genStatus').textContent = 'Resolving conflicts...';

            setTimeout(() => {
                const result = runTimetableAlgorithm(data);

                document.getElementById('genProgress').style.width = '100%';
                document.getElementById('genStatus').textContent = 'Complete!';

                if (result.success) {
                    data.timetable = result.timetable;
                    _cache.timetable = result.timetable;
                    // Save timetable to backend
                    apiPost('/timetable', result.timetable);
                    showToast('Timetable generated successfully!', 'success');
                    document.getElementById('generationResult').innerHTML = `
                        <div style="background:#ecfdf5;padding:16px;border-radius:var(--radius);border:1px solid var(--success);">
                            <h4 style="color:var(--success);margin-bottom:8px;"><i class="fas fa-check-circle"></i> Timetable Generated Successfully!</h4>
                            <p>No conflicts detected. You can now view timetables class-wise, teacher-wise, block-wise, or school-wide.</p>
                            <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">
                                <button class="btn btn-primary btn-sm" onclick="switchTimetableTab('class')">View Class Wise</button>
                                <button class="btn btn-primary btn-sm" onclick="switchTimetableTab('teacher')">View Teacher Wise</button>
                                <button class="btn btn-primary btn-sm" onclick="switchTimetableTab('block')">View Block Wise</button>
                                <button class="btn btn-primary btn-sm" onclick="switchTimetableTab('school')">View School Wise</button>
                            </div>
                        </div>
                    `;
                } else {
                    document.getElementById('generationResult').innerHTML = `
                        <div style="background:#fef2f2;padding:16px;border-radius:var(--radius);border:1px solid var(--danger);">
                            <h4 style="color:var(--danger);margin-bottom:8px;"><i class="fas fa-times-circle"></i> Generation Failed</h4>
                            <p>${result.error}</p>
                        </div>
                    `;
                }
            }, 500);
        }, 500);
    }, 300);
}

// ===== TIMETABLE ALGORITHM =====
function runTimetableAlgorithm(data) {
    const timetable = {};
    const teacherSchedule = {};

    // Initialize
    data.teachers.forEach(t => {
        teacherSchedule[t.name] = {};
        DAYS.forEach(day => { teacherSchedule[t.name][day] = {}; });
    });

    data.classes.forEach(cls => {
        cls.divisions.forEach(div => {
            const key = `${cls.name}-${div}`;
            timetable[key] = {};
            DAYS.forEach(day => { timetable[key][day] = {}; });
        });
    });

    // Build assignments grouped by teacher (busiest first)
    const teacherAssignments = {};
    data.classes.forEach(cls => {
        cls.divisions.forEach(div => {
            const key = `${cls.name}-${div}`;
            cls.subjects.forEach(sub => {
                if (sub.periodsPerWeek > 0 && sub.teacher) {
                    if (!teacherAssignments[sub.teacher]) teacherAssignments[sub.teacher] = [];
                    for (let i = 0; i < sub.periodsPerWeek; i++) {
                        teacherAssignments[sub.teacher].push({
                            classDiv: key, subject: sub.name, teacher: sub.teacher
                        });
                    }
                }
            });
        });
    });

    // Sort teachers by load (busiest first)
    const sortedTeachers = Object.keys(teacherAssignments).sort(
        (a, b) => teacherAssignments[b].length - teacherAssignments[a].length
    );

    let bestFailCount = Infinity;
    let bestTimetable = null;
    let bestTeacherSchedule = null;
    const maxAttempts = 30;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        // Reset
        Object.keys(timetable).forEach(key => {
            DAYS.forEach(day => { timetable[key][day] = {}; });
        });
        data.teachers.forEach(t => {
            DAYS.forEach(day => { teacherSchedule[t.name][day] = {}; });
        });

        // Vary teacher order each attempt
        const teacherOrder = [...sortedTeachers];
        if (attempt % 3 === 1) {
            // Reverse
            teacherOrder.reverse();
        } else if (attempt % 3 === 2) {
            // Shuffle
            shuffleArray(teacherOrder);
        }

        let failCount = 0;

        for (const teacherName of teacherOrder) {
            const assignments = [...teacherAssignments[teacherName]];
            shuffleArray(assignments);

            // Group by classDiv to spread divisions evenly
            const byClassDiv = {};
            assignments.forEach(a => {
                if (!byClassDiv[a.classDiv]) byClassDiv[a.classDiv] = [];
                byClassDiv[a.classDiv].push(a);
            });

            // Interleave divisions for even spread
            const interleaved = [];
            const classDivKeys = Object.keys(byClassDiv);
            shuffleArray(classDivKeys);
            let maxLen = Math.max(...classDivKeys.map(k => byClassDiv[k].length));
            for (let i = 0; i < maxLen; i++) {
                for (const key of classDivKeys) {
                    if (i < byClassDiv[key].length) {
                        interleaved.push(byClassDiv[key][i]);
                    }
                }
            }

            const unplaced = [];
            for (const assignment of interleaved) {
                if (!placeAssignment(assignment, timetable, teacherSchedule, data, false)) {
                    unplaced.push(assignment);
                }
            }

            // Retry unplaced with relaxed constraints
            for (const assignment of unplaced) {
                if (!placeAssignment(assignment, timetable, teacherSchedule, data, true)) {
                    failCount++;
                }
            }
        }

        if (failCount === 0) {
            return { success: true, timetable };
        }

        if (failCount < bestFailCount) {
            bestFailCount = failCount;
            bestTimetable = JSON.parse(JSON.stringify(timetable));
            bestTeacherSchedule = JSON.parse(JSON.stringify(teacherSchedule));
        }
    }

    // If we still have failures, try one more pass using the best result and filling gaps
    if (bestTimetable) {
        // Restore best
        Object.keys(bestTimetable).forEach(key => { timetable[key] = bestTimetable[key]; });
        Object.keys(bestTeacherSchedule).forEach(key => { teacherSchedule[key] = bestTeacherSchedule[key]; });
    }

    return {
        success: false,
        error: `Could not place ${bestFailCount} period(s) after ${maxAttempts} attempts. Check if any teacher has too many periods across divisions to fit without time conflicts.`
    };
}

function placeAssignment(assignment, timetable, teacherSchedule, data, relaxed = false) {
    const { classDiv, subject, teacher: assignedTeacherName } = assignment;
    const teacher = data.teachers.find(t => t.name === assignedTeacherName);
    if (!teacher) return false;

    const days = [...DAYS];
    const periods = [...PERIODS];

    // Sort days: prefer days with fewer periods of this subject for this class
    days.sort((a, b) => {
        const countA = Object.values(timetable[classDiv][a]).filter(s => s.subject === subject).length;
        const countB = Object.values(timetable[classDiv][b]).filter(s => s.subject === subject).length;
        if (countA !== countB) return countA - countB;
        // Then prefer days where teacher has fewer periods
        const tA = Object.keys(teacherSchedule[teacher.name][a]).length;
        const tB = Object.keys(teacherSchedule[teacher.name][b]).length;
        if (tA !== tB) return tA - tB;
        // Then prefer days where class has fewer periods filled
        const cA = Object.keys(timetable[classDiv][a]).length;
        const cB = Object.keys(timetable[classDiv][b]).length;
        return cA - cB;
    });

    // Slight randomization among equal-priority days
    for (let i = 0; i < days.length - 1; i++) {
        const countI = Object.values(timetable[classDiv][days[i]]).filter(s => s.subject === subject).length;
        const countNext = Object.values(timetable[classDiv][days[i + 1]]).filter(s => s.subject === subject).length;
        if (countI === countNext && Math.random() < 0.35) {
            [days[i], days[i + 1]] = [days[i + 1], days[i]];
        }
    }

    shuffleArray(periods);

    for (const day of days) {
        const subjectsToday = Object.values(timetable[classDiv][day])
            .filter(slot => slot.subject === subject).length;
        const maxPerDay = relaxed ? 3 : 2;
        if (subjectsToday >= maxPerDay) continue;

        for (const period of periods) {
            if (timetable[classDiv][day][period]) continue;
            if (period === 1 && teacher.isBlockHead) continue;
            if (teacherSchedule[teacher.name][day][period]) continue;

            const teacherPeriodsToday = Object.keys(teacherSchedule[teacher.name][day]).length;
            if (teacherPeriodsToday >= (teacher.maxPeriodsPerDay || 7)) continue;

            timetable[classDiv][day][period] = { subject, teacher: teacher.name };
            teacherSchedule[teacher.name][day][period] = classDiv;
            return true;
        }
    }

    return false;
}

function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
}

// ===== TIMETABLE VIEWS =====
function renderViewClass() {
    const data = getData();
    if (Object.keys(data.timetable).length === 0) {
        return emptyTimetableState();
    }

    const classDivs = Object.keys(data.timetable).sort();
    const selectedDiv = classDivs[0] || '';

    return `
        <div class="filter-bar">
            <label style="font-weight:600;">Select Class:</label>
            <select id="classDivSelect" onchange="renderClassTimetable()">
                ${classDivs.map(cd => `<option value="${cd}">Class ${cd}</option>`).join('')}
            </select>
            <div style="margin-left:auto;display:flex;gap:8px;">
                <button class="btn btn-outline btn-sm" onclick="printTimetable()"><i class="fas fa-print"></i> Print</button>
                <button class="btn btn-outline btn-sm" onclick="exportToPDF()"><i class="fas fa-file-pdf"></i> PDF</button>
                <button class="btn btn-outline btn-sm" onclick="exportToExcel('class')"><i class="fas fa-file-excel"></i> Excel</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-body" id="timetableDisplay">
                ${renderTimetableForClass(selectedDiv, data)}
            </div>
        </div>
    `;
}

function renderClassTimetable() {
    const data = getData();
    const selected = document.getElementById('classDivSelect').value;
    document.getElementById('timetableDisplay').innerHTML = renderTimetableForClass(selected, data);
}

function renderTimetableForClass(classDiv, data) {
    const schedule = data.timetable[classDiv];
    if (!schedule) return '<p>No timetable found.</p>';

    return `
        <h3 style="margin-bottom:16px;">Timetable for Class ${classDiv}</h3>
        <div class="table-container">
            <table class="timetable-grid">
                <thead>
                    <tr>
                        <th class="day-header">Day</th>
                        ${PERIODS.map((p, i) => `<th>Period ${p}<br><small>${PERIOD_TIMES[i]}</small></th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${DAYS.map(day => `
                        <tr>
                            <td class="day-header" style="background:var(--primary-dark);color:white;font-weight:700;">${day}</td>
                            ${PERIODS.map(p => {
                                const slot = schedule[day] && schedule[day][p];
                                if (slot) {
                                    return `<td>
                                        <div class="timetable-cell">
                                            <div class="subject">${slot.subject}</div>
                                            <div class="teacher">${slot.teacher}</div>
                                        </div>
                                    </td>`;
                                }
                                return `<td><span style="color:#ccc;">-</span></td>`;
                            }).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderViewTeacher() {
    const data = getData();
    if (Object.keys(data.timetable).length === 0) {
        return emptyTimetableState();
    }

    const teachers = data.teachers.map(t => t.name).sort();
    const selectedTeacher = teachers[0] || '';

    return `
        <div class="filter-bar">
            <label style="font-weight:600;">Select Teacher:</label>
            <select id="teacherSelect" onchange="renderTeacherTimetable()">
                ${teachers.map(t => `<option value="${t}">${t}</option>`).join('')}
            </select>
            <div style="margin-left:auto;display:flex;gap:8px;">
                <button class="btn btn-outline btn-sm" onclick="printTimetable()"><i class="fas fa-print"></i> Print</button>
                <button class="btn btn-outline btn-sm" onclick="exportToPDF()"><i class="fas fa-file-pdf"></i> PDF</button>
                <button class="btn btn-outline btn-sm" onclick="exportToExcel('teacher')"><i class="fas fa-file-excel"></i> Excel</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-body" id="timetableDisplay">
                ${renderTimetableForTeacher(selectedTeacher, data)}
            </div>
        </div>
    `;
}

function renderTeacherTimetable() {
    const data = getData();
    const selected = document.getElementById('teacherSelect').value;
    document.getElementById('timetableDisplay').innerHTML = renderTimetableForTeacher(selected, data);
}

function renderTimetableForTeacher(teacherName, data) {
    // Build teacher schedule from all class timetables
    const schedule = {};
    DAYS.forEach(day => { schedule[day] = {}; });

    Object.entries(data.timetable).forEach(([classDiv, classSchedule]) => {
        DAYS.forEach(day => {
            if (classSchedule[day]) {
                PERIODS.forEach(p => {
                    const slot = classSchedule[day][p];
                    if (slot && slot.teacher === teacherName) {
                        schedule[day][p] = { subject: slot.subject, classDiv };
                    }
                });
            }
        });
    });

    const totalPeriods = DAYS.reduce((sum, day) => sum + Object.keys(schedule[day]).length, 0);

    return `
        <h3 style="margin-bottom:8px;">Timetable for ${teacherName}</h3>
        <p style="color:var(--text-light);margin-bottom:16px;">Total periods/week: <strong>${totalPeriods}</strong></p>
        <div class="table-container">
            <table class="timetable-grid">
                <thead>
                    <tr>
                        <th class="day-header">Day</th>
                        ${PERIODS.map((p, i) => `<th>Period ${p}<br><small>${PERIOD_TIMES[i]}</small></th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${DAYS.map(day => `
                        <tr>
                            <td class="day-header" style="background:var(--primary-dark);color:white;font-weight:700;">${day}</td>
                            ${PERIODS.map(p => {
                                const slot = schedule[day][p];
                                if (slot) {
                                    return `<td>
                                        <div class="timetable-cell">
                                            <div class="subject">${slot.subject}</div>
                                            <div class="class-info">Class ${slot.classDiv}</div>
                                        </div>
                                    </td>`;
                                }
                                return `<td style="background:#f0fdf4;"><span style="color:#86efac;">Free</span></td>`;
                            }).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderViewBlock() {
    const data = getData();
    if (Object.keys(data.timetable).length === 0) {
        return emptyTimetableState();
    }

    const blocks = data.blocks.map(b => b.name);
    if (blocks.length === 0) {
        return `<div class="empty-state"><i class="fas fa-building"></i><h3>No Blocks Defined</h3><p>Add blocks and assign classes to them first.</p></div>`;
    }

    const selectedBlock = blocks[0];

    return `
        <div class="filter-bar">
            <label style="font-weight:600;">Select Block:</label>
            <select id="blockSelect" onchange="renderBlockTimetable()">
                ${blocks.map(b => `<option value="${b}">${b}</option>`).join('')}
            </select>
            <div style="margin-left:auto;display:flex;gap:8px;">
                <button class="btn btn-outline btn-sm" onclick="printTimetable()"><i class="fas fa-print"></i> Print</button>
                <button class="btn btn-outline btn-sm" onclick="exportToPDF()"><i class="fas fa-file-pdf"></i> PDF</button>
                <button class="btn btn-outline btn-sm" onclick="exportToExcel('block')"><i class="fas fa-file-excel"></i> Excel</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-body" id="timetableDisplay">
                ${renderTimetableForBlock(selectedBlock, data)}
            </div>
        </div>
    `;
}

function renderBlockTimetable() {
    const data = getData();
    const selected = document.getElementById('blockSelect').value;
    document.getElementById('timetableDisplay').innerHTML = renderTimetableForBlock(selected, data);
}

function renderTimetableForBlock(blockName, data) {
    // Find all classes in this block
    const blockClasses = data.classes.filter(c => c.block === blockName);
    if (blockClasses.length === 0) {
        return `<p>No classes assigned to ${blockName}.</p>`;
    }

    let html = `<h3 style="margin-bottom:16px;">Block: ${blockName}</h3>`;

    blockClasses.forEach(cls => {
        cls.divisions.forEach(div => {
            const key = `${cls.name}-${div}`;
            const schedule = data.timetable[key];
            if (schedule) {
                html += `
                    <h4 style="margin:16px 0 8px;">Class ${key}</h4>
                    <div class="table-container" style="margin-bottom:20px;">
                        <table class="timetable-grid">
                            <thead>
                                <tr>
                                    <th class="day-header">Day</th>
                                    ${PERIODS.map((p, i) => `<th>P${p}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${DAYS.map(day => `
                                    <tr>
                                        <td class="day-header" style="background:var(--primary-dark);color:white;font-weight:700;">${day.slice(0, 3)}</td>
                                        ${PERIODS.map(p => {
                                            const slot = schedule[day] && schedule[day][p];
                                            if (slot) {
                                                return `<td><div class="timetable-cell"><div class="subject" style="font-size:11px;">${slot.subject}</div><div class="teacher">${slot.teacher.split(' ')[0]}</div></div></td>`;
                                            }
                                            return `<td>-</td>`;
                                        }).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }
        });
    });

    return html;
}

function renderViewSchool() {
    const data = getData();
    if (Object.keys(data.timetable).length === 0) {
        return emptyTimetableState();
    }

    const daySelect = DAYS[0];

    return `
        <div class="filter-bar">
            <label style="font-weight:600;">Select Day:</label>
            <select id="schoolDaySelect" onchange="renderSchoolTimetable()">
                ${DAYS.map(d => `<option value="${d}">${d}</option>`).join('')}
            </select>
            <div style="margin-left:auto;display:flex;gap:8px;">
                <button class="btn btn-outline btn-sm" onclick="printTimetable()"><i class="fas fa-print"></i> Print</button>
                <button class="btn btn-outline btn-sm" onclick="exportToPDF()"><i class="fas fa-file-pdf"></i> PDF</button>
                <button class="btn btn-outline btn-sm" onclick="exportToExcel('school')"><i class="fas fa-file-excel"></i> Excel</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-body" id="timetableDisplay">
                ${renderSchoolForDay(daySelect, data)}
            </div>
        </div>
    `;
}

function renderSchoolTimetable() {
    const data = getData();
    const selected = document.getElementById('schoolDaySelect').value;
    document.getElementById('timetableDisplay').innerHTML = renderSchoolForDay(selected, data);
}

function renderSchoolForDay(day, data) {
    const classDivs = Object.keys(data.timetable).sort();

    return `
        <h3 style="margin-bottom:16px;">School Timetable — ${day}</h3>
        <div class="table-container">
            <table class="timetable-grid">
                <thead>
                    <tr>
                        <th class="day-header">Class</th>
                        ${PERIODS.map((p, i) => `<th>Period ${p}<br><small>${PERIOD_TIMES[i]}</small></th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${classDivs.map(cd => {
                        const schedule = data.timetable[cd];
                        return `
                            <tr>
                                <td style="font-weight:700;background:var(--bg);">Class ${cd}</td>
                                ${PERIODS.map(p => {
                                    const slot = schedule[day] && schedule[day][p];
                                    if (slot) {
                                        return `<td><div class="timetable-cell"><div class="subject">${slot.subject}</div><div class="teacher">${slot.teacher}</div></div></td>`;
                                    }
                                    return `<td>-</td>`;
                                }).join('')}
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function emptyTimetableState() {
    return `
        <div class="empty-state">
            <i class="fas fa-calendar-times"></i>
            <h3>No Timetable Generated</h3>
            <p>Generate a timetable first to view it here.</p>
            <button class="btn btn-primary" onclick="navigateTo('generate')"><i class="fas fa-magic"></i> Generate Timetable</button>
        </div>
    `;
}

// ===== UTILITY FUNCTIONS =====
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.remove();
}

function showToast(message, type = '') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function printTimetable() {
    window.print();
}

// ===== EXPORT FUNCTIONS =====
function exportToPDF() {
    window.print();
}

function exportToExcel(type) {
    const data = getData();
    let csv = '';
    let filename = 'timetable';

    if (type === 'class') {
        const classDiv = document.getElementById('classDivSelect')?.value;
        if (!classDiv) return;
        filename = `timetable-class-${classDiv}`;
        csv = generateClassCSV(classDiv, data);
    } else if (type === 'teacher') {
        const teacher = document.getElementById('teacherSelect')?.value;
        if (!teacher) return;
        filename = `timetable-teacher-${teacher.replace(/\s+/g, '_')}`;
        csv = generateTeacherCSV(teacher, data);
    } else if (type === 'block') {
        const block = document.getElementById('blockSelect')?.value;
        if (!block) return;
        filename = `timetable-block-${block.replace(/\s+/g, '_')}`;
        csv = generateBlockCSV(block, data);
    } else if (type === 'school') {
        const day = document.getElementById('schoolDaySelect')?.value;
        if (!day) return;
        filename = `timetable-school-${day}`;
        csv = generateSchoolCSV(day, data);
    }

    downloadCSV(csv, filename + '.csv');
}

function generateClassCSV(classDiv, data) {
    const schedule = data.timetable[classDiv];
    if (!schedule) return '';
    let csv = `Timetable for Class ${classDiv}\n\n`;
    csv += 'Day,' + PERIODS.map((p, i) => `Period ${p} (${PERIOD_TIMES[i]})`).join(',') + '\n';
    DAYS.forEach(day => {
        const row = [day];
        PERIODS.forEach(p => {
            const slot = schedule[day] && schedule[day][p];
            row.push(slot ? `${slot.subject} - ${slot.teacher}` : '-');
        });
        csv += row.join(',') + '\n';
    });
    return csv;
}

function generateTeacherCSV(teacherName, data) {
    let csv = `Timetable for ${teacherName}\n\n`;
    csv += 'Day,' + PERIODS.map((p, i) => `Period ${p} (${PERIOD_TIMES[i]})`).join(',') + '\n';

    DAYS.forEach(day => {
        const row = [day];
        PERIODS.forEach(p => {
            let found = null;
            Object.entries(data.timetable).forEach(([classDiv, classSchedule]) => {
                const slot = classSchedule[day] && classSchedule[day][p];
                if (slot && slot.teacher === teacherName) {
                    found = `${slot.subject} (${classDiv})`;
                }
            });
            row.push(found || 'Free');
        });
        csv += row.join(',') + '\n';
    });
    return csv;
}

function generateBlockCSV(blockName, data) {
    const blockClasses = data.classes.filter(c => c.block === blockName);
    let csv = `Block: ${blockName}\n\n`;

    blockClasses.forEach(cls => {
        cls.divisions.forEach(div => {
            const key = `${cls.name}-${div}`;
            const schedule = data.timetable[key];
            if (schedule) {
                csv += `\nClass ${key}\n`;
                csv += 'Day,' + PERIODS.map(p => `P${p}`).join(',') + '\n';
                DAYS.forEach(day => {
                    const row = [day];
                    PERIODS.forEach(p => {
                        const slot = schedule[day] && schedule[day][p];
                        row.push(slot ? `${slot.subject}` : '-');
                    });
                    csv += row.join(',') + '\n';
                });
            }
        });
    });
    return csv;
}

function generateSchoolCSV(day, data) {
    const classDivs = Object.keys(data.timetable).sort();
    let csv = `School Timetable - ${day}\n\n`;
    csv += 'Class,' + PERIODS.map((p, i) => `Period ${p} (${PERIOD_TIMES[i]})`).join(',') + '\n';

    classDivs.forEach(cd => {
        const schedule = data.timetable[cd];
        const row = [`Class ${cd}`];
        PERIODS.forEach(p => {
            const slot = schedule[day] && schedule[day][p];
            row.push(slot ? `${slot.subject} - ${slot.teacher}` : '-');
        });
        csv += row.join(',') + '\n';
    });
    return csv;
}

function downloadCSV(csv, filename) {
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Exported successfully!', 'success');
}

// ===== EXCEL UPLOAD =====
async function handleExcelUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    event.target.value = '';

    try {
        const data = await file.arrayBuffer();
        const workbook = XLSX.read(data, { type: 'array' });
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });

        // Parse: each division becomes its own class entry
        const classes = [];
        let currentDiv = null;

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            if (!row || row.length === 0) continue;

            const [cls, division, block, type, classTeacher, subject, teacher, periods] = row;

            // Skip header rows and separator rows
            if (cls === 'Class' || subject === 'Subject') continue;
            if (String(cls).startsWith('---')) continue;

            // New division starts when Column A (Class) AND Column B (Division) have values
            if (cls && String(cls).trim() && division && String(division).trim()) {
                if (currentDiv) classes.push(currentDiv);
                currentDiv = {
                    name: String(cls).trim(),
                    divisions: [String(division).trim().toUpperCase()],
                    block: String(block || '').trim(),
                    classType: String(type || '').trim(),
                    classTeacher: String(classTeacher || '').trim(),
                    subjects: []
                };
            }

            // Add subject if present
            if (currentDiv && subject && String(subject).trim()) {
                const periodsNum = parseInt(periods) || 0;
                if (periodsNum > 0) {
                    currentDiv.subjects.push({
                        name: String(subject).trim(),
                        teacher: String(teacher || '').trim(),
                        periodsPerWeek: periodsNum
                    });
                }
            }
        }
        if (currentDiv) classes.push(currentDiv);

        if (classes.length === 0) {
            showToast('No valid class data found in the file', 'error');
            return;
        }

        // Validate
        let errors = [];
        classes.forEach(cls => {
            const total = cls.subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0);
            if (total !== 35) {
                errors.push(`Class ${cls.name}-${cls.divisions[0]}: total = ${total} (must be 35)`);
            }
            cls.subjects.forEach(sub => {
                if (!sub.teacher) {
                    errors.push(`Class ${cls.name}-${cls.divisions[0]}: no teacher for ${sub.name}`);
                }
            });
        });

        if (errors.length > 0) {
            const msg = errors.slice(0, 3).join('\n');
            showToast(`Errors: ${errors[0]}`, 'error');
            console.log('All errors:', errors);
            if (!confirm(`Found ${errors.length} error(s):\n${msg}${errors.length > 3 ? '\n...' : ''}\n\nUpload anyway (skip invalid)?`)) {
                return;
            }
            // Filter out invalid
            const valid = classes.filter(cls => {
                const total = cls.subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0);
                return total === 35 && cls.subjects.every(s => s.teacher);
            });
            if (valid.length === 0) { showToast('No valid entries to upload', 'error'); return; }
            classes.length = 0;
            classes.push(...valid);
        }

        // Save each class-division to API
        let created = 0;
        for (const cls of classes) {
            await apiPost('/classes', cls);
            created++;
        }

        await fetchData();
        showToast(`${created} class-division(s) created from Excel!`, 'success');
        renderPage('classes');

    } catch (e) {
        showToast('Error reading Excel file: ' + e.message, 'error');
        console.error(e);
    }
}

// ===== INIT =====
fetchData().then(() => {
    renderPage('dashboard');
});
