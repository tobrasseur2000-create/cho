from flask import flash
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///cho.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

db = SQLAlchemy(app)


class Membre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), default="")
    statut = db.Column(db.String(20), default="student")
    titre = db.Column(db.String(50))
    annee_entree = db.Column(db.Integer)
    comite = db.Column(db.String(50))
    merite = db.Column(db.Integer, default=0)
    non_seance = db.Column(db.String(20), default="jamais")
    regime = db.Column(db.String(30), default="normal")
    regime_details = db.Column(db.String(200), default="")

    def code_anno(self):
        return code_anno(self.titre, self.annee_entree, self.comite)


def code_anno(titre, annee_entree, comite):
    if not annee_entree:
        return ""
    anciennete = date.today().year - annee_entree
    return f"{titre or ''} {anciennete} ans ({comite or ''})".strip()


@app.route("/")
def index():
    membres = Membre.query.order_by(Membre.nom).all()
    return render_template("index.html", membres=membres)


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if request.method == "POST":
        m = Membre(
            nom=request.form["nom"],
            prenom=request.form["prenom"],
            statut=request.form["statut"],
            titre=request.form["titre"],
            annee_entree=int(request.form["annee_entree"] or 0),
            comite=request.form["comite"],
            merite=int(request.form["merite"] or 0),
            non_seance=request.form["non_seance"],
            regime=request.form["regime"],
            regime_details=request.form.get("regime_details", ""),
        )
        db.session.add(m)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("membre.html", m=None)


@app.route("/modifier/<int:id>", methods=["GET", "POST"])
def modifier(id):
    m = Membre.query.get_or_404(id)
    if request.method == "POST":
        m.nom = request.form["nom"]
        m.prenom = request.form["prenom"]
        m.statut = request.form["statut"]
        m.titre = request.form["titre"]
        m.annee_entree = int(request.form["annee_entree"] or 0)
        m.comite = request.form["comite"]
        m.merite = int(request.form["merite"] or 0)
        m.non_seance = request.form["non_seance"]
        m.regime = request.form["regime"]
        m.regime_details = request.form.get("regime_details", "")
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("membre.html", m=m)


@app.route("/supprimer/<int:id>", methods=["POST"])
def supprimer(id):
    m = Membre.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("index"))


# Création des tables au chargement (nécessaire pour gunicorn sur Render)
with app.app_context():
    db.create_all()
@app.route("/fix-db")
def fix_db():
    from sqlalchemy import text
    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE membre ADD COLUMN IF NOT EXISTS prenom VARCHAR(100) DEFAULT ''"))
        conn.execute(text("ALTER TABLE membre ADD COLUMN IF NOT EXISTS statut VARCHAR(20) DEFAULT 'student'"))
        conn.execute(text("ALTER TABLE membre ADD COLUMN IF NOT EXISTS regime VARCHAR(30) DEFAULT 'normal'"))
        conn.execute(text("ALTER TABLE membre ADD COLUMN IF NOT EXISTS regime_details VARCHAR(200) DEFAULT ''"))
    return "✅ Base corrigée ! Tu peux supprimer cette route maintenant."

if __name__ == "__main__":
    app.run(debug=True)
import io
import pandas as pd

@app.route("/import", methods=["GET", "POST"])
def import_members():
    if request.method == "POST":
        file = request.files.get("fichier")
        if not file or file.filename == "":
            flash("Aucun fichier choisi")
            return redirect(url_for("import_members"))
        try:
            df = pd.read_excel(io.BytesIO(file.read()))
        except Exception:
            flash("Impossible de lire ce fichier (format .xlsx attendu)")
            return redirect(url_for("import_members"))

        # nettoie les noms de colonnes : minuscules, sans espaces
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        created = 0
        for _, row in df.iterrows():
            if pd.isna(row.get("nom")):
                continue  # ligne sans nom → ignorée

            def get(col, default=""):
                v = row.get(col, default)
                return default if pd.isna(v) else v

            m = Membre(
                nom=str(get("nom")).strip(),
                prenom=str(get("prenom")).strip(),
                statut=str(get("statut", "student")).strip(),
                titre=str(get("titre")).strip() or None,
                annee_entree=int(get("annee_entree", 0)) if str(get("annee_entree", "")).strip() else None,
                comite=str(get("comite")).strip() or None,
                merite=int(get("merite", 0)) if str(get("merite", "")).strip() else 0,
                non_seance=str(get("non_seance", "jamais")).strip(),
                regime=str(get("regime", "normal")).strip(),
                regime_details=str(get("regime_details")).strip(),
            )
            db.session.add(m)
            created += 1

        db.session.commit()
        flash(f"✅ {created} membres importés !")
        return redirect(url_for("index"))

    return render_template("import.html")
