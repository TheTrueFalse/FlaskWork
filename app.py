import os
# 1. 'jsonify' foi adicionado aqui
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy import select, delete
from sqlalchemy import func
import time

app = Flask(__name__)

# --- Configuração da Base de Dados ---
DB_USER = "neondb_owner"
DB_PASSWORD = "npg_7qPbIwLmQ1Nf"
DB_HOST = "ep-young-field-a89tdevs-pooler.eastus2.azure.neon.tech"
DB_PORT = "5432"
DB_NAME = "neondb"

DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelos (Classes) ---

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True)
    nm_usuario = db.Column(db.String, nullable=False)
    cpf_usuario = db.Column(db.String, nullable=False)
    emprego_atual = db.Column(db.String)
    
    candidaturas = db.relationship('CandidatoVaga', back_populates='usuario')

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nm_usuario': self.nm_usuario,
            'cpf_usuario': self.cpf_usuario,
            'emprego_atual': self.emprego_atual
        }

class VagaEmprego(db.Model):
    __tablename__ = 'vaga_emprego'

    id_vaga = db.Column(db.Integer, primary_key=True)
    titulo_vaga = db.Column(db.String, nullable=False)
    empresa_vaga = db.Column(db.String, nullable=False)
    salario_vaga = db.Column(db.Integer, nullable=False)
    descricao_vaga = db.Column(db.String, nullable=False)
    candidaturas_vaga = db.Column(db.Integer) 

    candidatos = db.relationship('CandidatoVaga', back_populates='vaga')

    def to_dict(self):
        return {
            'id_vaga': self.id_vaga,
            'titulo_vaga': self.titulo_vaga,
            'empresa_vaga': self.empresa_vaga,
            'salario_vaga': self.salario_vaga,
            'descricao_vaga': self.descricao_vaga,
            'candidaturas_vaga': self.candidaturas_vaga
        }

