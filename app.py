import os
from logging import debug
from re import escape, split
from flask import Flask, render_template, session, url_for, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

import ast
import mysql.connector
import mariadb
import io
import csv


from werkzeug.wrappers import response

# IMPORTI

UPLOAD_FOLDER = "static/uploads/"

konekcija = mysql.connector.connect(
    passwd="",
    user="root",
    database="evidencijastudenata",
    port=3307,
    auth_plugin='mysql_native_password',
)

kursor = konekcija.cursor(dictionary=True)

app = Flask(__name__)
app.secret_key = "poggers123"


app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "evidencija.atvss@gmail.com"
app.config["MAIL_PASSWORD"] = "atvss123loz"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)

# deklaracija upload direktorijuma
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def send_email(ime, prezime, email, lozinka):
    msg = Message(subject="Korisnički nalog",
                  sender="ATVSS Evidencija studenata", recipients=[email],)
    msg.html = render_template(
        "email.html", ime=ime, prezime=prezime,  lozinka=lozinka)
    mail.send(msg)
    return "Sent"

# LOGIKA I RUTE


def ulogovan():
    if "ulogovani_korisnik" in session:
        return True
    else:
        return False


def rola():
    if ulogovan():
        return ast.literal_eval(session["ulogovani_korisnik"]).pop("rola")
# /login


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        forma = request.form
        upit = "SELECT * FROM korisnici WHERE email = %s"
        vrednost = (forma["email"],)
        kursor.execute(upit, vrednost)
        korisnik = kursor.fetchone()

        if korisnik != None:
            if korisnik["lozinka"] == forma["lozinka"]:
                session["ulogovani_korisnik"] = str(korisnik)
                return redirect(url_for("korisnici"))
            else:
                return render_template("login.html")

        else:
            return render_template("login.html")
# /logout


@app.route("/logout", methods=["GET"])
def logout():
    session.pop('ulogovani_korisnik', None)
    return render_template("login.html")


# KORISNICI
# /korisnici
@app.route("/korisnici", methods=["GET"])
def korisnici():

    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():
        upit = "SELECT * FROM korisnici LIMIT 10 OFFSET %s"

        strana = request.args.get("page", "1")

        offset = int(strana) * 10 - 10
        prethodna_strana = ""
        sledeca_strana = "/korisnici?page=2"

        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(
                split_path) + "=" + str(int(strana) - 1)

        vrednost = (offset,)
        kursor.execute(upit, vrednost)
        korisnici = kursor.fetchall()

        # ✔️
        return render_template("korisnici.html", rola=rola(), korisnici=korisnici, sledeca_strana=sledeca_strana, prethodna_strana=prethodna_strana, strana=strana)

    else:
        return redirect(url_for("login"))
# /korisnici/dodajkorisnika


@app.route("/dodajkorisnika/", methods=["GET", "POST"])
def dodajkorisnika():
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():
        if request.method == "GET":
            return render_template("dodajkorisnika.html")  # ✔️

        if request.method == "POST":
            forma = request.form
            # heshovanaLozinka = generate_password_hash(forma["lozinka"])
            vrednosti = (
                forma["ime"],
                forma["prezime"],
                forma["email"],
                forma["rola"],
                forma["lozinka"],
            )

            upit = """ INSERT INTO
                            korisnici(ime,prezime,email,rola,lozinka)
                            VALUES(%s, %s, %s, %s, %s)
                    """
            kursor.execute(upit, vrednosti)
            konekcija.commit()

            send_email(forma["ime"], forma["prezime"],
                       forma["email"], forma["lozinka"])

            return redirect(url_for("korisnici"))

    else:
        return redirect(url_for("login"))
# /korisnici/izmenikorisnika


@app.route("/izmenikorisnika/<id>", methods=["GET", "POST"])
def izmenikorisnika(id):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        if request.method == "GET":
            upit = " SELECT * FROM korisnici WHERE id = %s "
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            korisnik = kursor.fetchone()
            return render_template("izmenikorisnika.html", korisnik=korisnik)

        if request.method == "POST":
            upit = """ UPDATE korisnici SET
                            ime = %s,
                            prezime = %s,
                            email = %s,
                            rola = %s,
                            lozinka = %s
                            WHERE id = %s
                        """

            forma = request.form
            vrednosti = (
                forma["ime"],
                forma["prezime"],
                forma["email"],
                forma["rola"],
                forma["lozinka"],
                id
            )
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for("korisnici"))

    else:
        return redirect(url_for("login"))
