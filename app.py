from flask import Flask, request, redirect, session, render_template_string, send_from_directory
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import urllib.parse
import urllib.request

app = Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")
app.secret_key = "bhiriya-admin-secret-key-2026"

DATABASE = "village.db"

ADMIN_USERNAME = "@abhay"
ADMIN_PASSWORD = "9935"

# ============================================================
# GOOGLE FORM / GOOGLE SHEET SETTINGS
# ============================================================
GOOGLE_APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbxnIo59iJ5JyI00EGy2LRwr5lrplNhqHMA4qp2AhYUL3D22-y51jdj6DKY_vAqpuJ9Qkw"
    "/exec"
)
GOOGLE_API_SECRET = "BHIRIYA_2026_FAMILY_SECRET_987654"

# Public Google Form link:
# Isko apne actual Google Form URL se replace kar dena.
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf_RuGeQi0lAY854gbRPZISqMjN-YxEWgyOJQ12HCwgZVP4vg/viewform?usp=dialog"

# ============================================================
# UPLOAD SETTINGS
# ============================================================
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def create_database():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id TEXT UNIQUE,
            head_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            address TEXT NOT NULL,
            members TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            complaint_date TEXT,
            photo TEXT
        )
    """)

    columns = db.execute("PRAGMA table_info(complaints)").fetchall()
    column_names = [c["name"] for c in columns]

    if "complaint_date" not in column_names:
        db.execute("ALTER TABLE complaints ADD COLUMN complaint_date TEXT")

    if "photo" not in column_names:
        db.execute("ALTER TABLE complaints ADD COLUMN photo TEXT")

    db.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


# ============================================================
# HELPERS
# ============================================================
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def admin_logged_in():
    return session.get("admin_logged_in") is True


def safe(value):
    return value if value is not None else ""


# ============================================================
# GOOGLE SHEET API
# ============================================================
def google_sheet_get(action="pending", row=None):
    params = {
        "action": action,
        "token": GOOGLE_API_SECRET,
    }

    if row is not None:
        params["row"] = str(row)

    url = GOOGLE_APPS_SCRIPT_URL + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:
        return {
            "success": False,
            "message": str(error),
        }


def google_sheet_post(action, row, family_id=""):
    data = {
        "action": action,
        "row": str(row),
        "token": GOOGLE_API_SECRET,
    }

    if family_id:
        data["family_id"] = family_id

    encoded = urllib.parse.urlencode(data).encode("utf-8")

    try:
        req = urllib.request.Request(
            GOOGLE_APPS_SCRIPT_URL,
            data=encoded,
            headers={"User-Agent": "Mozilla/5.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:
        return {
            "success": False,
            "message": str(error),
        }


# ============================================================
# COMMON STYLE
# ============================================================
STYLE = r"""
:root{
    --bg:#07130f;
    --bg2:#0c2017;
    --card:#10271c;
    --card2:#153524;
    --text:#effaf3;
    --muted:#a8c2b2;
    --line:rgba(255,255,255,.10);
    --gold:#e6c66b;
    --green:#29b873;
    --green2:#77e2aa;
    --red:#ff7070;
    --blue:#85bfff;
    --shadow:0 20px 60px rgba(0,0,0,.28);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
    margin:0;
    font-family:Segoe UI,Arial,sans-serif;
    color:var(--text);
    background:
      radial-gradient(circle at 10% 0%,rgba(41,184,115,.15),transparent 30%),
      radial-gradient(circle at 90% 5%,rgba(230,198,107,.10),transparent 26%),
      var(--bg);
}
a{text-decoration:none;color:inherit}
.container{width:min(1180px,92%);margin:auto}
.developer-banner{
    width:100%;
    text-align:center;
    padding:10px 14px;
    background:#0c2017;
    color:#e6c66b;
    border-bottom:1px solid rgba(255,255,255,.10);
    font-size:14px;
    font-weight:800;
    letter-spacing:.2px;
}
.nav{
    position:sticky;
    top:0;
    z-index:100;
    backdrop-filter:blur(18px);
    background:rgba(7,19,15,.82);
    border-bottom:1px solid var(--line);
}
.nav-inner{
    min-height:72px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    padding:10px 0;
}
.logo{font-weight:900;font-size:20px}
.logo span{color:var(--gold)}
.nav-links{
    display:flex;
    flex-wrap:wrap;
    gap:6px;
}
.nav-links a{
    color:var(--muted);
    font-size:14px;
    padding:9px 12px;
    border-radius:11px;
}
.nav-links a:hover{
    color:#fff;
    background:rgba(255,255,255,.06);
}
.hero{
    padding:82px 0 62px;
    min-height:590px;
    background:linear-gradient(145deg,rgba(17,51,35,.75),rgba(7,19,15,.8));
}
.hero-grid{
    display:grid;
    grid-template-columns:1.2fr .8fr;
    gap:42px;
    align-items:center;
}
.badge{
    display:inline-block;
    padding:8px 12px;
    border:1px solid var(--line);
    border-radius:999px;
    color:var(--green2);
    background:rgba(255,255,255,.04);
    font-size:13px;
}
.hero h1{
    font-size:clamp(46px,7vw,82px);
    line-height:.94;
    margin:18px 0;
}
.hero h1 span{color:var(--gold)}
.hero p{
    color:var(--muted);
    font-size:18px;
    line-height:1.7;
    max-width:720px;
}
.actions{
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-top:22px;
}
.btn{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    border:0;
    border-radius:13px;
    padding:12px 17px;
    font-weight:800;
    cursor:pointer;
}
.btn-primary{background:var(--gold);color:#111}
.btn-dark{
    color:#fff;
    background:rgba(255,255,255,.07);
    border:1px solid var(--line);
}
.btn-danger{background:#6d2222;color:#fff}
.btn:hover{filter:brightness(1.06)}
.hero-card,.card,.req-card{
    background:linear-gradient(160deg,rgba(21,53,36,.96),rgba(10,28,20,.98));
    border:1px solid var(--line);
    border-radius:22px;
    box-shadow:var(--shadow);
}
.hero-card{padding:28px}
.card{padding:22px}
.section{padding:72px 0}
.section-head{
    display:flex;
    justify-content:space-between;
    align-items:end;
    gap:20px;
    margin-bottom:24px;
}
.section h2{font-size:36px;margin:0}
.sub{color:var(--muted);line-height:1.6}
.kicker{
    color:var(--green2);
    text-transform:uppercase;
    letter-spacing:1.4px;
    font-size:12px;
}
.big{
    color:var(--gold);
    font-weight:900;
    font-size:52px;
}
.grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:18px;
}
.location{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:14px;
}
.value{
    margin-top:7px;
    font-size:22px;
    font-weight:800;
}
.icon{font-size:31px}
.card:hover,.req-card:hover{
    transform:translateY(-3px);
    transition:.18s ease;
}
.notice-list{display:grid;gap:14px}
.notice{
    padding:18px;
    border:1px solid var(--line);
    border-radius:18px;
    background:rgba(255,255,255,.035);
}
.notice small{color:var(--muted)}
.form-wrap{max-width:780px;margin:40px auto}
.form-card{padding:30px}
label{
    display:block;
    margin:14px 0 7px;
    font-weight:700;
}
input,textarea,select{
    width:100%;
    padding:13px 14px;
    border:1px solid var(--line);
    border-radius:12px;
    background:#081a12;
    color:#fff;
    outline:0;
}
textarea{min-height:135px;resize:vertical}
input:focus,textarea:focus,select:focus{
    border-color:rgba(119,226,170,.65);
}
.table-wrap{
    overflow:auto;
    border:1px solid var(--line);
    border-radius:18px;
}
table{
    width:100%;
    min-width:850px;
    border-collapse:collapse;
}
th,td{
    padding:14px;
    border-bottom:1px solid var(--line);
    text-align:left;
}
th{color:var(--green2);font-size:13px}
td{color:#dceee3}
.status{
    display:inline-flex;
    padding:6px 10px;
    border-radius:999px;
    font-size:12px;
    font-weight:900;
}
.pending{background:rgba(230,198,107,.16);color:var(--gold)}
.progress{background:rgba(133,191,255,.14);color:var(--blue)}
.resolved{background:rgba(41,184,115,.16);color:var(--green2)}
.alert,.success{
    padding:14px 16px;
    border-radius:14px;
    margin:14px 0;
}
.alert{
    background:rgba(255,112,112,.10);
    border:1px solid rgba(255,112,112,.25);
}
.success{
    background:rgba(41,184,115,.10);
    border:1px solid rgba(41,184,115,.25);
}
.admin-top{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:14px;
    margin-bottom:22px;
}
.stat .n{
    color:var(--gold);
    font-size:34px;
    font-weight:900;
}
.req-grid{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:18px;
}
.req-card{padding:22px}
.new{
    display:inline-block;
    color:var(--green2);
    background:rgba(41,184,115,.14);
    padding:6px 10px;
    border-radius:999px;
    font-size:12px;
    font-weight:900;
}
.info{
    color:var(--muted);
    margin-top:12px;
    line-height:1.6;
}
.members{
    background:rgba(0,0,0,.15);
    border-radius:12px;
    padding:12px;
    margin-top:6px;
    white-space:pre-line;
    color:#eaf7ee;
}
.empty{
    text-align:center;
    padding:44px 22px;
    border:1px dashed var(--line);
    border-radius:22px;
    color:var(--muted);
}
.back{
    display:inline-block;
    color:var(--green2);
    margin-bottom:18px;
}
.footer{
    padding:35px 0;
    border-top:1px solid var(--line);
    color:var(--muted);
}
.mini{
    font-size:13px;
    color:var(--muted);
}
.inline{display:inline}
.small-btn{
    padding:9px 12px;
    border-radius:10px;
    font-size:13px;
}
@media(max-width:900px){
    .hero-grid,.grid,.location,.admin-top,.req-grid{
        grid-template-columns:1fr 1fr;
    }
}
@media(max-width:650px){
    .nav-inner{
        align-items:flex-start;
        flex-direction:column;
    }
    .nav-links{
        width:100%;
        display:grid;
        grid-template-columns:repeat(2,1fr);
    }
    .hero-grid,.grid,.location,.admin-top,.req-grid{
        grid-template-columns:1fr;
    }
    .hero{padding:54px 0 38px}
}
"""


def page(title, content):
    admin_link = (
        "<a href='/admin-dashboard'>Admin</a>"
        if admin_logged_in()
        else "<a href='/admin'>Admin Login</a>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Mera Bhiriya</title>
<style>{STYLE}</style>
</head>
<body>

<div class="developer-banner">🌐 This Website Developed by Abhay Dixit</div>

<nav class="nav">
    <div class="container nav-inner">
        <a class="logo" href="/">🏡 Mera <span>Bhiriya</span></a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/#about">Gaon Ki Jankari</a>
            <a href="/#services">Services</a>
            <a href="/complaint">Complaint</a>
            <a href="/track">Track</a>
            <a href="/#notices">Notices</a>
            {admin_link}
        </div>
    </div>
</nav>

{content}

<footer class="footer">
  <div class="container">
    <b>🏡 Mera Bhiriya</b> · Digital Village Portal<br>
    Bhiriya, Tehsil Shahabad, Block Pihani, District Hardoi, Uttar Pradesh
  </div>
</footer>

</body>
</html>"""


# ============================================================
# HOME
# ============================================================
@app.route("/")
def home():
    db = get_db()

    notices = db.execute(
        "SELECT * FROM notices ORDER BY id DESC LIMIT 5"
    ).fetchall()

    family_count = db.execute(
        "SELECT COUNT(*) AS n FROM families"
    ).fetchone()["n"]

    complaint_count = db.execute(
        "SELECT COUNT(*) AS n FROM complaints"
    ).fetchone()["n"]

    resolved_count = db.execute(
        "SELECT COUNT(*) AS n FROM complaints WHERE status='Resolved'"
    ).fetchone()["n"]

    db.close()

    notice_html = ""

    if notices:
        for n in notices:
            notice_html += f"""
            <div class="notice">
                <h3>📢 {safe(n["title"])}</h3>
                <p>{safe(n["description"])}</p>
                <small>{safe(n["created_at"])}</small>
            </div>
            """
    else:
        notice_html = '<div class="empty">No notice available right now.</div>'

    google_form_button = ""
    if GOOGLE_FORM_URL and not GOOGLE_FORM_URL.startswith("PASTE_"):
        google_form_button = f"""
        <a class="btn btn-dark" target="_blank" href="{GOOGLE_FORM_URL}">
            📝 Google Family Form
        </a>
        """

    content = f"""
<section class="hero">
  <div class="container" style="margin-bottom:30px">
    <img src="/static/images/village-bhiriya.png" alt="Bhiriya Village - Chnadan Lal Baba Mandir" style="width:100%;height:520px;object-fit:cover;border-radius:24px;border:1px solid var(--line);box-shadow:var(--shadow);display:block">
  </div>

  <div class="container hero-grid">
    <div>
      <div class="badge">🌿 Digital Village Portal</div>
      <h1>WELCOME TO<br><span>BHIRIYA</span></h1>
      <p>
        Bhiriya gaon ki jankari, family information, complaints
        aur important updates ek hi jagah.
      </p>

      <div class="actions">
        <a class="btn btn-primary" href="/family">👨‍👩‍👧‍👦 Family Data</a>
        {google_form_button}
        <a class="btn btn-dark" href="/complaint">📢 Complaint</a>
      </div>
    </div>

    <div class="hero-card">
      <div class="kicker">Village Snapshot</div>
      <div class="big">BHIRIYA</div>
      <p>
        Tehsil Shahabad · Block Pihani · District Hardoi · Uttar Pradesh
      </p>
      <hr style="border-color:var(--line);margin:22px 0">
      <div class="kicker">Portal Purpose</div>
      <p>
        Village information, citizen services, complaints and
        verified family records in one digital portal.
      </p>
    </div>
  </div>
</section>

<section class="section" id="about">
  <div class="container">
    <div class="section-head">
      <div>
        <h2>📍 Gaon Ki Jankari</h2>
        <p class="sub">Bhiriya ki basic location details.</p>
      </div>
    </div>

    <div class="location">
      <div class="card">
        <div class="kicker">Village</div>
        <div class="value">Bhiriya</div>
      </div>
      <div class="card">
        <div class="kicker">Tehsil</div>
        <div class="value">Shahabad</div>
      </div>
      <div class="card">
        <div class="kicker">Block</div>
        <div class="value">Pihani</div>
      </div>
      <div class="card">
        <div class="kicker">District</div>
        <div class="value">Hardoi</div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="services">
  <div class="container">
    <div class="section-head">
      <div>
        <h2>⚡ Services</h2>
        <p class="sub">Useful village services in one place.</p>
      </div>
    </div>

    <div class="grid">
      <a class="card" href="/family">
        <div class="icon">👨‍👩‍👧‍👦</div>
        <h3>Family Data</h3>
        <p>Basic family information website me submit karein.</p>
      </a>

      <a class="card" href="/complaint">
        <div class="icon">📢</div>
        <h3>Complaint</h3>
        <p>Road, water, electricity, cleanliness etc. report karein.</p>
      </a>

      <a class="card" href="/track">
        <div class="icon">🔎</div>
        <h3>Track Complaint</h3>
        <p>Complaint ID se current status check karein.</p>
      </a>

      <a class="card" href="/family-requests">
        <div class="icon">📋</div>
        <h3>Google Family Requests</h3>
        <p>Admin Google Form se aayi requests verify karein.</p>
      </a>

      <a class="card" href="/admin-dashboard">
        <div class="icon">🛠️</div>
        <h3>Admin Panel</h3>
        <p>Families, complaints and notices manage karein.</p>
      </a>

      <a class="card" href="/#notices">
        <div class="icon">📣</div>
        <h3>Notice Board</h3>
        <p>Village ke latest updates dekhein.</p>
      </a>
    </div>
  </div>
</section>

<section class="section" id="notices">
  <div class="container">
    <div class="section-head">
      <div>
        <h2>📋 Bhiriya Notice Board</h2>
        <p class="sub">Latest important notices.</p>
      </div>
    </div>

    <div class="notice-list">
      {notice_html}
    </div>
  </div>
</section>

<section class="section">
  <div class="container grid">
    <div class="card">
      <div class="kicker">Families</div>
      <div class="value">{family_count}</div>
      <p>Website family records.</p>
    </div>

    <div class="card">
      <div class="kicker">Complaints</div>
      <div class="value">{complaint_count}</div>
      <p>Total complaints submitted.</p>
    </div>

    <div class="card">
      <div class="kicker">Resolved</div>
      <div class="value">{resolved_count}</div>
      <p>Complaints marked resolved.</p>
    </div>
  </div>
</section>
"""

    return page("Home", content)


# ============================================================
# FAMILY FORM
# ============================================================
@app.route("/family")
def family():
    google_button = ""
    if GOOGLE_FORM_URL and not GOOGLE_FORM_URL.startswith("PASTE_"):
        google_button = f"""
        <div class="card" style="margin-top:18px">
          <h3>📝 Google Form se submit karein</h3>
          <p class="sub">
            Google Form wali family request admin verification ke liye
            Google Sheet me jayegi.
          </p>
          <a class="btn btn-primary" target="_blank" href="{GOOGLE_FORM_URL}">
            Open Google Family Form
          </a>
        </div>
        """

    content = f"""
<section class="section">
  <div class="container form-wrap">
    <a class="back" href="/">← Back to Home</a>

    <div class="card form-card">
      <h2>👨‍👩‍👧‍👦 Family Information</h2>
      <p class="sub">Direct website family entry.</p>

      <form method="POST" action="/add-family">
        <label>Family Head Name</label>
        <input name="head_name" required>

        <label>Mobile Number</label>
        <input name="mobile" required maxlength="15">

        <label>House / Mohalla / Address</label>
        <input name="address" required>

        <label>Family Members</label>
        <textarea name="members" required
          placeholder="Example: Aman, Ayush, Riya"></textarea>

        <div class="actions">
          <button class="btn btn-primary" type="submit">
            ✅ Submit Family Data
          </button>
        </div>
      </form>
    </div>

    {google_button}
  </div>
</section>
"""
    return page("Family Data", content)


@app.route("/add-family", methods=["POST"])
def add_family():
    head_name = request.form.get("head_name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    address = request.form.get("address", "").strip()
    members = request.form.get("members", "").strip()

    if not all([head_name, mobile, address, members]):
        return redirect("/family")

    db = get_db()

    cursor = db.execute(
        """
        INSERT INTO families
        (head_name, mobile, address, members)
        VALUES (?, ?, ?, ?)
        """,
        (head_name, mobile, address, members),
    )

    family_id = f"BHR-FAM-{cursor.lastrowid:04d}"

    db.execute(
        "UPDATE families SET family_id=? WHERE id=?",
        (family_id, cursor.lastrowid),
    )

    db.commit()
    db.close()

    return redirect("/family-success/" + family_id)


@app.route("/family-success/<family_id>")
def family_success(family_id):
    content = f"""
<section class="section">
  <div class="container form-wrap">
    <div class="card form-card" style="text-align:center">
      <div style="font-size:64px">✅</div>
      <h2>Family Data Submitted</h2>
      <p>Your family data has been saved successfully.</p>

      <div class="success">
        <b>Family ID: {family_id}</b><br>
        Is ID ko save karke rakhein.
      </div>

      <div class="actions" style="justify-content:center">
        <a class="btn btn-primary" href="/">🏠 Home</a>
        <a class="btn btn-dark" href="/family">📝 Add Another</a>
      </div>
    </div>
  </div>
</section>
"""
    return page("Family Submitted", content)


# ============================================================
# GOOGLE FAMILY REQUESTS
# ============================================================
@app.route("/family-requests")
def family_requests():
    if not admin_logged_in():
        return redirect("/admin")

    result = google_sheet_get("pending")

    if not result.get("success"):
        cards = f"""
        <div class="alert">
            ⚠️ Google Sheet connection failed.<br>
            <span class="mini">{safe(result.get("message", "Unknown error"))}</span>
        </div>
        """
    else:
        families = result.get("families", [])

        if not families:
            cards = """
            <div class="empty">
              <h2>✅ No Pending Requests</h2>
              <p>Google Form se abhi koi new family request pending nahi hai.</p>
              <p class="mini">Google Form submit hone ke baad Refresh karein.</p>
            </div>
            """
        else:
            cards_list = []

            for family_data in families:
                row = family_data.get("_row", "")
                head = safe(family_data.get("Family Head Name", ""))
                mobile = safe(family_data.get("Mobile Number", ""))
                address = safe(family_data.get("House / Mohalla / Address", ""))
                members = safe(family_data.get("Family Members", ""))
                timestamp = safe(family_data.get("Timestamp", ""))

                cards_list.append(f"""
                <div class="req-card">
                    <span class="new">NEW REQUEST</span>

                    <h2>👤 {head}</h2>

                    <div class="info">
                      📅 <b>Submitted:</b> {timestamp}
                    </div>

                    <div class="info">
                      📱 <b>Mobile:</b> {mobile}
                    </div>

                    <div class="info">
                      📍 <b>Address:</b><br>
                      {address}
                    </div>

                    <div class="info">
                      👨‍👩‍👧‍👦 <b>Family Members:</b>
                      <div class="members">{members}</div>
                    </div>

                    <div class="actions">
                      <form class="inline"
                            action="/admin/approve-family-request"
                            method="POST">

                        <input type="hidden" name="row" value="{row}">
                        <input type="hidden" name="head_name" value="{head}">
                        <input type="hidden" name="mobile" value="{mobile}">
                        <input type="hidden" name="address" value="{address}">
                        <input type="hidden" name="members" value="{members}">

                        <button class="btn btn-primary" type="submit"
                          onclick="return confirm('Is family request ko approve karke website me add karna hai?')">
                          ✅ Approve & Add
                        </button>
                      </form>

                      <form class="inline"
                            action="/admin/reject-family-request"
                            method="POST">

                        <input type="hidden" name="row" value="{row}">

                        <button class="btn btn-dark" type="submit"
                          onclick="return confirm('Is family request ko reject karna hai?')">
                          ❌ Reject
                        </button>
                      </form>
                    </div>
                </div>
                """)

            cards = '<div class="req-grid">' + "".join(cards_list) + '</div>'

    content = f"""
<section class="section">
  <div class="container">
    <a class="back" href="/admin-dashboard">← Dashboard</a>

    <div class="section-head">
      <div>
        <div class="kicker">Google Form → Sheet</div>
        <h2>📋 Family Requests</h2>
        <p class="sub">
          Pending Google Form requests ko yahin verify karein.
        </p>
      </div>

      <a class="btn btn-dark" href="/family-requests">↻ Refresh</a>
    </div>

    {cards}
  </div>
</section>
"""
    return page("Family Requests", content)


@app.route("/admin/approve-family-request", methods=["POST"])
def approve_family_request():
    if not admin_logged_in():
        return redirect("/admin")

    row = request.form.get("row", type=int)
    head_name = request.form.get("head_name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    address = request.form.get("address", "").strip()
    members = request.form.get("members", "").strip()

    if not row or not all([head_name, mobile, address, members]):
        return redirect("/family-requests")

    db = get_db()

    existing = db.execute(
        """
        SELECT id, family_id
        FROM families
        WHERE head_name=? AND mobile=? AND address=? AND members=?
        """,
        (head_name, mobile, address, members),
    ).fetchone()

    if existing:
        db.close()
        google_sheet_post("approve", row, "ALREADY-IMPORTED")
        return redirect("/family-requests")

    cursor = db.execute(
        """
        INSERT INTO families
        (head_name, mobile, address, members)
        VALUES (?, ?, ?, ?)
        """,
        (head_name, mobile, address, members),
    )

    family_id = f"BHR-FAM-{cursor.lastrowid:04d}"

    db.execute(
        "UPDATE families SET family_id=? WHERE id=?",
        (family_id, cursor.lastrowid),
    )

    db.commit()
    db.close()

    google_result = google_sheet_post(
        "approve",
        row,
        family_id
    )

    if not google_result.get("success"):
        content = f"""
        <section class="section">
          <div class="container form-wrap">
            <div class="card form-card">
              <div class="alert">
                ⚠️ Family <b>{family_id}</b> website me add ho gayi hai,
                lekin Google Sheet status update nahi ho paya.
              </div>

              <p class="mini">
                Reason: {safe(google_result.get("message", "Unknown error"))}
              </p>

              <a class="btn btn-primary" href="/family-requests">
                Back to Requests
              </a>
            </div>
          </div>
        </section>
        """
        return page("Google Sheet Warning", content)

    return redirect("/family-requests")


@app.route("/admin/reject-family-request", methods=["POST"])
def reject_family_request():
    if not admin_logged_in():
        return redirect("/admin")

    row = request.form.get("row", type=int)

    if not row:
        return redirect("/family-requests")

    result = google_sheet_post("reject", row)

    if not result.get("success"):
        content = f"""
        <section class="section">
          <div class="container form-wrap">
            <div class="card form-card">
              <div class="alert">
                ⚠️ Google Sheet me request reject nahi ho paayi.
              </div>

              <p class="mini">
                Reason: {safe(result.get("message", "Unknown error"))}
              </p>

              <a class="btn btn-primary" href="/family-requests">
                Back to Requests
              </a>
            </div>
          </div>
        </section>
        """
        return page("Reject Error", content)

    return redirect("/family-requests")


# ============================================================
# FAMILY MANAGEMENT
# ============================================================
@app.route("/families")
def families():
    if not admin_logged_in():
        return redirect("/admin")

    search = request.args.get("search", "").strip()

    db = get_db()

    if search:
        value = f"%{search}%"
        data = db.execute(
            """
            SELECT *
            FROM families
            WHERE family_id LIKE ?
               OR head_name LIKE ?
               OR mobile LIKE ?
               OR address LIKE ?
            ORDER BY id DESC
            """,
            (value, value, value, value),
        ).fetchall()
    else:
        data = db.execute(
            "SELECT * FROM families ORDER BY id DESC"
        ).fetchall()

    db.close()

    rows = []

    for f in data:
        rows.append(f"""
        <tr>
            <td><b>{safe(f["family_id"])}</b></td>
            <td>{safe(f["head_name"])}</td>
            <td>{safe(f["mobile"])}</td>
            <td>{safe(f["address"])}</td>
            <td>
              <div class="actions">
                <a class="btn btn-dark small-btn"
                   href="/family-details/{f["id"]}">View</a>

                <a class="btn btn-dark small-btn"
                   href="/admin/edit-family/{f["id"]}">Edit</a>

                <form class="inline"
                      method="POST"
                      action="/admin/delete-family/{f["id"]}">
                    <button class="btn btn-dark small-btn"
                      type="submit"
                      onclick="return confirm('Family record delete karna hai?')">
                      Delete
                    </button>
                </form>
              </div>
            </td>
        </tr>
        """)

    table_rows = "".join(rows)

    if not table_rows:
        table_rows = '<tr><td colspan="5">No family records found.</td></tr>'

    content = f"""
<section class="section">
  <div class="container">
    <a class="back" href="/admin-dashboard">← Dashboard</a>

    <div class="section-head">
      <div>
        <h2>👨‍👩‍👧‍👦 Family Management</h2>
        <p class="sub">Search, view, edit and delete family records.</p>
      </div>
    </div>

    <form class="actions" method="GET">
      <input
        style="flex:1;min-width:230px"
        name="search"
        value="{search}"
        placeholder="Search family ID, name, mobile or address"
      >
      <button class="btn btn-primary" type="submit">
        🔎 Search
      </button>
      <a class="btn btn-dark" href="/families">Reset</a>
    </form>

    <div class="table-wrap" style="margin-top:20px">
      <table>
        <thead>
          <tr>
            <th>Family ID</th>
            <th>Head</th>
            <th>Mobile</th>
            <th>Address</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
  </div>
</section>
"""
    return page("Families", content)


@app.route("/family-details/<int:family_db_id>")
def family_details(family_db_id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()

    family_data = db.execute(
        "SELECT * FROM families WHERE id=?",
        (family_db_id,),
    ).fetchone()

    db.close()

    if not family_data:
        return redirect("/families")

    content = f"""
<section class="section">
  <div class="container form-wrap">
    <a class="back" href="/families">← Family List</a>

    <div class="card form-card">
      <div class="kicker">Family ID</div>
      <h2>{safe(family_data["family_id"])}</h2>

      <p><b>👤 Family Head:</b><br>{safe(family_data["head_name"])}</p>
      <p><b>📱 Mobile:</b><br>{safe(family_data["mobile"])}</p>
      <p><b>📍 Address:</b><br>{safe(family_data["address"])}</p>
      <p><b>👨‍👩‍👧‍👦 Family Members:</b><br>{safe(family_data["members"])}</p>

      <div class="actions">
        <a class="btn btn-primary"
           href="/admin/edit-family/{family_data["id"]}">
          ✏️ Edit
        </a>

        <form method="POST"
              action="/admin/delete-family/{family_data["id"]}">
          <button class="btn btn-dark"
            type="submit"
            onclick="return confirm('Family delete karna hai?')">
            🗑️ Delete
          </button>
        </form>
      </div>
    </div>
  </div>
</section>
"""
    return page("Family Details", content)


@app.route("/admin/edit-family/<int:family_id>")
def edit_family(family_id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()

    family_data = db.execute(
        "SELECT * FROM families WHERE id=?",
        (family_id,),
    ).fetchone()

    db.close()

    if not family_data:
        return redirect("/families")

    content = f"""
<section class="section">
  <div class="container form-wrap">
    <a class="back" href="/families">← Family List</a>

    <div class="card form-card">
      <h2>✏️ Edit Family</h2>

      <form method="POST"
            action="/admin/update-family/{family_id}">

        <label>Family Head Name</label>
        <input name="head_name" required value="{safe(family_data["head_name"])}">

        <label>Mobile Number</label>
        <input name="mobile" required value="{safe(family_data["mobile"])}">

        <label>House / Mohalla / Address</label>
        <input name="address" required value="{safe(family_data["address"])}">

        <label>Family Members</label>
        <textarea name="members" required>{safe(family_data["members"])}</textarea>

        <div class="actions">
          <button class="btn btn-primary" type="submit">
            💾 Save Changes
          </button>
          <a class="btn btn-dark" href="/families">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</section>
"""
    return page("Edit Family", content)


@app.route("/admin/update-family/<int:family_id>", methods=["POST"])
def update_family(family_id):
    if not admin_logged_in():
        return redirect("/admin")

    head_name = request.form.get("head_name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    address = request.form.get("address", "").strip()
    members = request.form.get("members", "").strip()

    db = get_db()

    db.execute(
        """
        UPDATE families
        SET head_name=?, mobile=?, address=?, members=?
        WHERE id=?
        """,
        (
            head_name,
            mobile,
            address,
            members,
            family_id,
        ),
    )

    db.commit()
    db.close()

    return redirect("/family-details/" + str(family_id))


@app.route("/admin/delete-family/<int:family_id>", methods=["POST"])
def delete_family(family_id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    db.execute("DELETE FROM families WHERE id=?", (family_id,))
    db.commit()
    db.close()

    return redirect("/families")


# ============================================================
# COMPLAINT
# ============================================================
@app.route("/complaint")
def complaint():
    content = """
<section class="section">
  <div class="container form-wrap">
    <a class="back" href="/">← Back to Home</a>

    <div class="card form-card">
      <h2>📢 Register Complaint</h2>
      <p class="sub">Village related issue report karein.</p>

      <form method="POST"
            action="/add-complaint"
            enctype="multipart/form-data">

        <label>Name</label>
        <input name="name" required>

        <label>Mobile Number</label>
        <input name="mobile" required maxlength="15">

        <label>Complaint Category</label>
        <select name="category" required>
          <option value="">Select category</option>
          <option>Road</option>
          <option>Water</option>
          <option>Electricity</option>
          <option>Cleanliness</option>
          <option>Street Light</option>
          <option>School</option>
          <option>Health</option>
          <option>Drainage</option>
          <option>Other</option>
        </select>

        <label>Description</label>
        <textarea name="description" required
          placeholder="Problem detail me likhein"></textarea>

        <label>Optional Photo</label>
        <input type="file" name="photo"
               accept=".png,.jpg,.jpeg,.webp">

        <div class="actions">
          <button class="btn btn-primary" type="submit">
            🚀 Submit Complaint
          </button>
        </div>
      </form>
    </div>
  </div>
</section>
"""
    return page("Complaint", content)


@app.route("/add-complaint", methods=["POST"])
def add_complaint():
    name = request.form.get("name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not all([name, mobile, category, description]):
        return redirect("/complaint")

    complaint_date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    photo = request.files.get("photo")
    photo_filename = None

    if photo and photo.filename and allowed_file(photo.filename):
        safe_name = secure_filename(photo.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        photo_filename = timestamp + "_" + safe_name

        photo.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                photo_filename,
            )
        )

    db = get_db()

    cursor = db.execute(
        """
        INSERT INTO complaints
        (name,mobile,category,description,status,complaint_date,photo)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            name,
            mobile,
            category,
            description,
            "Pending",
            complaint_date,
            photo_filename,
        ),
    )

    complaint_id = f"BHR-{cursor.lastrowid:04d}"

    db.execute(
        "UPDATE complaints SET complaint_id=? WHERE id=?",
        (complaint_id, cursor.lastrowid),
    )

    db.commit()
    db.close()

    return redirect("/complaint-success/" + complaint_id)


@app.route("/complaint-success/<complaint_id>")
def complaint_success(complaint_id):
    content = f"""
<section class="section">
  <div class="container form-wrap">
    <div class="card form-card" style="text-align:center">
      <div style="font-size:64px">✅</div>
      <h2>Complaint Submitted</h2>

      <p>Your complaint has been saved successfully.</p>

      <div class="success">
        <b>Complaint ID: {complaint_id}</b><br>
        Is ID ko save karke rakhein.
      </div>

      <div class="actions" style="justify-content:center">
        <a class="btn btn-primary" href="/track">🔎 Track Complaint</a>
        <a class="btn btn-dark" href="/">🏠 Home</a>
      </div>
    </div>
  </div>
</section>
"""
    return page("Complaint Submitted", content)


@app.route("/track")
def track():
    content = """
<section class="section">
  <div class="container form-wrap">
    <a class="back" href="/">← Back to Home</a>

    <div class="card form-card">
      <h2>🔎 Track Complaint</h2>
      <p class="sub">
        Complaint ID enter karke current status check karein.
      </p>

      <form method="POST" action="/track-complaint">
        <label>Complaint ID</label>
        <input name="complaint_id"
               placeholder="Example: BHR-0001"
               required>

        <div class="actions">
          <button class="btn btn-primary" type="submit">
            Track Status
          </button>
        </div>
      </form>
    </div>
  </div>
</section>
"""
    return page("Track Complaint", content)


@app.route("/track-complaint", methods=["POST"])
def track_complaint():
    complaint_id = request.form.get(
        "complaint_id", ""
    ).strip().upper()

    db = get_db()

    complaint_data = db.execute(
        """
        SELECT * FROM complaints
        WHERE complaint_id=?
        """,
        (complaint_id,),
    ).fetchone()

    db.close()

    result_html = ""

    if not complaint_data:
        result_html = """
        <div class="alert">
          ❌ Complaint ID not found. Please check the ID.
        </div>
        """
    else:
        status = complaint_data["status"] or "Pending"

        status_class = {
            "Pending": "pending",
            "In Progress": "progress",
            "Resolved": "resolved",
        }.get(status, "pending")

        photo_html = ""

        if complaint_data["photo"]:
            photo_html = f"""
            <p>
              <a class="light-link"
                 target="_blank"
                 href="/uploads/{secure_filename(complaint_data["photo"])}">
                 📷 View Photo
              </a>
            </p>
            """

        result_html = f"""
        <div class="card" style="margin-top:20px">
          <div class="kicker">Complaint</div>
          <h2>{safe(complaint_data["complaint_id"])}</h2>

          <p><b>Name:</b> {safe(complaint_data["name"])}</p>
          <p><b>Category:</b> {safe(complaint_data["category"])}</p>
          <p><b>Description:</b> {safe(complaint_data["description"])}</p>
          <p><b>Date:</b> {safe(complaint_data["complaint_date"])}</p>

          <p>
            <b>Status:</b>
            <span class="status {status_class}">
              {safe(status)}
            </span>
          </p>

          {photo_html}
        </div>
        """

    content = f"""
<section class="section">
  <div class="container form-wrap">
    <a class="back" href="/track">← Search Again</a>

    <div class="card form-card">
      <h2>🔎 Complaint Result</h2>

      <form method="POST" action="/track-complaint">
        <label>Complaint ID</label>
        <input name="complaint_id"
               value="{complaint_id}"
               required>

        <div class="actions">
          <button class="btn btn-primary" type="submit">
            Track
          </button>
        </div>
      </form>

      {result_html}
    </div>
  </div>
</section>
"""
    return page("Track Complaint", content)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
    )


# ============================================================
# ADMIN LOGIN
# ============================================================
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            session["admin_logged_in"] = True
            return redirect("/admin-dashboard")

        error = "Invalid username or password."

    content = f"""
<section class="section">
  <div class="container form-wrap" style="max-width:520px">

    <div class="card form-card">
      <div class="icon">🔐</div>
      <h2>Admin Login</h2>
      <p class="sub">Mera Bhiriya administration panel.</p>

      {"<div class='alert'>❌ " + error + "</div>" if error else ""}

      <form method="POST">
        <label>Username</label>
        <input name="username" required autocomplete="off">

        <label>Password</label>
        <input type="password"
               name="password"
               required
               autocomplete="new-password">

        <div class="actions">
          <button class="btn btn-primary" type="submit">
            🔐 Login
          </button>
        </div>
      </form>
    </div>
  </div>
</section>
"""
    return page("Admin Login", content)


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect("/admin")


# ============================================================
# ADMIN DASHBOARD
# ============================================================
@app.route("/admin-dashboard")
def admin_dashboard():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()

    families = db.execute(
        "SELECT COUNT(*) AS n FROM families"
    ).fetchone()["n"]

    complaints = db.execute(
        "SELECT COUNT(*) AS n FROM complaints"
    ).fetchone()["n"]

    pending = db.execute(
        "SELECT COUNT(*) AS n FROM complaints WHERE status='Pending'"
    ).fetchone()["n"]

    resolved = db.execute(
        "SELECT COUNT(*) AS n FROM complaints WHERE status='Resolved'"
    ).fetchone()["n"]

    notices = db.execute(
        "SELECT COUNT(*) AS n FROM notices"
    ).fetchone()["n"]

    db.close()

    content = f"""
<section class="section">
  <div class="container">

    <div class="section-head">
      <div>
        <div class="kicker">Admin Panel</div>
        <h2>🛠️ Welcome, Admin</h2>
        <p class="sub">
          Bhiriya portal ka complete management center.
        </p>
      </div>

      <a class="btn btn-dark" href="/admin-logout">
        Logout
      </a>
    </div>

    <div class="admin-top">
      <div class="card stat">
        <div class="n">{families}</div>
        <div class="mini">Families</div>
      </div>

      <div class="card stat">
        <div class="n">{complaints}</div>
        <div class="mini">Complaints</div>
      </div>

      <div class="card stat">
        <div class="n">{pending}</div>
        <div class="mini">Pending</div>
      </div>

      <div class="card stat">
        <div class="n">{resolved}</div>
        <div class="mini">Resolved</div>
      </div>
    </div>

    <div class="grid">
      <a class="card" href="/family-requests">
        <div class="icon">📋</div>
        <h3>Google Family Requests</h3>
        <p>
          Google Form se aayi requests approve/reject karein.
        </p>
      </a>

      <a class="card" href="/families">
        <div class="icon">👨‍👩‍👧‍👦</div>
        <h3>Family Management</h3>
        <p>
          Existing family records manage karein.
        </p>
      </a>

      <a class="card" href="/complaints">
        <div class="icon">📢</div>
        <h3>Complaint Management</h3>
        <p>
          Complaints review aur status update karein.
        </p>
      </a>

      <a class="card" href="/admin/notices">
        <div class="icon">📣</div>
        <h3>Notice Board</h3>
        <p>
          {notices} notices manage karein.
        </p>
      </a>

      <a class="card" href="/">
        <div class="icon">🌐</div>
        <h3>Open Website</h3>
        <p>
          Public village portal open karein.
        </p>
      </a>
    </div>

  </div>
</section>
"""
    return page("Admin Dashboard", content)


# ============================================================
# COMPLAINT MANAGEMENT
# ============================================================
@app.route("/complaints")
def complaints():
    if not admin_logged_in():
        return redirect("/admin")

    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    db = get_db()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if status_filter in {
        "Pending",
        "In Progress",
        "Resolved"
    }:
        query += " AND status=?"
        params.append(status_filter)

    if search:
        value = f"%{search}%"
        query += """
          AND (
            complaint_id LIKE ?
            OR name LIKE ?
            OR mobile LIKE ?
            OR category LIKE ?
            OR description LIKE ?
          )
        """
        params.extend([value] * 5)

    query += " ORDER BY id DESC"

    data = db.execute(query, params).fetchall()

    db.close()

    rows = []

    for c in data:
        status = c["status"] or "Pending"

        status_class = {
            "Pending": "pending",
            "In Progress": "progress",
            "Resolved": "resolved",
        }.get(status, "pending")

        photo_html = ""

        if c["photo"]:
            photo_html = f"""
              <a class="light-link"
                 target="_blank"
                 href="/uploads/{secure_filename(c["photo"])}">
                 View
              </a>
            """

        rows.append(f"""
        <tr>
          <td>
            <b>{safe(c["complaint_id"])}</b><br>
            <span class="mini">{safe(c["complaint_date"])}</span>
          </td>

          <td>
            {safe(c["name"])}<br>
            {safe(c["mobile"])}
          </td>

          <td>{safe(c["category"])}</td>

          <td style="max-width:320px">
            {safe(c["description"])}
          </td>

          <td>{photo_html}</td>

          <td>
            <form method="POST"
                  action="/admin/update-complaint/{c["id"]}">
              <select name="status"
                      onchange="this.form.submit()">
                <option {"selected" if status=="Pending" else ""}>
                  Pending
                </option>
                <option {"selected" if status=="In Progress" else ""}>
                  In Progress
                </option>
                <option {"selected" if status=="Resolved" else ""}>
                  Resolved
                </option>
              </select>
            </form>

            <span class="status {status_class}"
                  style="margin-top:7px">
              {safe(status)}
            </span>
          </td>

          <td>
            <form method="POST"
                  action="/admin/delete-complaint/{c["id"]}">
              <button class="btn btn-dark small-btn"
                type="submit"
                onclick="return confirm('Is complaint ko permanently delete karna hai?')">
                Delete
              </button>
            </form>
          </td>
        </tr>
        """)

    table_rows = "".join(rows)

    if not table_rows:
        table_rows = '<tr><td colspan="7">No complaint records found.</td></tr>'

    content = f"""
<section class="section">
  <div class="container">

    <a class="back" href="/admin-dashboard">← Dashboard</a>

    <div class="section-head">
      <div>
        <h2>📢 Complaint Management</h2>
        <p class="sub">
          Search, filter, update status and delete complaints.
        </p>
      </div>
    </div>

    <form class="actions" method="GET">
      <input name="search"
             value="{search}"
             placeholder="Search ID, name, mobile, category..."
             style="flex:1;min-width:220px">

      <select name="status" style="max-width:200px">
        <option value="">All Status</option>
        <option {"selected" if status_filter=="Pending" else ""}>
          Pending
        </option>
        <option {"selected" if status_filter=="In Progress" else ""}>
          In Progress
        </option>
        <option {"selected" if status_filter=="Resolved" else ""}>
          Resolved
        </option>
      </select>

      <button class="btn btn-primary" type="submit">
        🔎 Filter
      </button>

      <a class="btn btn-dark" href="/complaints">
        Reset
      </a>
    </form>

    <div class="table-wrap" style="margin-top:20px">
      <table>
        <thead>
          <tr>
            <th>ID / Date</th>
            <th>Citizen</th>
            <th>Category</th>
            <th>Description</th>
            <th>Photo</th>
            <th>Status</th>
            <th>Delete</th>
          </tr>
        </thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>

  </div>
</section>
"""
    return page("Complaints", content)


@app.route(
    "/admin/update-complaint/<int:complaint_id>",
    methods=["POST"]
)
def update_complaint(complaint_id):
    if not admin_logged_in():
        return redirect("/admin")

    status = request.form.get("status", "Pending")

    if status not in {
        "Pending",
        "In Progress",
        "Resolved"
    }:
        status = "Pending"

    db = get_db()

    db.execute(
        "UPDATE complaints SET status=? WHERE id=?",
        (status, complaint_id),
    )

    db.commit()
    db.close()

    return redirect("/complaints")


@app.route(
    "/admin/delete-complaint/<int:complaint_id>",
    methods=["POST"]
)
def delete_complaint(complaint_id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()

    complaint_data = db.execute(
        "SELECT photo FROM complaints WHERE id=?",
        (complaint_id,),
    ).fetchone()

    if complaint_data and complaint_data["photo"]:
        path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            complaint_data["photo"],
        )

        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.execute(
        "DELETE FROM complaints WHERE id=?",
        (complaint_id,),
    )

    db.commit()
    db.close()

    return redirect("/complaints")


# ============================================================
# NOTICES
# ============================================================
@app.route("/admin/notices")
def admin_notices():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()

    notices = db.execute(
        "SELECT * FROM notices ORDER BY id DESC"
    ).fetchall()

    db.close()

    rows = []

    for n in notices:
        rows.append(f"""
        <tr>
          <td>{safe(n["title"])}</td>
          <td>{safe(n["description"])}</td>
          <td>{safe(n["created_at"])}</td>
          <td>
            <form method="POST"
                  action="/admin/delete-notice/{n["id"]}">
              <button class="btn btn-dark small-btn"
                type="submit"
                onclick="return confirm('Notice delete karna hai?')">
                Delete
              </button>
            </form>
          </td>
        </tr>
        """)

    table_rows = "".join(rows)

    if not table_rows:
        table_rows = '<tr><td colspan="4">No notices found.</td></tr>'

    content = f"""
<section class="section">
  <div class="container">

    <a class="back" href="/admin-dashboard">← Dashboard</a>

    <div class="grid">
      <div class="card">
        <h2>📣 Add Notice</h2>

        <form method="POST"
              action="/admin/add-notice">

          <label>Notice Title</label>
          <input name="title" required>

          <label>Description</label>
          <textarea name="description" required></textarea>

          <div class="actions">
            <button class="btn btn-primary" type="submit">
              Publish Notice
            </button>
          </div>
        </form>
      </div>

      <div class="card">
        <h2>📋 Notice Board</h2>
        <p class="sub">
          Latest notices public home page par show hongi.
        </p>
      </div>
    </div>

    <div class="table-wrap" style="margin-top:20px">
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Created</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
  </div>
</section>
"""
    return page("Notice Management", content)


@app.route("/admin/add-notice", methods=["POST"])
def add_notice():
    if not admin_logged_in():
        return redirect("/admin")

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if title and description:
        db = get_db()

        db.execute(
            """
            INSERT INTO notices (title, description)
            VALUES (?, ?)
            """,
            (title, description),
        )

        db.commit()
        db.close()

    return redirect("/admin/notices")


@app.route(
    "/admin/delete-notice/<int:notice_id>",
    methods=["POST"]
)
def delete_notice(notice_id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()

    db.execute(
        "DELETE FROM notices WHERE id=?",
        (notice_id,),
    )

    db.commit()
    db.close()

    return redirect("/admin/notices")


# ============================================================
# 404
# ============================================================
@app.errorhandler(404)
def not_found(error):
    content = """
<section class="section">
  <div class="container form-wrap">

    <div class="card form-card" style="text-align:center">
      <div style="font-size:62px">404</div>
      <h2>Page Not Found</h2>
      <p class="sub">
        Ye page available nahi hai.
      </p>

      <a class="btn btn-primary" href="/">
        🏠 Home
      </a>
    </div>

  </div>
</section>
"""
    return page("404", content), 404


# ============================================================
# START APP
# ============================================================
create_database()

if __name__ == "__main__":
    app.run(debug=True)
