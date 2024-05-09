from flask import Flask, redirect, url_for, render_template, request, session
from flask_mysqldb import MySQL
import hashlib

app = Flask(__name__)
app.secret_key = "mysecretkey"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'risorse_multimediali'
mysql = MySQL(app)

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

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO utenti (nome, cognome, telefono, email, città, indirizzo, password) VALUES (%s, %s, %s, %s, %s, %s, %s)", (nome, cognome, telefono, email, citta, indirizzo, password))
        mysql.connection.commit()

        cur.close()
        return "success"
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

        cur = mysql.connection.cursor()
        cur.execute(f"SELECT email, password, admin FROM utenti WHERE email = '{mail}'")
        user = cur.fetchone()
        cur.close()

        if user and user[1] == password:
            session["idusr"] = user[0]
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
       cur = mysql.connection.cursor()
       cur.execute(f"""
            SELECT nome, cognome, telefono, email, città, indirizzo, admin
            FROM utenti WHERE email = '{session['email']}'
""")
       user = cur.fetchone()
       cur.close()
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
    cur = mysql.connection.cursor()
    catalogo = cur.execute("SELECT id, nome FROM risorse WHERE stato = 'Disponibile'")
    dati = cur.fetchall()
    cur.close()

    if not catalogo > 0:
        return redirect(url_for("home"))
    return render_template("catalogo.html", dati=dati, loggedIn=("email" in session))

@app.route("/catalogo/dettagli", methods=["GET", "POST"])
def dettagli_catalogo ():
    if request.method == "POST":
        id_ris = request.args.get("idusr")
        data_inizio = request.form["data_inizio"]
        
        cur = mysql.connection.cursor()
        cur.execute(f"""
            INSERT INTO prestiti (IdRisorsa, IdUtente, Data_inizio, stato) VALUES ('{id_ris}', '{session["idusr"]}', '{data_inizio}', 'Prenotato') 
        """)
        mysql.connection.commit()
        cur.execute(f"UPDATE risorse SET Stato = 'In prestito' WHERE Id = '{id_ris}'")
        return redirect(url_for("home"))
    else:
        id_ris = request.args.get("id")
        cur = mysql.connection.cursor()
        cur.execute(f"""
                SELECT risorse.Id, risorse.nome, categorie.nome, risorse.Stato, risorse.Descrizione 
                FROM risorse 
                INNER JOIN categorie ON categorie.Id = risorse.IdCategoria
                WHERE risorse.id = '{id_ris}'
        """)
        dettagli = cur.fetchone()
        cur.close()
        return render_template("dettagli_catalogo.html", dettagli=dettagli)

@app.route("/categorie")
def categorie ():
    if "admin" in session and "admin" in session and session["admin"]:
        cur = mysql.connection.cursor()
        q_cat = cur.execute("SELECT * FROM categorie")
        dettagli_categorie = cur.fetchall()
        cur.close()
        if not q_cat > 0:
            return render_template("categorie.html", categorie=dettagli_categorie)
    
        return render_template("categorie.html", categorie=dettagli_categorie)
    return redirect(url_for("home"))

@app.route("/categorie/dettagli")
def dettagli_categorie ():
    if "admin" in session and session["admin"]:
        id_cat = request.args.get("id_cat")
        cur = mysql.connection.cursor()
        cur.execute(f"SELECT * FROM categorie WHERE id = {id_cat}")
        cat = cur.fetchone()
        cur.close()
        return render_template("dettagli_categoria.html", categoria=cat)
    return redirect(url_for("home"))

