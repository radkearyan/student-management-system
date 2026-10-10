// Fees Ledger, Admin Management, and Card Gateway Simulator

let CURRENT_RECEIPT_FEE_ID = null;

async function loadFeesLedger() {
    let url = '/api/fees';
    const params = new URLSearchParams();

    if (STATE && STATE.user && STATE.user.role === 'student') {
        params.append('student_id', STATE.user.reference_id);
    } else {
        const searchInput = document.getElementById('fee-search-input');
        const statusFilter = document.getElementById('fee-status-filter');
        if (searchInput && searchInput.value.trim()) {
            params.append('search', searchInput.value.trim());
        }
        if (statusFilter && statusFilter.value && statusFilter.value !== 'all') {
            params.append('status', statusFilter.value);
        }
    }

    if (params.toString()) {
        url += '?' + params.toString();
    }

    const res = await API.get(url);
    const body = document.getElementById('fees-table-body');
    if (!body) return;
    body.innerHTML = '';

    const records = Array.isArray(res) ? res : (res && res.fees ? res.fees : (res && res.records ? res.records : []));

    if (!records || records.length === 0) {
        body.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No fee statements found.</td></tr>';
        const collectedEl = document.getElementById('ledger-collected');
        const pendingEl = document.getElementById('ledger-pending');
        if (collectedEl) collectedEl.textContent = formatCurrency(0);
        if (pendingEl) pendingEl.textContent = formatCurrency(0);
        return;
    }

    let collected = 0;
    let pending = 0;
    const isStudent = STATE && STATE.user && STATE.user.role === 'student';

    records.forEach(r => {
        if (r.status === 'Paid') {
            collected += r.amount;
        } else {
            pending += r.amount;
        }

        const tr = document.createElement('tr');
        const statusClass = r.status === 'Paid' ? 'text-green font-bold' : 'text-red font-bold';
        
        let actionBtn = '';
        if (r.status === 'Pending') {
            if (isStudent) {
                actionBtn = `<button class="btn btn-primary btn-small btn-pay-fees" data-id="${r.student_id}" data-amount="${r.amount}" style="padding:4px 8px; font-size:0.75rem;"><i class="fa-solid fa-credit-card"></i> Pay Now</button>`;
            } else {
                actionBtn = `
                    <div style="display:inline-flex; gap:4px;">
                        <button class="btn btn-primary btn-small btn-collect-offline" data-fee-id="${r.fee_id}" data-student="${r.student_id} - ${r.name || ''}" data-amount="${r.amount}" style="padding:4px 8px; font-size:0.75rem;" title="Collect Offline Payment">
                            <i class="fa-solid fa-hand-holding-dollar"></i> Collect
                        </button>
                        <button class="btn btn-outline btn-small btn-pay-fees" data-id="${r.student_id}" data-amount="${r.amount}" style="padding:4px 8px; font-size:0.75rem;" title="Test Online Card Checkout">
                            <i class="fa-solid fa-credit-card"></i> Card
                        </button>
                        <button class="btn btn-secondary btn-small btn-delete-fee" data-fee-id="${r.fee_id}" style="padding:4px 8px; font-size:0.75rem; background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3);" title="Revoke Fee Statement">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                `;
            }
        } else if (r.status === 'Paid') {
            actionBtn = `
                <div style="display:inline-flex; gap:4px;">
                    <button class="btn btn-primary btn-small btn-view-receipt" data-fee-id="${r.fee_id}" style="padding:4px 8px; font-size:0.75rem;" title="View Receipt">
                        <i class="fa-solid fa-receipt"></i> View
                    </button>
                    <button class="btn btn-secondary btn-small btn-download-receipt-direct" data-fee-id="${r.fee_id}" style="padding:4px 8px; font-size:0.75rem; background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3);" title="Download PDF Receipt">
                        <i class="fa-solid fa-file-pdf"></i> PDF
                    </button>
                </div>
            `;
        }

        tr.innerHTML = `
            <td><strong>${r.student_id}</strong></td>
            <td>${r.name || 'N/A'}</td>
            <td>${r.department || 'N/A'}</td>
            <td>${formatCurrency(r.amount)}</td>
            <td>${r.payment_date || '-'}</td>
            <td><span class="${statusClass}">${r.status}</span></td>
            <td><span style="font-family:monospace; font-size:0.75rem;">${r.txn_id || '-'}</span></td>
            <td>${actionBtn}</td>
        `;
        body.appendChild(tr);
    });

    const collectedEl = document.getElementById('ledger-collected');
    const pendingEl = document.getElementById('ledger-pending');
    if (collectedEl) collectedEl.textContent = formatCurrency(collected);
    if (pendingEl) pendingEl.textContent = formatCurrency(pending);

    // Bind Pay buttons
    body.querySelectorAll('.btn-pay-fees').forEach(btn => {
        btn.onclick = () => {
            const sid = btn.getAttribute('data-id');
            const amt = btn.getAttribute('data-amount');
            openPaymentModal(sid, amt);
        };
    });

    // Bind Admin Collect Offline buttons
    body.querySelectorAll('.btn-collect-offline').forEach(btn => {
        btn.onclick = () => {
            const feeId = btn.getAttribute('data-fee-id');
            const studentInfo = btn.getAttribute('data-student');
            const amt = btn.getAttribute('data-amount');
            openCollectModal(feeId, studentInfo, amt);
        };
    });

    // Bind Admin Delete Fee buttons
    body.querySelectorAll('.btn-delete-fee').forEach(btn => {
        btn.onclick = async () => {
            const feeId = btn.getAttribute('data-fee-id');
            if (confirm("Are you sure you want to revoke/delete this fee statement?")) {
                const deleteRes = await API.delete(`/api/fees/${feeId}`);
                if (deleteRes && deleteRes.success) {
                    showToast("Statement Deleted", deleteRes.message, "success");
                    loadFeesLedger();
                } else {
                    showToast("Error", deleteRes ? deleteRes.message : "Failed to delete fee statement.", "error");
                }
            }
        };
    });

    // Bind Receipt buttons
    body.querySelectorAll('.btn-view-receipt').forEach(btn => {
        btn.onclick = () => {
            const feeId = btn.getAttribute('data-fee-id');
            openReceiptModal(feeId);
        };
    });

    // Bind direct PDF download buttons
    body.querySelectorAll('.btn-download-receipt-direct').forEach(btn => {
        btn.onclick = () => {
            const feeId = btn.getAttribute('data-fee-id');
            downloadFeeReceiptPDF(feeId);
        };
    });
}

