"""Lee metadata real de S3 y publica un mensaje en SNS."""

import json
import os
from urllib.parse import unquote_plus

import boto3


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    sns = boto3.client("sns")
    published = []

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        parts = key.split("/")
        if len(parts) < 3 or parts[0] != "universidades" or not parts[1] or not key.endswith(".txt"):
            raise ValueError(f"Ruta de archivo no valida: {key}")

        tenant_id = parts[1]
        head = s3.head_object(Bucket=bucket, Key=key)
        metadata = head.get("Metadata", {})
        codigo_curso = metadata.get("codigo-curso", "").strip()
        codigo_alumno = metadata.get("codigo-alumno", "").strip()
        if not codigo_curso or not codigo_alumno:
            raise ValueError(
                f"Falta codigo-curso o codigo-alumno en la metadata de s3://{bucket}/{key}"
            )

        archivo = {
            "tenant_id": tenant_id,
            "archivo_id": key,
            "archivo_datos": {
                "last_modified": head["LastModified"].isoformat(),
                "size": head["ContentLength"],
                "bucket_name": bucket,
                "codigo_curso": codigo_curso,
                "codigo_alumno": codigo_alumno,
            },
        }
        response = sns.publish(
            TopicArn=os.environ["TOPIC_ARN"],
            Subject="Nuevo Archivo",
            Message=json.dumps(archivo),
            MessageAttributes={
                "tenant_id": {"DataType": "String", "StringValue": tenant_id}
            },
        )
        published.append(response["MessageId"])
        print(json.dumps({"archivo": archivo, "sns_message_id": response["MessageId"]}))

    return {"statusCode": 200, "published_message_ids": published}
