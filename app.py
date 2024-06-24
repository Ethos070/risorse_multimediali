from flask import Flask, redirect, url_for, render_template, request, session
import mysql.connector
import hashlib

app = Flask(__name__)
app.secret_key = "mysecretkey"


def get_db():
    db = mysql.connector.connect(
        host='mysql-8da69e6-risorse-multimediali.h.aivencloud.com',
        port=18790,
        user='avnadmin',
        password='',
        database='Risorse-multimediali',
        charset='utf8mb4',
        connect_timeout=10
    )
    return db

def encrypt_password(password):
    sha1 = hashlib.sha1()
    sha1.update(password.encode())
    return sha1.hexdigest()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/registrazione", methods=["GET", "POST"])
def registrazione():
    if request.method == "POST":
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        citta = request.form["citta"]
        indirizzo = request.form["indirizzo"]
        password = request.form["password"]
        password = encrypt_password(password)

        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO utenti (nome, cognome, telefono, email, citta, indirizzo, password) VALUES ('{nome}', '{cognome}', '{telefono}', '{email}', '{citta}', '{indirizzo}', '{password}')")
        db.commit()
        db.close()
        return render_template("login.html", errore=None)
    else:
        return render_template("registrazione.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if "email" in session:
        return redirect(url_for("home"))
    
    if request.method == "POST":
        mail = request.form["email"]
        password = request.form["password"]
        password = encrypt_password(password)

        db = get_db()
        cursor = db.cursor()
        query = f"SELECT email, password, admin, id FROM utenti WHERE email = '{mail}'"
        cursor.execute(query)
        user = cursor.fetchone()
        db.close()

        if user and user[1] == password:
            session["idusr"] = user[3]
            session["email"] = mail
            session["admin"] = True if user[2] == 1 else False
            return redirect(url_for("home"))
        else:
            return render_template("login.html", errore="Email o password errati")

    else:
        return render_template("login.html")

@app.route("/profilo")
def profilo ():
   if "email" in session:
       db = get_db()
       cursor = db.cursor()
       query = f"""
            SELECT nome, cognome, telefono, email, citta, indirizzo, admin
            FROM utenti WHERE email = '{session['email']}'"""
       cursor.execute(query)
       user = cursor.fetchone()
       db.close()
       admin = True if user[-1] == 1 else False
       return render_template("profilo.html", user=user,isAdmin=admin)
   else:
       return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("email")
    session.pop("admin")
    return redirect(url_for("home"))

@app.route("/catalogo")
def catalogo ():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome FROM risorse WHERE stato = 'Disponibile'")
    dati = cursor.fetchall()
    db.close()

    if dati:
        return render_template("catalogo.html", dati=dati, loggedIn=("email" in session))

    return redirect(url_for("home"))

@app.route("/catalogo/dettagli", methods=["GET", "POST"])
def dettagli_catalogo ():
    id_ris = request.args.get("id")
    if request.method == "POST":
        data_inizio = request.form["data_inizio"]
        
        db = get_db()
        cursor = db.cursor()
        query = f"INSERT INTO prestiti (IdRisorsa, IdUtente, Data_inizio, stato) VALUES ('{id_ris}', '{session['idusr']}', '{data_inizio}', 'Prenotato')"
        cursor.execute(query)
        db.commit()
        cursor.execute(f"UPDATE risorse SET Stato = 'In prestito' WHERE Id = '{id_ris}'")
        db.commit()
        db.close()
        
        return redirect(url_for("home"))
    else:
        db = get_db()
        cursor = db.cursor()
        query = f"""
                SELECT risorse.Id, risorse.nome, categorie.nome, risorse.Stato, risorse.Descrizione 
                FROM risorse 
                INNER JOIN categorie ON categorie.Id = risorse.IdCategoria
                WHERE risorse.id = '{id_ris}'
        """
        cursor.execute(query)
        dettagli = cursor.fetchone()
        db.close()
        return render_template("dettagli_catalogo.html", dettagli=dettagli)

@app.route("/categorie")
def categorie ():
    if "admin" in session and "admin" in session and session["admin"]:
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM categorie"
        cursor.execute(query)
        dettagli_categorie = cursor.fetchall()
        db.close()
    
        return render_template("categorie.html", categorie=dettagli_categorie)
    return redirect(url_for("home"))

@app.route("/categorie/dettagli")
def dettagli_categorie ():
    if "admin" in session and session["admin"]:
        id_cat = request.args.get("id_cat")
        db = get_db()
        cursor = db.cursor()
        query = f"SELECT * FROM categorie WHERE id = {id_cat}"
        cursor.execute(query)
        cat = cursor.fetchone()
        db.close()
        return render_template("dettagli_categoria.html", categoria=cat)
    return redirect(url_for("home"))

@app.route("/categorie/modifica", methods=["GET", "POST"])
def modifica_categorie ():
    if "admin" in session and session["admin"]:
        if request.method == "POST":
            id_cat = request.args.get("id_cat")
            nome_cat = request.form["nome_cat"]
            descrizione = request.form["descrizione"]

            db = get_db()
            cursor = db.cursor()
            query = f"UPDATE categorie SET nome = '{nome_cat}', descrizione = '{descrizione}' WHERE id = {id_cat}"
            cursor.execute(query)
            db.commit()
            db.close()
            return redirect(url_for("categorie"))
        else:
            id_cat = request.args.get("id_cat")
            db = get_db()
            cursor = db.cursor()
            query = f"SELECT * FROM categorie WHERE id = {id_cat}"
            cursor.execute(query)
            cat = cursor.fetchone()
            db.close()
            return render_template("modifica_categoria.html", categoria=cat)
    return redirect(url_for("home"))

@app.route("/categorie/elimina")
def elimina_categorie ():
    if "admin" in session and session["admin"]:
        id_cat = request.args.get("id_cat")
        db = get_db()
        cur = db.cursor()
        cur.execute(f"DELETE FROM categorie WHERE id = {id_cat}")
        db.commit()
        db.close()
        return redirect(url_for("categorie"))
    return redirect(url_for("home"))

@app.route("/categorie/aggiungi", methods=["GET", "POST"])
def aggiungi_categorie ():
    if "admin" in session and session["admin"]:
        if request.method == "POST":
            nome_cat = request.form["nome_cat"]
            descrizione = request.form["descrizione"]
            db = get_db()
            cur = db.cursor()
            cur.execute(f"INSERT INTO categorie (nome, descrizione) VALUES ('{nome_cat}', '{descrizione}')")
            db.commit()
            db.close()
            return redirect(url_for("categorie"))
        else:
            return render_template("modifica_categoria.html", categoria=None)
    return redirect(url_for("home"))

@app.route("/risorse")
def risorse ():
    if "admin" in session and session["admin"]:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, nome, stato FROM risorse")
        dettagli_risorse = cur.fetchall()
        db.close()
        if dettagli_risorse is None:
            return render_template("risorse.html", risorse=None)
        
        return render_template("risorse.html", risorse=dettagli_risorse)
    return redirect(url_for("home"))

@app.route("/risorse/dettagli")
def dettagli_risorse ():
    if "admin" in session and session["admin"]:
        id_ris = request.args.get("id_ris")
        db = get_db()
        cur = db.cursor()
        cur.execute(f"""
                    SELECT risorse.Id, risorse.nome, categorie.Nome, risorse.Stato, risorse.descrizione 
                    FROM `risorse`
                    INNER JOIN categorie
                    ON categorie.Id = risorse.IdCategoria 
                    WHERE risorse.id = '{id_ris}'
""")
        ris = cur.fetchone()
        db.close()
        return render_template("dettagli_risorsa.html", risorsa=ris)
    return redirect(url_for("home"))

@app.route("/risorse/modifica", methods=["GET", "POST"])
def modifica_risorse ():
    if "admin" in session and session["admin"]:
        db = get_db()
        cur = db.cursor()
        if request.method == "POST":
            id_ris = request.args.get("id_ris")
            nome_ris = request.form["nome_ris"]
            categoria = request.form["lista_cat"]
            stato = request.form["lista_stati"]
            descrizione = request.form["descrizione"]
            cur.execute(f"UPDATE risorse SET nome = '{nome_ris}', IdCategoria = {categoria}, Stato = '{stato}', descrizione = '{descrizione}' WHERE id = {id_ris}")
            db.commit()
            db.close()
            return redirect(url_for("risorse"))
        else:
            id_ris = request.args.get("id_ris")
            cur.execute(f"""
                    SELECT risorse.Id, risorse.nome, categorie.Nome, risorse.Stato, risorse.descrizione 
                    FROM `risorse`
                    INNER JOIN categorie
                    ON categorie.Id = risorse.IdCategoria 
                    WHERE risorse.id = '{id_ris}'
""")
            ris = cur.fetchone()
            cur.close()
            cur = db.cursor()
            cur.execute("SELECT * FROM categorie")
            categorie = cur.fetchall()
            db.close()
            return render_template("modifica_risorsa.html", risorsa=ris, categorie=categorie)
    return redirect(url_for("home"))

@app.route("/risorse/elimina")
def elimina_risorse ():
    if "admin" in session and session["admin"]:
        id_ris = request.args.get("id_ris")
        db = get_db()
        cur = db.cursor()
        cur.execute(f"DELETE FROM risorse WHERE id = {id_ris}")
        db.commit()
        db.close()
        return redirect(url_for("risorse"))
    return redirect(url_for("home"))

@app.route("/risorse/aggiungi", methods=["GET", "POST"])
def aggiungi_risorse ():
    if "admin" in session and session["admin"]:
        if request.method == "POST":
            nome_ris = request.form["nome_ris"]
            categoria = request.form["lista_cat"]
            stato = request.form["lista_stati"]
            descrizione = request.form["descrizione"]
            db = get_db()
            cur = db.cursor()
            cur.execute(f"INSERT INTO risorse (nome, IdCategoria, Stato, descrizione) VALUES ('{nome_ris}', {categoria}, '{stato}', '{descrizione}')")
            db.commit()
            db.close()
            return redirect(url_for("risorse"))
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id, nome FROM categorie")
            categorie = cur.fetchall()
            db.close()
            return render_template("modifica_risorsa.html", risorsa=None, categorie=categorie)
    return redirect(url_for("home"))

@app.route("/prestiti")
def prestiti ():
    if "admin" in session and session["admin"]:
        db = get_db()
        cur = db.cursor()
        q_risorse = cur.execute("""
                        SELECT prestiti.Id, risorse.Nome, utenti.Nome, prestiti.Stato, prestiti.Data_inizio, prestiti.Data_fine
                        FROM `prestiti` 
                        inner JOIN utenti on utenti.Id = prestiti.IdUtente 
                        INNER JOIN risorse on risorse.id = prestiti.IdRisorsa
""")

            
        prestiti = cur.fetchall()
        db.close()
        return render_template("prestiti.html", prestiti=prestiti)
    return redirect(url_for("home"))

@app.route("/prestiti/dettagli")
def dettagli_prestiti ():
    if "admin" in session and session["admin"]:
        id_pre = request.args.get("id_pre")
        db = get_db()
        cur = db.cursor()
        cur.execute(f"""
                    SELECT prestiti.Id, risorse.Nome, utenti.Nome, prestiti.Stato, prestiti.Data_inizio, prestiti.Data_fine, prestiti.note
                    FROM `prestiti` 
                    inner JOIN utenti on utenti.Id = prestiti.IdUtente 
                    INNER JOIN risorse on risorse.id = prestiti.IdRisorsa
                    WHERE prestiti.id = '{id_pre}'
""")
        prestito = cur.fetchone()
        db.close()
        return render_template("dettagli_prestito.html", prestito=prestito)
    return redirect(url_for("home"))

@app.route("/prestiti/modifica", methods=["GET", "POST"])
def modifica_prestiti ():
    if "admin" in session and session["admin"]:
        if request.method == "POST":
            id_pre = request.args.get("id_pre")
            id_ris = request.form["id_ris"]
            id_utente = request.form["id_utente"]
            data_inizio = request.form["data_inizio"]
            data_fine = request.form["data_fine"]
            stato = request.form["stato"]
            note = request.form["note"]

            db = get_db()
            cur = db.cursor()
            cur.execute(f"UPDATE prestiti SET IdRisorsa = {id_ris}, IdUtente = {id_utente}, Stato = '{stato}', Data_inizio = '{data_inizio}', Data_fine = '{data_fine}', note = '{note}' WHERE id = {id_pre}")
            db.commit()
            db.close()
            return redirect(url_for("prestiti"))
        else:
            id_pre = request.args.get("id_pre")
            db = get_db()
            cur = db.cursor()
            cur.execute(f"SELECT * FROM prestiti WHERE id = {id_pre}")
            prestito = cur.fetchone()

            cur.execute("SELECT id, nome FROM risorse")
            risorse = cur.fetchall()

            cur.execute("SELECT id, nome FROM utenti")
            utenti = cur.fetchall()

            db.close()
            return render_template("modifica_prestito.html", prestito=prestito, risorse=risorse, utenti=utenti)
    return redirect(url_for("home"))

@app.route("/prestiti/aggiungi", methods=["GET", "POST"])
def aggiungi_prestiti ():
    if "admin" in session and session["admin"]:
        if request.method == "POST":
            id_ris = request.form["id_ris"]
            id_utente = request.form["id_utente"]
            data_inizio = request.form["data_inizio"]
            data_fine = request.form["data_fine"]
            stato = request.form["stato"]
            note = request.form["note"]

            db = get_db()
            cur = db.cursor()
            cur.execute(f"INSERT INTO prestiti (IdRisorsa, IdUtente, Data_inizio, Data_fine, Stato, Note) VALUES ({id_ris}, {id_utente}, '{data_inizio}', '{data_fine}', '{stato}', '{note}')")
            db.commit()
            db.close()
            return redirect(url_for("prestiti"))
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id, nome FROM risorse")
            risorse = cur.fetchall()

            cur.execute("SELECT id, nome FROM utenti")
            utenti = cur.fetchall()
            db.close()
            return render_template("modifica_prestito.html", prestito=None, risorse=risorse, utenti=utenti)
    return redirect(url_for("home"))

@app.route("/prestiti/elimina")
def elimina_prestiti ():
    if "admin" in session and session["admin"]:
        id_pre = request.args.get("id_pre")
        db = get_db()
        cur = db.cursor()
        cur.execute(f"DELETE FROM prestiti WHERE id = {id_pre}")
        db.commit()
        db.close()
        return redirect(url_for("prestiti"))
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