// Helper to dynamically populate student dropdown in modal
async function populateStudentDropdown() {
    const select = document.getElementById('add-fee-student-id');
    if (!select) return;
    const res = await API.get('/api/students');
    let students = Array.isArray(res) ? res : (res && res.students ? res.students : []);
    if (students.length > 0) {
        select.innerHTML = '<option value="">-- Choose Student --</option>' + students.map(s => `
            <option value="${s.student_id}">${s.student_id} - ${s.name || 'Student'} (${s.department || 'General'})</option>
        `).join('');
    } else {
        select.innerHTML = '<option value="">No registered students found</option>';
    }
}

// Payment modal triggers
function openPaymentModal(studentId, amount) {
    const paymentModal = document.getElementById('payment-modal');
    if (!paymentModal) return;

    const sidInput = document.getElementById('pay-student-id');
    const amtInput = document.getElementById('pay-amount-display');
    if (sidInput) sidInput.value = studentId;
    if (amtInput) amtInput.value = formatCurrency(amount);
    
    // Set visual credit card fields
    const nameDisplay = document.getElementById('card-display-name');
    const numDisplay = document.getElementById('card-display-num');
    if (nameDisplay) nameDisplay.textContent = (STATE && STATE.user && STATE.user.username ? STATE.user.username : 'CARD HOLDER').toUpperCase();
    if (numDisplay) numDisplay.textContent = "•••• •••• •••• ••••";
    
    paymentModal.classList.remove('hidden');
}

// Admin Collect Offline modal trigger
function openCollectModal(feeId, studentInfo, amount) {
    const collectModal = document.getElementById('collect-fee-modal');
    if (!collectModal) return;

    document.getElementById('collect-fee-id').value = feeId;
    document.getElementById('collect-student-info').value = studentInfo;
    document.getElementById('collect-amount-info').value = formatCurrency(amount);

    collectModal.classList.remove('hidden');
}

