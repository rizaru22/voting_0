from flask import Flask, render_template,request,redirect,url_for   ,session
from flask_mysqldb import MySQL,MySQLdb
from secrets import token_hex
import bcrypt
import os
from werkzeug.utils import secure_filename
from uuid import uuid4

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = token_hex(16)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


mysql = MySQL(app)

def login_condition():
    if 'id_admin' not in session:
        return redirect(url_for('login'))
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if cek_koneksi() == False:
            return render_template('database_error.html')
                
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM admin WHERE username = %s ', [username])
        user_data= cursor.fetchone()
        cursor.close()
        
        if user_data:
            stored_password = user_data[2]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                session['id_admin'] = user_data[0]
                session['username'] = user_data[1]
                session['nama'] = user_data[3]
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid credentials')    
    
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    # if 'id_admin' not in session:
    #     return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pemilihan')
    pemilihan = cursor.fetchall()
    cursor.close()
    return render_template('pemilihan/index.html', data=pemilihan)

@app.route('/tambah_pemilihan', methods=['GET','POST'])

def tambah_pemilihan():
    # if 'id_admin' not in session:
    #     return redirect(url_for('login'))
    
    if request.method == 'POST':
        nama_pemilihan = request.form['nama_pemilihan']
        status = request.form['status']
        tanggal_mulai=request.form['tanggal_mulai']
        tanggal_selesai=request.form['tanggal_selesai']
        id_admin=session['id_admin']
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO pemilihan (nama_pemilihan,tanggal_mulai,tanggal_selesai, status,id_admin) VALUES (%s,%s,%s,%s, %s)', (nama_pemilihan,tanggal_mulai,tanggal_selesai, status,id_admin))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('pemilihan/create.html')

@app.route('/edit_pemilihan/<int:id>', methods=['GET','POST'])
def edit_daftar_pemilihan(id):
    # if 'id_admin' not in session:
    #     return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pemilihan WHERE id_pemilihan = %s', (id,))
    pemilihan = cursor.fetchone()
    
    if request.method == 'POST':
        nama_pemilihan = request.form['nama_pemilihan']
        tanggal_mulai=request.form['tanggal_mulai']
        tanggal_selesai=request.form['tanggal_selesai']
        status = request.form['status']
        id_admin=session['id_admin']
        
        cursor.execute('UPDATE pemilihan SET nama_pemilihan = %s,  tanggal_mulai=%s,tanggal_selesai=%s, status = %s, id_admin=%s WHERE id_pemilihan = %s', (nama_pemilihan,tanggal_mulai,tanggal_selesai, status,id_admin, id))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('dashboard'))
    
    cursor.close()
    return render_template('pemilihan/edit.html', data=pemilihan)

@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'POST':
        code = request.form['code']
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM verification_codes WHERE code = %s', (code,))
        verification = cursor.fetchone()
        cursor.close()
        
        if verification:
            session['verified'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('verify.html', error='Invalid verification code')
    
    return render_template('verify.html')

def cek_koneksi():
    try:
        mysql.connection.ping()
        return True
    except:
        return False

@app.route('/seeder')
def seeder():
    if cek_koneksi() == False:
        return "Database connection error"
    
    salt=bcrypt.gensalt()
    plain_password='admin123'
    dummy_password=bcrypt.hashpw(plain_password.encode('utf-8'),salt)
    dummy_username='admin'
    dummy_nama='Administrator'
    
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT IGNORE INTO admin (username, password,nama) VALUES (%s, %s,%s)", (dummy_username, dummy_password,dummy_nama))

        
    mysql.connection.commit()
    cursor.close()
    
    return "Database seeded successfully"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/kelas')
def kelas():
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM kelas')
    kelas= cursor.fetchall()
    cursor.close()
    return render_template('kelas/index.html', data=kelas)


@app.route('/tambah_kelas',methods=['GET','POST'])
def tambah_kelas():
    if request.method=='POST':
        kode_kelas=request.form['kode_kelas']
        
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO kelas (kode_kelas) VALUES (%s)',[kode_kelas])
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('kelas'))
    
    return render_template('kelas/create.html')

@app.route('/edit_kelas/<int:id>',methods=['GET','POST'])
def edit_kelas(id):
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM kelas WHERE id_kelas=%s',[id])
    kelas=cursor.fetchone()
    if request.method=='POST':
        kode_kelas=request.form['kode_kelas']
        cursor.execute('UPDATE kelas SET kode_kelas=%s WHERE id_kelas=%s',[kode_kelas,id])
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('kelas'))
    
    return render_template('kelas/edit.html',data=kelas)