@app.route("/categorie/modifica", methods=["GET", "POST"])
def modifica_categorie ():
    if "admin" in session and session["admin"]:
        cur = mysql.connection.cursor()
        if request.method == "POST":
            id_cat = request.args.get("id_cat")
            nome_cat = request.form["nome_cat"]
            descrizione = request.form["descrizione"]
            cur.execute(f"UPDATE categorie SET nome = '{nome_cat}', descrizione = '{descrizione}' WHERE id = {id_cat}")
            mysql.connection.commit()
            cur.close()
            return redirect(url_for("categorie"))
        else:
            id_cat = request.args.get("id_cat")
            cur.execute(f"SELECT * FROM categorie WHERE id = {id_cat}")
            cat = cur.fetchone()
            cur.close()
            return render_template("modifica_categoria.html", categoria=cat)
    return redirect(url_for("home"))

@app.route("/categorie/elimina")
def elimina_categorie ():
    if "admin" in session and session["admin"]:
        id_cat = request.args.get("id_cat")
        cur = mysql.connection.cursor()
        cur.execute(f"DELETE FROM categorie WHERE id = {id_cat}")
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("categorie"))
    return redirect(url_for("home"))

@app.route("/categorie/aggiungi", methods=["GET", "POST"])
def aggiungi_categorie ():
    if "admin" in session and session["admin"]:
        if request.method == "POST":
            nome_cat = request.form["nome_cat"]
            descrizione = request.form["descrizione"]
            cur = mysql.connection.cursor()
            cur.execute(f"INSERT INTO categorie (nome, descrizione) VALUES ('{nome_cat}', '{descrizione}')")
            mysql.connection.commit()
            cur.close()
            return redirect(url_for("categorie"))
        else:
            return render_template("modifica_categoria.html", categoria=None)
    return redirect(url_for("home"))

@app.route("/risorse")
def risorse ():
    if "admin" in session and session["admin"]:
        cur = mysql.connection.cursor()
        q_risorse = cur.execute("SELECT id, nome, stato FROM risorse")
        print(q_risorse)
        if not q_risorse > 0:
            return render_template("risorse.html", risorse=None)
            
        dettagli_risorse = cur.fetchall()
        cur.close()

        return render_template("risorse.html", risorse=dettagli_risorse)
    return redirect(url_for("home"))

@app.route("/risorse/dettagli")
def dettagli_risorse ():
    if "admin" in session and session["admin"]:
        id_ris = request.args.get("id_ris")
        cur = mysql.connection.cursor()
        cur.execute(f"""
                    SELECT risorse.Id, risorse.nome, categorie.Nome, risorse.Stato, risorse.descrizione 
                    FROM `risorse`
                    INNER JOIN categorie
                    ON categorie.Id = risorse.IdCategoria 
                    WHERE risorse.id = '{id_ris}'
""")
        ris = cur.fetchone()
        cur.close()
        return render_template("dettagli_risorsa.html", risorsa=ris)
    return redirect(url_for("home"))

@app.route("/risorse/modifica", methods=["GET", "POST"])
def modifica_risorse ():
    if "admin" in session and session["admin"]:
        cur = mysql.connection.cursor()
        if request.method == "POST":
            id_ris = request.args.get("id_ris")
            nome_ris = request.form["nome_ris"]
            categoria = request.form["lista_cat"]
            stato = request.form["lista_stati"]
            descrizione = request.form["descrizione"]
            cur.execute(f"UPDATE risorse SET nome = '{nome_ris}', IdCategoria = {categoria}, Stato = '{stato}', descrizione = '{descrizione}' WHERE id = {id_ris}")
            mysql.connection.commit()
            cur.close()
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
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT * FROM categorie")
            categorie = cur2.fetchall()
            cur2.close()
            return render_template("modifica_risorsa.html", risorsa=ris, categorie=categorie)
    return redirect(url_for("home"))

