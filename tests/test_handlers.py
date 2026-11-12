import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src import crear_archivo, leer_metadata


class LeerMetadataTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "bucket-taller"},
                    "object": {"key": "universidades/UTEC/archivo+01.txt"},
                }
            }]
        }
        self.head = {
            "Metadata": {"codigo-curso": "CS2032", "codigo-alumno": "202410083"},
            "LastModified": datetime(2026, 11, 12, tzinfo=timezone.utc),
            "ContentLength": 8,
        }

    @patch.dict(os.environ, {"TOPIC_ARN": "arn:aws:sns:us-east-1:904208419583:tema"})
    @patch.object(leer_metadata.boto3, "client")
    def test_publica_metadata_real_de_s3(self, client):
        s3 = MagicMock()
        s3.head_object.return_value = self.head
        sns = MagicMock()
        sns.publish.return_value = {"MessageId": "mensaje-1"}
        client.side_effect = lambda service: {"s3": s3, "sns": sns}[service]

        result = leer_metadata.lambda_handler(self.event, None)

        s3.head_object.assert_called_once_with(
            Bucket="bucket-taller", Key="universidades/UTEC/archivo 01.txt"
        )
        payload = json.loads(sns.publish.call_args.kwargs["Message"])
        self.assertEqual(payload["archivo_datos"]["codigo_curso"], "CS2032")
        self.assertEqual(payload["archivo_datos"]["codigo_alumno"], "202410083")
        self.assertEqual(payload["archivo_datos"]["size"], 8)
        self.assertEqual(sns.publish.call_args.kwargs["MessageAttributes"]["tenant_id"]["StringValue"], "UTEC")
        self.assertEqual(result["published_message_ids"], ["mensaje-1"])

    @patch.dict(os.environ, {"TOPIC_ARN": "arn:aws:sns:us-east-1:904208419583:tema"})
    @patch.object(leer_metadata.boto3, "client")
    def test_no_publica_si_falta_codigo_alumno(self, client):
        s3 = MagicMock()
        s3.head_object.return_value = {**self.head, "Metadata": {"codigo-curso": "CS2032"}}
        sns = MagicMock()
        client.side_effect = lambda service: {"s3": s3, "sns": sns}[service]

        with self.assertRaises(ValueError):
            leer_metadata.lambda_handler(self.event, None)
        sns.publish.assert_not_called()


class CrearArchivoTests(unittest.TestCase):
    @patch.dict(os.environ, {"TABLE_NAME": "t_archivos_UTEC"})
    @patch.object(crear_archivo.boto3, "resource")
    def test_guarda_ambos_codigos_en_dynamodb(self, resource):
        table = MagicMock()
        resource.return_value.Table.return_value = table
        archivo = {
            "tenant_id": "UTEC",
            "archivo_id": "universidades/UTEC/archivo01.txt",
            "archivo_datos": {
                "codigo_curso": "CS2032", "codigo_alumno": "202410083", "size": 8
            },
        }
        event = {"Records": [{"Sns": {"Message": json.dumps(archivo)}}]}

        crear_archivo.lambda_handler(event, None)

        resource.return_value.Table.assert_called_once_with("t_archivos_UTEC")
        table.put_item.assert_called_once_with(Item=archivo)

    @patch.dict(os.environ, {"TABLE_NAME": "t_archivos_UTEC"})
    @patch.object(crear_archivo.boto3, "resource")
    def test_no_guarda_otro_tenant(self, resource):
        table = MagicMock()
        resource.return_value.Table.return_value = table
        event = {"Records": [{"Sns": {"Message": json.dumps({
            "tenant_id": "UNIV2",
            "archivo_id": "universidades/UNIV2/archivo01.txt",
            "archivo_datos": {"codigo_curso": "CS2032", "codigo_alumno": "202410083"},
        })}}]}

        with self.assertRaises(ValueError):
            crear_archivo.lambda_handler(event, None)
        table.put_item.assert_not_called()


if __name__ == "__main__":
    unittest.main()
