function quizApp() {
    return {
        question: {id: 1, text: '', options: []},
        modal: '',
        disabled: [false, false, false, false],
        selected: null,
        init() {
            fetch('/questions/1')
                .then(r => r.json())
                .then(q => { this.question = q; });
            this.connectSSE();
            document.body.addEventListener('htmx:afterRequest', (e) => this.handleAttempt(e));
        },
        connectSSE() {
            const evt = new EventSource('/events/group/1');
            evt.onmessage = (ev) => {
                const data = JSON.parse(ev.data);
                const tbody = document.getElementById('scoreboard');
                tbody.innerHTML = '';
                data.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${row.user}</td><td>${row.points}</td>`;
                    tbody.appendChild(tr);
                });
            };
        },
        handleAttempt(e) {
            if (e.detail.requestConfig.path !== '/attempts') return;
            const resp = JSON.parse(e.detail.xhr.responseText);
            if (resp.correct) {
                this.modal = `\u00a1Correcto! +${resp.gained_points} pts`;
                this.disabled = [true, true, true, true];
            } else {
                this.modal = 'Incorrecto';
                this.disabled[resp.option] = true;
            }
            document.getElementById('modal').style.display = 'block';
        }
    };
}

