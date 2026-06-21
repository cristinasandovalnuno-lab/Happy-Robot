# HappyRobot Logistics — Middleware de Carrier Sales (TMS)

Middleware en **API Gateway + Lambda** que expone el Legacy TMS (protocolo TCP
crudo) y la verificación FMCSA como una API REST simple que el workflow de
HappyRobot puede llamar como *tool* durante la llamada con el carrier.

## Qué cubre este repo (y qué no)

Este repo es **la capa de integración backend con el TMS y FMCSA, más negociación y logging de llamadas**. Cubre:

- Verificación de autoridad FMCSA (`/carrier/verify`). Confirmado que la
  API real funciona en producción (AWS) - el 403 que veíamos en pruebas
  locales era un bloqueo de IP residencial, no de la key (ver TESTING.md).
  `FMCSA_MODE=mock` queda como fallback documentado de contingencia, no
  como default.
- Búsqueda, detalle y reserva de loads contra el Legacy TMS.
- Negociación (`/negotiate`): decide accept/counter/reject contra
  `max_rate` (campo `MAX_BUY` del TMS) sin revelarlo nunca al caller, con
  hasta 3 rondas y una curva de concesión que se acerca al techo en cada
  ronda sin superarlo jamás. Lógica pura en `common/negotiation.py`,
  testeada sin red en `tests/test_negotiation.py`.
- `verify_carrier` es un puente puro hacia la API de FMCSA - no escribe
  en ninguna base de datos ni conoce Twin. Toda la captura de datos
  (tanto el resultado normal de cada llamada como las verificaciones
  fallidas) vive 100% dentro del workflow de HappyRobot, vía nodos
  nativos "Write to Twin": uno tras el `Extract` al final de la
  conversación para el outcome normal, y otro disparado por una rama
  condicional justo después de llamar a este endpoint, cuando
  `verified` es `false`. No hay ninguna base de datos externa
  (DynamoDB ni otra) en este proyecto, y ninguna Lambda llama
  directamente al gateway de Twin - es deliberado, para mantener el
  middleware totalmente desacoplado de la capa de datos.
- Manejo explícito de las 4 categorías de fallo del TMS (timeout, partial
  response, malformed response, delayed termination).
- Ocultamiento de `max_rate` / `MAX_BUY` en cada respuesta — nunca sale de
  estas Lambdas hacia el agente.

**No** cubre:

- El workflow del agente de voz en sí (prompt, flujo de conversación).
- El envío y verificación del OTP — normalmente vía SMS nativo de la
  plataforma HappyRobot.
- El dashboard operativo — implementado como una App nativa de
  HappyRobot ("Carrier Ops Console"), fuera de este repositorio (tiene
  su propio repo gestionado por la plataforma).
- El handoff al senior rep (mockeado dentro del propio workflow).

## Estructura

```
middleware/
├── template.yaml          # AWS SAM: API Gateway + 5 Lambdas, sin base de datos externa (Twin para todo el almacenamiento)
├── requirements.txt        # vacío a propósito: solo stdlib
├── .env.example
├── src/
│   ├── common/
│   │   ├── tms_codec.py     # encode/decode del wire protocol
│   │   ├── tms_client.py    # socket TCP + manejo de fallos + reintentos
│   │   ├── tms_faults.py    # excepciones por categoría de fallo
│   │   ├── negotiation.py   # lógica pura de accept/counter/reject
│   │   ├── fmcsa_client.py  # cliente real de la QCMobile API
│   │   ├── fmcsa_mock_client.py  # fallback de contingencia
│   │   ├── config.py        # lee env vars -> clientes (TMS / FMCSA)
│   │   └── http.py          # helpers de respuesta API Gateway
│   ├── verify_carrier/app.py   # POST /carrier/verify
│   ├── search_loads/app.py     # POST /loads/search
│   ├── get_load/app.py         # GET  /loads/{load_id}
│   ├── book_load/app.py        # POST /loads/{load_id}/book
│   └── negotiate/app.py        # POST /negotiate
├── scripts/                 # pruebas standalone, sin AWS ni HappyRobot
│   ├── test_tms_connection.py
│   ├── test_fmcsa_key.py
│   ├── test_handlers_direct.py
│   ├── probe_loads.py
│   └── test_local_api.sh
├── tests/                   # unit tests sin red (pytest)
│   ├── test_tms_codec.py
│   └── test_negotiation.py
└── events/*.json            # eventos de ejemplo para `sam local invoke`
```

## Plan de trabajo (orden recomendado)

1. **Probar las credenciales del TMS de forma aislada**, antes de tocar
   AWS: `scripts/test_tms_connection.py`. Si esto falla, no tiene sentido
   seguir.
2. **Codec del protocolo** (`tms_codec.py`) — encode de requests, parseo
   tolerante de líneas, detección de `END` / `ERR`. Cubierto por
   `tests/test_tms_codec.py`, sin red.
3. **Cliente TCP con manejo de fallos** (`tms_client.py`) — timeout de
   lectura, detección de partial response, cierre proactivo tras `END`
   (evita depender de "delayed termination"), reintentos acotados solo
   para comandos idempotentes.
4. **Las 3 Lambdas + API Gateway** vía SAM (`template.yaml`).
5. **Pruebas locales con SAM** (`sam local start-api` + `scripts/test_local_api.sh`,
   o `sam local invoke` con los eventos de `events/`) — esto simula API
   Gateway sin desplegar nada todavía.
6. **Deploy real** (`sam deploy --guided`) — obtienes la URL base y la API
   key para configurar el tool/webhook en el workflow de HappyRobot.
7. **Conectar a HappyRobot**: en el workflow, configura un nodo de tipo
   "tool"/"webhook" apuntando a la URL de salida (`ApiUrl`), método y
   header `x-api-key`.
8. **Pendiente**: OTP vía SMS nativo; KPIs + suite de QA + casos
   adversariales; entregables (email, build doc, video). El dashboard
   Docker ya está construido en `../happyrobot-dashboard`.

## Despliegue

Requiere [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
y credenciales de AWS configuradas.

```bash
sam build
sam deploy --guided
# Te pedirá los parámetros TmsHost, TmsPort, TmsAuthToken, FmcsaApiKey, FmcsaMode.
# NoEcho:true en el template evita que se impriman en los logs de CFN.
```

Al terminar, `sam deploy` imprime el output `ApiUrl`. Para ver el valor de
la API key generada:

```bash
aws apigateway get-api-keys --name-query happyrobot-carrier-sales-key --include-values
```

## Seguridad / manejo de credenciales

- El token (`TMS_AUTH_TOKEN`) viaja como parámetro `NoEcho` de
  CloudFormation y como variable de entorno de cada Lambda — nunca
  hardcodeado en el código fuente.
- `.env` está en `.gitignore`. No commitees `.env` ni el token real en
  ningún otro archivo si este repo va a ser público.
- Cada endpoint de API Gateway requiere `x-api-key` (ver `template.yaml`).

Ver también `TESTING.md` para el detalle de cómo probar cada pieza sin
necesidad del agente de HappyRobot.