# /korisnici/izbrisikorisnika


@app.route("/izbrisikorisnika/<id>", methods=["POST"])
def izbrisikorisnika(id):

    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        upit = """ DELETE FROM korisnici WHERE id = %s
            """

        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("korisnici"))

    else:
        return redirect(url_for("login"))
# PREDMETI
# /predmeti


@app.route("/predmeti", methods=["GET"])
def predmeti():
    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        upit = "SELECT * FROM predmeti"
        kursor.execute(upit)
        predmeti = kursor.fetchall()

        return render_template("predmeti.html", predmeti=predmeti, rola=rola())

    else:
        return redirect(url_for("login"))

# /predmeti/dodajpredmet


@app.route("/dodajpredmet", methods=["GET", "POST"])
def dodajpredmet():
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        if request.method == "GET":
            return render_template("dodajpredmet.html")  # ✔️

        if request.method == "POST":
            forma = request.form
            vrednosti = (
                forma["sifra"],
                forma["naziv"],
                forma["godStudija"],
                forma["espb"],
                forma["status"]
            )

            upit = """ INSERT INTO
                        predmeti(sifra,naziv,god_studija, espb, status)
                        VALUES(%s, %s, %s, %s, %s)
                """
            kursor.execute(upit, vrednosti)
            konekcija.commit()

            return redirect(url_for("predmeti"))
    else:
        return redirect(url_for("login"))
# /predmeti/izmenipredmet


@app.route("/izmenipredmet/<id>", methods=["GET", "POST"])
def izmenipredmet(id):
    if ulogovan():
        if rola() == 'Administrat':
            if request.method == "GET":
                upit = " SELECT * FROM predmeti WHERE id = %s "
                vrednost = (id,)
                kursor.execute(upit, vrednost)
                predmet = kursor.fetchone()
                return render_template("izmenipredmet.html", predmet=predmet)

            if request.method == "POST":
                upit = """ UPDATE predmeti SET
                            sifra = %s,
                            naziv = %s,
                            god_studija = %s,
                            espb = %s,
                            status = %s
                            WHERE id = %s
                        """

                forma = request.form
                vrednosti = (
                    forma["sifra"],
                    forma["naziv"],
                    forma["god_studija"],
                    forma["espb"],
                    forma["status"],
                    id
                )
                kursor.execute(upit, vrednosti)
                konekcija.commit()
                return redirect(url_for("predmeti"))
        else:
            return redirect(url_for("predmeti"))
    else:
        return redirect(url_for("login"))
# /predmeti/izbrisipredmet


@app.route("/izbrisipredmet/<id>", methods=["POST"])
def izbrisipredmet(id):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():
        upit = "DELETE FROM predmeti WHERE id = %s"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("predmeti"))

    else:
        return redirect(url_for("login"))
# STUDENTI

# /studenti