class CandidatoVaga(db.Model):
    __tablename__ = 'candidato_vaga'

    cod_cand_vaga = db.Column(db.Integer, primary_key=True)
    id_vaga = db.Column(db.Integer, db.ForeignKey('vaga_emprego.id_vaga'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)

    vaga = db.relationship('VagaEmprego', back_populates='candidatos')
    usuario = db.relationship('Usuario', back_populates='candidaturas')

    def to_dict(self):
        return {
            'cod_cand_vaga': self.cod_cand_vaga,
            'id_vaga': self.id_vaga,
            'id_usuario': self.id_usuario
        }

# --- Rota Principal (HTML) ---

@app.route('/')
def index():
    try:
        vaga_id = request.args.get('vaga_id', type=int)
        
        search_query = request.args.get('search_query', '')

        query = select(VagaEmprego)

        if search_query:
            query = query.where(VagaEmprego.titulo_vaga.ilike(f'%{search_query}%'))

        query = query.order_by(VagaEmprego.id_vaga.desc())
        vagas_list = db.session.execute(query).scalars().all()
        
        vaga_selecionada = None
        if vaga_id:
            vaga_selecionada = db.session.get(VagaEmprego, vaga_id)

    except Exception as e:
        print(f"Erro ao procurar vagas na BD: {e}")
        vagas_list = []
        vaga_selecionada = None
        search_query = '' 

    # Alterne aqui para testar
    mock_user = {'user_type': 'admin', 'nome': 'Admin'} 
    #mock_user = {'user_type': 'user', 'nome': 'João'}

    return render_template(
        'index.html', 
        vagas=vagas_list, 
        vaga=vaga_selecionada, 
        user=mock_user, 
        search_query=search_query
    )


# --- ROTAS DE AÇÃO DO HTML ---

@app.route('/vaga/<int:id_vaga>/candidatar', methods=['POST'])
def candidatar_vaga(id_vaga):
    
    id_usuario_mock = 1 

    try:
        vaga = db.session.get(VagaEmprego, id_vaga)
        if not vaga:
            return "Vaga não encontrada", 404
        
        usuario = db.session.get(Usuario, id_usuario_mock)
        if not usuario:
            return "Utilizador mock (ID 1) não encontrado. Adicione-o à base de dados.", 404

        candidatura_existente = db.session.execute(
            select(CandidatoVaga).where(
                CandidatoVaga.id_vaga == id_vaga,
                CandidatoVaga.id_usuario == id_usuario_mock
            )
        ).first()
        
        if candidatura_existente:
            print("Utilizador já candidatado!")
            return redirect(url_for('index', vaga_id=id_vaga))

        nova_candidatura = CandidatoVaga(id_vaga=id_vaga, id_usuario=id_usuario_mock)
        db.session.add(nova_candidatura)
        db.session.commit()
        
        print(f"Utilizador {id_usuario_mock} candidatou-se à vaga {id_vaga}")

        return redirect(url_for('index', vaga_id=id_vaga))

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao candidatar: {e}")
        return "Erro ao processar candidatura", 500

@app.route('/vaga/<int:id_vaga>/deletar', methods=['POST'])
def deletar_vaga_form(id_vaga):
    try:
        vaga = db.session.get(VagaEmprego, id_vaga)
        if vaga is None:
            return "Vaga não encontrada", 404
            
        db.session.execute(delete(CandidatoVaga).where(CandidatoVaga.id_vaga == id_vaga))
            
        db.session.delete(vaga)
        db.session.commit()
        
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        return "Erro ao eliminar vaga", 500

@app.route('/vaga/<int:id_vaga>/editar', methods=['GET', 'POST'])
def editar_vaga(id_vaga):
    vaga = db.session.get(VagaEmprego, id_vaga)
    if not vaga:
        return "Vaga não encontrada", 404

    if request.method == 'POST':
        try:
            vaga.titulo_vaga = request.form['titulo_vaga']
            vaga.empresa_vaga = request.form['empresa_vaga']
            vaga.salario_vaga = int(request.form['salario_vaga'])
            vaga.descricao_vaga = request.form['descricao_vaga']
            
            db.session.commit()
            
            return redirect(url_for('index', vaga_id=id_vaga))
        except Exception as e:
            db.session.rollback()
            return "Erro ao guardar edição", 500
    
    return render_template('editar_vaga.html', vaga=vaga)

# ROTA DE API PARA CRIAR (POST) E LER (GET) VAGAS
@app.route("/VagaEmprego", methods=["GET", "POST"])
def vaga_api():
    
    # Se for POST, o código para CRIAR uma vaga
    if request.method == 'POST':
        try:
            data = request.json 
            
            if not data or 'titulo_vaga' not in data or 'descricao_vaga' not in data or 'empresa_vaga' not in data or 'salario_vaga' not in data:
                return jsonify({"error": "Dados inválidos: titulo, descricao, empresa e salario são obrigatórios."}), 400

            nova_vaga = VagaEmprego(
                titulo_vaga=data['titulo_vaga'],
                empresa_vaga=data['empresa_vaga'],
                salario_vaga=data['salario_vaga'],
                descricao_vaga=data['descricao_vaga'],
                candidaturas_vaga=data.get('candidaturas_vaga', 0)
            )
            
            db.session.add(nova_vaga)
            db.session.commit()
            
            return jsonify(nova_vaga.to_dict()), 201 
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Erro ao criar vaga: {str(e)}"}), 500
    
    if request.method == 'GET':
        try:
            vagas_list = db.session.execute(select(VagaEmprego).order_by(VagaEmprego.id_vaga.desc())).scalars().all()
            return jsonify([vaga.to_dict() for vaga in vagas_list])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/VagaEmprego/<int:id_vaga>", methods=["GET", "PUT", "DELETE"])
    def vaga_api_detalhe(id_vaga):
        
        vaga = db.session.get(VagaEmprego, id_vaga)
        
        if not vaga:
            return jsonify({"error": "Vaga não encontrada"}), 404

        if request.method == 'GET':
            return jsonify(vaga.to_dict())

        if request.method == 'PUT':
            try:
                data = request.json
                
                vaga.titulo_vaga = data.get('titulo_vaga', vaga.titulo_vaga)
                vaga.empresa_vaga = data.get('empresa_vaga', vaga.empresa_vaga)
                vaga.salario_vaga = data.get('salario_vaga', vaga.salario_vaga)
                vaga.descricao_vaga = data.get('descricao_vaga', vaga.descricao_vaga)

                db.session.commit()
                return jsonify(vaga.to_dict()), 200 # 200 OK
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Erro ao atualizar vaga: {str(e)}"}), 500

        if request.method == 'DELETE':
            try:
                db.session.execute(delete(CandidatoVaga).where(CandidatoVaga.id_vaga == id_vaga))
                
                db.session.delete(vaga)
                db.session.commit()
                return jsonify({"message": "Vaga deletada com sucesso"}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Erro ao deletar vaga: {str(e)}"}), 500

# --- Bloco de Execução ---

if __name__ == '__main__':
    with app.app_context():
         # db.create_all() # Descomente se precisar de criar as tabelas pela primeira vez
         print("Contexto da aplicação carregado.")
         
    app.run(debug=True, port=5153)