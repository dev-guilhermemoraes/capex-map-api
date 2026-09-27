"""API principal do Mapa de Capex Industrial (MVP Sprint 02).

Responsável pelo CRUD dos projetos, agregações para o painel e pela
integração com o serviço externo de geocoding (Nominatim/OpenStreetMap).
Documentação Swagger em /openapi/swagger.
"""
import json
import logging
import os
from collections import Counter, defaultdict

from flask import redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag
from sqlalchemy.exc import IntegrityError

from model import Projeto, db
from schemas import (
    ListaProjetosSchema, MensagemSchema, ProjetoBody, ProjetoPath,
    ProjetoQuery, ProjetoSchema, ProjetoUpdateBody, ResumoSchema,
)
from services.geocoding import geocodificar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("capex-api")

info = Info(title="Capex Map API", version="1.0.0",
            description="CRUD de projetos de investimento industrial no Brasil")
app = OpenAPI(__name__, info=info)
CORS(app)

DB_DIR = os.getenv("DB_DIR", os.path.join(os.path.dirname(__file__), "database"))
os.makedirs(DB_DIR, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(DB_DIR, 'capex.sqlite3')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

tag_doc = Tag(name="Documentação", description="Swagger da API")
tag_proj = Tag(name="Projeto", description="Cadastro, consulta, edição e remoção de projetos")
tag_resumo = Tag(name="Resumo", description="Indicadores agregados para o painel")


def carregar_seed():
    """Popula o banco com o dataset curado offline, se estiver vazio."""
    if Projeto.query.count() > 0:
        return
    caminho = os.path.join(os.path.dirname(__file__), "data", "seed.json")
    with open(caminho, encoding="utf-8") as f:
        for item in json.load(f):
            db.session.add(Projeto(**item))
    db.session.commit()
    logger.info("Seed carregado com %d projetos", Projeto.query.count())


with app.app_context():
    db.create_all()
    carregar_seed()


def erro(msg: str, codigo: int):
    return {"mensagem": msg}, codigo


@app.get("/", tags=[tag_doc])
def home():
    """Redireciona para a documentação Swagger."""
    return redirect("/openapi/swagger")


@app.get("/projetos", tags=[tag_proj], responses={200: ListaProjetosSchema})
def listar_projetos(query: ProjetoQuery):
    """Lista os projetos, com filtros opcionais por UF, setor e status."""
    q = Projeto.query
    if query.uf:
        q = q.filter(Projeto.uf == query.uf.upper())
    if query.setor:
        q = q.filter(Projeto.setor == query.setor)
    if query.status:
        q = q.filter(Projeto.status == query.status)
    projetos = [p.to_dict() for p in q.order_by(Projeto.nome).all()]
    return {"total": len(projetos), "projetos": projetos}, 200


@app.get("/projetos/<int:projeto_id>", tags=[tag_proj],
         responses={200: ProjetoSchema, 404: MensagemSchema})
def buscar_projeto(path: ProjetoPath):
    """Retorna um projeto pelo ID."""
    projeto = db.session.get(Projeto, path.projeto_id)
    if not projeto:
        return erro("Projeto não encontrado", 404)
    return projeto.to_dict(), 200


@app.post("/projetos", tags=[tag_proj],
          responses={201: ProjetoSchema, 409: MensagemSchema, 422: MensagemSchema})
def criar_projeto(body: ProjetoBody):
    """Cadastra um projeto. Sem coordenadas, geocodifica cidade/UF via Nominatim."""
    dados = body.model_dump()
    dados["uf"] = dados["uf"].upper()

    if dados["latitude"] is None or dados["longitude"] is None:
        coords = geocodificar(dados["cidade"], dados["uf"])
        if coords is None:
            return erro("Não foi possível localizar a cidade informada. "
                        "Confira o nome/UF ou informe latitude e longitude.", 422)
        dados["latitude"], dados["longitude"] = coords

    projeto = Projeto(**dados)
    try:
        db.session.add(projeto)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return erro("Já existe um projeto com esse nome", 409)
    logger.info("Projeto criado: %s (%s/%s)", projeto.nome, projeto.cidade, projeto.uf)
    return projeto.to_dict(), 201


@app.put("/projetos/<int:projeto_id>", tags=[tag_proj],
         responses={200: ProjetoSchema, 404: MensagemSchema, 409: MensagemSchema, 422: MensagemSchema})
def atualizar_projeto(path: ProjetoPath, body: ProjetoUpdateBody):
    """Atualiza os campos enviados. Se cidade/UF mudarem sem novas coordenadas, geocodifica de novo."""
    projeto = db.session.get(Projeto, path.projeto_id)
    if not projeto:
        return erro("Projeto não encontrado", 404)

    mudancas = body.model_dump(exclude_unset=True)
    if "uf" in mudancas and mudancas["uf"]:
        mudancas["uf"] = mudancas["uf"].upper()

    local_mudou = any(k in mudancas and mudancas[k] != getattr(projeto, k) for k in ("cidade", "uf"))
    coords_enviadas = "latitude" in mudancas and "longitude" in mudancas
    for campo, valor in mudancas.items():
        setattr(projeto, campo, valor)

    if local_mudou and not coords_enviadas:
        coords = geocodificar(projeto.cidade, projeto.uf)
        if coords is None:
            db.session.rollback()
            return erro("Não foi possível localizar a nova cidade informada.", 422)
        projeto.latitude, projeto.longitude = coords

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return erro("Já existe um projeto com esse nome", 409)
    return projeto.to_dict(), 200


@app.delete("/projetos/<int:projeto_id>", tags=[tag_proj],
            responses={200: MensagemSchema, 404: MensagemSchema})
def remover_projeto(path: ProjetoPath):
    """Remove um projeto pelo ID."""
    projeto = db.session.get(Projeto, path.projeto_id)
    if not projeto:
        return erro("Projeto não encontrado", 404)
    db.session.delete(projeto)
    db.session.commit()
    return {"mensagem": f"Projeto '{projeto.nome}' removido"}, 200


@app.get("/resumo", tags=[tag_resumo], responses={200: ResumoSchema})
def resumo():
    """Totais de projetos e investimento por UF, setor e status."""
    projetos = Projeto.query.all()
    invest_uf = defaultdict(float)
    for p in projetos:
        invest_uf[p.uf] += p.investimento_mi or 0
    return {
        "total_projetos": len(projetos),
        "investimento_total_mi": sum(p.investimento_mi or 0 for p in projetos),
        "por_uf": {uf: {"projetos": n, "investimento_mi": invest_uf[uf]}
                   for uf, n in Counter(p.uf for p in projetos).items()},
        "por_setor": dict(Counter(p.setor for p in projetos)),
        "por_status": dict(Counter(p.status for p in projetos)),
    }, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
