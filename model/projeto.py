from datetime import datetime

from model import db


class Projeto(db.Model):
    """Projeto de investimento industrial (capex) mapeado no Brasil."""

    __tablename__ = "projeto"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), unique=True, nullable=False)
    empresa = db.Column(db.String(120), nullable=False)
    setor = db.Column(db.String(60), nullable=False)
    cidade = db.Column(db.String(80), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    investimento_mi = db.Column(db.Float, nullable=True)  # R$ milhões
    fonte = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "empresa": self.empresa,
            "setor": self.setor,
            "cidade": self.cidade,
            "uf": self.uf,
            "status": self.status,
            "investimento_mi": self.investimento_mi,
            "fonte": self.fonte,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
