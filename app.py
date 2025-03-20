from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.secret_key = "rahasia_super_admin"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Model Database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # "admin" atau "user"

class Berita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    gambar = db.Column(db.String(255), nullable=True)
    waktu = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Komentar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    berita_id = db.Column(db.Integer, db.ForeignKey("berita.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("komentar.id"), nullable=True)
    waktu = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    berita_id = db.Column(db.Integer, db.ForeignKey("berita.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# Halaman Utama (Daftar Berita)
@app.route("/")
def index():
    berita = Berita.query.order_by(Berita.waktu.desc()).all()
    return render_template("index.html", berita=berita)

# Detail Berita
@app.route("/berita/<int:id>")
def detail_berita(id):
    berita = Berita.query.get_or_404(id)
    komentar = Komentar.query.filter_by(berita_id=id).all()
    return render_template("berita.html", berita=berita, komentar=komentar)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Login berhasil!", "success")
            return redirect(url_for("index"))
        else:
            flash("Username atau password salah!", "danger")
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logout berhasil!", "success")
    return redirect(url_for("index"))

# Halaman Admin (Tambah Berita)
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        flash("Akses ditolak!", "danger")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        judul = request.form["judul"]
        kategori = request.form["kategori"]
        isi = request.form["isi"]
        berita_baru = Berita(judul=judul, kategori=kategori, isi=isi)
        db.session.add(berita_baru)
        db.session.commit()
        flash("Berita berhasil ditambahkan!", "success")
        return redirect(url_for("admin_dashboard"))

    berita = Berita.query.all()
    return render_template("admin_dashboard.html", berita=berita)

# Hapus Berita (Admin)
@app.route("/hapus_berita/<int:id>")
def hapus_berita(id):
    if "role" not in session or session["role"] != "admin":
        flash("Akses ditolak!", "danger")
        return redirect(url_for("login"))

    berita = Berita.query.get_or_404(id)
    db.session.delete(berita)
    db.session.commit()
    flash("Berita berhasil dihapus!", "success")
    return redirect(url_for("admin_dashboard"))

# Register Pengguna
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        user_baru = User(username=username, password=hashed_password, role="user")
        db.session.add(user_baru)
        db.session.commit()
        flash("Registrasi berhasil, silakan login!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# Tambah Komentar
@app.route("/komentar/<int:berita_id>", methods=["POST"])
def tambah_komentar(berita_id):
    if "user_id" not in session:
        flash("Silakan login untuk berkomentar!", "danger")
        return redirect(url_for("login"))

    isi = request.form["isi"]
    komentar_baru = Komentar(berita_id=berita_id, user_id=session["user_id"], isi=isi)
    db.session.add(komentar_baru)
    db.session.commit()
    flash("Komentar berhasil ditambahkan!", "success")
    return redirect(url_for("detail_berita", id=berita_id))

# Like Berita
@app.route("/like/<int:berita_id>")
def like_berita(berita_id):
    if "user_id" not in session:
        flash("Silakan login untuk menyukai berita!", "danger")
        return redirect(url_for("login"))

    like = Like.query.filter_by(berita_id=berita_id, user_id=session["user_id"]).first()
    if like:
        db.session.delete(like)
        flash("Like dihapus!", "warning")
    else:
        like_baru = Like(berita_id=berita_id, user_id=session["user_id"])
        db.session.add(like_baru)
        flash("Berita disukai!", "success")

    db.session.commit()
    return redirect(url_for("detail_berita", id=berita_id))

# Jalankan Aplikasi
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Membuat database jika belum ada
    app.run(debug=True)