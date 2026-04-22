import os
import sqlite3
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = None  # Cheksiz hajm

# Ma'lumotlar bazasini modernizatsiya qilish
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT, filesize INTEGER)''')
    
    try:
        c.execute("SELECT filesize FROM files LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE files ADD COLUMN filesize INTEGER DEFAULT 0")
        
    conn.commit()
    conn.close()

if not os.path.exists('uploads'):
    os.makedirs('uploads')
init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>---Sattorxonov &&& Abdurashid---</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --neon: #00f2fe;
            --purple: #7000ff;
            --glass: rgba(0, 0, 0, 0.7);
        }

        * { box-sizing: border-box; }

        body, html {
            margin: 0; padding: 0;
            background: #000;
            color: white;
            font-family: 'Rajdhani', sans-serif;
            overflow-x: hidden;
            min-height: 100vh;
        }

        #canvas-container {
            position: fixed; top: 0; left: 0; z-index: -1;
            width: 100%; height: 100%;
        }

        .app-wrapper {
            width: 100%;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 20px;
            backdrop-filter: blur(5px);
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid rgba(0, 242, 254, 0.2);
        }

        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: clamp(1.5rem, 5vw, 2.5rem);
            margin: 0;
            background: linear-gradient(90deg, #fff, var(--neon));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 15px rgba(0, 242, 254, 0.5);
        }

        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
        }

        .glass-panel {
            background: var(--glass);
            backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            padding: 35px;
            width: 100%;
            margin: 15px 0;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 1);
        }

        input {
            width: 100%;
            padding: 18px;
            margin: 10px 0;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0, 242, 254, 0.3);
            border-radius: 15px;
            color: #fff;
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            transition: 0.3s;
        }

        input:focus {
            border-color: var(--neon);
            box-shadow: 0 0 15px var(--neon);
            outline: none;
        }

        button {
            padding: 18px 30px;
            margin: 10px 0;
            border-radius: 15px;
            border: none;
            background: linear-gradient(135deg, var(--neon), var(--purple));
            color: white;
            font-weight: 700;
            cursor: pointer;
            text-transform: uppercase;
            transition: 0.3s;
            font-family: 'Orbitron', sans-serif;
            width: 100%;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 25px var(--neon);
        }

        .tab-btn-container {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }

        .tab-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 10px;
            font-size: 12px;
        }

        .tab-btn.active {
            background: var(--neon);
            color: #000;
        }

        .file-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            width: 100%;
            margin-top: 20px;
        }

        .file-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            border-left: 4px solid var(--neon);
        }

        .drop-zone {
            width: 100%;
            height: 180px;
            border: 2px dashed var(--neon);
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            background: rgba(0, 242, 254, 0.03);
            margin-bottom: 15px;
        }

        .hidden { display: none; }

        .progress-wrapper { width: 100%; margin: 15px 0; }
        .bar-bg { width: 100%; height: 8px; background: #111; border-radius: 10px; }
        #bar-fill { width: 0%; height: 100%; background: var(--neon); border-radius: 10px; transition: 0.2s; }

        @media (max-width: 600px) {
            .app-wrapper { padding: 10px; }
            h1 { font-size: 1.6rem; }
        }
    </style>
</head>
<body>

<div id="canvas-container"></div>

<div class="app-wrapper">
    <header>
        <h1>Online Free Disk</h1>
        <div id="user-status" class="hidden">
            <span style="border: 1px solid var(--neon); padding: 5px 15px; border-radius: 20px;" id="display-name">User</span>
        </div>
    </header>

    <div class="main-content">
        <div id="auth-container" class="glass-panel" style="max-width: 450px;">
            <div class="tab-btn-container">
                <button class="tab-btn active" id="login-tab-btn" onclick="toggleAuth('login')">KIRISH</button>
                <button class="tab-btn" id="register-tab-btn" onclick="toggleAuth('register')">RO'YXATDAN O'TISH</button>
            </div>

            <div id="login-form">
                <input type="text" id="login-user" placeholder="Login">
                <input type="password" id="login-pass" placeholder="Parol">
                <button onclick="handleLogin()">TIZIMGA KIRISH</button>
            </div>

            <div id="register-form" class="hidden">
                <input type="text" id="reg-user" placeholder="Yangi login">
                <input type="password" id="reg-pass" placeholder="Yangi parol">
                <button onclick="handleRegister()" style="background: linear-gradient(135deg, #7000ff, #00f2fe);">PROFIL YARATISH</button>
            </div>
        </div>

        <div id="dashboard" class="hidden" style="width: 100%;">
            <div class="glass-panel" style="display: flex; flex-wrap: wrap; justify-content: space-around; text-align: center; gap: 15px;">
                <div>
                    <div style="font-size: 11px; opacity: 0.6;">BAND XOTIRA</div>
                    <div id="stat-storage" style="font-size: 18px; color: var(--neon);">0 MB</div>
                </div>
                <div>
                    <div style="font-size: 11px; opacity: 0.6;">FAYLLAR SONI</div>
                    <div id="stat-count" style="font-size: 18px; color: var(--neon);">0</div>
                </div>
                <div>
                    <div style="font-size: 11px; opacity: 0.6;">STATUS</div>
                    <div style="font-size: 18px; color: #00e676;">ONLINE</div>
                </div>
            </div>

            <div style="display: flex; gap: 10px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px;">
                <button onclick="switchTab('upload-tab')" style="flex:1;">YUKLASH</button>
                <button onclick="loadFiles()" style="flex:1;">OMBOR</button>
                <button onclick="switchTab('profile-tab')" style="flex:1;">PROFIL</button>
                <button onclick="location.reload()" style="background: #ff1744; flex:0.5;">CHIQISH</button>
            </div>

            <div id="upload-tab" class="tab-content glass-panel">
                <h3>YANGI FAYL</h3>
                <div class="drop-zone" id="drop-zone">
                    <p id="file-name-display">Faylni tanlang yoki tashlang</p>
                    <input type="file" id="file-input" class="hidden">
                </div>
                <div id="upload-progress" class="hidden progress-wrapper">
                    <div id="progress-text">0% Yuklanmoqda...</div>
                    <div class="bar-bg"><div id="bar-fill"></div></div>
                </div>
                <button onclick="uploadFile()">SERVERGA YUBORISH</button>
            </div>

            <div id="files-tab" class="tab-content hidden">
                <input type="text" id="search-input" placeholder="Fayllardan qidirish..." onkeyup="filterFiles()" style="margin-bottom: 20px; background: rgba(0,0,0,0.5);">
                <div class="file-grid" id="file-list"></div>
            </div>

            <div id="profile-tab" class="tab-content hidden glass-panel">
                <h3>PROFIL SOZLAMALARI</h3>
                <input type="text" id="upd-user" placeholder="Loginni o'zgartirish">
                <input type="password" id="upd-pass" placeholder="Yangi parol">
                <button onclick="updateProfile()">SAQLASH</button>
            </div>
        </div>
    </div>
</div>

<script>
    let currentUser = null;
    let allFiles = [];

    // --- Background 3D Space ---
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('canvas-container').appendChild(renderer.domElement);

    const starsGeo = new THREE.BufferGeometry();
    const starsCount = 6000;
    const posArr = new Float32Array(starsCount * 3);
    for(let i=0; i<starsCount*3; i++) posArr[i] = (Math.random() - 0.5) * 200;
    starsGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
    const starsMat = new THREE.PointsMaterial({ size: 0.1, color: 0xffffff });
    const starField = new THREE.Points(starsGeo, starsMat);
    scene.add(starField);

    camera.position.z = 1;
    function animate() { requestAnimationFrame(animate); starField.rotation.y += 0.0004; renderer.render(scene, camera); }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // --- Auth Logic ---
    function toggleAuth(mode) {
        const loginForm = document.getElementById('login-form');
        const regForm = document.getElementById('register-form');
        const lBtn = document.getElementById('login-tab-btn');
        const rBtn = document.getElementById('register-tab-btn');

        if(mode === 'login') {
            loginForm.classList.remove('hidden'); regForm.classList.add('hidden');
            lBtn.classList.add('active'); rBtn.classList.remove('active');
        } else {
            loginForm.classList.add('hidden'); regForm.classList.remove('hidden');
            rBtn.classList.add('active'); lBtn.classList.remove('active');
        }
    }

    async function handleLogin() {
        const u = document.getElementById('login-user').value;
        const p = document.getElementById('login-pass').value;
        if(!u || !p) return alert("Ma'lumotni kiriting!");
        const res = await fetch('/login', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p})
        });
        const data = await res.json();
        if(data.status === 'ok') loginSuccess(data.user_id, u);
        else alert("Login yoki parol xato!");
    }

    async function handleRegister() {
        const u = document.getElementById('reg-user').value;
        const p = document.getElementById('reg-pass').value;
        if(!u || !p) return alert("Ma'lumotni to'ldiring!");
        const res = await fetch('/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p})
        });
        const data = await res.json();
        if(data.status === 'ok') {
            alert("Ro'yxatdan o'tdingiz! Endi kirish qilishingiz mumkin.");
            toggleAuth('login');
        } else alert("Bu login band!");
    }

    function loginSuccess(id, name) {
        currentUser = { id, username: name };
        document.getElementById('display-name').innerText = name;
        document.getElementById('auth-container').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
        document.getElementById('user-status').classList.remove('hidden');
        updateStats();
    }

    // --- Core Func ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    dropZone.onclick = () => fileInput.click();
    fileInput.onchange = () => { if(fileInput.files[0]) document.getElementById('file-name-display').innerText = fileInput.files[0].name; };

    function switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
        document.getElementById(tabId).classList.remove('hidden');
    }

    async function updateStats() {
        const res = await fetch(`/profile_info/${currentUser.id}`);
        const data = await res.json();
        document.getElementById('stat-storage').innerText = data.storage;
    }

    function uploadFile() {
        const file = fileInput.files[0];
        if(!file) return alert("Fayl tanlang!");
        document.getElementById('upload-progress').classList.remove('hidden');
        const fd = new FormData();
        fd.append('file', file);
        fd.append('user_id', currentUser.id);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload');
        xhr.upload.onprogress = (e) => {
            const p = Math.round((e.loaded / e.total) * 100);
            document.getElementById('bar-fill').style.width = p + '%';
            document.getElementById('progress-text').innerText = p + '%';
        };
        xhr.onload = () => { alert("Yuklandi!"); updateStats(); loadFiles(); document.getElementById('upload-progress').classList.add('hidden'); };
        xhr.send(fd);
    }

    async function loadFiles() {
        const res = await fetch(`/files/${currentUser.id}`);
        allFiles = await res.json();
        document.getElementById('stat-count').innerText = allFiles.length;
        renderFiles(allFiles);
        switchTab('files-tab');
    }

    function renderFiles(files) {
        const list = document.getElementById('file-list');
        list.innerHTML = '';
        files.forEach(f => {
            const card = document.createElement('div');
            card.className = 'file-card';
            card.innerHTML = `
                <div style="word-break: break-all; margin-bottom: 10px;">${f.filename}</div>
                <div style="display: flex; gap: 5px;">
                    <button onclick="download('${f.filename}')" style="padding: 10px; font-size: 10px;">YUKLASH</button>
                    <button onclick="deleteFile(${f.id})" style="background: #ff1744; padding: 10px; font-size: 10px; width: 40px;">X</button>
                </div>
            `;
            list.appendChild(card);
        });
    }

    function filterFiles() {
        const q = document.getElementById('search-input').value.toLowerCase();
        renderFiles(allFiles.filter(f => f.filename.toLowerCase().includes(q)));
    }

    async function updateProfile() {
        const u = document.getElementById('upd-user').value || currentUser.username;
        const p = document.getElementById('upd-pass').value;
        if(!p) return alert("Yangi parolni kiriting!");
        await fetch('/update_profile', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: currentUser.id, username: u, password: p})
        });
        alert("Saqlandi! Tizimga qayta kiring."); location.reload();
    }

    function download(n) { window.location.href = `/download/${n}`; }
    async function deleteFile(id) { if(confirm("O'chirilsinmi?")) { await fetch(`/delete_file/${id}`, {method: 'POST'}); loadFiles(); } }
</script>
</body>
</html>
"""

# --- Backend Server ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (data['username'], data['password']))
        uid = c.lastrowid
        conn.commit()
        return jsonify({'status': 'ok', 'user_id': uid})
    except:
        return jsonify({'status': 'error', 'msg': 'Login band!'})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (data['username'], data['password']))
    u = c.fetchone()
    conn.close()
    if u: return jsonify({'status': 'ok', 'user_id': u[0]})
    return jsonify({'status': 'error'})

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    uid = request.form['user_id']
    if file:
        name = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], name)
        file.save(path)
        size = os.path.getsize(path)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO files (user_id, filename, filesize) VALUES (?, ?, ?)", (uid, name, size))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

@app.route('/profile_info/<int:user_id>')
def profile_info(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id=?", (user_id,))
    u = c.fetchone()
    c.execute("SELECT SUM(filesize) FROM files WHERE user_id=?", (user_id,))
    size = c.fetchone()[0] or 0
    size_mb = round(size / (1024 * 1024), 2)
    conn.close()
    return jsonify({'username': u[0], 'storage': f"{size_mb} MB"})

@app.route('/files/<int:user_id>')
def get_files(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, filename FROM files WHERE user_id=? ORDER BY id DESC", (user_id,))
    res = [{'id': r[0], 'filename': r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify(res)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/delete_file/<int:id>', methods=['POST'])
def delete_file(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT filename FROM files WHERE id=?", (id,))
    f = c.fetchone()
    if f:
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f[0]))
        except: pass
        c.execute("DELETE FROM files WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET username=?, password=? WHERE id=?", (data['username'], data['password'], data['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
