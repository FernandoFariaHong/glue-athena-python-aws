# 🛒 Vendas Lakehouse: Python + AWS Glue + Amazon Athena

Mini data lake de ponta a ponta, simples e totalmente automatizado com Python (`boto3`).
Você sobe um CSV de vendas, o **Glue** transforma em **Parquet particionado**, o **Crawler** cria a tabela no **Data Catalog** e o **Athena** consulta tudo com SQL.

---

## 📑 Sumário

1. [Visão geral](#-visão-geral)
2. [Arquitetura](#-arquitetura)
3. [Estrutura do projeto](#-estrutura-do-projeto)
4. [Pré-requisitos](#-pré-requisitos)
5. [Passo a passo](#-passo-a-passo)
6. [O que cada peça faz](#-o-que-cada-peça-faz)
7. [Custos](#-custos)
8. [Limpeza (importante!)](#-limpeza-importante)
9. [Problemas comuns](#-problemas-comuns)
10. [Próximos passos](#-próximos-passos)

---

## 🔎 Visão geral

| Etapa | Serviço | O que acontece |
|-------|---------|----------------|
| 1. Origem | Python | Gera `data/vendas.csv` com 5.000 vendas fictícias |
| 2. Armazenamento | S3 | Guarda os dados em camadas (`raw/` e `curated/`) |
| 3. Transformação | Glue Job (PySpark) | Limpa, tipa, calcula `valor_total` e grava Parquet particionado por `ano`/`mes` |
| 4. Catálogo | Glue Crawler | Descobre o schema e registra a tabela `vendas` |
| 5. Consulta | Athena | Roda SQL direto sobre os arquivos no S3 |

## 🏗 Arquitetura

```
 data/vendas.csv
       │  (upload via boto3)
       ▼
 ┌───────────────┐   Glue Job (PySpark)    ┌─────────────────────┐
 │ S3  raw/      │ ──────────────────────► │ S3  curated/        │
 │ vendas.csv    │  limpa + tipa + Parquet │ ano=2024/mes=1/...  │
 └───────────────┘                         └──────────┬──────────┘
                                                      │ Glue Crawler
                                                      ▼
                                           ┌─────────────────────┐
                                           │ Glue Data Catalog   │
                                           │ vendas_db.vendas    │
                                           └──────────┬──────────┘
                                                      │ SQL
                                                      ▼
                                           ┌─────────────────────┐
                                           │ Amazon Athena       │
                                           │ resultados em S3    │
                                           └─────────────────────┘
```

## 📁 Estrutura do projeto

```
.
├── README.md
├── requirements.txt          # boto3 e pytest
├── data/                     # CSV gerado localmente (vendas.csv)
├── glue/
│   └── transformar_vendas.py # script PySpark que roda DENTRO do Glue
├── sql/                      # consultas do Athena (uma por arquivo)
│   ├── 01_receita_por_mes.sql
│   ├── 02_top_produtos.sql
│   └── 03_receita_por_regiao_trimestre.sql
├── src/
│   ├── config.py             # nomes, região, prefixos (tudo em um lugar)
│   ├── gerar_dados.py        # passo 1: cria o CSV
│   ├── setup_aws.py          # passo 2: cria a infraestrutura
│   ├── executar_pipeline.py  # passo 3: roda Job + Crawler
│   ├── consultar_athena.py   # passo 4: executa os .sql
│   └── destruir.py           # passo 5: apaga tudo
└── tests/
    └── test_gerar_dados.py
```

## ✅ Pré-requisitos

- **Python 3.10+** (`python --version`)
- **Conta AWS** com permissão para S3, IAM, Glue e Athena (um usuário com `AdministratorAccess` em conta de estudo resolve)
- **AWS CLI** instalada e configurada: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

## 🚀 Passo a passo

> Todos os comandos são executados **na raiz do projeto**.

### Passo 1 — Preparar o ambiente Python

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

### Passo 2 — Configurar credenciais da AWS

```bash
aws configure
```

Informe `Access Key`, `Secret Key`, região (ex.: `us-east-1`) e formato `json`.
Confirme que funcionou:

```bash
aws sts get-caller-identity
```

> 💡 Para usar outra região: `set AWS_REGION=sa-east-1` (Windows) ou `export AWS_REGION=sa-east-1` (Linux/macOS) **antes** de rodar os scripts. Use a mesma região em todos os passos.
> Nunca coloque chaves de acesso dentro do código ou do Git.

### Passo 3 — Gerar os dados de exemplo

```bash
python src/gerar_dados.py
```

Resultado esperado: `5000 linhas gravadas em data/vendas.csv`.
(Opcional) valide o código: `pytest`.

### Passo 4 — Criar a infraestrutura na AWS

```bash
python src/setup_aws.py
```

Cria, de forma **idempotente** (pode rodar várias vezes):

- bucket S3 `vendas-lakehouse-<id-da-conta>-<região>` (acesso público bloqueado)
- role IAM para o Glue, com acesso apenas a esse bucket
- upload do CSV para `raw/vendas/` e do script para `scripts/`
- database `vendas_db`, Glue Job e Glue Crawler

### Passo 5 — Executar o pipeline

```bash
python src/executar_pipeline.py
```

O script dispara o Job, espera terminar (~2 a 5 min), dispara o Crawler e espera também. Você verá o status a cada 15 segundos. Ao final, a tabela `vendas_db.vendas` existe.

### Passo 6 — Consultar com Athena

```bash
python src/consultar_athena.py                 # roda todas as consultas de sql/
python src/consultar_athena.py 02_top_produtos.sql   # roda uma só
```

Exemplo de saída:

```
=== 02_top_produtos.sql ===
  produto  | itens_vendidos | receita    | preco_medio
  ---------+----------------+------------+------------
  Notebook | 2987           | 10450000.5 | 3501.2
  ...
```

Você também pode abrir o **console do Athena**, escolher o database `vendas_db` e rodar SQL manualmente. (Na primeira vez, defina o local de resultados em *Settings* para `s3://<seu-bucket>/athena-results/`.)

### Passo 7 — Limpar tudo

```bash
python src/destruir.py
```

Digite `sim` para confirmar. Veja a seção [Limpeza](#-limpeza-importante).

## 🧩 O que cada peça faz

**`glue/transformar_vendas.py` (ETL)**
- *Extract*: lê o CSV em `raw/`.
- *Transform*: converte tipos, normaliza texto, remove nulos e duplicados, descarta valores inválidos, cria `valor_total`, `ano` e `mes`.
- *Load*: grava **Parquet** em `curated/`, particionado por `ano/mes`.

**Por que Parquet + partições?** Parquet é colunar e comprimido; partições deixam o Athena ler só as pastas necessárias. Como o Athena cobra por dados lidos, isso reduz custo e tempo. Compare `01_receita_por_mes.sql` com `03_receita_por_regiao_trimestre.sql`: a segunda filtra por `ano`/`mes` e lê menos dados.

**`src/config.py`** concentra nomes e prefixos. Quer outro bucket? `set PROJECT_BUCKET=meu-bucket-unico`.

**Schema final da tabela `vendas`**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id_venda | int | Identificador único |
| data_venda | date | Data da venda |
| produto | string | Nome do produto |
| regiao | string | Região do Brasil |
| quantidade | int | Itens vendidos |
| preco_unitario | double | Preço por item |
| valor_total | double | `quantidade × preco_unitario` |
| ano, mes | int | Colunas de partição |

## 💰 Custos

Com este volume (poucos KB) o custo é **centavos**, mas não é zero:

- **Glue Job**: cobrado por DPU-hora (2 workers G.1X, mínimo de 1 min). É o item mais relevante: poucos centavos por execução.
- **Crawler**: cobrado por DPU-hora, mínimo de 10 s.
- **Athena**: ~US$ 5 por TB lido (mínimo de 10 MB por consulta).
- **S3**: desprezível aqui.

Consulte os preços atuais na página oficial de cada serviço e **rode a limpeza ao terminar**.

## 🧹 Limpeza (importante!)

`python src/destruir.py` remove bucket (com conteúdo), job, crawler, database/tabelas e a role IAM. Depois confira no console se não restou nada.

## 🛠 Problemas comuns

| Sintoma | Causa / solução |
|---------|-----------------|
| `NoCredentialsError` | Rode `aws configure` novamente. |
| `AccessDenied` / `AccessDeniedException` | Seu usuário não tem permissão para S3/IAM/Glue/Athena. |
| `Role ... cannot be assumed` ou erro de `iam:PassRole` ao criar o job | A role recém-criada ainda propaga: aguarde ~30 s e rode `setup_aws.py` de novo. |
| Job `FAILED` | Veja os logs no CloudWatch (`/aws-glue/jobs/error`) ou em *Glue → Job runs → Error logs*. |
| `TABLE_NOT_FOUND` no Athena | O Crawler ainda não rodou. Execute `executar_pipeline.py`. |
| Athena: `No output location provided` no console | Defina o local de resultados nas *Settings* do Athena. |
| Bucket já existe (outra conta) | Defina `PROJECT_BUCKET` com um nome único. |

## 🔭 Próximos passos

- Agendar o Job com um **Glue Trigger** ou **EventBridge**.
- Trocar o Crawler por **Glue Data Quality** e schemas explícitos.
- Converter a infraestrutura para **Terraform** ou **AWS CDK**.
- Conectar o Athena a **QuickSight** ou **Power BI** para dashboards.
- Adicionar CI com `pytest` e `ruff`.
