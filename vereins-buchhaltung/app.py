from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import csv
import io

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('buchhaltung.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaktionen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT,
            zweck TEXT,
            kategorie TEXT,
            betrag REAL,
            typ TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('buchhaltung.db')
    cursor = conn.cursor()
    
    # Alle Buchungen laden
    cursor.execute('SELECT * FROM transaktionen ORDER BY datum DESC')
    transaktionen = cursor.fetchall()
    
    # Gesamteinnahmen berechnen
    cursor.execute("SELECT SUM(betrag) FROM transaktionen WHERE typ = 'Einnahme'")
    gesamteinnahmen = cursor.fetchone()[0] or 0.0
    
    # Gesamtausgaben berechnen
    cursor.execute("SELECT SUM(betrag) FROM transaktionen WHERE typ = 'Ausgabe'")
    gesamtausgaben = cursor.fetchone()[0] or 0.0
    
    # Saldo (Gewinn/Verlust)
    saldo = gesamteinnahmen - gesamtausgaben
    
    conn.close()
    
    return render_template('index.html', 
                           transaktionen=transaktionen, 
                           gesamteinnahmen=gesamteinnahmen, 
                           gesamtausgaben=gesamtausgaben, 
                           saldo=saldo)

@app.route('/add', methods=['POST'])
def add():
    datum = request.form['datum']
    zweck = request.form['zweck']
    kategorie = request.form['kategorie']
    betrag = float(request.form['betrag'])
    typ = request.form['typ']

    conn = sqlite3.connect('buchhaltung.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO transaktionen (datum, zweck, kategorie, betrag, typ) VALUES (?, ?, ?, ?, ?)',
                   (datum, zweck, kategorie, betrag, typ))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/clear', methods=['POST'])
def clear():
    conn = sqlite3.connect('buchhaltung.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transaktionen')
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/export')
def export():
    conn = sqlite3.connect('buchhaltung.db')
    cursor = conn.cursor()
    cursor.execute('SELECT datum, zweck, kategorie, typ, betrag FROM transaktionen')
    rows = cursor.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['Datum', 'Zweck', 'Kategorie', 'Typ', 'Betrag'])
    cw.writerows(rows)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=steuerberater_rohdaten.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)