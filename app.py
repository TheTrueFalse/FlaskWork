import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy import select
from sqlalchemy import func
import time

app = Flask(__name__)

DB_USER = "neondb_owner"
DB_PASSWORD = "npg_7qPbIwLmQ1Nf"
DB_HOST = "ep-young-field-a89tdevs-pooler.eastus2.azure.neon.tech"
DB_PORT = "5432"
DB_NAME = "neondb"

DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class VagaEmprego(db.Model):
    __tablename__ = 'vaga_emprego'

    id_vaga = db.Column(db.Integer, primary_key=True)
    nm_vaga = db.Column(db.String(100), nullable=False)
    ds_vaga = db.Column(db.Text, nullable=False)
    localidade = db.Column(db.String(50), default='Remoto')

    def to_dict(self):
        return {
            'id_vaga': self.id_vaga,
            'nm_vaga': self.nm_vaga,
            'ds_vaga': self.ds_vaga,
            'localidade': self.localidade
        }

#essa parada aq é a clasee para a tabela que vai guardar as inscrições 
class InscricaoVaga(db.Model):
    __tablename__ = 'inscricao_vaga'  # usei um pouco da muleta aq 

    id_inscricao = db.Column(db.Integer, primary_key=True)
    id_vaga = db.Column(db.Integer, db.ForeignKey('vaga_emprego.id_vaga'), nullable=False)

    # Exemplo de outro campo qualquer, ajusta conforme o schema real(chat deu suporte)
    nm_pessoa = db.Column(db.String(100), nullable=False)

    vaga = db.relationship('VagaEmprego', backref='inscricoes')

    def to_dict(self):
        return {
            'id_inscricao': self.id_inscricao,
            'id_vaga': self.id_vaga,
            'nm_pessoa': self.nm_pessoa
        }

@app.route('/')
def index():
    try:
        vagas_list = db.session.execute(select(VagaEmprego).order_by(VagaEmprego.id_vaga.desc())).scalars().all()
    except Exception as e:
        print(f"Erro ao buscar vagas do DB: {e}")
        vagas_list = [] 

    mock_user = {'user_type': 'admin', 'name': 'Admin'} 
    #mock_user = {'user_type': 'user', 'name': 'João'}

    return render_template('index.html', vagas=vagas_list, user=mock_user)


@app.route("/VagaEmprego", methods=["POST"])
def criarVaga():
    try:
        data = request.json
        if not data or 'nm_vaga' not in data or 'ds_vaga' not in data:
            return jsonify({"error": "Dados inválidos: nome e descrição da vaga são obrigatórios."}), 400

        nova_vaga = VagaEmprego(
            nm_vaga=data['nm_vaga'],
            ds_vaga=data['ds_vaga'],
            localidade=data.get('localidade', 'Remoto')
        )
        
        db.session.add(nova_vaga)
        db.session.commit()
        
        return jsonify(nova_vaga.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao criar vaga: {str(e)}"}), 500


@app.route("/VagaEmprego", methods=["GET"])
def buscaTodasVagas():
    try:
        vagas_list = db.session.execute(select(VagaEmprego).order_by(VagaEmprego.id_vaga.desc())).scalars().all()
        return jsonify([vaga.to_dict() for vaga in vagas_list])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/VagaEmprego/<int:id_vaga>", methods=["PUT"])
def atualizaVaga(id_vaga):
    try:
        vaga = db.session.get(VagaEmprego, id_vaga)
        
        if vaga is None:
            return jsonify({"error": f"Vaga com ID {id_vaga} não encontrada."}), 404
            
        data = request.json
        
        if 'nm_vaga' in data:
            vaga.nm_vaga = data['nm_vaga']
        if 'ds_vaga' in data:
            vaga.ds_vaga = data['ds_vaga']
        if 'localidade' in data:
            vaga.localidade = data['localidade']
            
        db.session.commit()
        return jsonify(vaga.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao atualizar vaga: {str(e)}"}), 500


@app.route("/VagaEmprego/<int:id_vaga>", methods=["DELETE"])
def delete_task(id_vaga):
    try:
        vaga = db.session.get(VagaEmprego, id_vaga)

        if vaga is None:
            return jsonify({"error": f"Vaga com ID {id_vaga} não encontrada."}), 404
            
        db.session.delete(vaga)
        db.session.commit()
        
        return jsonify({"message": f"Vaga com ID {id_vaga} deletada com sucesso."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao deletar vaga: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5153)

#viado essa aq ela é apra as pessoas estão inscritas em uma vaga específica
@app.route("/VagaEmprego/<int:id_vaga>/inscritos", methods=["GET"])
def contar_inscritos_vaga(id_vaga):
    try:
        vaga = db.session.get(VagaEmprego, id_vaga)
        if vaga is None:
            return jsonify({"error": f"Vaga com ID {id_vaga} não encontrada."}), 404

        total_inscritos = db.session.execute(
            select(func.count(InscricaoVaga.id_inscricao)).where(InscricaoVaga.id_vaga == id_vaga)
        ).scalar_one()

        return jsonify({
            "id_vaga": id_vaga,
            "nm_vaga": vaga.nm_vaga,
            "total_inscritos": total_inscritos
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar inscritos da vaga: {str(e)}"}), 500


# rota para listar todas as vagas com a contagem de inscritos
@app.route("/VagaEmprego/inscritos", methods=["GET"])
def listar_vagas_com_inscritos():
    try:
        resultado = db.session.execute(
            select(
                VagaEmprego.id_vaga,
                VagaEmprego.nm_vaga,
                VagaEmprego.localidade,
                func.count(InscricaoVaga.id_inscricao).label("total_inscritos")
            ).join(
                InscricaoVaga,
                VagaEmprego.id_vaga == InscricaoVaga.id_vaga,
                isouter=True
            ).group_by(
                VagaEmprego.id_vaga,
                VagaEmprego.nm_vaga,
                VagaEmprego.localidade
            ).order_by(
                VagaEmprego.id_vaga.desc()
            )
        ).all()

        response = []
        for row in resultado:
            response.append({
                "id_vaga": row.id_vaga,
                "nm_vaga": row.nm_vaga,
                "localidade": row.localidade,
                "total_inscritos": row.total_inscritos
            })

        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar vagas com inscritos: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5153)