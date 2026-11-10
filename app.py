import io
import csv
import pathlib
from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy

folder = pathlib.Path(__file__).parent.resolve()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(folder / "cho.db")
db = SQLAlchemy(app)

COMITES = ["—", "Oedipus", "Boulimicus", "Maniacus", "Mythomanus",
           "Psychopathus", "Delirius", "Cerebrus"]
CODES_COMITE = {"Oedipus": 100000, "Boulimicus": 200000, "Maniacus": 300000,
                "Mythomanus": 400000, "Psychopathus": 500000,
                "Delirius": 600000, "Cerebrus": 700000}
APPARTENANCES = {
    "membre": 10000, "président(e) honoraire": 10000,
    "grand(e)-maître(sse) honoraire": 10000, "contre-sénateur/trice": 10000,
    "extra-muros": 20000, "sénateur/trice": 30000, "membre fondateur": 30000,
    "Rector Sanatori": 40000,
}
MERITES = ["", "membre", "chevalier", "officier", "commandeur",
           "praticien(ne) en chef"]
REGIMES = ["normal", "végétarien", "cumul", "allergie/intolérance"]


def code_anno(appartenance, annee, comite):
    if comite in CODES_COMITE:
        return CODES_COMITE[comite]
    return APPARTENANCES.get(appartenance, 10000) + int(annee)


class Membre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    statut = db.Column(db.String(10), nullable=False)
    regime = db.Column(db.String(30), default="normal")
    regime_details = db.Column(db.String(200), default="")
    annee_entree = db.Column(db.Integer, nullable=False)
    appartenance = db.Column(db.String(50), default="membre")
    comite = db.Column(db.String(30), default="—")
    merite = db.Column(db.Integer, default=0)
    non_seance = db.Column(db.String(20), default="jamais")


@app.route("/")
def index():
    membres = Membre.query.order_by(Membre.nom).all()
    for m in membres:
        m.code = code_anno(m.appartenance, m.annee_entree, m.comite)
    return render_template("index.html", membres=membres)


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if request.method == "POST":
        m = Membre(
            nom=request.form["nom"], prenom=request.form["prenom"],
            statut=request.form["statut"], regime=request.form["regime"],
            regime_details=request.form.get("regime_details", ""),
            annee_entree=int(request.form["annee_entree"]),
            appartenance=request.form["appartenance"],
            comite=request.form["comite"],
            merite=int(request.form["merite"]),
            non_seance=request.form["non_seance"])
        db.session.add(m)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("membre.html", m=None)


@app.route("/modifier/<int:mid>", methods=["GET", "POST"])
def modifier(mid):
    m = Membre.query.get_or_404(mid)
    if request.method == "POST":
        m.nom = request.form["nom"]
        m.prenom = request.form["prenom"]
        m.statut = request.form["statut"]
        m.regime = request.form["regime"]
        m.regime_details = request.form.get("regime_details", "")
        m.annee_entree = int(request.form["annee_entree"])
        m.appartenance = request.form["appartenance"]
        m.comite = request.form["comite"]
        m.merite = int(request.form["merite"])
        m.non_seance = request.form["non_seance"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("membre.html", m=m)


@app.route("/supprimer/<int:mid>")
def supprimer(mid):
    db.session.delete(Membre.query.get_or_404(mid))
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/export")
def export():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Nom", "Prénom", "Statut", "Régime", "Détails régime",
                "Année entrée", "Appartenance", "Comité", "Mérite",
                "Non-séance", "Code ANNO"])
    for m in Membre.query.order_by(Membre.nom):
        w.writerow([m.nom, m.prenom, m.statut, m.regime, m.regime_details,
                    m.annee_entree, m.appartenance, m.comite,
                    MERITES[m.merite] or "non décoré(e)", m.non_seance,
                    code_anno(m.appartenance, m.annee_entree, m.comite)])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment;filename=membres.csv"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
