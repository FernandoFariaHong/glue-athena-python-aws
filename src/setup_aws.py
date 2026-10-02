"""Cria (de forma idempotente) toda a infraestrutura: bucket, role, database, job e crawler,
e envia o CSV e o script do Glue para o S3."""
import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

import config as c

RAIZ = Path(__file__).resolve().parent.parent
s3 = boto3.client("s3", region_name=c.REGION)
iam = boto3.client("iam")
glue = boto3.client("glue", region_name=c.REGION)


def criar_bucket() -> None:
    try:
        s3.head_bucket(Bucket=c.bucket())
        print(f"[ok] bucket já existe: {c.bucket()}")
        return
    except ClientError:
        pass
    kwargs = {"Bucket": c.bucket()}
    if c.REGION != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": c.REGION}
    s3.create_bucket(**kwargs)
    s3.put_public_access_block(
        Bucket=c.bucket(),
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    print(f"[criado] bucket: {c.bucket()}")


def criar_role() -> str:
    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "glue.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    try:
        arn = iam.create_role(
            RoleName=c.ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust)
        )["Role"]["Arn"]
        print(f"[criado] role: {c.ROLE_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
        arn = iam.get_role(RoleName=c.ROLE_NAME)["Role"]["Arn"]
        print(f"[ok] role já existe: {c.ROLE_NAME}")

    iam.attach_role_policy(
        RoleName=c.ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
    )
    acesso_s3 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
                "Resource": [f"arn:aws:s3:::{c.bucket()}", f"arn:aws:s3:::{c.bucket()}/*"],
            }
        ],
    }
    iam.put_role_policy(
        RoleName=c.ROLE_NAME, PolicyName="acesso-bucket-projeto", PolicyDocument=json.dumps(acesso_s3)
    )
    return arn


def enviar_arquivos() -> None:
    csv_local = RAIZ / "data" / "vendas.csv"
    if not csv_local.exists():
        raise SystemExit("data/vendas.csv não encontrado. Rode antes: python src/gerar_dados.py")
    s3.upload_file(str(csv_local), c.bucket(), f"{c.RAW_PREFIX}vendas.csv")
    s3.upload_file(
        str(RAIZ / "glue" / "transformar_vendas.py"),
        c.bucket(),
        f"{c.SCRIPTS_PREFIX}transformar_vendas.py",
    )
    print("[ok] CSV e script do Glue enviados ao S3")


def criar_database() -> None:
    try:
        glue.create_database(DatabaseInput={"Name": c.DATABASE})
        print(f"[criado] database Glue: {c.DATABASE}")
    except glue.exceptions.AlreadyExistsException:
        print(f"[ok] database já existe: {c.DATABASE}")


def criar_job(role_arn: str) -> None:
    definicao = {
        "Role": role_arn,
        "Command": {
            "Name": "glueetl",
            "ScriptLocation": c.s3_uri(f"{c.SCRIPTS_PREFIX}transformar_vendas.py"),
            "PythonVersion": "3",
        },
        "DefaultArguments": {
            "--RAW_PATH": c.s3_uri(c.RAW_PREFIX),
            "--CURATED_PATH": c.s3_uri(c.CURATED_PREFIX),
            "--job-language": "python",
        },
        "GlueVersion": "4.0",
        "WorkerType": "G.1X",
        "NumberOfWorkers": 2,
        "Timeout": 15,
    }
    try:
        glue.create_job(Name=c.JOB_NAME, **definicao)
        print(f"[criado] job Glue: {c.JOB_NAME}")
    except glue.exceptions.AlreadyExistsException:
        glue.update_job(JobName=c.JOB_NAME, JobUpdate=definicao)
        print(f"[atualizado] job Glue: {c.JOB_NAME}")


def criar_crawler(role_arn: str) -> None:
    definicao = {
        "Role": role_arn,
        "DatabaseName": c.DATABASE,
        "Targets": {"S3Targets": [{"Path": c.s3_uri(c.CURATED_PREFIX)}]},
    }
    try:
        glue.create_crawler(Name=c.CRAWLER_NAME, **definicao)
        print(f"[criado] crawler: {c.CRAWLER_NAME}")
    except glue.exceptions.AlreadyExistsException:
        glue.update_crawler(Name=c.CRAWLER_NAME, **definicao)
        print(f"[atualizado] crawler: {c.CRAWLER_NAME}")


def main() -> None:
    criar_bucket()
    role_arn = criar_role()
    enviar_arquivos()
    criar_database()
    # A role recém-criada leva alguns segundos para propagar; se o Glue reclamar, rode de novo.
    criar_job(role_arn)
    criar_crawler(role_arn)
    print("\nInfraestrutura pronta. Próximo passo: python src/executar_pipeline.py")


if __name__ == "__main__":
    main()
