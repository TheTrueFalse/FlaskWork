import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

DB_USER = "neondb_owner"
DB_PASSWORD = "npg_7qPbIwLmQ1Nf"
DB_HOST = "ep-young-field-a89tdevs-pooler.eastus2.azure.neon.tech"
DB_PORT = "5432"
DB_NAME = "neondb"

DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)

#Rotas da API ------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/VagaEmprego", methods=["POST"])
def criarVaga():
    return

@app.route("/VagaEmprego", methods=["GET"])
def buscaVaga():
    return

@app.route("/VagaEmprego/<string:nm_vaga>", methods=["GET"])
def buscaVaga(nm_vaga):
    return

@app.route("/VagaEmprego/<int:id_vaga>", methods=["PUT"])
def atualizaVaga(id_vaga):
    return

@app.route("/VagaEmprego/<int:id_vaga>", methods=["DELETE"])
def delete_task(id_vaga):
    return

if __name__ == '__main__':
    app.run(debug=True, port=5153)
