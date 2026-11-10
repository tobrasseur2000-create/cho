import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///cho.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

db = SQLAlchemy(app)


class Membre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    titre = db.Column(db.String(50))
    annee_entree = db.Column(db.Integer)
    comite = db.Column(db.String(50))
    merite = db.Column(db.Integer, default=0)
    non_seance = db.Column(db.Text)

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
            titre=request.form["titre"],
            annee_entree=int(request.form["annee_entree"] or 0),
            comite=request.form["comite"],
            merite=int(request.form["merite"] or 0),
            non_seance=request.form["non_seance"],
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
        m.titre = request.form["titre"]
        m.annee_entree = int(request.form["annee_entree"] or 0)
        m.comite = request.form["comite"]
        m.merite = int(request.form["merite"] or 0)
        m.non_seance = request.form["non_seance"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("membre.html", m=m)


@app.route("/supprimer/<int:id>", methods=["POST"])
def supprimer(id):
    m = Membre.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