// Initialize listeners on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // 1. Payment modal close buttons
    const paymentModal = document.getElementById('payment-modal');
    const closePayment = document.getElementById('btn-close-payment-modal');
    const cancelPayment = document.getElementById('btn-cancel-payment-modal');
    if (closePayment && paymentModal) closePayment.onclick = () => paymentModal.classList.add('hidden');
    if (cancelPayment && paymentModal) cancelPayment.onclick = () => paymentModal.classList.add('hidden');

    // 2. Card auto-format
    const cardNumInput = document.getElementById('pay-card-number');
    if (cardNumInput) {
        cardNumInput.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
            let matches = val.match(/\d{4,16}/g);
            let match = matches && matches[0] || '';
            let parts = [];

            for (let i=0, len=match.length; i<len; i+=4) {
                parts.push(match.substring(i, i+4));
            }

            const displayEl = document.getElementById('card-display-num');
            if (parts.length > 0) {
                e.target.value = parts.join(' ');
                if (displayEl) displayEl.textContent = parts.join(' ');
            } else {
                if (displayEl) displayEl.textContent = "•••• •••• •••• ••••";
            }
        });
    }

    // 3. Payment submit
    const paymentForm = document.getElementById('payment-gateway-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const student_id = document.getElementById('pay-student-id').value;
            const rawAmt = document.getElementById('pay-amount-display').value.replace(/[^0-9.-]+/g,"");
            const amount = parseFloat(rawAmt);
            const card_number = document.getElementById('pay-card-number').value;

            const res = await API.post('/api/fees/pay', { student_id, amount, card_number });
            if (res && res.success) {
                showToast("Payment Successful", res.message, "success");
                if (paymentModal) paymentModal.classList.add('hidden');
                loadFeesLedger();
            } else {
                showToast("Payment Failed", res && res.message ? res.message : "Failed to process card.", "error");
            }
        });
    }

    // 4. Assign Fee Statement Modal (Admin)
    const addFeeModal = document.getElementById('add-fee-modal');
    const btnOpenAssign = document.getElementById('btn-open-assign-fee-modal');
    const closeAddFee = document.getElementById('btn-close-add-fee-modal');
    const cancelAddFee = document.getElementById('btn-cancel-add-fee-modal');

    if (btnOpenAssign && addFeeModal) {
        btnOpenAssign.onclick = () => {
            addFeeModal.classList.remove('hidden');
            populateStudentDropdown();
        };
    }
    if (closeAddFee && addFeeModal) closeAddFee.onclick = () => addFeeModal.classList.add('hidden');
    if (cancelAddFee && addFeeModal) cancelAddFee.onclick = () => addFeeModal.classList.add('hidden');

    const targetSelect = document.getElementById('add-fee-target');
    const groupStudent = document.getElementById('group-fee-student');
    const groupDept = document.getElementById('group-fee-department');
    if (targetSelect) {
        targetSelect.onchange = () => {
            if (targetSelect.value === 'department') {
                if (groupStudent) groupStudent.classList.add('hidden');
                if (groupDept) groupDept.classList.remove('hidden');
            } else {
                if (groupStudent) groupStudent.classList.remove('hidden');
                if (groupDept) groupDept.classList.add('hidden');
            }
        };
    }

    const addFeeForm = document.getElementById('add-fee-form');
    if (addFeeForm) {
        addFeeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const targetScope = document.getElementById('add-fee-target')?.value || 'individual';
            const amount = parseFloat(document.getElementById('add-fee-amount').value);
            const status = document.getElementById('add-fee-status').value;

            if (targetScope === 'department') {
                const department = document.getElementById('add-fee-department').value;
                const res = await API.post('/api/fees/bulk-add', { department, amount, status });
                if (res && res.success) {
                    showToast("Bulk Fee Assigned", res.message, "success");
                    addFeeForm.reset();
                    if (addFeeModal) addFeeModal.classList.add('hidden');
                    loadFeesLedger();
                } else {
                    showToast("Error", res && res.message ? res.message : "Failed to assign bulk fee statements.", "error");
                }
            } else {
                const student_id = document.getElementById('add-fee-student-id').value.trim();
                if (!student_id) {
                    showToast("Missing Selection", "Please select a student.", "warning");
                    return;
                }
                const res = await API.post('/api/fees/add', { student_id, amount, status });
                if (res && res.success) {
                    showToast("Fee Statement Assigned", res.message, "success");
                    addFeeForm.reset();
                    if (addFeeModal) addFeeModal.classList.add('hidden');
                    loadFeesLedger();
                } else {
                    showToast("Error", res && res.message ? res.message : "Failed to assign fee statement.", "error");
                }
            }
        });
    }

    // 5. Collect Offline Payment Modal (Admin)
    const collectModal = document.getElementById('collect-fee-modal');
    const closeCollect = document.getElementById('btn-close-collect-fee-modal');
    const cancelCollect = document.getElementById('btn-cancel-collect-fee-modal');

    if (closeCollect && collectModal) closeCollect.onclick = () => collectModal.classList.add('hidden');
    if (cancelCollect && collectModal) cancelCollect.onclick = () => collectModal.classList.add('hidden');

    const collectForm = document.getElementById('collect-fee-form');
    if (collectForm) {
        collectForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fee_id = document.getElementById('collect-fee-id').value;
            const payment_method = document.getElementById('collect-payment-method').value;

            const res = await API.post(`/api/fees/collect/${fee_id}`, { payment_method });
            if (res && res.success) {
                showToast("Success", res.message, "success");
                if (collectModal) collectModal.classList.add('hidden');
                loadFeesLedger();
                openReceiptModal(fee_id);
            } else {
                showToast("Error", res && res.message ? res.message : "Failed to record payment.", "error");
            }
        });
    }

    // 6. Search & Filter event listeners
    const searchInput = document.getElementById('fee-search-input');
    const statusFilter = document.getElementById('fee-status-filter');

    if (searchInput) {
        let timer = null;
        searchInput.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(loadFeesLedger, 300);
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', loadFeesLedger);
    }
});