@app.route('/voters')
def voters():
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM voters JOIN kelas ON voters.id_kelas = kelas.id_kelas ORDER BY kelas.kode_kelas ')
    voters= cursor.fetchall()
    cursor.close()
    return render_template('voters/index.html', data=voters)

@app.route('/tambah_voter',methods=['GET','POST'])
def tambah_voter():
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM kelas')
    kelas= cursor.fetchall()
    cursor.close()
    
    if request.method=='POST':
        nama=request.form['nama']
        id_kelas=request.form['kelas']
        
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO voters (nama, id_kelas) VALUES (%s,%s)', (nama, id_kelas))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('voters'))
    
    return render_template('voters/create.html', kelas=kelas)

@app.route('/edit_voter/<int:id>',methods=['GET','POST'])
def edit_voter(id):
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM kelas')
    kelas= cursor.fetchall()
    
    cursor.execute('SELECT * FROM voters WHERE id_voter=%s',[id])
    voter=cursor.fetchone()
    
    if request.method=='POST':
        nama=request.form['nama']
        id_kelas=request.form['kelas']
        
        cursor.execute('UPDATE voters SET nama=%s, id_kelas=%s WHERE id_voter=%s', (nama, id_kelas, id))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('voters'))
    
    return render_template('voters/edit.html',data=voter, kelas=kelas)

@app.route('/hapus_voter/<int:id>',methods=['POST'])
def hapus_voter(id):
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM voters WHERE id_voter=%s',[id])
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('voters'))


@app.route('/kandidat')
def kandidat(): 
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM candidates JOIN pemilihan ON candidates.id_pemilihan = pemilihan.id_pemilihan WHERE pemilihan.status="T" ')
    kandidat= cursor.fetchall()
    cursor.close()
    return render_template('kandidat/index.html', data=kandidat)



@app.route('/tambah_kandidat',methods=['GET','POST'])
def tambah_kandidat():
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pemilihan WHERE status="T" ')
    pemilihan= cursor.fetchall()
    cursor.close()
    
    if request.method=='POST':
        nama=request.form['nama']
        foto=request.files['foto']
        visi=request.form['visi']
        misi=request.form['misi']
        id_pemilihan=request.form['pemilihan']
        
        if foto and allowed_file(foto.filename):
            filename =f"{uuid4().hex}_{secure_filename(foto.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(filepath)
            

        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO candidates (nama, foto,visi,misi, id_pemilihan) VALUES (%s,%s,%s,%s,%s)', (nama, filename,visi,misi, id_pemilihan))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('kandidat'))
    
    return render_template('kandidat/create.html', pemilihan=pemilihan)

@app.route('/delete_kandidat/<int:id>',methods=['POST'])
def hapus_kandidat(id):
    if request.method=='POST':
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM candidates WHERE id_candidate=%s',[id])
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('kandidat'))
    
@app.route('/edit_kandidat/<int:id>',methods=['GET','POST'])
def edit_kandidat(id):
    cursor= mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pemilihan WHERE status="T" ')
    pemilihan= cursor.fetchall()
    
    cursor.execute('SELECT * FROM candidates WHERE id_candidate=%s',[id])
    kandidat=cursor.fetchone()
    
    if request.method=='POST':
        nama=request.form['nama']
        foto=request.files['foto']
        visi=request.form['visi']
        misi=request.form['misi']
        id_pemilihan=request.form['pemilihan']
        
        if foto and allowed_file(foto.filename):
            filename =f"{uuid4().hex}_{secure_filename(foto.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(filepath)
            cursor.execute('UPDATE candidates SET nama=%s, foto=%s, visi=%s, misi=%s, id_pemilihan=%s WHERE id_candidate=%s', (nama, filename,visi,misi, id_pemilihan, id))
        else:
            cursor.execute('UPDATE candidates SET nama=%s, visi=%s, misi=%s, id_pemilihan=%s WHERE id_candidate=%s', (nama,visi,misi, id_pemilihan, id))
            
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('kandidat'))
    
    return render_template('kandidat/edit.html',data=kandidat, pemilihan=pemilihan)

if __name__ == '__main__':
    app.run(debug=True)
