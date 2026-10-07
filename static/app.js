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


/* =========================
   Fakturalista
   ========================= */

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


/* =========================
   Visa faktura
   ========================= */

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

                    <td>
                        ${l.quantity ?? '-'}
                    </td>

                    <td>
                        ${unitName(l.unit)}
                    </td>

                    <td>
                        ${
        l.unit_price != null
            ? money(l.unit_price, i.currency)
            : '-'
    }
                    </td>

                    <td>
                        ${
        l.line_total != null
            ? money(l.line_total, i.currency)
            : '-'
    }
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
                    <b>
                        ${money(i.total_amount, i.currency)}
                    </b>
                </td>
            </tr>

        </table>
    `;
}


/* =========================
   Ladda upp fakturor
   ========================= */

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


/* =========================
   Sök
   ========================= */

$('#search').oninput = load;


/* =========================
   AI-chat
   ========================= */

function addMessage(text, sender) {
    const messages = $('#messages');

    const placeholder = messages.querySelector('.chat-placeholder');

    if (placeholder) {
        placeholder.remove();
    }

    const message = document.createElement('div');

    message.classList.add(
        'message',
        sender
    );

    message.textContent = text;

    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;

    return message;
}


async function askQuestion() {
    const input = $('#question');

    const q = input.value.trim();

    if (!q) return;


    /* Visa användarens fråga */

    addMessage(q, 'user');


    /* Töm inputfältet */

    input.value = '';


    /* Visa tillfälligt AI-meddelande */

    const thinkingMessage = addMessage(
        'Tänker...',
        'ai'
    );


    try {

        const response = await fetch('/api/ask', {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                question: q
            })
        });


        if (!response.ok) {
            thinkingMessage.textContent =
                'Något gick fel när AI:n skulle svara.';

            return;
        }


        const result = await response.json();


        /* Ersätt "Tänker..." med svaret */

        thinkingMessage.textContent = result.answer;


        /* Scrolla ner till svaret */

        $('#messages').scrollTop =
            $('#messages').scrollHeight;

    } catch (error) {

        thinkingMessage.textContent =
            'Kunde inte kontakta AI:n.';

    }
}


/* Fråga-knappen */

$('#ask').onclick = askQuestion;


/* Enter skickar frågan */

$('#question').addEventListener(
    'keydown',
    event => {

        if (event.key === 'Enter') {
            event.preventDefault();

            askQuestion();
        }
    }
);


/* =========================
   Temporärt:
   töm databasen
   ========================= */

const clearButton =
    document.createElement('button');


clearButton.textContent =
    'Töm databasen';


clearButton.style.marginTop =
    '10px';


clearButton.style.background =
    '#c62828';


clearButton.style.color =
    'white';


clearButton.onclick = async () => {

    const confirmed = confirm(
        'Är du säker på att du vill radera alla fakturor?'
    );


    if (!confirmed) return;


    const response = await fetch(
        '/api/invoices',
        {
            method: 'DELETE'
        }
    );


    if (!response.ok) {
        alert(
            'Kunde inte tömma databasen.'
        );

        return;
    }


    $('#detail').innerHTML = '';

    await load();


    alert(
        'Databasen är tömd.'
    );
};


$('#list')
    .parentElement
    .appendChild(clearButton);


/* =========================
   Start
   ========================= */

load();