from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["Anunciado", "Licenciamento", "Em obras", "Em operação", "Suspenso"]


class ProjetoBody(BaseModel):
    """Dados para cadastrar um projeto. Latitude/longitude são opcionais:
    se omitidas, a API consulta o serviço de geocoding (Nominatim/OSM)."""

    nome: str = Field(..., min_length=3, max_length=160, examples=["Nova fábrica de celulose"])
    empresa: str = Field(..., min_length=2, max_length=120, examples=["Suzano"])
    setor: str = Field(..., min_length=2, max_length=60, examples=["Papel e celulose"])
    cidade: str = Field(..., min_length=2, max_length=80, examples=["Ribas do Rio Pardo"])
    uf: str = Field(..., min_length=2, max_length=2, examples=["MS"])
    status: Status = Field("Anunciado")
    investimento_mi: Optional[float] = Field(None, ge=0, description="Investimento em R$ milhões")
    fonte: Optional[str] = Field(None, max_length=300, description="URL da notícia/fonte")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class ProjetoUpdateBody(BaseModel):
    """Campos que podem ser alterados (todos opcionais)."""

    nome: Optional[str] = Field(None, min_length=3, max_length=160)
    empresa: Optional[str] = Field(None, min_length=2, max_length=120)
    setor: Optional[str] = Field(None, min_length=2, max_length=60)
    cidade: Optional[str] = Field(None, min_length=2, max_length=80)
    uf: Optional[str] = Field(None, min_length=2, max_length=2)
    status: Optional[Status] = None
    investimento_mi: Optional[float] = Field(None, ge=0)
    fonte: Optional[str] = Field(None, max_length=300)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class ProjetoPath(BaseModel):
    projeto_id: int = Field(..., description="ID do projeto")


class ProjetoQuery(BaseModel):
    """Filtros opcionais para a listagem."""

    uf: Optional[str] = Field(None, max_length=2)
    setor: Optional[str] = None
    status: Optional[Status] = None


class ProjetoSchema(BaseModel):
    id: int
    nome: str
    empresa: str
    setor: str
    cidade: str
    uf: str
    status: str
    investimento_mi: Optional[float] = None
    fonte: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ListaProjetosSchema(BaseModel):
    total: int
    projetos: List[ProjetoSchema]


class ResumoSchema(BaseModel):
    """Totais agregados para o painel."""

    total_projetos: int
    investimento_total_mi: float
    por_uf: dict
    por_setor: dict
    por_status: dict


class MensagemSchema(BaseModel):
    mensagem: str
