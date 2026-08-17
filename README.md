# Chatbot de Rifas

Bot automatizado para gestionar ventas de rifas por WhatsApp y Telegram.

## Estado

✅ **Producción:** https://rifa-chatbot-production.up.railway.app/admin

## Stack

- **Python 3.12** - Lenguaje
- **Flask** - Servidor web
- **Railway** - Hosting
- **PostgreSQL** - Base de datos (persistente)
- **Telegram Bot** - Chat con clientes

## Características

### Bot de Telegram
- Conversación automática con clientes
- Reserva de boletas
- Envío de comprobantes de pago
- Notificaciones al admin

### Panel Admin
- Crear/eliminar rifas
- Rango de números (ej: 0000-9999)
- Ver boletas disponibles/reservadas/vendidas
- Aprobar o rechazar pagos
- Finalizar rifas
- Estadísticas en tiempo real

### Flujo de Compra
1. Cliente escribe al bot
2. Elige número de boleta
3. Recibe datos de pago
4. Envía comprobante
5. Admin recibe notificación
6. Admin aprueba → cliente notificado

## Configuración

### Variables de Entorno (Railway)

```
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
TELEGRAM_ENABLED=true
TELEGRAM_NOTIF_PAGO=true
TELEGRAM_NOTIF_NO_ENTIENDO=true
WEBHOOK_VERIFY_TOKEN=mi_token_seguro
DATABASE_URL=postgres://...
```

### Desarrollo Local

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

## Estructura

```
rifa-chatbot/
├── app.py                 # Servidor Flask
├── bot.py                 # Lógica del chatbot
├── database.py            # Base de datos (PostgreSQL/SQLite)
├── webhook.py            # Webhooks de WhatsApp y Telegram
├── telegram.py           # Notificaciones y bot
├── whatsapp.py           # Cliente WhatsApp
├── config.py             # Configuración
├── utils/
│   └── messages.py      # Mensajes del bot
└── database/
    └── schema.sql       # Esquema SQLite
```

## Despliegue

1. Crear repositorio en GitHub
2. Conectar a Railway
3. Crear PostgreSQL en Railway
4. Agregar variables de entorno
5. Deploy automático

## Pendientes

- [ ] WhatsApp Business API
- [ ] Más idiomas
- [ ] Reportes avanzados
