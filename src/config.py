"""Configurações centrais do projeto. Tudo pode ser sobrescrito por variável de ambiente."""
import os
from functools import lru_cache

import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
PROJECT = "vendas-lakehouse"

DATABASE = os.getenv("GLUE_DATABASE", "vendas_db")
JOB_NAME = f"{PROJECT}-transformar-vendas"
CRAWLER_NAME = f"{PROJECT}-crawler-curated"
ROLE_NAME = f"{PROJECT}-glue-role"

# Prefixos dentro do bucket (camadas do data lake)
RAW_PREFIX = "raw/vendas/"
CURATED_PREFIX = "curated/vendas/"
SCRIPTS_PREFIX = "scripts/"
ATHENA_PREFIX = "athena-results/"


@lru_cache(maxsize=1)
def account_id() -> str:
    return boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]


@lru_cache(maxsize=1)
def bucket() -> str:
    """Nomes de bucket são globais; incluir o ID da conta evita colisões."""
    return os.getenv("PROJECT_BUCKET") or f"{PROJECT}-{account_id()}-{REGION}"


def s3_uri(prefix: str) -> str:
    return f"s3://{bucket()}/{prefix}"
