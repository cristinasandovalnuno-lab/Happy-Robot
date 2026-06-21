# Cómo probar todo sin el agente de HappyRobot

Cuatro capas de prueba, de menor a mayor dependencia de infraestructura.
Avanza a la siguiente capa solo si la anterior pasa.

> **Nota sobre FMCSA**: la API real (`mobile.fmcsa.dot.gov`) devuelve 403
> desde muchas redes residenciales/domésticas — probado desde Python,
> desde el navegador, y confirmado que **no** es un problema de la key ni
> del user-agent. Probado en AWS CloudShell (incluso en una región fuera
> de EE.UU., `eu-west-1`) la misma key con la misma URL devolvió `200 OK`
> con datos reales. Conclusión: es un bloqueo por reputación de IP
> (residencial vs infraestructura cloud), no geográfico en el sentido
> estricto de "debe ser EE.UU.". Como las Lambdas corren en AWS, la
> verificación real funciona en producción aunque falle en pruebas desde
> casa. `FMCSA_MODE=mock` queda como fallback de contingencia documentado
> si la API real llegara a fallar el día de una demo.

## 1. Credenciales del TMS en crudo (ningún framework, ninguna nube)

```bash
cd middleware
pip install -r requirements-dev.txt   # solo pytest, para el paso 2

export TMS_HOST=tramway.proxy.rlwy.net
export TMS_PORT=17159
export TMS_AUTH_TOKEN=hr-fde-cristinasandoval-2026

python scripts/test_tms_connection.py
```

`test_tms_connection.py` primero hace `DEBUG_ECHO` (no pasa por fault
injection, así que si esto falla es un problema de red/auth, no de
inestabilidad del TMS) y luego `LOAD_QUERY` + `LOAD_GET` reales. `LOAD_BOOK`
queda comentado a propósito para no reservar loads de prueba por accidente.

Si `DEBUG_ECHO` falla:
- Error de conexión / timeout al conectar → revisa host/puerto, firewall,
  o que el proxy de Railway (`tramway.proxy.rlwy.net`) esté accesible
  desde donde estás corriendo el script.
- `AUTH_FAILED` → el token está mal copiado o expiró.

Para probar varias combinaciones de filtros de `LOAD_QUERY` de una sola
vez: `python scripts/probe_loads.py`.

Para probar FMCSA (puede dar 403 desde tu red, ver nota arriba - eso no
significa que esté mal):

```bash
export FMCSA_API_KEY=cdc33e44d693a3a58451898d4ec9df862c65b954
python scripts/test_fmcsa_key.py 872144
```

## 2. Lógica pura, sin red en absoluto

```bash
pytest tests/ -v
```

Esto valida dos cosas sin abrir ningún socket ni llamar a AWS: el
encode/decode del wire protocol contra los transcripts exactos del
manual del protocolo (`test_tms_codec.py`), y la lógica de decisión de
`/negotiate` - accept/counter/reject, que el counter nunca supere
`max_rate`, y que `max_rate` nunca aparezca en el resultado
(`test_negotiation.py`).

## 3. Lambdas + API Gateway, en local (SAM, sin desplegar a AWS)

```bash
sam build
sam local invoke VerifyCarrierFunction --event events/verify_carrier_event.json
sam local invoke SearchLoadsFunction --event events/search_loads_event.json
sam local invoke GetLoadFunction     --event events/get_load_event.json
sam local invoke BookLoadFunction    --event events/book_load_event.json
sam local invoke NegotiateFunction   --event events/negotiate_event.json
```

`VerifyCarrierFunction` escribe a `failed_verifications` en Twin (vía
su gateway REST) cuando una verificación falla. Localmente, sin pasarle
`TWIN_GATEWAY_URL` y `TWIN_ORG_ID` reales, esa escritura falla
silenciosamente (es un best-effort, no tumba la respuesta - ver el
comentario en `verify_carrier/app.py`), así que la verificación en sí
se puede probar local sin problema, pero confirmar que el log llega a
Twin de verdad solo se puede hacer **después** de `sam deploy`
(sección 4), apuntando a un gateway real.

`sam local invoke` lee `template.yaml`, así que para que las Lambdas
tengan las env vars necesitas pasarle los parámetros o un archivo de
overrides:

