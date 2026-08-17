# Chatbot de Rifas

Bot automatizado para gestionar ventas de rifas por WhatsApp y Telegram.

## Estado

✅ **Producción:** https://rifa-chatbot-production.up.railway.app/admin

## ¿Qué hace?

Un chatbot que automatiza la venta de rifas:

1. Cliente escribe al bot (Telegram)
2. Elige el número de boleta
3. Recibe datos para pagar
4. Envía foto del comprobante
5. Admin recibe notificación
6. Admin aprueba → cliente confirmado

## Características

### 🤖 Bot de Telegram
- Conversación automática
- Reserva de boletas
- Envío de comprobantes
- Notificaciones al admin
- Tono amigable y conversacional

### 📊 Panel Admin (Web)
- Crear rifas con rango de números (ej: 0000-9999)
- Eliminar rifas
- Finalizar rifas
- Ver estadísticas en tiempo real
  - Boletas disponibles
  - Boletas separadas
  - Boletas vendidas
  - Ganancias
- Buscador de boletas
- Aprobar/rechazar pagos
- Vista de pestañas para múltiples rifas
- Auto-refresh cada 30 segundos

### 📱 Notificaciones
- Telegram: notificaciones de pagos pendientes
- Botones para aprobar/rechazar directamente

## Stack

- **Python 3.12**
- **Flask** (servidor web)
- **Railway** (hosting)
- **PostgreSQL** (base de datos persistente)
- **Telegram Bot API**

## Variables de Entorno

```
TELEGRAM_BOT_TOKEN=8866976276:AAFYd-3PCGJY54WubludIh0tel3aG7EUmek
TELEGRAM_CHAT_ID=1691674037
TELEGRAM_ENABLED=true
TELEGRAM_NOTIF_PAGO=true
TELEGRAM_NOTIF_NO_ENTIENDO=true
WEBHOOK_VERIFY_TOKEN=mi_token_seguro
DATABASE_URL=postgresql://...
```

## Cómo Usar

### Crear una Rifa
1. Ir al admin
2. Click en "+ Crear Nueva Rifa"
3. Llenar:
   - Nombre (ej: "Rifa Navidad")
   - Precio por boleta
   - Desde (ej: 0000)
   - Hasta (ej: 9999)
   - Fecha del sorteo
4. Click en "Crear Rifa"

### Aprobar Pagos
1. Llega notificación al admin por Telegram
2. Click en botón "APROBAR"
3. Cliente notificado automáticamente

### Finalizar Rifa
1. Click en botón verde "Finalizar Rifa"
2. La rifa se marca como terminada

## Desarrollo

```powershell
# Clonar
git clone https://github.com/SantiArias05/rifa-chatbot.git
cd rifa-chatbot

# Instalar dependencias
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configurar variables
copy .env.example .env

# Correr localmente
python app.py
```

## Estructura del Proyecto

```
rifa-chatbot/
├── app.py                 # Servidor Flask principal
├── bot.py                 # Lógica del chatbot
├── database.py            # Base de datos (PostgreSQL/SQLite)
├── webhook.py            # Webhooks de WhatsApp y Telegram
├── telegram.py           # Notificaciones y clase del bot
├── whatsapp.py           # Cliente WhatsApp
├── config.py            # Configuración centralizada
├── utils/
│   └── messages.py     # Mensajes del bot
├── database/
│   └── schema.sql      # Esquema SQLite
└── requirements.txt    # Dependencias Python
```

## Deploy en Railway

1. Crear cuenta en Railway
2. New Project → Connect GitHub
3. Seleccionar repositorio
4. Agregar variables de entorno
5. Railway hace deploy automáticamente

## Pendientes / Mejoras

- [ ] WhatsApp Business API (actualmente solo Telegram)
- [ ] Más idiomas
- [ ] Reportes avanzados
- [ ] Exportar lista de boletas
- [ ] Enviar lista por WhatsApp

---

**Fecha de creación:** Agosto 2026
**Desarrollado para:** Santiago Arias
