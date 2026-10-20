# OFX Importer – UNIFEOB Integração de Dados

**Grupo PI:**

| RA | Nome |
|----|------|
| 25000071 | Thales Vasconcellos Tardelli Sabbag de Paula |
| 25001039 | João Miguel da Silva Calvacante |
| 25001528 | Matheus Barrense Mendes dos Santos |
| 25000700 | Gabriel Henrique Sartório |
| 25000171 | Fernando Nogueira da Silva |
| 25000079 | Kayky Juan Tavares dos Reis |

---

## Funcionalidades

1. **Importação de arquivo OFX** – upload via navegador, parse do SGML e persistência no PostgreSQL
2. **Banco de dados PostgreSQL** – tabelas `contas`, `categorias` e `lancamentos`
3. **Classificação de lançamentos** – o usuário associa cada lançamento a uma categoria (Receita / Despesa)
4. **Dashboard** – visão geral com KPIs (total, sem categoria, receitas, despesas)
5. **Relatório** – totais por categoria com resultado líquido

---

## Pré-requisitos

- Python 3.10+
- PostgreSQL 14+

---

## Instalação

```bash
# 1. Clone / copie o projeto
cd ofx_projeto

# 2. Crie o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Crie o banco de dados no PostgreSQL
psql -U postgres -c "CREATE DATABASE ofx_db;"
```

---

## Configuração (variáveis de ambiente)

Crie um arquivo `.env` ou exporte antes de rodar:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ofx_db
export DB_USER=postgres
export DB_PASSWORD=sua_senha
export SECRET_KEY=chave-secreta-qualquer
```

---

## Executar

```bash
python app.py
```

Acesse: **http://localhost:5000**

Na primeira execução, o script cria as tabelas e insere as categorias padrão automaticamente.

---

## Estrutura do banco de dados

```
contas
  id, bank_id, branch_id, acct_id (UNIQUE), acct_type,
  moeda, saldo, saldo_data, criado_em

categorias
  id, nome (UNIQUE), tipo (RECEITA | DESPESA), descricao

lancamentos
  id, conta_id (FK), fitid, trntype, data_lancamento,
  valor, memo, categoria_id (FK), importado_em
  UNIQUE(conta_id, fitid)   ← evita duplicatas
```

---

## Fluxo de uso

```
Upload .ofx  →  Parse  →  PostgreSQL  →  Classificar  →  Relatório
```

1. Acesse **Importar OFX** e envie o arquivo `.ofx`
2. Vá para **Classificar** e atribua uma categoria a cada lançamento
3. Consulte o **Relatório** para ver o resultado por categoria
