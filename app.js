// ===== School Timetable Management System =====
// Data stored in Python backend with SQLite

// ===== DATA LAYER =====
const API_BASE = '/api';
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const PERIODS = [1, 2, 3, 4, 5, 6, 7];
const PERIOD_TIMES = [
    '9:45 - 10:30', '10:30 - 11:15', '11:25 - 12:05', '12:05 - 12:45',
    '1:45 - 2:30', '2:30 - 3:10', '3:20 - 4:00'
];

const PERIOD_TIMES_FRIDAY = [
    '9:30 - 10:15', '10:15 - 11:00', '11:10 - 11:50', '11:50 - 12:30',
    '2:00 - 2:40', '2:40 - 3:20', '3:30 - 4:00'
];

function getPeriodTime(index, day) {
    if (day === 'Friday') return PERIOD_TIMES_FRIDAY[index] || '';
    return PERIOD_TIMES[index] || '';
}

const ALL_SUBJECTS_8_9 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT',
    'PET', 'Music', 'Work Experience', 'Art'
];

const ALL_SUBJECTS_8 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT',
    'PET', 'Music', 'Art'
];

const ALL_SUBJECTS_9 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT',
    'PET', 'Art', 'Work Experience'
];

const ALL_SUBJECTS_10 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT'
];