```bash
sam local invoke SearchLoadsFunction \
  --event events/search_loads_event.json \
  --parameter-overrides "TmsHost=tramway.proxy.rlwy.net TmsPort=17159 TmsAuthToken=hr-fde-cristinasandoval-2026 FmcsaApiKey=cdc33e44d693a3a58451898d4ec9df862c65b954"
```

Para probar como si fuera la API real (con rutas, no función por función):

```bash
sam local start-api \
  --parameter-overrides "TmsHost=tramway.proxy.rlwy.net TmsPort=17159 TmsAuthToken=hr-fde-cristinasandoval-2026 FmcsaApiKey=cdc33e44d693a3a58451898d4ec9df862c65b954"

# en otra terminal:
bash scripts/test_local_api.sh
```

Alternativa sin Docker (llama a los handlers como funciones de Python
normales, útil para iterar rápido): `python scripts/test_handlers_direct.py`.

## 4. API desplegada en AWS (todavía sin HappyRobot)

Después de `sam deploy --guided` (ver README.md), repite las mismas
pruebas de `scripts/test_local_api.sh` apuntando a la URL real:

```bash
export BASE_URL="https://<api-id>.execute-api.<region>.amazonaws.com/prod"
curl -s -X POST "$BASE_URL/carrier/verify" \
  -H "x-api-key: <tu-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"mc_number": "872144"}'

curl -s -X POST "$BASE_URL/loads/search" \
  -H "x-api-key: <tu-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"origin_state": "GA", "destination_state": "TX", "equipment_type": "DRY_VAN"}'
```

Solo cuando esta capa funciona tiene sentido configurar el tool/webhook
dentro del workflow de HappyRobot apuntando a esta URL.

## Casos de fallo a probar a propósito (para la suite de QA del challenge)

El TMS inyecta fallos de forma no determinística en comandos operacionales
(no en `DEBUG_ECHO`). No puedes forzar una categoría específica a demanda,
pero sí puedes:

- Correr `LOAD_QUERY`/`LOAD_GET` varias veces en bucle (10–20 intentos) y
  loguear cuántas veces `tms_client.py` lanza `TMSTimeoutFault`,
  `TMSPartialResponseFault` o `TMSMalformedResponseFault` — eso te da una
  tasa de fallo observada para documentar en el build doc.
- Bajar `read_timeout` deliberadamente (por ejemplo a 0.5s) para forzar
  timeouts y confirmar que el cliente cierra el socket y reintenta según
  lo esperado, sin colgarse.
- Probar `LOAD_BOOK` dos veces seguidas contra el mismo `LOAD_ID` para
  confirmar el comportamiento `ALREADY_BOOKED` documentado en
  `book_load/app.py`.

## Casos de QA confirmados para `/carrier/verify`

Probados contra la API real de FMCSA desde la Lambda desplegada en AWS
(`us-east-1`), el 17/06/2026. Como FMCSA es una base de datos pública que
cambia con el tiempo, estos resultados pueden variar en el futuro si se
re-ejecutan - lo que no debería cambiar es el *comportamiento* del
endpoint ante cada tipo de caso (verified true/false, manejo de
`content` vacío, etc.).

| MC number | Resultado | Carrier | Para qué sirve como caso de prueba |
|---|---|---|---|
| `872144` | `verified: true` | Ouza Transportation Inc | Caso feliz estándar - usado también en el resto de la suite (negotiate, book, etc.) |
| `999999` | `verified: true` | TLA Trucking LLC | Confirma que un MC "que parece de relleno" puede ser real - no asumir que números redondos están libres |
| `1` | `verified: true` | Preferred Development Corporation | MC histórico (el más antiguo asignado) - confirma que el endpoint no falla con números bajos |
| `9999999` | `verified: false`, `reason: "MC number no encontrado en FMCSA"`, `carrier: null` | — | Caso negativo limpio - `content` vacío en la respuesta de FMCSA, manejado sin excepción |

Pendiente de encontrar (no se localizó uno al azar): un MC real con
`allowedToOperate: "N"` o con `oosDate` no nulo, para probar el camino de
"autorizado pero con problema de seguridad/autoridad" distinto del simple
"no encontrado". Si apareciera uno durante pruebas futuras, documentarlo
aquí.

