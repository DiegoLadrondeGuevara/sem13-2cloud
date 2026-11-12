"""Guarda en DynamoDB el mensaje SNS filtrado para UTEC."""

import json
import os

import boto3


def lambda_handler(event, context):
    table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    saved = []

    for record in event["Records"]:
        archivo = json.loads(record["Sns"]["Message"])
        if archivo["tenant_id"] != "UTEC":
            raise ValueError("Solo se admiten archivos del tenant UTEC")
        datos = archivo["archivo_datos"]
        if not datos.get("codigo_curso") or not datos.get("codigo_alumno"):
            raise ValueError("Faltan los codigos obligatorios en el mensaje SNS")

        item = {
            "tenant_id": archivo["tenant_id"],
            "archivo_id": archivo["archivo_id"],
            "archivo_datos": datos,
        }
        table.put_item(Item=item)
        saved.append(item["archivo_id"])
        print(json.dumps({"guardado": item}))

    return {"statusCode": 200, "saved_file_ids": saved}
