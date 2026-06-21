"""Helpers para construir respuestas de API Gateway Lambda Proxy.

Incluye cabeceras CORS en toda respuesta - el dashboard externo
(React/Vite en Docker) llama a esta API directamente desde el
navegador, así que cada respuesta necesita Access-Control-Allow-Origin
además de la configuración de CORS a nivel de API Gateway (que solo
cubre el preflight OPTIONS, no el body real de cada respuesta).
"""
import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
        "body": json.dumps(body),
    }


def error_response(status_code: int, message: str, **extra) -> dict:
    return response(status_code, {"error": message, **extra})