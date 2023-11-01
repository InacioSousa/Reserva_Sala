from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
import pymysql
from datetime import datetime

app = Flask(__name__)
app.secret_key = '1234567890'

# Configure a conexão com o banco de dados MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:q1w2e3r4@localhost/db_sala'
db = SQLAlchemy(app)

# Defina a classe User para mapear a tabela de usuários no MySQL
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    nome = db.Column(db.String(80), nullable=True)
    sobrenome = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), nullable=True)

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    horario = db.Column(db.Time, nullable=False)
    sala_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # Adicione outros campos conforme necessário

# Configure a rota estática para servir arquivos CSS da pasta "static"
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Rota padrão para a página inicial
@app.route('/')
def home():
    if 'user_id' in session:
        return 'Você está logado'
    return 'Você não está logado. <a href="/login">Faça login</a>'

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id  # Salvar o ID do usuário na sessão
            return redirect(url_for('reserva_sala'))  # Redireciona para a página de reserva após o login bem-sucedido
        else:
            flash('Credenciais incorretas', 'error')  # Mensagem de erro em caso de credenciais incorretas
    return render_template('login.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Rota para cadastro
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nome = request.form['nome']
        sobrenome = request.form['sobrenome']
        email = request.form['email']

        new_user = User(username=username, password=password, nome=nome, sobrenome=sobrenome, email=email)
        db.session.add(new_user)
        db.session.commit()
        return 'Cadastro realizado com sucesso. <a href="/login">Faça login</a>'
    return render_template('cadastrar.html')

# Rota para reserva de sala
@app.route('/reserva', methods=['GET', 'POST'])
def reserva_sala():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redireciona para o login se o usuário não estiver autenticado

    if request.method == 'POST':
        data = request.form['data']
        horario = request.form['horario']
        sala_id = request.form['sala_id']

        # Verifique se a sala está disponível na data e horário especificados
        if not sala_esta_disponivel(data, horario, sala_id):
            flash('Erro: A sala já está reservada para este horário.', 'error')
        else:
            # Crie uma nova reserva associada ao usuário atual
            nova_reserva = Reserva(data=data, horario=horario, sala_id=sala_id, user_id=session['user_id'])

            # Adicione a reserva ao banco de dados
            db.session.add(nova_reserva)
            db.session.commit()
            flash('Reserva realizada com sucesso.', 'success')

    # Renderize o formulário de reserva
    return render_template('reserva.html')

# Função para verificar a disponibilidade da sala
def sala_esta_disponivel(data, horario, sala_id):
    data_hora = datetime.strptime(f'{data} {horario}', '%Y-%m-%d %H:%M')
    reserva_existente = Reserva.query.filter_by(
        data=data_hora.date(),
        horario=data_hora.time(),
        sala_id=sala_id
    ).first()
    return reserva_existente is None

if __name__ == '__main__':
    app.run(debug=True)
