let lastDate = null;

async function fetchPredictiveTexts() {
    const response = await fetch('/api/predictive_texts');
    return await response.json();
}

function initPage() {
    populateSearchFields();
    updateFields();
    updateBalance();
    loadRecords();
    loadPredictiveTexts();

    // تهيئة flatpickr مع صيغة التاريخ الصحيحة
    flatpickr("#date", {
        dateFormat: "d/m/Y",
        locale: "ar",
        enableTime: false,
        monthSelectorType: "dropdown", // إعادة قائمة الشهور كما كانت
        disableMobile: false
    });

    flatpickr("#editDate", {
        dateFormat: "d/m/Y",
        locale: "ar",
        enableTime: false,
        monthSelectorType: "dropdown",
        disableMobile: false
    });
}

function populateSearchFields() {
    const searchMonth = document.getElementById('searchMonth');
    const searchYear = document.getElementById('searchYear');
    
    for (let i = 1; i <= 12; i++) {
        searchMonth.innerHTML += `<option value="${i.toString().padStart(2, '0')}">${i.toString().padStart(2, '0')}</option>`;
    }
    for (let i = 2024; i <= 2034; i++) {
        searchYear.innerHTML += `<option value="${i}">${i}</option>`;
    }
}

function updateFields() {
    const type = document.getElementById('transactionType').value;
    document.getElementById('expenseTypeDiv').style.display = type === 'مصروفات' ? 'block' : 'none';
    document.querySelector('.btn-primary').innerText = type === 'مصروفات' ? 'إضافة مصروفات' : 'إضافة عهدة';
}

async function addEntry() {
    const date = document.getElementById('date').value;
    const type = document.getElementById('transactionType').value;
    const amount = document.getElementById('amount').value;
    const expenseType = document.getElementById('expenseType').value;

    if (!date || !amount) {
        alert('يرجى ملء جميع الحقول المطلوبة');
        return;
    }

    try {
        const response = await fetch('/api/add_entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, type, amount, expense_type: expenseType })
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            lastDate = date;
            document.getElementById('amount').value = '';
            document.getElementById('expenseType').value = '';
            updateBalance();
            loadRecords();
        } else {
            alert(`خطأ: ${result.error}`);
        }
    } catch (error) {
        alert(`خطأ في الاتصال: ${error.message}`);
    }
}

async function updateBalance() {
    try {
        const response = await fetch('/api/get_data');
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'فشل في جلب البيانات');
        
        const records = data.records || [];
        const expenses = records.filter(d => d.type !== 'عهدة').reduce((sum, d) => sum + d.amount, 0);
        const advances = records.filter(d => d.type === 'عهدة').reduce((sum, d) => sum + d.amount, 0);
        document.getElementById('balance').innerHTML = `<strong>${(advances - expenses).toLocaleString('en')} جنيه مصري</strong>`;
    } catch (error) {
        console.error('خطأ في تحديث الرصيد:', error);
        document.getElementById('balance').innerHTML = '<strong>غير متاح</strong>';
    }
}

function fillPreviousDate() {
    if (lastDate) {
        document.getElementById('date').value = lastDate;
    }
}

async function updateSuggestions() {
    const input = document.getElementById('expenseType').value.trim();
    const suggestions = document.getElementById('suggestions');
    suggestions.innerHTML = '';
    suggestions.style.display = 'none';

    if (input.length >= 2) {
        const predictiveTexts = await fetchPredictiveTexts();
        const matches = predictiveTexts.filter(type => type.includes(input));
        if (matches.length > 0) {
            suggestions.style.display = 'block';
            matches.forEach(match => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = match;
                li.onclick = () => {
                    document.getElementById('expenseType').value = match;
                    suggestions.style.display = 'none';
                };
                suggestions.appendChild(li);
            });
        }
    }
}

async function updateEditSuggestions() {
    const input = document.getElementById('editExpenseType').value.trim();
    const suggestions = document.getElementById('editSuggestions');
    suggestions.innerHTML = '';
    suggestions.style.display = 'none';

    if (input.length >= 2) {
        const predictiveTexts = await fetchPredictiveTexts();
        const matches = predictiveTexts.filter(type => type.includes(input));
        if (matches.length > 0) {
            suggestions.style.display = 'block';
            matches.forEach(match => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = match;
                li.onclick = () => {
                    document.getElementById('editExpenseType').value = match;
                    suggestions.style.display = 'none';
                };
                suggestions.appendChild(li);
            });
        }
    }
}