// Special subjects with fixed 1 period/week for class 8 and 9
const SPECIAL_SUBJECTS = ['PET', 'Music', 'Work Experience', 'Art'];

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
    const uniqueClasses = [...new Set(data.classes.map(c => c.name))];
    const totalDivisions = data.classes.length;
    const hasTimeTable = Object.keys(data.timetable).length > 0;

    return `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon blue"><i class="fas fa-chalkboard"></i></div>
                <div class="stat-info">
                    <h3>${uniqueClasses.length}</h3>
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

    // Get unique class names and blocks for bulk delete
    const uniqueClasses = [...new Set(data.classes.map(c => c.name))].sort();
    const uniqueBlocks = [...new Set(data.classes.map(c => c.block).filter(b => b))].sort();

    return `
        <div class="panel">
            <div class="panel-header">
                <h2>Classes</h2>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">
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
                    <div class="filter-bar" style="margin-bottom:12px;">
                        <input type="text" class="form-control" id="classSearch" placeholder="Search division, block..." 
                            style="max-width:200px;" oninput="filterClasses()">
                        <select id="classClassFilter" class="form-control" style="width:auto;padding:6px 12px;font-size:13px;" onchange="filterClasses()">
                            <option value="">All Classes</option>
                            ${uniqueClasses.map(c => `<option value="${c}">Class ${c}</option>`).join('')}
                        </select>
                        <select id="classBlockFilter" class="form-control" style="width:auto;padding:6px 12px;font-size:13px;" onchange="filterClasses()">
                            <option value="">All Blocks</option>
                            ${uniqueBlocks.map(b => `<option value="${b}">${b}</option>`).join('')}
                        </select>
                    </div>
                    <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;align-items:center;">
                        <span style="font-weight:600;font-size:13px;color:var(--text-light);">Bulk Delete:</span>
                        <select id="bulkDeleteClass" class="form-control" style="width:auto;padding:6px 12px;font-size:13px;">
                            <option value="">By Class</option>
                            ${uniqueClasses.map(c => `<option value="${c}">Class ${c}</option>`).join('')}
                        </select>
                        <select id="bulkDeleteBlock" class="form-control" style="width:auto;padding:6px 12px;font-size:13px;">
                            <option value="">By Block</option>
                            ${uniqueBlocks.map(b => `<option value="${b}">${b}</option>`).join('')}
                        </select>
                        <button class="btn btn-sm btn-danger" onclick="bulkDeleteClasses()"><i class="fas fa-trash"></i> Delete Selected</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteAllClasses()" style="margin-left:auto;"><i class="fas fa-trash-alt"></i> Delete All</button>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Class</th>
                                    <th>Division</th>
                                    <th>Block</th>
                                    <th>Type</th>
                                    <th>Subjects</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="classTableBody">
                                ${data.classes.map((c, idx) => `
                                    <tr data-name="${c.divisions[0]?.toLowerCase() || ''}" data-block="${c.block || ''}" data-class="${c.name}">
                                        <td><strong>Class ${c.name}</strong></td>
                                        <td>${c.divisions.map(d => `<span class="chip">${d}</span>`).join('')}</td>
                                        <td><span class="badge badge-primary">${c.block || '-'}</span></td>
                                        <td><span style="font-size:12px;">${c.classType || '-'}</span></td>
                                        <td>
                                            ${getClassPeriodTotal(c)} periods
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

async function bulkDeleteClasses() {
    const data = getData();
    const byClass = document.getElementById('bulkDeleteClass').value;
    const byBlock = document.getElementById('bulkDeleteBlock').value;

    if (!byClass && !byBlock) {
        showToast('Please select a Class or Block to delete', 'warning');
        return;
    }

    let toDelete = data.classes;
    let desc = '';
    let params = [];

    if (byClass && byBlock) {
        toDelete = toDelete.filter(c => c.name === byClass && c.block === byBlock);
        desc = `Class ${byClass} in ${byBlock}`;
        params = [`className=${byClass}`, `block=${byBlock}`];
    } else if (byClass) {
        toDelete = toDelete.filter(c => c.name === byClass);
        desc = `all Class ${byClass} divisions`;
        params = [`className=${byClass}`];
    } else if (byBlock) {
        toDelete = toDelete.filter(c => c.block === byBlock);
        desc = `all classes in ${byBlock}`;
        params = [`block=${byBlock}`];
    }

    if (toDelete.length === 0) {
        showToast('No matching classes found', 'warning');
        return;
    }

    if (!confirm(`Delete ${toDelete.length} division(s) (${desc})?\n\nThis cannot be undone.`)) return;

    await fetch(`${API_BASE}/classes?${params.join('&')}`, { method: 'DELETE' });
    await fetchData();
    showToast(`${toDelete.length} division(s) deleted`, 'success');
    renderPage('classes');
}

async function deleteAllClasses() {
    const data = getData();
    if (data.classes.length === 0) return;

    if (!confirm(`⚠️ Delete ALL ${data.classes.length} class divisions?\n\nThis cannot be undone!`)) return;
    if (!confirm(`Are you absolutely sure? This will remove ALL class data.`)) return;

    await fetch(`${API_BASE}/classes`, { method: 'DELETE' });
    await fetchData();
    showToast('All classes deleted', 'success');
    renderPage('classes');
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
    let subjects;
    if (classNum === 10) subjects = ALL_SUBJECTS_10;
    else if (classNum === 8) subjects = ALL_SUBJECTS_8;
    else subjects = ALL_SUBJECTS_9;

    const defaultPeriods = {
        'PET': 1, 'Music': 1, 'Work Experience': 1, 'Art': 1
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
            <strong>Total:</strong> <span id="totalPeriodsCount">0</span> / <span id="targetPeriods">35</span> periods
            <small style="display:block;margin-top:4px;">Class 8 & 9: enter 32 (PET/Music/Art auto-added). Class 10: must equal 35.</small>
        </div>
        <script>
            setTimeout(() => {
                const inputs = document.querySelectorAll('[data-subject]');
                const updateTotal = () => {
                    let total = 0;
                    inputs.forEach(inp => { total += parseInt(inp.value) || 0; });
                    const el = document.getElementById('totalPeriodsCount');
                    const classNum = document.getElementById('className')?.value;
                    const target = (classNum === '8' || classNum === '9') ? 32 : 35;
                    const targetEl = document.getElementById('targetPeriods');
                    if (targetEl) targetEl.textContent = target;
                    if (el) {
                        el.textContent = total;
                        el.style.color = total === target ? 'var(--success)' : (total > target ? 'var(--danger)' : 'var(--text)');
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

    // Check if class-division already exists (when adding new)
    if (editIdx === null) {
        const existing = data.classes.filter(c => c.name === className);
        const existingDivs = existing.flatMap(c => c.divisions);
        const conflicts = uniqueDivisions.filter(d => existingDivs.includes(d));
        if (conflicts.length > 0) {
            showToast(`Class ${className} division(s) ${conflicts.join(', ')} already exist!`, 'error');
            return;
        }
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
    const isClass8or9 = (className === '8' || className === '9');

    if (!isClass8or9 && totalPeriods !== 35) {
        showToast(`Total periods must be 35 (5 days × 7 periods). Current: ${totalPeriods}`, 'warning');
        return;
    }

    // Auto-add special subjects for class 8 & 9 only if missing and total < 35
    if (isClass8or9 && totalPeriods < 35) {
        const specialSubjects = [];
        // PET: class 8 and 9
        specialSubjects.push({ name: 'PET', periodsPerWeek: 1, teacher: 'Shajir' });
        // Music: class 8 only
        if (className === '8') {
            specialSubjects.push({ name: 'Music', periodsPerWeek: 1, teacher: 'Divya' });
        }
        // Art: class 8 and 9
        specialSubjects.push({ name: 'Art', periodsPerWeek: 1, teacher: 'Udayesh' });
        // Work Experience: class 9 only
        if (className === '9') {
            specialSubjects.push({ name: 'Work Experience', periodsPerWeek: 1, teacher: 'Sheeba' });
        }
        for (const sp of specialSubjects) {
            const currentTotal = subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0);
            if (currentTotal >= 35) break;
            if (!subjects.find(s => s.name === sp.name)) {
                subjects.push(sp);
            }
        }
    }

    // Final validation
    const finalTotal = subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0);
    if (finalTotal !== 35) {
        showToast(`Total periods must be 35. Current: ${finalTotal}`, 'warning');
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
        showLoading('Saving class...');
        try {
            const classData = { name: className, divisions: uniqueDivisions, block, classType, classTeacher, subjects };
            if (editIdx !== null) {
                await apiPut(`/classes/${data.classes[editIdx].id}`, classData);
            } else {
                await apiPost('/classes', classData);
            }
            await fetchData();
            hideLoading();
            closeModal('classModal');
            showToast(`Class ${className} ${editIdx !== null ? 'updated' : 'created'}!`, 'success');
            renderPage('classes');
        } catch (e) { hideLoading(); showToast('Error saving class', 'error'); }
    };
    doSave();
}

// Helper: calculate class total periods counting shared only once
function getClassPeriodTotal(cls) {
    let total = 0;
    const counted = new Set();
    (cls.subjects || []).forEach(sub => {
        if (sub.shared && sub.sharedGroup) {
            if (!counted.has(sub.sharedGroup)) {
                counted.add(sub.sharedGroup);
                total += sub.periodsPerWeek;
            }
        } else if (sub.periodsPerWeek > 0) {
            total += sub.periodsPerWeek;
        }
    });
    return total;
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
                <p><strong>Total Periods/Week:</strong> ${getClassPeriodTotal(cls)}</p>
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
                <h2>Teachers (${data.teachers.length})</h2>
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
                    <div class="filter-bar" style="margin-bottom:16px;">
                        <input type="text" class="form-control" id="teacherSearch" placeholder="Search teacher name..." 
                            style="max-width:250px;" oninput="filterTeachers()">
                    </div>
                    <div class="table-container" id="teacherTableContainer">
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
                            <tbody id="teacherTableBody">
                                ${data.teachers.map((t, idx) => {
                                    const total = teacherTotalPeriods[t.name] || 0;
                                    const maxWeek = (t.maxPeriodsPerDay || 6) * 5;
                                    const overloaded = total > maxWeek;
                                    return `
                                    <tr data-name="${t.name.toLowerCase()}">
                                        <td><strong>${t.name}</strong></td>
                                        <td>${t.subjects && t.subjects.length > 0 ? t.subjects.map(s => `<span class="chip">${s}</span>`).join('') : '<span style="color:var(--text-light);font-size:12px;">Not yet assigned</span>'}</td>
                                        <td>
                                            <strong style="color:${overloaded ? 'var(--danger)' : 'var(--text)'};">${total}</strong>
                                            <span style="color:var(--text-light);font-size:11px;">/ ${maxWeek} max</span>
                                            ${overloaded ? '<span class="badge badge-danger" style="margin-left:4px;">Overloaded</span>' : ''}
                                        </td>
                                        <td>${t.isBlockHead ? `<span class="badge badge-warning">${t.headOfBlock}</span>` : '-'}</td>
                                        <td>${t.maxPeriodsPerDay || 6}</td>
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
                        min="1" max="7" value="${teacher ? (teacher.maxPeriodsPerDay || 6) : 5}">
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
        showLoading('Saving teacher...');
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
            hideLoading();
            closeModal('teacherModal');
            showToast(`Teacher ${name} ${editIdx !== null ? 'updated' : 'added'}!`, 'success');
            renderPage('teachers');
        } catch (e) { hideLoading(); showToast('Error saving teacher', 'error'); }
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
                    <div class="filter-bar" style="margin-bottom:16px;">
                        <input type="text" class="form-control" id="blockSearch" placeholder="Search block name..." 
                            style="max-width:250px;" oninput="filterBlocks()">
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr><th>Block Name</th><th>Head</th><th>Description</th><th>Classes Assigned</th><th>Actions</th></tr>
                            </thead>
                            <tbody id="blockTableBody">
                                ${data.blocks.map((b, idx) => {
                                    const assignedClasses = data.classes.filter(c => c.block === b.name);
                                    return `
                                        <tr data-name="${b.name.toLowerCase()}">
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
        showLoading('Saving block...');
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
            hideLoading();
            closeModal('blockModal');
            showToast(`Block ${name} ${editIdx !== null ? 'updated' : 'added'}!`, 'success');
            renderPage('blocks');
        } catch (e) { hideLoading(); showToast('Error saving block', 'error'); }
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
                    <button class="btn btn-outline" onclick="showTimetableHistory()" style="margin-left:12px;">
                        <i class="fas fa-history"></i> History
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
    const MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience'];
    const MAX_PET_PER_SLOT = 5;
    const MAX_ART_PER_SLOT = 2; // strictly 2 classes max at a time

    // Build needs: for each classDiv, what subjects need to be scheduled
    const classDivs = [];
    const needs = {}; // classDiv -> [{subject, teacher, count, shared, sharedGroup}]

    data.classes.forEach(cls => {
        cls.divisions.forEach(div => {
            const key = `${cls.name}-${div}`;
            classDivs.push(key);
            needs[key] = [];
            const processedGroups = new Set();

            cls.subjects.forEach(sub => {
                if (sub.periodsPerWeek > 0 && sub.teacher) {
                    if (sub.shared && sub.sharedGroup) {
                        if (!processedGroups.has(sub.sharedGroup)) {
                            processedGroups.add(sub.sharedGroup);
                            // Find all teachers in this group
                            const groupTeachers = cls.subjects
                                .filter(s => s.sharedGroup === sub.sharedGroup)
                                .map(s => ({ teacher: s.teacher, subject: s.name }));
                            needs[key].push({
                                subject: groupTeachers.map(g => g.subject).join('/'),
                                teacher: groupTeachers.map(g => g.teacher).join('/'),
                                teachers: groupTeachers.map(g => g.teacher),
                                count: sub.periodsPerWeek,
                                shared: true,
                                isMultiClass: false
                            });
                        }
                    } else {
                        needs[key].push({
                            subject: sub.name,
                            teacher: sub.teacher,
                            teachers: [sub.teacher],
                            count: sub.periodsPerWeek,
                            shared: false,
                            isMultiClass: MULTI_CLASS_SUBJECTS.includes(sub.name)
                        });
                    }
                }
            });
        });
    });

    // Class teacher map
    const classTeacherMap = {};
    data.classes.forEach(cls => {
        cls.divisions.forEach(div => {
            const key = `${cls.name}-${div}`;
            if (cls.classTeacher) classTeacherMap[key] = cls.classTeacher;
        });
    });

    let bestFailCount = Infinity;
    let bestTimetable = null;
    let lastFailedDetails = {};
    const maxAttempts = 50;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        // Init timetable and remaining counts
        const timetable = {};
        const teacherBusy = {}; // teacher -> day -> period -> true
        const remaining = {}; // classDiv -> copy of needs with count

        classDivs.forEach(cd => {
            timetable[cd] = {};
            DAYS.forEach(d => { timetable[cd][d] = {}; });
            remaining[cd] = needs[cd].map(n => ({ ...n, left: n.count }));
        });

        data.teachers.forEach(t => {
            teacherBusy[t.name] = {};
            DAYS.forEach(d => { teacherBusy[t.name][d] = {}; });
        });

        // STEP 1: Place class teachers in period 1 (soft priority)
        const ctEntries = Object.entries(classTeacherMap);
        shuffleArray(ctEntries);
        for (const [cd, ctName] of ctEntries) {
            if (!teacherBusy[ctName]) continue;
            const teacher = data.teachers.find(t => t.name === ctName);
            if (!teacher || teacher.isBlockHead) continue;

            const days = [...DAYS]; shuffleArray(days);
            for (const day of days) {
                if (timetable[cd][day][1]) continue;
                if (teacherBusy[ctName][day][1]) continue;

                // Find a subject this class teacher teaches
                const sub = remaining[cd].find(r => r.left > 0 && !r.shared && r.teachers.includes(ctName) && !r.isMultiClass);
                if (sub) {
                    timetable[cd][day][1] = { subject: sub.subject, teacher: sub.teacher };
                    teacherBusy[ctName][day][1] = true;
                    sub.left--;
                    break;
                }
            }
        }

        // STEP 2: Slot-by-slot scheduling
        // ===== SCHEDULING CONSTRAINTS =====
        const SCIENCE_SUBJECTS = ['Physics', 'Chemistry', 'Biology'];
        const SCIENCE_HARD_NO = [7]; // strictly prohibited
        const SCIENCE_SOFT_NO = [5, 6]; // should avoid but not strict
        const FEEDING_MOTHERS = ['Jaleela', 'Shafeedha'];
        const FRIDAY_NO_P4 = ['Swalih', 'Fuaad', 'Bavakutty']; // no period 4 on Friday only
        const RASHID_NO_PERIODS = [1, 4]; // daily
        const FRIDAY_RESTRICTED = ['Saheer', 'Yasir']; // no periods 4,5 on Friday
        const NO_PERIOD_1 = ['Bindya']; // no period 1 daily
        const ART_PREFERRED_PERIODS = [6, 7];

        const dayOrder = [...DAYS];
        const periodOrder = [...PERIODS];
        if (attempt % 2 === 1) { shuffleArray(dayOrder); }

        for (const day of dayOrder) {
            const pOrder = [...periodOrder];
            // Don't shuffle periods - process in order to ensure rules like feeding mothers work
            // (P4 must be processed before P5 to check correctly)

            for (const period of pOrder) {
                const cdOrder = [...classDivs];
                // Prioritize classes that have restricted teachers needing this period
                const RESTRICTED_TEACHERS = ['Rashid', 'Bindya', 'Jaleela', 'Shafeedha', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty'];
                cdOrder.sort((a, b) => {
                    // Classes with restricted teachers get priority
                    const hasRestrictedA = remaining[a].some(r => r.left > 0 && r.teachers.some(t => RESTRICTED_TEACHERS.includes(t.trim())));
                    const hasRestrictedB = remaining[b].some(r => r.left > 0 && r.teachers.some(t => RESTRICTED_TEACHERS.includes(t.trim())));
                    if (hasRestrictedA && !hasRestrictedB) return -1;
                    if (!hasRestrictedA && hasRestrictedB) return 1;
                    const remA = remaining[a].reduce((s, r) => s + r.left, 0);
                    const remB = remaining[b].reduce((s, r) => s + r.left, 0);
                    return remB - remA;
                });
                if (Math.random() < 0.2) shuffleArray(cdOrder);

                const usedTeachersThisSlot = new Set();
                let petUsed = 0;
                let artUsed = 0;

                for (const cd of cdOrder) {
                    if (timetable[cd][day][period]) continue;

                    const candidates = remaining[cd].filter(r => {
                        if (r.left <= 0) return false;

                        const subToday = Object.values(timetable[cd][day]).filter(s => s.subject === r.subject).length;
                        if (subToday >= 2) return false;

                        // Rule 2: Science - HARD NO for period 7, soft avoid for 5,6
                        if (SCIENCE_SUBJECTS.includes(r.subject)) {
                            if (SCIENCE_HARD_NO.includes(period)) return false;
                            if (SCIENCE_SOFT_NO.includes(period)) return false; // prefer morning
                        }

                        // Rule 1: Art - strictly max 2 classes simultaneous, preferred periods 6,7
                        if (r.subject === 'Art') {
                            if (artUsed >= MAX_ART_PER_SLOT) return false;
                        }

                        if (r.isMultiClass) {
                            if (r.subject === 'PET' && petUsed >= MAX_PET_PER_SLOT) return false;
                            return true;
                        }

                        if (r.shared) {
                            return r.teachers.every(t => {
                                if (!teacherBusy[t]) return true;
                                if (teacherBusy[t][day][period]) return false;
                                if (usedTeachersThisSlot.has(t)) return false;
                                // Strict rules for shared teachers too
                                if (t.trim() === 'Rashid' && (period === 1 || period === 4)) return false;
                                if (t.trim() === 'Bindya' && period === 1) return false;
                                if ((t.trim() === 'Saheer' || t.trim() === 'Yasir') && day === 'Friday' && (period === 4 || period === 5)) return false;
                                if ((t.trim() === 'Swalih' || t.trim() === 'Fuaad' || t.trim() === 'Bavakutty') && day === 'Friday' && period === 4) return false;
                                if ((t.trim() === 'Jaleela' || t.trim() === 'Shafeedha') && (period === 4 || period === 5)) {
                                    const otherPeriod = period === 4 ? 5 : 4;
                                    if (teacherBusy[t] && teacherBusy[t][day] && teacherBusy[t][day][otherPeriod]) return false;
                                }
                                return true;
                            });
                        }

                        // Normal teacher checks
                        const t = r.teachers[0];
                        if (!t) return false;

                        // ===== STRICT TEACHER RULES (checked first) =====
                        // Rule 10: Rashid - no P1 and P4 daily
                        if (t.trim() === 'Rashid' && (period === 1 || period === 4)) return false;
                        // Rule 13: Bindya - no P1 daily
                        if (t.trim() === 'Bindya' && period === 1) return false;
                        // Rule 6: Feeding mothers - either P4 or P5 must be free
                        if ((t.trim() === 'Jaleela' || t.trim() === 'Shafeedha') && (period === 4 || period === 5)) {
                            const otherPeriod = period === 4 ? 5 : 4;
                            if (teacherBusy[t] && teacherBusy[t][day] && teacherBusy[t][day][otherPeriod]) return false;
                            let otherBusy = false;
                            classDivs.forEach(otherCd => {
                                if (timetable[otherCd][day][otherPeriod] && 
                                    timetable[otherCd][day][otherPeriod].teacher &&
                                    timetable[otherCd][day][otherPeriod].teacher.includes(t)) {
                                    otherBusy = true;
                                }
                            });
                            if (otherBusy) return false;
                        }
                        // Rule 7: Swalih - Friday: no P4, IT only P5
                        if (t.trim() === 'Swalih' && day === 'Friday') {
                            if (period === 4) return false;
                            if (r.subject === 'IT' && period !== 5) return false;
                        }
                        // Rule 8,9: Fuaad, Bavakutty - no P4 Friday
                        if ((t.trim() === 'Fuaad' || t.trim() === 'Bavakutty' || t.trim() === 'Swalih') && day === 'Friday' && period === 4) return false;
                        // Rule 11: Saheer & Yasir - no P4,P5 Friday
                        if ((t.trim() === 'Saheer' || t.trim() === 'Yasir') && day === 'Friday' && (period === 4 || period === 5)) return false;
                        // ===== END STRICT RULES =====

                        if (usedTeachersThisSlot.has(t)) return false;
                        if (teacherBusy[t] && teacherBusy[t][day][period]) return false;

                        // Block head: no period 1
                        if (period === 1) {
                            const teacherObj = data.teachers.find(tc => tc.name === t);
                            if (teacherObj && teacherObj.isBlockHead) return false;
                        }

                        // Rule 3: Max periods per day
                        // Non-IT teachers: max 5/day
                        // IT teachers: can exceed 5 but must include IT
                        if (!r.isMultiClass && teacherBusy[t]) {
                            const periodsToday = Object.keys(teacherBusy[t][day]).filter(p => teacherBusy[t][day][p]).length;
                            const teacherObj = data.teachers.find(tc => tc.name === t);
                            const maxPeriods = teacherObj?.maxPeriodsPerDay || 6;
                            // Check if this teacher teaches IT (from their assignments)
                            const teachesIT = remaining[cd].some(s => s.teachers.includes(t) && s.subject === 'IT') ||
                                Object.values(timetable[cd][day]).some(s => s && s.teacher === t && s.subject === 'IT');
                            const isITTeacher = needs[cd] && needs[cd].some(n => n.teachers.includes(t) && n.subject === 'IT');
                            
                            if (isITTeacher) {
                                // IT teacher: allow up to maxPeriods (6)
                                if (periodsToday >= maxPeriods) return false;
                            } else {
                                // Non-IT teacher: max 5
                                if (periodsToday >= 5) return false;
                            }
                        }

                        return true;
                    });

                    if (candidates.length === 0) continue;

                    // Pick: prefer subjects whose teacher has fewer periods today (spread load)
                    // Rule 1: Art prefers periods 6,7
                    candidates.sort((a, b) => {
                        // Art preference for periods 6,7
                        if (a.subject === 'Art' && ART_PREFERRED_PERIODS.includes(period)) return -1;
                        if (b.subject === 'Art' && ART_PREFERRED_PERIODS.includes(period)) return 1;

                        const aLoad = a.teachers.reduce((sum, t) => {
                            return sum + (teacherBusy[t] ? Object.keys(teacherBusy[t][day]).filter(p => teacherBusy[t][day][p]).length : 0);
                        }, 0);
                        const bLoad = b.teachers.reduce((sum, t) => {
                            return sum + (teacherBusy[t] ? Object.keys(teacherBusy[t][day]).filter(p => teacherBusy[t][day][p]).length : 0);
                        }, 0);
                        if (aLoad !== bLoad) return aLoad - bLoad;
                        return b.left - a.left;
                    });
                    const pickIdx = (Math.random() < 0.3 && candidates.length > 1) ? 1 : 0;
                    const pick = candidates[pickIdx];

                    // Place it
                    timetable[cd][day][period] = { subject: pick.subject, teacher: pick.teacher, shared: pick.shared };
                    pick.left--;

                    if (pick.isMultiClass) {
                        if (pick.subject === 'PET') petUsed++;
                        if (pick.subject === 'Art') artUsed++;
                    } else {
                        // Mark teachers as used
                        pick.teachers.forEach(t => {
                            usedTeachersThisSlot.add(t);
                            if (teacherBusy[t]) teacherBusy[t][day][period] = true;
                        });
                    }
                }
            }
        }

        // STEP 3: Fill any remaining blanks with relaxed constraints (allow up to 7 periods/day)
        // But KEEP strict rules for feeding mothers, Rashid, Bindya, Friday restrictions
        classDivs.forEach(cd => {
            DAYS.forEach(day => {
                PERIODS.forEach(period => {
                    if (timetable[cd][day][period]) return; // already filled

                    const candidates = remaining[cd].filter(r => {
                        if (r.left <= 0) return false;
                        const subToday = Object.values(timetable[cd][day]).filter(s => s.subject === r.subject).length;
                        if (subToday >= 3) return false;

                        if (r.isMultiClass) return true;

                        if (r.shared) {
                            return r.teachers.every(t => {
                                if (!teacherBusy[t]) return true;
                                if (teacherBusy[t][day][period]) return false;
                                // Strict rules
                                if (t.trim() === 'Rashid' && (period === 1 || period === 4)) return false;
                                if (t.trim() === 'Bindya' && period === 1) return false;
                                if ((t.trim() === 'Saheer' || t.trim() === 'Yasir') && day === 'Friday' && (period === 4 || period === 5)) return false;
                                if ((t.trim() === 'Swalih' || t.trim() === 'Fuaad' || t.trim() === 'Bavakutty') && day === 'Friday' && period === 4) return false;
                                if ((t.trim() === 'Jaleela' || t.trim() === 'Shafeedha') && (period === 4 || period === 5)) {
                                    const otherPeriod = period === 4 ? 5 : 4;
                                    if (teacherBusy[t] && teacherBusy[t][day] && teacherBusy[t][day][otherPeriod]) return false;
                                }
                                return true;
                            });
                        }

                        const t = r.teachers[0];
                        if (!t) return false;

                        // ===== STRICT RULES (never relaxed) =====
                        if (t.trim() === 'Rashid' && (period === 1 || period === 4)) return false;
                        if (t.trim() === 'Bindya' && period === 1) return false;
                        if ((t.trim() === 'Jaleela' || t.trim() === 'Shafeedha') && (period === 4 || period === 5)) {
                            const otherPeriod = period === 4 ? 5 : 4;
                            if (teacherBusy[t] && teacherBusy[t][day] && teacherBusy[t][day][otherPeriod]) return false;
                            let otherBusy = false;
                            classDivs.forEach(otherCd => {
                                if (timetable[otherCd][day][otherPeriod] &&
                                    timetable[otherCd][day][otherPeriod].teacher &&
                                    timetable[otherCd][day][otherPeriod].teacher.includes(t)) {
                                    otherBusy = true;
                                }
                            });
                            if (otherBusy) return false;
                        }
                        if ((t.trim() === 'Swalih' || t.trim() === 'Fuaad' || t.trim() === 'Bavakutty') && day === 'Friday' && period === 4) return false;
                        if ((t.trim() === 'Saheer' || t.trim() === 'Yasir') && day === 'Friday' && (period === 4 || period === 5)) return false;
                        // ===== END STRICT =====

                        if (teacherBusy[t] && teacherBusy[t][day][period]) return false;
                        return true;
                    });

                    if (candidates.length > 0) {
                        candidates.sort((a, b) => b.left - a.left);
                        const pick = candidates[0];
                        timetable[cd][day][period] = { subject: pick.subject, teacher: pick.teacher, shared: pick.shared };
                        pick.left--;
                        if (!pick.isMultiClass) {
                            pick.teachers.forEach(t => {
                                if (teacherBusy[t]) teacherBusy[t][day][period] = true;
                            });
                        }
                    }
                });
            });
        });

        // STEP 4: Final check - all slots should be filled. If any remain, force-fill respecting rules
        // (This should rarely trigger if Steps 2+3 work correctly)
        classDivs.forEach(cd => {
            DAYS.forEach(day => {
                PERIODS.forEach(period => {
                    if (timetable[cd][day][period]) return;
                    // Try to find any subject with teacher free (respecting rules)
                    const candidates = remaining[cd].filter(r => {
                        if (r.left <= 0) return false;
                        if (r.isMultiClass) return true;
                        if (r.shared) {
                            return r.teachers.every(t => !teacherBusy[t] || !teacherBusy[t][day][period]);
                        }
                        const t = r.teachers[0];
                        if (!t) return false;
                        if (teacherBusy[t] && teacherBusy[t][day][period]) return false;
                        // Still respect rules
                        if (t.trim() === 'Rashid' && (period === 1 || period === 4)) return false;
                        if (t.trim() === 'Bindya' && period === 1) return false;
                        if ((t.trim() === 'Saheer' || t.trim() === 'Yasir') && day === 'Friday' && (period === 4 || period === 5)) return false;
                        if ((t.trim() === 'Swalih' || t.trim() === 'Fuaad' || t.trim() === 'Bavakutty') && day === 'Friday' && period === 4) return false;
                        return true;
                    });
                    if (candidates.length > 0) {
                        candidates.sort((a, b) => b.left - a.left);
                        const pick = candidates[0];
                        timetable[cd][day][period] = { subject: pick.subject, teacher: pick.teacher, shared: pick.shared };
                        pick.left--;
                        if (!pick.isMultiClass) {
                            pick.teachers.forEach(t => { if (teacherBusy[t]) teacherBusy[t][day][period] = true; });
                        }
                    }
                });
            });
        });

        // Count failures
        let failCount = 0;
        const failedDetails = {};
        classDivs.forEach(cd => {
            remaining[cd].forEach(r => {
                if (r.left > 0) {
                    failCount += r.left;
                    const key = `${r.teachers[0]} (${r.subject.split('/')[0]})`;
                    failedDetails[key] = (failedDetails[key] || 0) + r.left;
                }
            });
        });

        if (failCount === 0) {
            return { success: true, timetable };
        }

        if (failCount < bestFailCount) {
            bestFailCount = failCount;
            bestTimetable = JSON.parse(JSON.stringify(timetable));
            lastFailedDetails = { ...failedDetails };
        }
    }

    if (bestTimetable) {
        // Post-process: fix rule violations by SWAPPING (not deleting)
        // For each violation, find another period in the same day where we can swap
        
        classDivs.forEach(cd => {
            DAYS.forEach(day => {
                PERIODS.forEach(period => {
                    const slot = bestTimetable[cd][day][period];
                    if (!slot || !slot.teacher) return;
                    const teacher = slot.teacher;

                    let violated = false;
                    // Check Rashid
                    if (teacher.includes('Rashid') && (period === 1 || period === 4)) violated = true;
                    // Check Bindya
                    if (teacher.includes('Bindya') && period === 1) violated = true;
                    // Check Saheer & Yasir Friday P4,P5
                    if ((teacher.includes('Saheer') || teacher.includes('Yasir')) && day === 'Friday' && (period === 4 || period === 5)) violated = true;
                    // Check Swalih/Fuaad/Bavakutty Friday P4
                    if ((teacher.includes('Swalih') || teacher.includes('Fuaad') || teacher.includes('Bavakutty')) && day === 'Friday' && period === 4) violated = true;

                    if (!violated) return;

                    // Try to swap with another period in same class/day that doesn't have this teacher
                    let swapped = false;
                    for (const otherPeriod of PERIODS) {
                        if (otherPeriod === period) continue;
                        const otherSlot = bestTimetable[cd][day][otherPeriod];
                        if (!otherSlot) continue;

                        // Check if the OTHER teacher would be okay in the violated period
                        const otherTeacher = otherSlot.teacher || '';
                        let otherOk = true;
                        if (otherTeacher.includes('Rashid') && (period === 1 || period === 4)) otherOk = false;
                        if (otherTeacher.includes('Bindya') && period === 1) otherOk = false;
                        if ((otherTeacher.includes('Saheer') || otherTeacher.includes('Yasir')) && day === 'Friday' && (period === 4 || period === 5)) otherOk = false;
                        if ((otherTeacher.includes('Swalih') || otherTeacher.includes('Fuaad') || otherTeacher.includes('Bavakutty')) && day === 'Friday' && period === 4) otherOk = false;

                        // Check if the violating teacher would be okay in the other period
                        let thisOk = true;
                        if (teacher.includes('Rashid') && (otherPeriod === 1 || otherPeriod === 4)) thisOk = false;
                        if (teacher.includes('Bindya') && otherPeriod === 1) thisOk = false;
                        if ((teacher.includes('Saheer') || teacher.includes('Yasir')) && day === 'Friday' && (otherPeriod === 4 || otherPeriod === 5)) thisOk = false;
                        if ((teacher.includes('Swalih') || teacher.includes('Fuaad') || teacher.includes('Bavakutty')) && day === 'Friday' && otherPeriod === 4) thisOk = false;

                        // Check teacher conflicts: is the violating teacher free in otherPeriod across all classes?
                        let teacherFreeInOther = true;
                        classDivs.forEach(otherCd => {
                            if (otherCd === cd) return;
                            const s = bestTimetable[otherCd][day][otherPeriod];
                            if (s && s.teacher && s.teacher.includes(teacher.split('/')[0])) {
                                teacherFreeInOther = false;
                            }
                        });

                        let otherTeacherFreeInThis = true;
                        classDivs.forEach(otherCd => {
                            if (otherCd === cd) return;
                            const s = bestTimetable[otherCd][day][period];
                            if (s && s.teacher && s.teacher.includes(otherTeacher.split('/')[0])) {
                                otherTeacherFreeInThis = false;
                            }
                        });

                        if (otherOk && thisOk && teacherFreeInOther && otherTeacherFreeInThis) {
                            // Swap
                            bestTimetable[cd][day][period] = otherSlot;
                            bestTimetable[cd][day][otherPeriod] = slot;
                            swapped = true;
                            break;
                        }
                    }
                    // If can't swap within same day, try other days (leave as is — rule is best effort)
                });

                // Feeding mothers: if both P4 and P5 occupied, try to swap one
                ['Jaleela', 'Shafeedha'].forEach(fm => {
                    const p4 = bestTimetable[cd][day][4];
                    const p5 = bestTimetable[cd][day][5];
                    const p4HasFM = p4 && p4.teacher && p4.teacher.includes(fm);
                    const p5HasFM = p5 && p5.teacher && p5.teacher.includes(fm);
                    if (p4HasFM && p5HasFM) {
                        // Try to swap P5 with another period
                        for (const otherP of [1, 2, 3, 6, 7]) {
                            const otherSlot = bestTimetable[cd][day][otherP];
                            if (!otherSlot) continue;
                            if (otherSlot.teacher && otherSlot.teacher.includes(fm)) continue; // same teacher
                            // Swap P5's slot with otherP
                            bestTimetable[cd][day][5] = otherSlot;
                            bestTimetable[cd][day][otherP] = p5;
                            break;
                        }
                    }
                });
            });
        });

        return { success: true, timetable: bestTimetable };
    }

    const failList = Object.entries(lastFailedDetails).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k}: ${v} periods`).join('<br>');
    return {
        success: false,
        error: `Could not place ${bestFailCount} period(s) after ${maxAttempts} attempts.<br><br><strong>Teachers with conflicts:</strong><br>${failList}`
    };
}

function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
}

// ===== TIMETABLE VIEWS =====
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
                        ${PERIODS.map((p, i) => `<th>Period ${p}<br><small>${getPeriodTime(i, typeof day !== 'undefined' ? day : 'Monday')}</small></th>`).join('')}
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
                    if (slot && (slot.teacher === teacherName || (slot.teacher && slot.teacher.includes(teacherName)))) {
                        if (!schedule[day][p]) {
                            schedule[day][p] = { subject: slot.subject, classes: [classDiv] };
                        } else {
                            schedule[day][p].classes.push(classDiv);
                        }
                    }
                });
            }
        });
    });

    let totalPeriods = 0;
    DAYS.forEach(day => { totalPeriods += Object.keys(schedule[day]).length; });

    return `
        <h3 style="margin-bottom:8px;">Timetable for ${teacherName}</h3>
        <p style="color:var(--text-light);margin-bottom:16px;">Total periods/week: <strong>${totalPeriods}</strong></p>
        <div class="table-container">
            <table class="timetable-grid">
                <thead>
                    <tr>
                        <th class="day-header">Day</th>
                        <th>Period 1</th>
                        <th>Period 2</th>
                        <th style="background:#f59e0b;color:white;width:60px;">Interval</th>
                        <th>Period 3</th>
                        <th>Period 4</th>
                        <th style="background:#ef4444;color:white;width:70px;">Lunch</th>
                        <th>Period 5</th>
                        <th>Period 6</th>
                        <th style="background:#f59e0b;color:white;width:60px;">Interval</th>
                        <th>Period 7</th>
                    </tr>
                </thead>
                <tbody>
                    ${DAYS.map(day => `
                        <tr>
                            <td class="day-header" style="background:var(--primary-dark);color:white;font-weight:700;">${day}</td>
                            ${[1,2].map(p => {
                                const slot = schedule[day][p];
                                if (slot) return `<td><div class="timetable-cell"><div class="subject">${slot.subject}</div><div class="class-info">${slot.classes.join(', ')}</div></div></td>`;
                                return `<td style="background:#f0fdf4;"><span style="color:#86efac;">Free</span></td>`;
                            }).join('')}
                            <td style="background:#fffbeb;text-align:center;font-size:10px;color:#92400e;">☕</td>
                            ${[3,4].map(p => {
                                const slot = schedule[day][p];
                                if (slot) return `<td><div class="timetable-cell"><div class="subject">${slot.subject}</div><div class="class-info">${slot.classes.join(', ')}</div></div></td>`;
                                return `<td style="background:#f0fdf4;"><span style="color:#86efac;">Free</span></td>`;
                            }).join('')}
                            <td style="background:#fef2f2;text-align:center;font-size:10px;color:#991b1b;">🍽️</td>
                            ${[5,6].map(p => {
                                const slot = schedule[day][p];
                                if (slot) return `<td><div class="timetable-cell"><div class="subject">${slot.subject}</div><div class="class-info">${slot.classes.join(', ')}</div></div></td>`;
                                return `<td style="background:#f0fdf4;"><span style="color:#86efac;">Free</span></td>`;
                            }).join('')}
                            <td style="background:#fffbeb;text-align:center;font-size:10px;color:#92400e;">☕</td>
                            ${[7].map(p => {
                                const slot = schedule[day][p];
                                if (slot) return `<td><div class="timetable-cell"><div class="subject">${slot.subject}</div><div class="class-info">${slot.classes.join(', ')}</div></div></td>`;
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
                        ${PERIODS.map((p, i) => `<th>Period ${p}<br><small>${getPeriodTime(i, typeof day !== 'undefined' ? day : 'Monday')}</small></th>`).join('')}
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

function showLoading(msg = 'Saving...') {
    let el = document.getElementById('loadingOverlay');
    if (!el) {
        el = document.createElement('div');
        el.id = 'loadingOverlay';
        el.innerHTML = `
            <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.3);z-index:3000;display:flex;align-items:center;justify-content:center;">
                <div style="background:white;border-radius:12px;padding:24px 36px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,0.2);">
                    <div style="width:36px;height:36px;border:3px solid #e2e8f0;border-top-color:var(--primary);border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 12px;"></div>
                    <p id="loadingText" style="font-size:14px;color:var(--text);">${msg}</p>
                </div>
            </div>
        `;
        document.body.appendChild(el);
    } else {
        document.getElementById('loadingText').textContent = msg;
    }
}

function hideLoading() {
    document.getElementById('loadingOverlay')?.remove();
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
    csv += 'Day,' + PERIODS.map((p, i) => `Period ${p} (${getPeriodTime(i, typeof day !== 'undefined' ? day : 'Monday')})`).join(',') + '\n';
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
    csv += 'Day,' + PERIODS.map((p, i) => `Period ${p} (${getPeriodTime(i, typeof day !== 'undefined' ? day : 'Monday')})`).join(',') + '\n';

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
    csv += 'Class,' + PERIODS.map((p, i) => `Period ${p} (${getPeriodTime(i, typeof day !== 'undefined' ? day : 'Monday')})`).join(',') + '\n';

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

// ===== TIMETABLE HISTORY =====
async function showTimetableHistory() {
    showLoading('Loading history...');
    try {
        const history = await fetch(`${API_BASE}/timetable/history`).then(r => r.json());
        hideLoading();

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = 'historyModal';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3><i class="fas fa-history"></i> Timetable History</h3>
                    <button class="modal-close" onclick="closeModal('historyModal')">&times;</button>
                </div>
                <div class="modal-body">
                    ${history.length === 0 ? `
                        <div class="empty-state">
                            <i class="fas fa-clock"></i>
                            <h3>No History Yet</h3>
                            <p>Generate a timetable to start building history.</p>
                        </div>
                    ` : `
                        <div class="table-container">
                            <table>
                                <thead><tr><th>#</th><th>Saved At</th><th>Actions</th></tr></thead>
                                <tbody>
                                    ${history.map((h, i) => `
                                        <tr>
                                            <td>${i + 1}</td>
                                            <td>${h.saved_at !== 'Unknown' ? new Date(h.saved_at).toLocaleString() : 'Unknown'}</td>
                                            <td>
                                                <button class="btn btn-sm btn-primary" onclick="restoreTimetable(${h.id})"><i class="fas fa-undo"></i> Restore</button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline" onclick="closeModal('historyModal')">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    } catch (e) {
        hideLoading();
        showToast('Error loading history', 'error');
    }
}

async function restoreTimetable(historyId) {
    if (!confirm('Restore this timetable version? Current timetable will be replaced.')) return;
    showLoading('Restoring...');
    try {
        await fetch(`${API_BASE}/timetable/restore/${historyId}`, { method: 'POST' });
        await fetchData();
        hideLoading();
        closeModal('historyModal');
        showToast('Timetable restored!', 'success');
        renderPage('timetable');
    } catch (e) {
        hideLoading();
        showToast('Error restoring timetable', 'error');
    }
}

// ===== SEARCH & FILTER =====
function filterTeachers() {
    const search = (document.getElementById('teacherSearch')?.value || '').toLowerCase();
    const rows = document.querySelectorAll('#teacherTableBody tr');
    rows.forEach(row => {
        const name = row.getAttribute('data-name') || '';
        row.style.display = name.includes(search) ? '' : 'none';
    });
}

function filterClasses() {
    const search = (document.getElementById('classSearch')?.value || '').toLowerCase();
    const blockFilter = document.getElementById('classBlockFilter')?.value || '';
    const classFilter = document.getElementById('classClassFilter')?.value || '';
    const rows = document.querySelectorAll('#classTableBody tr');
    rows.forEach(row => {
        const name = row.getAttribute('data-name') || '';
        const block = row.getAttribute('data-block') || '';
        const cls = row.getAttribute('data-class') || '';
        const matchSearch = !search || name.includes(search) || block.includes(search);
        const matchBlock = !blockFilter || block === blockFilter;
        const matchClass = !classFilter || cls === classFilter;
        row.style.display = (matchSearch && matchBlock && matchClass) ? '' : 'none';
    });
}

function filterBlocks() {
    const search = (document.getElementById('blockSearch')?.value || '').toLowerCase();
    const rows = document.querySelectorAll('#blockTableBody tr');
    rows.forEach(row => {
        const name = row.getAttribute('data-name') || '';
        row.style.display = name.includes(search) ? '' : 'none';
    });
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
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '', raw: false });

        // Parse: each division becomes its own class entry
        const classes = [];
        let currentDiv = null;
        let headerRow = -1;

        // Find header row (contains "Class" and "Subject" or "Division")
        for (let i = 0; i < Math.min(rows.length, 10); i++) {
            const row = rows[i];
            if (!row) continue;
            const rowStr = row.join(' ').toLowerCase();
            if (rowStr.includes('class') && (rowStr.includes('subject') || rowStr.includes('division'))) {
                headerRow = i;
                break;
            }
        }

        const startRow = headerRow + 1;
        console.log(`Excel: ${rows.length} rows, header at row ${headerRow}, parsing from row ${startRow}`);

        for (let i = startRow; i < rows.length; i++) {
            const row = rows[i];
            if (!row || row.length < 6) continue;

            // Read all columns, handle both string and number types
            let cls = String(row[0] || '').trim();
            let division = String(row[1] || '').trim();
            let block = String(row[2] || '').trim();
            let type = String(row[3] || '').trim();
            let classTeacher = String(row[4] || '').trim();
            let subject = String(row[5] || '').trim();
            let teacher = String(row[6] || '').trim();
            let periods = row[7];

            // Clean up class value (might be "10.0" from Excel number)
            if (cls) cls = cls.replace('.0', '');

            // Skip title/instruction rows
            if (cls.toLowerCase().includes('kkhms') || cls.toLowerCase().includes('each row')) continue;
            if (cls.startsWith('---')) continue;
            if (subject.toLowerCase() === 'subject') continue;

            // New division starts when Column A (Class) AND Column B (Division) have values
            if (cls && division && /^(8|9|10)$/.test(cls)) {
                if (currentDiv) classes.push(currentDiv);
                currentDiv = {
                    name: cls,
                    divisions: [division.toUpperCase()],
                    block: block,
                    classType: type,
                    classTeacher: classTeacher,
                    subjects: []
                };
            }

            // Add subject if present
            if (currentDiv && subject) {
                // Parse periods - handle various formats
                let periodsNum = 0;
                if (periods !== null && periods !== undefined && periods !== '') {
                    periodsNum = parseInt(String(periods).replace('.0', '')) || 0;
                }

                if (periodsNum > 0 && subject.length > 0) {
                    // Handle slash-separated teachers/subjects (shared periods)
                    const teachers = teacher.split('/').map(t => t.trim()).filter(t => t);
                    const subjects_split = subject.split('/').map(s => s.trim()).filter(s => s);

                    if (teachers.length > 1) {
                        // Multiple teachers sharing this period slot
                        const groupId = `shared_${currentDiv.subjects.length}`;
                        for (let ti = 0; ti < teachers.length; ti++) {
                            const subName = subjects_split.length > 1 ? subjects_split[ti] || subjects_split[0] : subject;
                            currentDiv.subjects.push({
                                name: subName,
                                teacher: teachers[ti],
                                periodsPerWeek: periodsNum,
                                shared: true,
                                sharedGroup: groupId
                            });
                        }
                    } else {
                        currentDiv.subjects.push({
                            name: subject,
                            teacher: teacher,
                            periodsPerWeek: periodsNum,
                            shared: false,
                            sharedGroup: null
                        });
                    }
                }
            }
        }
        if (currentDiv) classes.push(currentDiv);

        console.log(`Parsed ${classes.length} class-divisions from Excel`);
        classes.forEach(c => {
            const rawTotal = c.subjects.reduce((s, sub) => s + sub.periodsPerWeek, 0);
            let classTotal = 0;
            const cg = new Set();
            c.subjects.forEach(sub => {
                if (sub.shared && sub.sharedGroup) {
                    if (!cg.has(sub.sharedGroup)) { cg.add(sub.sharedGroup); classTotal += sub.periodsPerWeek; }
                } else { classTotal += sub.periodsPerWeek; }
            });
            const sharedCount = c.subjects.filter(s => s.shared).length;
            console.log(`  ${c.name}-${c.divisions[0]}: ${c.subjects.length} entries, classTotal=${classTotal}, rawTotal=${rawTotal}, shared=${sharedCount}`);
        });

        if (classes.length === 0) {
            showToast('No valid class data found in the file. Check console for details.', 'error');
            return;
        }

        // Validate
        let errors = [];
        classes.forEach(cls => {
            // Calculate class total: shared subjects count only once (same period slot)
            let total = 0;
            const countedGroups = new Set();
            cls.subjects.forEach(sub => {
                if (sub.shared && sub.sharedGroup) {
                    if (!countedGroups.has(sub.sharedGroup)) {
                        countedGroups.add(sub.sharedGroup);
                        total += sub.periodsPerWeek;
                    }
                    // Skip additional teachers in same group
                } else {
                    total += sub.periodsPerWeek;
                }
            });
            const isClass8or9 = (cls.name === '8' || cls.name === '9');
            const validTotals = isClass8or9 ? [31, 32, 33, 34, 35] : [35];

            if (!validTotals.includes(total)) {
                errors.push(`Class ${cls.name}-${cls.divisions[0]}: total = ${total} (must be ${isClass8or9 ? '≤35' : '35'})`);
            }

            // Auto-add special subjects for class 8/9 only if missing and total < 35
            if (isClass8or9 && total < 35) {
                const specials = [];
                // PET: class 8 and 9
                specials.push({ name: 'PET', periodsPerWeek: 1, teacher: 'Shajir' });
                // Music: class 8 only
                if (cls.name === '8') {
                    specials.push({ name: 'Music', periodsPerWeek: 1, teacher: 'Divya' });
                }
                // Art: class 8 and 9
                specials.push({ name: 'Art', periodsPerWeek: 1, teacher: 'Udayesh' });
                // Work Experience: class 9 only
                if (cls.name === '9') {
                    specials.push({ name: 'Work Experience', periodsPerWeek: 1, teacher: 'Sheeba' });
                }
                for (const sp of specials) {
                    // Recalculate total counting shared only once
                    let curTotal = 0;
                    const cg = new Set();
                    cls.subjects.forEach(sub => {
                        if (sub.shared && sub.sharedGroup) {
                            if (!cg.has(sub.sharedGroup)) { cg.add(sub.sharedGroup); curTotal += sub.periodsPerWeek; }
                        } else { curTotal += sub.periodsPerWeek; }
                    });
                    if (curTotal >= 35) break;
                    if (!cls.subjects.find(s => s.name === sp.name)) {
                        cls.subjects.push(sp);
                    }
                }
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

        // Check for duplicates against existing data
        const existingData = getData();
        const existingKeys = existingData.classes.map(c => `${c.name}-${c.divisions[0]}`);
        const duplicates = classes.filter(cls => existingKeys.includes(`${cls.name}-${cls.divisions[0]}`));
        const newClasses = classes.filter(cls => !existingKeys.includes(`${cls.name}-${cls.divisions[0]}`));

        if (duplicates.length > 0) {
            const dupNames = duplicates.map(d => `${d.name}-${d.divisions[0]}`).join(', ');
            const action = confirm(
                `⚠️ Duplicate entries found!\n\n` +
                `Already exists: ${dupNames}\n\n` +
                `Choose an option:\n` +
                `• OK = Skip duplicates, upload only new (${newClasses.length} entries)\n` +
                `• Cancel = Abort upload entirely`
            );

            if (!action) {
                showToast('Upload cancelled', 'warning');
                return;
            }

            if (newClasses.length === 0) {
                showToast('All entries already exist. Nothing to upload.', 'warning');
                return;
            }

            // Replace classes with only new ones
            classes.length = 0;
            classes.push(...newClasses);
        }

        // Save each class-division to API
        let created = 0;
        const total = classes.length;

        // Show progress overlay
        const progressOverlay = document.createElement('div');
        progressOverlay.id = 'uploadProgress';
        progressOverlay.innerHTML = `
            <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:3000;display:flex;align-items:center;justify-content:center;">
                <div style="background:white;border-radius:12px;padding:32px 40px;min-width:400px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.2);">
                    <i class="fas fa-file-excel" style="font-size:40px;color:var(--success);margin-bottom:16px;"></i>
                    <h3 style="margin-bottom:8px;">Uploading Classes...</h3>
                    <p id="uploadStatusText" style="color:var(--text-light);margin-bottom:16px;">0 / ${total} divisions</p>
                    <div style="width:100%;height:10px;background:#e2e8f0;border-radius:5px;overflow:hidden;">
                        <div id="uploadProgressBar" style="height:100%;background:var(--primary);border-radius:5px;transition:width 0.2s;width:0%;"></div>
                    </div>
                    <p id="uploadCurrentItem" style="font-size:12px;color:var(--text-light);margin-top:8px;"></p>
                </div>
            </div>
        `;
        document.body.appendChild(progressOverlay);

        for (const cls of classes) {
            await apiPost('/classes', cls);
            created++;
            const pct = Math.round((created / total) * 100);
            document.getElementById('uploadProgressBar').style.width = pct + '%';
            document.getElementById('uploadStatusText').textContent = `${created} / ${total} divisions`;
            document.getElementById('uploadCurrentItem').textContent = `Class ${cls.name}-${cls.divisions[0]}`;
        }

        // Remove progress overlay
        document.getElementById('uploadProgress')?.remove();

        await fetchData();
        showToast(`${created} class-division(s) created from Excel!`, 'success');
        renderPage('classes');

    } catch (e) {
        showToast('Error reading Excel file: ' + e.message, 'error');
        console.error(e);
    }
}

// ===== INIT =====
showLoading('Loading data...');
fetchData().then(() => {
    hideLoading();
    renderPage('dashboard');
});