@app.route("/studenti", methods=["GET"])
def studenti():
    if ulogovan():

        strana = request.args.get("page", "1")
        offset = int(strana) * 5 - 5

        prethodna_strana = ""
        sledeca_strana = "/studenti?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")

            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(
                split_path) + "=" + str(int(strana) - 1)

        args = request.args.to_dict()
        order_by = "id"
        order_type = "asc"

        if "order_by" in args:
            order_by = args["order_by"].lower()
            if (
                "prethodni_order_by" in args
                and args["prethodni_order_by"] == args["order_by"]
            ):
                if args["order_type"] == "asc":
                    order_type = "desc"

        s_ime = "%%"
        s_prezime = "%%"
        s_broj_indeksa = "%%"
        s_god_studija = "%%"
        s_prosek_ocena_od = "0"
        s_prosek_ocena_do = "10"

        if "prosek_ocena_od" in args:
            if args["prosek_ocena_od"] == "":
                s_prosek_ocena_od = "0"
            else:
                s_prosek_ocena_od = args["prosek_ocena_od"]
        if "prosek_ocena_do" in args:
            if args["prosek_ocena_do"] == "":
                s_prosek_ocena_do = "10"
            else:
                s_prosek_ocena_do = args["prosek_ocena_do"]
        s_espb_od = "0"
        s_espb_do = "240"
        if "espb_od" in args:
            if args["espb_od"] == "":
                s_espb_od = "0"
            else:
                s_espb_od = args["espb_od"]
        if "espb_do" in args:
            if args["espb_do"] == "":
                s_espb_do = "240"
            else:
                s_espb_do = args["espb_do"]

        if "ime" in args:
            s_ime = "%" + args["ime"] + "%"
        if "prezime" in args:
            s_prezime = "%" + args["prezime"] + "%"
        if "broj_indeksa" in args:
            s_broj_indeksa = "%" + args["broj_indeksa"] + "%"
        if "god_studija" in args:
            s_god_studija = "%" + args["god_studija"] + "%"

        upit = "SELECT * FROM studenti WHERE ime LIKE %s AND prezime LIKE %s AND broj_indeksa LIKE %s AND god_studija LIKE %s AND espb >= %s AND espb <= %s AND prosek_ocena >= %s AND prosek_ocena <= %s ORDER BY " + \
            order_by + " " + order_type + " LIMIT 5 OFFSET %s"

        vrednosti = (
            s_ime,
            s_prezime,
            s_broj_indeksa,
            s_god_studija,
            s_espb_od,
            s_espb_do,
            s_prosek_ocena_od,
            s_prosek_ocena_do,
            offset,

        )
        kursor.execute(upit, vrednosti)
        studenti = kursor.fetchall()

        return render_template("studenti.html", studenti=studenti, rola=rola(), strana=strana, sledeca_strana=sledeca_strana, prethodna_strana=prethodna_strana, order_type=order_type, args=args)

    else:
        return redirect(url_for("login"))
# /student/<id>


@app.route("/student/<id>", methods=["GET"])
def student(id):
    if ulogovan():
        if request.method == "GET":
            studentUpit = " SELECT * FROM studenti WHERE id = %s"
            vrednost = (id,)

            kursor.execute(studentUpit, vrednost)
            student = kursor.fetchone()
            # --------------------------
            predmetiUpit = "SELECT * FROM predmeti"

            kursor.execute(predmetiUpit)
            predmeti = kursor.fetchall()
            # ----------------------------------

            oceneUpit = "SELECT * FROM ocene INNER JOIN predmeti ON ocene.predmet_id=predmeti.id WHERE student_id = %s"
            vrednost = (id,)

            kursor.execute(oceneUpit, vrednost)
            ocene = kursor.fetchall()

            return render_template("student.html", rola=rola(), student=student, predmeti=predmeti, ocene=ocene)

    else:
        return redirect(url_for("login"))

# /studenti/dodajstudenta


@app.route("/dodajstudenta", methods=["GET", "POST"])
def dodajstudenta():
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        if request.method == "GET":
            return render_template("dodajstudenta.html")

        if request.method == "POST":

            forma = request.form

            naziv_slike = ""

            if "slika" in request.files:
                file = request.files["slika"]

                if file.filename:
                    naziv_slike = forma["jmbgInput"] + file.filename
                    file.save(os.path.join(
                        app.config["UPLOAD_FOLDER"], naziv_slike))

            vrednosti = (
                forma["indexInput"],
                forma["nameInput"],
                forma["nameRoditeljInput"],
                forma["prezimeInput"],
                forma["emailInput"],
                forma["telInput"],
                forma["godStudija"],
                forma["espbInput"],
                forma["prosekInput"],
                forma["birthInput"],
                forma["jmbgInput"],
                naziv_slike,
            )

            upit = "INSERT INTO studenti (broj_indeksa, ime, ime_roditelja, prezime, email, broj_telefona, god_studija, espb, prosek_ocena, datum_rodjenja, jmbg, slika) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            kursor.execute(upit, vrednosti)
            konekcija.commit()

            return redirect(url_for("studenti"))
    else:
        return redirect(url_for("login"))
# /studenti/izmenistudenti


