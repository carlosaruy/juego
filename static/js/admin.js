function adminApp() {
    return {
        registrationOpen: true,
        remaining: 0,
        groups: [],
        groupFilter: '',
        init() {
            this.fetchStatus();
            this.connectSSE();
        },
        fetchStatus() {
            fetch('/admin/status')
                .then(r => r.json())
                .then(d => {
                    this.registrationOpen = d.registration_open;
                    this.remaining = d.remaining;
                });
        },
        toggleRegistration() {
            fetch('/admin/toggle-registration', {method: 'POST'})
                .then(r => r.json())
                .then(d => { this.registrationOpen = d.registration_open; });
        },
        connectSSE() {
            const evt = new EventSource('/events/admin');
            evt.addEventListener('scoreboard', ev => {
                const data = JSON.parse(ev.data);
                this.groups = [...new Set(data.map(r => r.group))];
                const tbody = this.$refs.scoreboard;
                tbody.innerHTML = '';
                data.forEach(row => {
                    if (this.groupFilter && parseInt(row.group) !== parseInt(this.groupFilter)) return;
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${row.group}</td><td>${row.user}</td><td>${row.points}</td>`;
                    tbody.appendChild(tr);
                });
            });
            evt.addEventListener('ping', () => {});
        }
    };
}