async function loadRecords() {
    try {
        const month = document.getElementById('searchMonth').value;
        const year = document.getElementById('searchYear').value;
        const type = document.getElementById('searchType').value;
        const url = `/api/get_data?${new URLSearchParams({ month, year, type }).toString()}`;
        
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'فشل في جلب البيانات');

        const tableBody = document.getElementById('recordsTable');
        tableBody.innerHTML = '';
        const records = data.records || [];
        records.forEach(row => {
            tableBody.innerHTML += `
                <tr>
                    <td>${row.id}</td>
                    <td>${row.date}</td>
                    <td>${row.type}</td>
                    <td>${row.amount.toLocaleString('en')}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editEntry(${row.id}, '${row.date}', '${row.type}', ${row.amount})">تعديل</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteEntry(${row.id})">حذف</button>
                    </td>
                </tr>
            `;
        });

        document.getElementById('totalAdvances').innerText = `${(data.total_advances || 0).toLocaleString('en')} جنيه مصري`;
        document.getElementById('totalExpenses').innerText = `${(data.total_expenses || 0).toLocaleString('en')} جنيه مصري`;
        localStorage.setItem('lastSearch', url);
    } catch (error) {
        console.error('خطأ في تحميل السجلات:', error);
        alert(`خطأ: ${error.message}`);
    }
}

function toggleEditExpenseType() {
    const type = document.getElementById('editType').value;
    document.getElementById('editExpenseTypeDiv').style.display = type === 'مصروفات' ? 'block' : 'none';
}

function editEntry(id, date, type, amount) {
    document.getElementById('editId').value = id;
    document.getElementById('editDate').value = date;
    document.getElementById('editType').value = type === 'عهدة' ? 'عهدة' : 'مصروفات';
    document.getElementById('editExpenseType').value = type !== 'عهدة' ? type : '';
    document.getElementById('editAmount').value = amount;
    toggleEditExpenseType();
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

async function saveEdit() {
    const id = document.getElementById('editId').value;
    const date = document.getElementById('editDate').value;
    const type = document.getElementById('editType').value;
    const expenseType = document.getElementById('editExpenseType').value;
    const amount = document.getElementById('editAmount').value;

    if (!date || !amount) {
        alert('يرجى ملء جميع الحقول المطلوبة');
        return;
    }

    try {
        const response = await fetch('/api/update_entry', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, date, type, amount, expense_type: expenseType })
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
            updateBalance();
            loadRecords();
        } else {
            alert(`خطأ: ${result.error}`);
        }
    } catch (error) {
        alert(`خطأ في الاتصال: ${error.message}`);
    }
}

async function deleteEntry(id) {
    if (confirm("هل أنت متأكد من حذف هذا السجل؟")) {
        try {
            const response = await fetch(`/api/delete_entry?id=${id}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                updateBalance();
                loadRecords();
            } else {
                alert(`خطأ: ${result.error}`);
            }
        } catch (error) {
            alert(`خطأ في الاتصال: ${error.message}`);
        }
    }
}

async function generatePDF() {
    try {
        const lastSearch = localStorage.getItem('lastSearch') || '/api/get_data';
        window.location.href = `/api/generate_pdf?url=${encodeURIComponent(lastSearch)}`;
    } catch (error) {
        alert(`خطأ في الطباعة: ${error.message}`);
    }
}

async function loadPredictiveTexts(searchQuery = '') {
    try {
        const predictiveTexts = await fetchPredictiveTexts();
        const filteredTexts = searchQuery ? predictiveTexts.filter(text => text.includes(searchQuery)) : predictiveTexts;
        const tableBody = document.getElementById('predictiveTable');
        tableBody.innerHTML = '';
        filteredTexts.forEach(text => {
            tableBody.innerHTML += `
                <tr>
                    <td>${text}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editPredictiveText('${text}')">تعديل</button>
                        <button class="btn btn-danger btn-sm" onclick="deletePredictiveText('${text}')">حذف</button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        alert(`خطأ في تحميل النصوص التنبؤية: ${error.message}`);
    }
}

async function addPredictiveText() {
    const text = document.getElementById('newPredictiveText').value.trim();
    if (!text) {
        alert('يرجى إدخال نص');
        return;
    }
    try {
        const response = await fetch('/api/predictive_texts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            document.getElementById('newPredictiveText').value = '';
            loadPredictiveTexts();
        } else {
            alert(`خطأ: ${result.error}`);
        }
    } catch (error) {
        alert(`خطأ في الاتصال: ${error.message}`);
    }
}

async function editPredictiveText(oldText) {
    const newText = prompt('أدخل النص الجديد:', oldText);
    if (newText && newText !== oldText) {
        try {
            const response = await fetch('/api/predictive_texts', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_text: oldText, new_text: newText })
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                loadPredictiveTexts();
            } else {
                alert(`خطأ: ${result.error}`);
            }
        } catch (error) {
            alert(`خطأ في الاتصال: ${error.message}`);
        }
    }
}

async function deletePredictiveText(text) {
    if (confirm(`هل أنت متأكد من حذف "${text}"؟`)) {
        try {
            const response = await fetch('/api/predictive_texts', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                loadPredictiveTexts();
            } else {
                alert(`خطأ: ${result.error}`);
            }
        } catch (error) {
            alert(`خطأ في الاتصال: ${error.message}`);
        }
    }
}

async function searchPredictiveTexts() {
    const searchQuery = document.getElementById('searchPredictiveText').value.trim();
    loadPredictiveTexts(searchQuery);
}