@app.route("/izmenistudenta/<id>", methods=["GET", "POST"])
def izmenistudenta(id):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        if request.method == "GET":
            upit = " SELECT * FROM studenti WHERE id = %s"
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            student = kursor.fetchone()
            return render_template("izmenistudenta.html", student=student)

        if request.method == "POST":

            forma = request.form

            naziv_slike = ""

            upit = """ UPDATE studenti SET
                            broj_indeksa = %s,
                            ime = %s,
                            ime_roditelja = %s,
                            prezime = %s,
                            email = %s,
                            broj_telefona = %s,
                            god_studija = %s,
                            espb = %s,
                            prosek_ocena = %s,
                            datum_rodjenja = %s,
                            jmbg = %s,
                            slika = %s
                            WHERE id = %s
                        """

            vrednosti = (
                forma["indexInput"],
                forma["nameInput"],
                forma["nameRoditeljInput"],
                forma["prezimeInput"],
                forma["emailInput"],
                forma["telInput"],
                forma["godStudija"],
                forma["espbInput"],
                forma["prosekInput"],
                forma["birthInput"],
                forma["jmbgInput"],
                naziv_slike,
                id
            )

            if "slika" in request.files:
                file = request.files["slika"]

                if file.filename:
                    naziv_slike = forma["jmbgInput"] + file.filename
                    file.save(os.path.join(
                        app.config["UPLOAD_FOLDER"], naziv_slike))

            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for("studenti"))

    else:
        return redirect(url_for("login"))
# /studenti/izbrisistudenti


@app.route("/izbrisistudenta/<id>", methods=["POST"])
def izbrisistudenta(id):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        upit = "DELETE FROM studenti WHERE id = %s"

        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("studenti"))

    else:
        return redirect(url_for("login"))


@app.route("/export/<tip>")
def export(tip):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        switch = {
            "studenti": "SELECT * FROM studenti",
            "korisnici": "SELECT * FROM korisnici",
            "predmeti": "SELECT * FROM predmeti",
        }

        upit = switch.get(tip)

        kursor.execute(upit)

        rezultat = kursor.fetchall()

        output = io.StringIO()

        writer = csv.writer(output)

        # br = 0

        for row in rezultat:
            red = []
            # br += 1
            for value in row.values():
                red.append(str(value))
            writer.writerow(red)

        output.seek(0)

        return response.Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=" + tip + ".csv"})

    else:
        return redirect(url_for("login"))
# /dodajocenu/id


@app.route("/dodajocenu/<id>", methods=["GET", "POST"])
def dodajocenu(id):
    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        upit = "INSERT INTO ocene (student_id, predmet_id, ocena, datum) VALUES (%s, %s, %s, %s)"

        forma = request.form
        vrednosti = (id,
                     forma['predmet'],
                     forma['ocena'],
                     forma['datum']
                     )
        kursor.execute(upit, vrednosti)
        konekcija.commit()

        # PROSEK OCENA
        upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id = %s"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        prosek_ocena = kursor.fetchone()

        # ESPB
        upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_id FROM ocene WHERE student_id = %s)"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        espb = kursor.fetchone()

        # Izmeni tabelu student
        upit = "UPDATE studenti SET espb = %s, prosek_ocena = %s WHERE id=%s"
        vrednosti = (
            espb['rezultat'],
            prosek_ocena['rezultat'],
            id
        )

        kursor.execute(upit, vrednosti)
        konekcija.commit()
        student = kursor.fetchone()

        return redirect(url_for("student", id=id, student=student, espb=espb, prosek_ocena=prosek_ocena,))

    else:
        return redirect(url_for("login"))

# IZMENI OCENU


@app.route("/izmeniocenu/<id>", methods=["GET", "POST"])
def izmeniocenu(id):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        if request.method == "GET":
            upit = "SELECT * FROM ocene WHERE id = %s"
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            ocena = kursor.fetchone()

            return render_template("izmeniocenu.html", ocena=ocena)

        if request.method == "POST":

            upit = "UPDATE ocene SET ocena = %s WHERE id = %s"

            forma = request.form
            vrednost = (forma["ocenaInput"], id)

            kursor.execute(upit, vrednost)
            konekcija.commit()

            return redirect(url_for("studenti"))

    else:
        return redirect(url_for("login"))
# IZBRISI OCENU


@app.route("/izbrisiocenu/<id>", methods=["POST"])
def izbrisiocenu(id):
    if (rola() == 'profesor'):
        return redirect(url_for('studenti'))

    if (rola() == 'student'):
        return redirect(url_for('studenti'))

    if ulogovan():

        upit = "DELETE FROM ocene WHERE id = %s"

        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()

        return redirect(url_for("student"))

    else:
        return redirect(url_for("login"))


# POKRETANJE
app.run(debug=True)
