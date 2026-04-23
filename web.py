"""
Ticket Bot - Web Dashboard (Flask)
"""

from flask import Flask, render_template_string, jsonify
import json, os, datetime

app = Flask(__name__)
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def get_stats():
    config = load_config()
    total_tickets = 0
    open_tickets = 0
    closed_tickets = 0
    guilds = len(config)

    for guild_id, guild_data in config.items():
        tickets = guild_data.get("tickets", {})
        for t in tickets.values():
            total_tickets += 1
            if t.get("status") == "open":
                open_tickets += 1
            else:
                closed_tickets += 1

    return {
        "total": total_tickets,
        "open": open_tickets,
        "closed": closed_tickets,
        "guilds": guilds,
        "uptime": "Online",
        "last_updated": datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M UTC")
    }

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎫 Ticket Bot Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg: #0d0f16;
            --bg2: #13151f;
            --bg3: #1a1d2e;
            --border: #2a2d3e;
            --accent: #5865f2;
            --accent2: #7289da;
            --green: #57f287;
            --red: #ed4245;
            --yellow: #fee75c;
            --text: #e3e5e8;
            --muted: #72767d;
        }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }

        /* NAV */
        nav {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }
        .nav-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text);
            text-decoration: none;
        }
        .nav-logo .logo-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }
        .nav-status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(87, 242, 135, 0.1);
            border: 1px solid rgba(87, 242, 135, 0.3);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--green);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* HERO */
        .hero {
            text-align: center;
            padding: 80px 2rem 60px;
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: -100px;
            left: 50%;
            transform: translateX(-50%);
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(88, 101, 242, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(88, 101, 242, 0.15);
            border: 1px solid rgba(88, 101, 242, 0.4);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--accent2);
            margin-bottom: 24px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .hero h1 {
            font-size: clamp(2.2rem, 5vw, 3.5rem);
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #fff 0%, var(--accent2) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero p {
            font-size: 1.1rem;
            color: var(--muted);
            max-width: 500px;
            margin: 0 auto 40px;
            line-height: 1.6;
        }
        .hero-buttons {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 28px;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            color: white;
            box-shadow: 0 4px 20px rgba(88, 101, 242, 0.4);
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(88, 101, 242, 0.5); }
        .btn-secondary {
            background: var(--bg3);
            color: var(--text);
            border: 1px solid var(--border);
        }
        .btn-secondary:hover { background: var(--border); }

        /* STATS */
        .container { max-width: 1100px; margin: 0 auto; padding: 0 2rem; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 60px;
        }
        .stat-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            border-radius: 16px 16px 0 0;
        }
        .stat-card.blue::before { background: linear-gradient(90deg, var(--accent), var(--accent2)); }
        .stat-card.green::before { background: linear-gradient(90deg, var(--green), #43b581); }
        .stat-card.red::before { background: linear-gradient(90deg, var(--red), #c03537); }
        .stat-card.yellow::before { background: linear-gradient(90deg, var(--yellow), #f0c030); }
        .stat-card:hover { transform: translateY(-4px); border-color: var(--accent); }
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            margin: 0 auto 16px;
        }
        .stat-card.blue .stat-icon { background: rgba(88,101,242,0.2); color: var(--accent2); }
        .stat-card.green .stat-icon { background: rgba(87,242,135,0.2); color: var(--green); }
        .stat-card.red .stat-icon { background: rgba(237,66,69,0.2); color: var(--red); }
        .stat-card.yellow .stat-icon { background: rgba(254,231,92,0.2); color: var(--yellow); }
        .stat-number {
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 4px;
            counter-reset: none;
        }
        .stat-label { font-size: 0.85rem; color: var(--muted); font-weight: 500; }

        /* FEATURES */
        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .section-sub {
            color: var(--muted);
            margin-bottom: 40px;
            font-size: 0.95rem;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 60px;
        }
        .feature-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            transition: all 0.3s;
        }
        .feature-card:hover { border-color: var(--accent); transform: translateY(-2px); }
        .feature-icon {
            width: 50px;
            height: 50px;
            background: rgba(88,101,242,0.15);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            margin-bottom: 16px;
        }
        .feature-card h3 { font-size: 1rem; font-weight: 600; margin-bottom: 8px; }
        .feature-card p { font-size: 0.875rem; color: var(--muted); line-height: 1.6; }

        /* COMMANDS */
        .commands-table {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 60px;
        }
        .commands-table table { width: 100%; border-collapse: collapse; }
        .commands-table th {
            background: var(--bg3);
            padding: 14px 20px;
            text-align: left;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
        }
        .commands-table td {
            padding: 14px 20px;
            font-size: 0.9rem;
            border-bottom: 1px solid var(--border);
        }
        .commands-table tr:last-child td { border-bottom: none; }
        .commands-table tr:hover td { background: var(--bg3); }
        .cmd-badge {
            background: rgba(88,101,242,0.2);
            color: var(--accent2);
            padding: 3px 10px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .perm-badge {
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .perm-admin { background: rgba(237,66,69,0.2); color: var(--red); }
        .perm-staff { background: rgba(88,101,242,0.2); color: var(--accent2); }
        .perm-all { background: rgba(87,242,135,0.2); color: var(--green); }

        /* SETUP */
        .setup-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 60px;
        }
        .step-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            position: relative;
        }
        .step-num {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            margin-bottom: 16px;
        }
        .step-card h3 { font-size: 0.95rem; font-weight: 600; margin-bottom: 8px; }
        .step-card p { font-size: 0.85rem; color: var(--muted); line-height: 1.5; }
        code {
            background: var(--bg3);
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.82rem;
            color: var(--accent2);
        }

        /* FOOTER */
        footer {
            background: var(--bg2);
            border-top: 1px solid var(--border);
            padding: 30px 2rem;
            text-align: center;
            color: var(--muted);
            font-size: 0.85rem;
        }
        footer span { color: var(--accent2); }

        /* REFRESH */
        .refresh-bar {
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            font-size: 0.85rem;
            color: var(--muted);
        }
        .refresh-btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 6px 16px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .refresh-btn:hover { background: var(--accent2); }

        @media (max-width: 600px) {
            nav { padding: 0 1rem; }
            .hero { padding: 60px 1rem 40px; }
            .container { padding: 0 1rem; }
        }
    </style>
</head>
<body>

<!-- NAV -->
<nav>
    <a href="/" class="nav-logo">
        <div class="logo-icon">🎫</div>
        Ticket Bot
    </a>
    <div class="nav-status">
        <div class="status-dot"></div>
        Online
    </div>
</nav>

<!-- HERO -->
<div class="hero">
    <div class="hero-badge">
        <i class="fas fa-bolt"></i>
        Discord Ticket Sistemi
    </div>
    <h1>Profesyonel<br>Ticket Yönetimi</h1>
    <p>Sunucunuz için tam özellikli, kolay kurulumlu Discord ticket botu. Destek taleplerinizi düzenli yönetin.</p>
    <div class="hero-buttons">
        <a href="https://discord.com/oauth2/authorize?client_id=1496490739645943933&permissions=8&integration_type=0&scope=bot" target="_blank" class="btn btn-primary">
            <i class="fab fa-discord"></i> Botu Ekle
        </a>
        <a href="#komutlar" class="btn btn-secondary">
            <i class="fas fa-book"></i> Komutlar
        </a>
    </div>
</div>

<!-- STATS -->
<div class="container">

    <div class="refresh-bar">
        <span><i class="fas fa-clock" style="margin-right:6px"></i>Son güncelleme: <span id="lastUpdate">{{ stats.last_updated }}</span></span>
        <button class="refresh-btn" onclick="refreshStats()"><i class="fas fa-sync-alt"></i> Yenile</button>
    </div>

    <div class="stats-grid">
        <div class="stat-card blue">
            <div class="stat-icon"><i class="fas fa-ticket"></i></div>
            <div class="stat-number" id="totalTickets">{{ stats.total }}</div>
            <div class="stat-label">Toplam Ticket</div>
        </div>
        <div class="stat-card green">
            <div class="stat-icon"><i class="fas fa-folder-open"></i></div>
            <div class="stat-number" id="openTickets">{{ stats.open }}</div>
            <div class="stat-label">Açık Ticket</div>
        </div>
        <div class="stat-card red">
            <div class="stat-icon"><i class="fas fa-folder"></i></div>
            <div class="stat-number" id="closedTickets">{{ stats.closed }}</div>
            <div class="stat-label">Kapalı Ticket</div>
        </div>
        <div class="stat-card yellow">
            <div class="stat-icon"><i class="fas fa-server"></i></div>
            <div class="stat-number" id="guilds">{{ stats.guilds }}</div>
            <div class="stat-label">Sunucu</div>
        </div>
    </div>

    <!-- FEATURES -->
    <div class="section-title">✨ Özellikler</div>
    <div class="section-sub">Ticket botunun tüm özellikleri</div>
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">🎫</div>
            <h3>Buton ile Ticket Aç</h3>
            <p>Kullanıcılar tek tıkla özel ticket kanalı açar. Kullanıcı başına 1 ticket limiti ile spam önlenir.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <h3>Ticket Kapatma & Silme</h3>
            <p>Staff ticket'ı kilitleyebilir, yeniden açabilir veya tamamen silebilir. 5 saniye gecikme ile güvenli silme.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <h3>Transcript Sistemi</h3>
            <p>Tüm mesaj geçmişini .txt dosyası olarak indir. Log kanalına otomatik gönderilir.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">👥</div>
            <h3>Kullanıcı Yönetimi</h3>
            <p>Ticket kanalına kullanıcı ekle veya çıkar. Staff rolü entegrasyonu ile yetki kontrolü.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>Log Kanalı</h3>
            <p>Her ticket işlemi (açma, kapama, silme, transcript) log kanalına otomatik bildirilir.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">♻️</div>
            <h3>Kalıcı Butonlar</h3>
            <p>Bot yeniden başlatılsa bile tüm butonlar çalışmaya devam eder. Persistent views ile kesintisiz hizmet.</p>
        </div>
    </div>

    <!-- COMMANDS -->
    <div id="komutlar" class="section-title">📋 Komutlar</div>
    <div class="section-sub">Tüm slash komutları ve yetki seviyeleri</div>
    <div class="commands-table">
        <table>
            <thead>
                <tr>
                    <th>Komut</th>
                    <th>Açıklama</th>
                    <th>Yetki</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="cmd-badge">/ticket-setup</span></td>
                    <td>Ticket panelini kur, staff rolü ve kategori belirle</td>
                    <td><span class="perm-badge perm-admin">Admin</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">/ticket-add</span></td>
                    <td>Ticket kanalına kullanıcı ekle</td>
                    <td><span class="perm-badge perm-staff">Staff</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">/ticket-remove</span></td>
                    <td>Ticket kanalından kullanıcı çıkar</td>
                    <td><span class="perm-badge perm-staff">Staff</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">/ticket-list</span></td>
                    <td>Açık ticketları listele</td>
                    <td><span class="perm-badge perm-staff">Staff</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">🎫 Ticket Aç</span></td>
                    <td>Buton ile özel ticket kanalı aç</td>
                    <td><span class="perm-badge perm-all">Herkes</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">🔒 Kapat</span></td>
                    <td>Ticket'ı kilitle, kullanıcı yazmasın</td>
                    <td><span class="perm-badge perm-all">Sahip / Staff</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">📋 Transcript</span></td>
                    <td>Mesaj geçmişini .txt olarak al</td>
                    <td><span class="perm-badge perm-all">Herkes</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">🗑️ Sil</span></td>
                    <td>Ticket kanalını tamamen sil</td>
                    <td><span class="perm-badge perm-staff">Staff</span></td>
                </tr>
                <tr>
                    <td><span class="cmd-badge">🔓 Yeniden Aç</span></td>
                    <td>Kapalı ticket'ı tekrar aktif et</td>
                    <td><span class="perm-badge perm-staff">Staff</span></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- SETUP -->
    <div class="section-title">🚀 Kurulum</div>
    <div class="section-sub">3 adımda botunu kur</div>
    <div class="setup-steps">
        <div class="step-card">
            <div class="step-num">1</div>
            <h3>Botu Ekle</h3>
            <p>Yukarıdaki "Bot Ekle" tuşuna bas. </p>
        </div>
        <div class="step-card">
            <div class="step-num">2</div>
            <h3>Panel Kur</h3>
            <p>Sunucunda <code>/ticket-setup</code> komutunu çalıştır, kanal ve rol seç. Hazır! 🎉.</p>
        </div>
        <div class="step-card">
            <div class="step-num">3</div>
            <h3>BOT HAZIR!</h3>
            <p>Botu Dilediğin Gibi Kullan👾</p>
        </div>
    </div>

</div>

<!-- FOOTER -->
<footer>
    <p>🎫 Ticket Bot &nbsp;•&nbsp; <span>discord.py</span> ile yapıldı &nbsp;•&nbsp; 7/24 çalışır</p>
</footer>

<script>
async function refreshStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('totalTickets').textContent = data.total;
        document.getElementById('openTickets').textContent = data.open;
        document.getElementById('closedTickets').textContent = data.closed;
        document.getElementById('guilds').textContent = data.guilds;
        document.getElementById('lastUpdate').textContent = data.last_updated;
    } catch(e) {
        console.log('Refresh failed', e);
    }
}
setInterval(refreshStats, 30000);
</script>

</body>
</html>
"""

@app.route("/")
def index():
    stats = get_stats()
    return render_template_string(HTML, stats=stats)

@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
