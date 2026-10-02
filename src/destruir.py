"""Remove TUDO que o projeto criou (bucket e conteúdo, job, crawler, database, role).

Uso: python src/destruir.py
"""
import boto3
from botocore.exceptions import ClientError

import config as c

glue = boto3.client("glue", region_name=c.REGION)
iam = boto3.client("iam")
s3 = boto3.resource("s3", region_name=c.REGION)


def tentar(descricao: str, fn) -> None:
    try:
        fn()
        print(f"[removido] {descricao}")
    except (ClientError, glue.exceptions.EntityNotFoundException):
        print(f"[ignorado] {descricao} (não existe)")


def main() -> None:
    if input(f"Apagar bucket '{c.bucket()}' e todos os recursos? (digite 'sim'): ") != "sim":
        raise SystemExit("Cancelado.")

    tentar("crawler", lambda: glue.delete_crawler(Name=c.CRAWLER_NAME))
    tentar("job", lambda: glue.delete_job(JobName=c.JOB_NAME))
    tentar("database + tabelas", lambda: glue.delete_database(Name=c.DATABASE))

    def apagar_bucket():
        b = s3.Bucket(c.bucket())
        b.objects.all().delete()
        b.delete()

    tentar("bucket", apagar_bucket)

    def apagar_role():
        iam.detach_role_policy(
            RoleName=c.ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
        )
        iam.delete_role_policy(RoleName=c.ROLE_NAME, PolicyName="acesso-bucket-projeto")
        iam.delete_role(RoleName=c.ROLE_NAME)

    tentar("role IAM", apagar_role)


if __name__ == "__main__":
    main()