@app.route("/risorse/elimina")
def elimina_risorse ():
    if "admin" in session and session["admin"]:
        id_ris = request.args.get("id_ris")
        cur = mysql.connection.cursor()
        cur.execute(f"DELETE FROM risorse WHERE id = {id_ris}")
        mysql.connection.commit()
        cur.close()
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
            cur = mysql.connection.cursor()
            cur.execute(f"INSERT INTO risorse (nome, IdCategoria, Stato, descrizione) VALUES ('{nome_ris}', {categoria}, '{stato}', '{descrizione}')")
            mysql.connection.commit()
            cur.close()
            return redirect(url_for("risorse"))
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, nome FROM categorie")
            categorie = cur.fetchall()
            cur.close()
            return render_template("modifica_risorsa.html", risorsa=None, categorie=categorie)
    return redirect(url_for("home"))

@app.route("/prestiti")
def prestiti ():
    if "admin" in session and session["admin"]:
        cur = mysql.connection.cursor()
        q_risorse = cur.execute("""
                            SELECT prestiti.Id, risorse.Nome, utenti.Nome, prestiti.Stato, prestiti.Data_inizio, prestiti.Data_fine
                            FROM `prestiti` 
                            inner JOIN utenti on utenti.Id = prestiti.IdUtente 
                            INNER JOIN risorse on risorse.id = prestiti.IdRisorsa
""")
        if not q_risorse > 0:
            return render_template("prestiti.html", prestiti=None)
            
        prestiti = cur.fetchall()
        cur.close()
        return render_template("prestiti.html", prestiti=prestiti)
    return redirect(url_for("home"))

@app.route("/prestiti/dettagli")
def dettagli_prestiti ():
    if "admin" in session and session["admin"]:
        id_pre = request.args.get("id_pre")
        cur = mysql.connection.cursor()
        cur.execute(f"""
                    SELECT prestiti.Id, risorse.Nome, utenti.Nome, prestiti.Stato, prestiti.Data_inizio, prestiti.Data_fine, prestiti.note
                    FROM `prestiti` 
                    inner JOIN utenti on utenti.Id = prestiti.IdUtente 
                    INNER JOIN risorse on risorse.id = prestiti.IdRisorsa
                    WHERE prestiti.id = '{id_pre}'
""")
        prestito = cur.fetchone()
        cur.close()
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
            cur = mysql.connection.cursor()
            cur.execute(f"UPDATE prestiti SET IdRisorsa = {id_ris}, IdUtente = {id_utente}, Stato = '{stato}', Data_inizio = '{data_inizio}', Data_fine = '{data_fine}', note = '{note}' WHERE id = {id_pre}")
            mysql.connection.commit()
            cur.close()
            return redirect(url_for("prestiti"))
        else:
            id_pre = request.args.get("id_pre")
            cur = mysql.connection.cursor()
            cur.execute(f"SELECT * FROM prestiti WHERE id = {id_pre}")
            prestito = cur.fetchone()
            cur.close()
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT id, nome FROM risorse")
            risorse = cur2.fetchall()
            cur2.close()
            cur3 = mysql.connection.cursor()
            cur3.execute("SELECT id, nome FROM utenti")
            utenti = cur3.fetchall()
            cur3.close()
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
            cur = mysql.connection.cursor()
            cur.execute(f"INSERT INTO prestiti (IdRisorsa, IdUtente, Data_inizio, Data_fine, Stato, Note) VALUES ({id_ris}, {id_utente}, '{data_inizio}', '{data_fine}', '{stato}', '{note}')")
            mysql.connection.commit()
            cur.close()
            return redirect(url_for("prestiti"))
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, nome FROM risorse")
            risorse = cur.fetchall()
            cur.close()
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT id, nome FROM utenti")
            utenti = cur2.fetchall()
            cur2.close()
            return render_template("modifica_prestito.html", prestito=None, risorse=risorse, utenti=utenti)
    return redirect(url_for("home"))

@app.route("/prestiti/elimina")
def elimina_prestiti ():
    if "admin" in session and session["admin"]:
        id_pre = request.args.get("id_pre")
        cur = mysql.connection.cursor()
        cur.execute(f"DELETE FROM prestiti WHERE id = {id_pre}")
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("prestiti"))
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
