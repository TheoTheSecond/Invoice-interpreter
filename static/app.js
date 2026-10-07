const $ = s => document.querySelector(s);

const unitNames = {
    DAY: 'dag',
    EA: 'st',
    H87: 'st',
    HUR: 'tim',
    KWH: 'kWh',
    KWT: 'kW',
    MAW: 'MW',
    MIL: 'tusen',
    MON: 'mån',
    MTQ: 'm³',
    MTR: 'm',
    MWH: 'MWh',
    PA: 'paket',
    PR: 'par',
    ZZ: 'annan'
};

function unitName(code) {
    return unitNames[code] || code || '';
}

function money(value, currency = 'SEK') {
    if (value === null || value === undefined) return '-';

    return new Intl.NumberFormat('sv-SE', {
        style: 'currency',
        currency: currency || 'SEK'
    }).format(value);
}

async function load() {
    let q = encodeURIComponent($('#search').value);

    let xs = await fetch('/api/invoices?q=' + q)
        .then(r => r.json());

    $('#list').innerHTML = xs.map(x => `
        <div class="item" data-id="${x.id}">
            <b>${x.filename}</b>
            <span>
                ${x.supplier || 'Okänd leverantör'} ·
                ${money(x.total_amount, x.currency)}
            </span>
        </div>
    `).join('');

    document.querySelectorAll('.item').forEach(
        x => x.onclick = () => show(x.dataset.id)
    );
}


async function show(id) {
    let x = await fetch('/api/invoices/' + id)
        .then(r => r.json());

    let i = x.invoice;

    $('#detail').innerHTML = `
        <h2>${i.filename}</h2>
        <p>
            <b>Leverantör:</b> ${i.supplier || '-'}<br>
            <b>Fakturanr:</b> ${i.invoice_number || '-'}<br>
            <b>Datum:</b> ${i.invoice_date || '-'}
        </p>
        <table>
            <tr>
                <th>Rad</th>
                <th>Antal</th>
                <th>Enhet</th>
                <th>Pris exkl. moms</th>
                <th>Radsumma exkl. moms</th>
            </tr>
            ${x.lines.map(l => `
    <tr>
        <td>${l.description || '-'}</td>
        <td>${l.quantity ?? '-'}</td>
        <td>${unitName(l.unit)}</td>
        <td>
            ${l.unit_price != null
        ? money(l.unit_price, i.currency)
        : '-'}
        </td>
        <td>
            ${l.line_total != null
        ? money(l.line_total, i.currency)
        : '-'}
        </td>
    </tr>
`).join('')}
            <tr class="summary-row">
                <td colspan="4">
                    <b>Summa exkl. moms</b>
                </td>
                <td>
                    ${money(i.subtotal, i.currency)}
                </td>
            </tr>
            <tr class="summary-row">
                <td colspan="4">
                    <b>Moms</b>
                </td>
                <td>
                    ${money(i.tax_amount, i.currency)}
                </td>
            </tr>
            <tr class="summary-row total-row">
                <td colspan="4">
                    <b>Summa inkl. moms</b>
                </td>
                <td>
                    <b>${money(i.total_amount, i.currency)}</b>
                </td>
            </tr>
        </table>
    `;
}
$('#files').onchange = async e => {
    let f = new FormData();

    [...e.target.files].forEach(
        x => f.append('files', x)
    );
    let r = await fetch('/api/upload', {
        method: 'POST',
        body: f
    });
    if (!r.ok) {
        alert((await r.json()).detail);
    }
    await load();
};
$('#search').oninput = load;
async function askQuestion() {
    let q = $('#question').value.trim();

    if (!q) return;

    $('#answer').textContent = 'Tänker...';

    let r = await fetch('/api/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: q
        })
    }).then(r => r.json());

    $('#answer').textContent = r.answer;
}

$('#ask').onclick = askQuestion;

$('#question').addEventListener('keydown', event => {
    if (event.key === 'Enter') {
        event.preventDefault();
        askQuestion();
    }
});
//temporärt
const clearButton = document.createElement('button');

clearButton.textContent = 'Töm databasen';
clearButton.style.marginTop = '10px';
clearButton.style.background = '#c62828';
clearButton.style.color = 'white';

clearButton.onclick = async () => {
    const confirmed = confirm(
        'Är du säker på att du vill radera alla fakturor?'
    );

    if (!confirmed) return;

    const response = await fetch('/api/invoices', {
        method: 'DELETE'
    });

    if (!response.ok) {
        alert('Kunde inte tömma databasen.');
        return;
    }

    $('#detail').innerHTML = '';
    await load();

    alert('Databasen är tömd.');
};

$('#list').parentElement.appendChild(clearButton);
load();