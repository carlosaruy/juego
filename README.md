# juego
Juego en equipo, resta puntos al responder erroneamente

## Deployment

```bash
export ADMIN_PASSWORD="supersecret"
uvicorn main:app --workers 2 --host 0.0.0.0 --port 8000
```
