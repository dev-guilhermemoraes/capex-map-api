# Capex Map API

API REST do **Mapa de Capex Industrial no Brasil**, MVP da Sprint 02 (Arquitetura de Software) da pós-graduação em Engenharia de Software.

Faz o cadastro, consulta, edição e remoção de projetos de investimento industrial, calcula indicadores agregados e integra com a API externa **Nominatim (OpenStreetMap)** para obter as coordenadas de cada projeto a partir da cidade e UF.

A interface que consome esta API está em: https://github.com/dev-guilhermemoraes/capex-map-front

## Tecnologias

- Python 3.12, Flask e flask-openapi3 (documentação Swagger automática)
- Flask-SQLAlchemy com SQLite
- Pydantic para validação
- Requests para consumir o Nominatim

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/projetos` | Lista projetos, com filtros opcionais `uf`, `setor` e `status` |
| GET | `/projetos/{id}` | Detalha um projeto |
| POST | `/projetos` | Cadastra um projeto. Sem latitude/longitude, geocodifica cidade/UF no Nominatim |
| PUT | `/projetos/{id}` | Atualiza os campos enviados. Se cidade/UF mudarem, geocodifica de novo |
| DELETE | `/projetos/{id}` | Remove um projeto |
| GET | `/resumo` | Totais de projetos e investimento por UF, setor e status |

Respostas de erro: `404` (projeto não encontrado), `409` (nome duplicado), `422` (dados inválidos ou cidade não localizada).

## Como executar

### Com Docker

Pré-requisito: Docker instalado.

```bash
docker build -t capex-api .
docker run -p 5000:5000 capex-api
```

Swagger: http://localhost:5000/openapi/swagger

Para subir a aplicação completa (API + interface), use o `docker-compose.yml` do repositório da interface.

### Sem Docker

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Origem dos dados

Na primeira execução o banco é populado com um dataset curado (`data/seed.json`), montado a partir de notícias públicas em pesquisa feita fora da aplicação. Não há IA conectada ao sistema em tempo de execução: o conteúdo é mantido pelas rotas da própria API.

## Estrutura

```
capex-map-api/
├── app.py                  # inicialização e rotas
├── model/                  # modelo SQLAlchemy (Projeto)
├── schemas/                # validação e documentação (Pydantic)
├── services/geocoding.py   # cliente do Nominatim
├── data/seed.json          # dataset inicial
├── requirements.txt
└── Dockerfile
```
