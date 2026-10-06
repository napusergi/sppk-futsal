"""Database SQLite: skema, data awal (seed), dan helper query."""
import os
import sqlite3
from flask import g
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "sppk_futsal.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('superadmin','pelatih','pemain')), player_id INTEGER REFERENCES players(id),
  full_name TEXT, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('pending','active','rejected')),
  requested_role TEXT, note TEXT DEFAULT '', approved_by TEXT, approved_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS criteria(
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, training TEXT NOT NULL, sort_order INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS position_profile(
  criterion_id INTEGER REFERENCES criteria(id) ON DELETE CASCADE, position INTEGER,
  score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 9), PRIMARY KEY(criterion_id, position));
CREATE TABLE IF NOT EXISTS players(
  id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, position INTEGER NOT NULL,
  alt_positions TEXT DEFAULT '', desired_position INTEGER, assessment TEXT DEFAULT 'Tes objektif',
  notes TEXT DEFAULT '', archived INTEGER DEFAULT 0, archived_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS skills(
  player_id INTEGER REFERENCES players(id), criterion_id INTEGER REFERENCES criteria(id) ON DELETE CASCADE,
  value INTEGER NOT NULL CHECK(value BETWEEN 1 AND 10), PRIMARY KEY(player_id, criterion_id));
CREATE TABLE IF NOT EXISTS results(
  id INTEGER PRIMARY KEY, player_id INTEGER REFERENCES players(id), target_position INTEGER,
  best_position INTEGER, best_ci REAL, payload TEXT, created_by TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS ahp_mode(
  position INTEGER PRIMARY KEY, mode TEXT NOT NULL DEFAULT 'auto' CHECK(mode IN ('auto','manual')),
  updated_by TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS pairwise(
  position INTEGER, ci INTEGER REFERENCES criteria(id) ON DELETE CASCADE,
  cj INTEGER REFERENCES criteria(id) ON DELETE CASCADE, value REAL NOT NULL, PRIMARY KEY(position, ci, cj));
CREATE TABLE IF NOT EXISTS positions(
  idx INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS trainings(
  id INTEGER PRIMARY KEY, criterion_id INTEGER NOT NULL REFERENCES criteria(id) ON DELETE CASCADE,
  name TEXT NOT NULL, description TEXT DEFAULT '', duration TEXT DEFAULT '',
  level TEXT DEFAULT 'Menengah' CHECK(level IN ('Dasar','Menengah','Lanjut')), sort_order INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS logs(
  id INTEGER PRIMARY KEY, username TEXT, role TEXT, category TEXT, action TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""

# posisi awal: (nama, deskripsi); indeks 0..n-1 dipakai sebagai kunci posisi di seluruh tabel
DEFAULT_POSITIONS = [
    ("Goalkeeper", "Penjaga gawang: refleks, positioning, komunikasi, dan distribusi bola."),
    ("Fixo/Anchor", "Pemain bertahan paling belakang: membaca permainan, passing, duel, dan komunikasi."),
    ("Ala/Flank", "Pemain sayap: kecepatan, dribbling, stamina, dan transisi menyerang-bertahan."),
    ("Pivot", "Penyerang target: menahan bola membelakangi gawang, kontrol bola, dan finishing."),
]

# nama, training, skor kebutuhan [GK, Anchor, Ala, Pivot] (1-9: High=9, Medium=5, Low=1)
CRITERIA = [
    ("Passing", "Rondo drills, passing under pressure", [5, 9, 7, 5]),
    ("Shooting", "Finishing drills di area sempit, shooting accuracy", [1, 5, 7, 9]),
    ("Dribbling", "Cone dribble, duel 1v1", [1, 3, 9, 7]),
    ("Ball Control", "Shielding bola, kontrol di ruang sempit", [5, 7, 9, 9]),
    ("Positioning", "Latihan defensive shape, simulasi transisi", [9, 9, 5, 5]),
    ("Decision Making", "Small-sided games, latihan situasi cepat", [7, 9, 7, 7]),
    ("Communication", "Latihan koordinasi tim, role-play defensive calls", [9, 9, 5, 5]),
    ("Stamina", "Interval sprint, aerobic endurance", [3, 7, 9, 7]),
    ("Agility", "Ladder drills, side-to-side shuffles", [9, 5, 9, 5]),
    ("Strength/Shielding", "Core stability, squat, latihan duel fisik", [5, 9, 3, 9]),
    ("Reflex", "Reaction ball, save drills jarak dekat, latihan refleks 1v1 kiper", [9, 1, 1, 1]),
]

# kode, nama, posisi utama, posisi alternatif, posisi diinginkan, catatan, skill (urut CRITERIA, 1-10)
PLAYERS = [
    ("GK1", "Gilang Kurniawan", 0, "", 0, "Refleks tinggi, passing medium", [5, 2, 2, 5, 8, 6, 7, 5, 7, 6, 9]),
    ("GK2", "Galih Kusuma", 0, "", 0, "Distribusi bola kuat, agility tinggi", [8, 3, 3, 6, 7, 7, 6, 5, 9, 5, 7]),
    ("AN1", "Andi Nugroho", 1, "", 1, "Passing tinggi, positioning kuat", [9, 5, 4, 7, 9, 8, 7, 6, 5, 7, 2]),
    ("AN2", "Arief Nasution", 1, "", 1, "Komunikasi tinggi, stamina kuat", [7, 4, 4, 6, 7, 7, 9, 9, 6, 7, 2]),
    ("AN3", "Agus Nainggolan", 1, "", 3, "Ball control tinggi, strength tinggi", [6, 5, 5, 9, 7, 6, 6, 6, 5, 9, 2]),
    ("AL1", "Aldo Lesmana", 2, "", 2, "Dribbling tinggi, agility tinggi", [6, 6, 9, 8, 5, 6, 5, 7, 9, 4, 2]),
    ("AL2", "Alif Lubis", 2, "", 2, "Shooting medium, stamina tinggi", [6, 5, 6, 6, 5, 5, 6, 9, 7, 5, 2]),
    ("AL3", "Aryo Laksono", 2, "", 1, "Passing tinggi, decision making tinggi", [9, 6, 6, 7, 6, 9, 6, 7, 6, 5, 2]),
    ("PV1", "Putra Vidianto", 3, "", 3, "Shooting tinggi, shielding kuat", [5, 9, 6, 7, 5, 6, 5, 6, 5, 9, 2]),
    ("PV2", "Panji Virgiawan", 3, "", 3, "Ball control tinggi, finishing medium", [6, 5, 7, 9, 5, 6, 5, 6, 6, 7, 2]),
    # pemain multi-posisi
    ("MX1", "Rizky Maulana", 1, "2", 2, "Anchor/Flank: passing & stamina tinggi, dribbling baik", [8, 6, 7, 7, 8, 8, 7, 8, 7, 7, 2]),
    ("MX2", "Bima Saputra", 2, "3", 3, "Flank/Pivot: shooting & ball control tinggi", [6, 8, 8, 8, 5, 7, 5, 7, 8, 7, 2]),
    ("MX3", "Dimas Pratama", 0, "1", 1, "Kiper-libero: distribusi bola, positioning & komunikasi kuat", [8, 4, 4, 7, 8, 8, 8, 6, 7, 6, 7]),
    ("MX4", "Fajar Hidayat", 1, "3", 3, "Anchor/Pivot: strength & shielding dominan", [7, 7, 5, 8, 7, 7, 7, 7, 5, 9, 2]),
    ("MX5", "Yoga Permana", 2, "1,3", 2, "Universal: skill merata di semua area lapangan", [7, 7, 7, 7, 7, 7, 7, 8, 7, 7, 3]),
    ("MX6", "Hendra Wijaya", 2, "1", 1, "Flank/Anchor: agility & decision making tinggi", [7, 6, 7, 7, 7, 8, 6, 8, 8, 6, 2]),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(reset=False):
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    migrate_users(con)
    con.executescript(SCHEMA)
    if con.execute("SELECT COUNT(*) FROM criteria").fetchone()[0] == 0:
        seed(con)
    if con.execute("SELECT COUNT(*) FROM positions").fetchone()[0] == 0:
        con.executemany("INSERT INTO positions(idx,name,description) VALUES(?,?,?)",
                        [(i, n, d) for i, (n, d) in enumerate(DEFAULT_POSITIONS)])
    if con.execute("SELECT COUNT(*) FROM trainings").fetchone()[0] == 0:
        seed_trainings(con)
    if not con.execute("SELECT 1 FROM users WHERE role='superadmin'").fetchone():
        con.execute("INSERT INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)",
                    ("superadmin", generate_password_hash("superadmin123"), "superadmin", "Super Admin"))
    con.commit()
    con.close()


def seed_trainings(con):
    """Pecah teks training lama per kriteria (dipisah koma) menjadi daftar latihan terpisah."""
    for cid, text in con.execute("SELECT id, training FROM criteria").fetchall():
        for k, part in enumerate(x.strip() for x in (text or "").split(",")):
            if part:
                con.execute("INSERT INTO trainings(criterion_id,name,duration,level,sort_order) VALUES(?,?,?,?,?)",
                            (cid, part[0].upper() + part[1:], "20 menit", "Menengah", k))


def migrate_users(con):
    """Database versi lama (tanpa kolom status/role superadmin) -> skema baru, data akun dipertahankan."""
    cols = [r[1] for r in con.execute("PRAGMA table_info(users)")]
    if not cols or "status" in cols:
        return
    con.execute("PRAGMA foreign_keys=OFF")
    con.execute("ALTER TABLE users RENAME TO users_old")
    con.executescript(SCHEMA)
    con.execute("INSERT INTO users(id,username,password_hash,role,player_id,full_name) "
                "SELECT id,username,password_hash,role,player_id,full_name FROM users_old")
    con.execute("DROP TABLE users_old")
    con.commit()


def seed(con):
    for i, (name, training, prof) in enumerate(CRITERIA):
        cid = con.execute("INSERT INTO criteria(name,training,sort_order) VALUES(?,?,?)", (name, training, i)).lastrowid
        for p, s in enumerate(prof):
            con.execute("INSERT INTO position_profile VALUES(?,?,?)", (cid, p, s))
    cids = [r[0] for r in con.execute("SELECT id FROM criteria ORDER BY sort_order")]
    con.execute("INSERT INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)",
                ("pelatih", generate_password_hash("pelatih123"), "pelatih", "Coach Utama"))
    for code, name, pos, alt, desired, notes, sk in PLAYERS:
        pid = con.execute("INSERT INTO players(code,name,position,alt_positions,desired_position,notes) VALUES(?,?,?,?,?,?)",
                          (code, name, pos, alt, desired, notes)).lastrowid
        for cid, v in zip(cids, sk):
            con.execute("INSERT INTO skills VALUES(?,?,?)", (pid, cid, v))
        con.execute("INSERT INTO users(username,password_hash,role,player_id,full_name) VALUES(?,?,?,?,?)",
                    (code.lower(), generate_password_hash("pemain123"), "pemain", pid, name))
    con.execute("INSERT INTO logs(username,role,category,action) VALUES('system','system','input',?)",
                (f"Seed data awal: {len(CRITERIA)} kriteria, {len(PLAYERS)} pemain",))
