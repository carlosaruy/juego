function quizApp() {
    return {
        username: '',
        group: '',
        question: {id: 1, text: '', options: []},
        disabled: [],
        modalVisible: false,
        modalText: '',
        userModal: false,
        current: 1,
        finished: false,
        finalScore: 0,
        scoreData: [],
        init() {
            this.username = localStorage.getItem('username');
            this.group = localStorage.getItem('group');
            if (!this.username || !this.group) {
                this.userModal = true;
            } else {
                this.start();
            }
        },
        saveUser() {
            localStorage.setItem('username', this.username);
            localStorage.setItem('group', this.group);
            this.userModal = false;
            this.start();
        },
        start() {
            this.connectSSE();
            this.loadQuestion();
        },
        loadQuestion() {
            fetch(`/questions/${this.current}`)
                .then(r => {
                    if (r.status === 404) {
                        this.finished = true;
                        this.finalScore = this.getMyPoints();
                        this.modalText = 'Juego terminado';
                        this.modalVisible = true;
                        return null;
                    }
                    return r.json();
                })
                .then(q => {
                    if (!q) return;
                    this.question = q;
                    this.disabled = new Array(q.options.length).fill(false);
                });
        },
        sendAttempt(option) {
            fetch('/attempts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_name: this.username,
                    group_id: parseInt(this.group),
                    question_id: this.question.id,
                    option: option
                })
            })
                .then(r => r.json())
                .then(resp => {
                    if (resp.correct) {
                        this.modalText = `\u2714 +${resp.gained_points} pts`;
                        this.disabled = this.disabled.map(() => true);
                        this.current += 1;
                        this.loadQuestion();
                    } else {
                        this.modalText = '\u274C';
                        this.disabled[option] = true;
                        if (resp.attempts_left === 0) {
                            this.current += 1;
                            this.loadQuestion();
                        }
                    }
                    this.modalVisible = true;
                });
        },
        closeModal() {
            this.modalVisible = false;
        },
        connectSSE() {
            const evt = new EventSource(`/events/group/${this.group}`);
            evt.addEventListener('scoreboard', ev => {
                const data = JSON.parse(ev.data);
                this.scoreData = data;
                const tbody = this.$refs.scoreboard;
                tbody.innerHTML = '';
                data.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${row.user}</td><td>${row.points}</td>`;
                    tbody.appendChild(tr);
                });
            });
        },
        getMyPoints() {
            const row = this.scoreData.find(r => r.user === this.username);
            return row ? row.points : 0;
        }
    };
}