// Receipt printable modal popup
async function openReceiptModal(feeId) {
    const res = await API.get(`/api/fees/receipt/${feeId}`);
    if (!res || !res.success) {
        showToast("Error", "Could not fetch fee receipt details.", "error");
        return;
    }

    const modal = document.getElementById('receipt-modal');
    if (!modal) return;

    const r = res.receipt;
    document.getElementById('rec-no').textContent = r.receipt_no;
    document.getElementById('rec-date').textContent = r.payment_date || new Date().toISOString().split('T')[0];
    document.getElementById('rec-txn').textContent = r.txn_id || 'TXN-OFFLINE';
    document.getElementById('rec-method').textContent = r.payment_method || 'Online NetBanking / Card Gateway';
    document.getElementById('rec-name').textContent = r.name || 'N/A';
    document.getElementById('rec-id').textContent = r.student_id;
    document.getElementById('rec-dept').textContent = r.department || 'General';
    document.getElementById('rec-course').textContent = r.course || 'B.Tech';
    document.getElementById('rec-amount').textContent = r.amount.toFixed(2);
    document.getElementById('rec-total-words').textContent = formatCurrency(r.amount);

    CURRENT_RECEIPT_FEE_ID = feeId;
    modal.classList.remove('hidden');

    const closeBtn1 = document.getElementById('btn-close-receipt-modal');
    const closeBtn2 = document.getElementById('btn-close-receipt-modal-footer');
    if (closeBtn1) closeBtn1.onclick = () => modal.classList.add('hidden');
    if (closeBtn2) closeBtn2.onclick = () => modal.classList.add('hidden');
}

async function downloadFeeReceiptPDF(feeId) {
    const targetFeeId = feeId || CURRENT_RECEIPT_FEE_ID;
    if (!targetFeeId) {
        showToast("Error", "No fee receipt selected for PDF download.", "warning");
        return;
    }

    const btn = document.getElementById('btn-download-receipt-pdf');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating PDF...';
    }

    try {
        const url = `/api/fees/receipt/${targetFeeId}/pdf`;
        const response = await fetch(url);
        if (!response.ok) {
            let errorMsg = "Could not download fee receipt PDF.";
            try {
                const errJson = await response.json();
                if (errJson && errJson.message) errorMsg = errJson.message;
            } catch (_) {}
            showToast("Export Failed", errorMsg, "error");
            return;
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `fee_receipt_${targetFeeId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast("Success", "Fee Payment Receipt PDF downloaded successfully.", "success");
    } catch (err) {
        console.error("PDF Receipt error:", err);
        showToast("Download Failed", "Network error while downloading PDF receipt.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    }
}
