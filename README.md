# Chatbot de Rifas (WhatsApp Business)

Bot automatizado para gestionar ventas de rifas por WhatsApp.
Pensado para correr 24/7 en una PC o VPS barato.

## Stack

- Python 3.10+
- Flask (webhook + panel admin)
- SQLite
- Meta WhatsApp Business Cloud API

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Editar .env con tus tokens reales
python database.py        # crea las tablas
python app.py             # levanta el servidor
```

## Estructura

```
rifa-chatbot/
├── app.py                    # Servidor Flask (webhook + admin panel)
├── bot.py                    # Lógica conversacional
├── database.py               # Capa de datos
├── config.py                 # Config desde .env
├── requirements.txt
├── .env                      # Secrets (NO commitear)
├── webhook.py                # Recepción de mensajes de WhatsApp
├── admin.py                  # Comandos admin
├── database/
│   └── schema.sql            # DDL
├── utils/
│   ├── __init__.py
│   ├── messages.py           # Plantillas
│   └── validators.py         # Validaciones
├── data/
│   ├── rifas.db
│   └── comprobantes/
└── logs/
    └── app.log
```

## Roadmap

- [ ] Webhook con verificación de firma de Meta
- [ ] State machine de conversación
- [ ] Panel admin web
- [ ] Job que libera reservas expiradas
- [ ] Exportación CSV/Excel
- [ ] Tests
