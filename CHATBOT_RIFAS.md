# Chatbot de Rifas - WhatsApp Business

---

## 1. Resumen del Proyecto

**Producto:** Chatbot automatizado para gestión de rifas por WhatsApp Business

**Usuario objetivo:** Vendedor de rifas que quiere automatizar la atención al cliente

**Funcionalidades:**
- Mostrar boletas disponibles (0000-9999)
- Reservar/separar boletas
- Capturar datos del cliente (nombre, teléfono, comprobante)
- Notificaciones al administrador cuando llega un comprobante
- Confirmación manual de pagos

**Costo:** $0/mes (tu PC como servidor)

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                         TU PC                                 │
│                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌───────────┐  │
│   │  WhatsApp  │      │   Python    │      │  SQLite   │  │
│   │  Business  │◄────►│   Chatbot   │◄────►│  (BD)     │  │
│   │    API     │      │             │      │           │  │
│   └─────────────┘      └──────┬──────┘      └───────────┘  │
│                                │                             │
│                                ▼                             │
│                       ┌─────────────┐                       │
│                       │  Flask/Fast  │                       │
│                       │  API        │                       │
│                       └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │  ADMIN (Vos)        │
                    │  - Notificaciones   │
                    │  - Aprobar/Rechazar │
                    └─────────────────────┘
```

---

## 3. Estructura de Archivos

```
rifa-chatbot/
├── app.py                    # Servidor principal (Flask/FastAPI)
├── bot.py                    # Lógica del chatbot
├── database.py               # Manejo de SQLite
├── config.py                 # Configuración (token, números)
├── requirements.txt          # Dependencias Python
├── .env                      # Variables de entorno (NO commitear)
├── webhook.py               # Recepciones de WhatsApp
├── admin.py                 # Comandos de administración
├── utils/
│   ├── __init__.py
│   ├── messages.py          # Plantillas de mensajes
│   └── validators.py        # Validaciones
├── data/
│   ├──rifas.db              # Base de datos (se crea solo)
│   └──comprobantes/         # Fotos de comprobantes
├── logs/
│   └── app.log              # Logs del sistema
└── README.md                # Instrucciones
```

---

## 4. Esquema de Base de Datos

### Tabla: rifas

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID único (auto) |
| numero | TEXT | Número de boleta (0000-9999) |
| estado | TEXT | disponible/reservada/vendida/cancelada |
| cliente_nombre | TEXT | Nombre completo |
| cliente_telefono | TEXT | Teléfono del cliente |
| precio | REAL | Precio de la boleta |
| comprobante_imagen | TEXT | Ruta de la foto |
| fecha_reserva | DATETIME | Cuándo se separó |
| fecha_pago | DATETIME | Cuándo se confirmó pago |
| notas | TEXT | Notas adicionales |

### Tabla: transacciones

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID único (auto) |
| rifa_id | INTEGER | FK a rifas |
| tipo | TEXT | reserva/pago/cancelacion |
| detalle | TEXT | Detalles |
| fecha | DATETIME | Cuándo ocurrió |

### Tabla: config

| Campo | Tipo | Descripción |
|-------|------|-------------|
| clave | TEXT | Nombre del setting |
| valor | TEXT | Valor del setting |

---

## 5. Flujo de Conversación

### Flujo Principal: Compra de Boleta

```
CLIENTE                     CHATBOT
─────────────────────────────────────────────────────────────
"Hola"                  →   "🎫 Hola! Bienvenido a Rifas [NOMBRE]"
                         "Tengo 4000 boletas disponibles ($ c/u)"
                         "¿Cuántas boletas querés comprar?"

"2"                     →   "Perfecto! Elige 2 números:"
                         "Ejemplo: 1234, 5678"
                         "O escribí 'disponibles' para ver lista"

"disponibles"           →   "📋 Boletas disponibles (primero 20):"
                         "0001, 0002, 0003, 0004..."
                         "(manda lista paginada)"

"0001 y 0002"          →   "✅ Selección: 0001, 0002"
                         "Total: $2000"
                         "Datos a enviar:"
                         "1. Nombre completo"
                         "2. Teléfono"
                         "3. Comprobante de pago"

[Manda foto + datos]    →   "📨 Comprobante recibido!"
                         "Te notifico cuando lo revise el admin."

─────────────────────────────────────────────────────────────
                         [GUARDA EN BD: estado="reservada"]
                         [TE NOTIFICA POR WHATSAPP]
─────────────────────────────────────────────────────────────

[VOS] "APROBAR 0001"    →   "✅ Boleta 0001 confirmada!"
                         "Mucha suerte! 🍀"
                         [ACTUALIZA BD: estado="vendida"]
```

### Flujo: Consulta de Disponibles

```
CLIENTE                     CHATBOT
─────────────────────────────────────────────────────────────
"disponibles"           →   "📋 Números disponibles:"
                         "0001-0050, 0100-0150, ..."

"buscar 5"              →   "🔍 Boletas que contienen '5':"
                         "0005, 0015, 0025... (hasta 20)"
```

---

## 6. Comandos de Administrador

| Comando | Descripción |
|---------|-------------|
| `APROBAR <numero>` | Confirma pago de boleta |
| `RECHAZAR <numero>` | Cancela reserva |
| `LISTA` | Ver todas las ventas |
| `DISPONIBLES` | Ver cuántas quedan |
| `ESTADO <numero>` | Ver estado de una boleta |
| `VENTAS` | Resumen de ventas |
| `EXPORTAR` | Exportar Excel/CSV |

---

## 7. Configuración (.env)

```env
# WhatsApp API
WHATSAPP_TOKEN=EAAC...
PHONE_NUMBER_ID=1234567890
WHATSAPP_BUSINESS_ID=987654321

# Admin
ADMIN_PHONE=+54911...

# Base de datos
DATABASE_URL=rifas.db

# App
HOST=0.0.0.0
PORT=5000
DEBUG=true
```

---

## 8. Dependencias (requirements.txt)

```txt
flask==3.0.0
flask-cors==4.0.0
openai-whatsapp-business==0.1.0
sqlalchemy==2.0.0
python-dotenv==1.0.0
pillow==10.0.0
requests==2.31.0
python-dateutil==2.8.0
```

---

## 9. Instalación Local

```bash
# 1. Clonar/Crear carpeta
mkdir rifa-chatbot
cd rifa-chatbot

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
copy .env.example .env
# Editar con tus datos

# 5. Inicializar base de datos
python app.py --init

# 6. Ejecutar
python app.py
```

---

## 10. Costos

| Ítem | Costo |
|------|-------|
| WhatsApp Business API | $0 (gratis hasta 1K chats/mes) |
| Python | $0 |
| SQLite | $0 |
| Tu PC (luz) | ~$5/mes |
| **Total** | **~$5/mes** |

---

## 11. Tech Stack

| Componente | Tecnología |
|------------|------------|
| Backend | Python + Flask |
| Base de datos | SQLite |
| WhatsApp | Meta WhatsApp Business API |
| Hosting | Tu PC local |
| Notificaciones | WhatsApp directo |

---

## 12. Próximos Pasos

1. [ ] Obtener token de Meta for Developers
2. [ ] Configurar Webhook
3. [ ] Ejecutar código
4. [ ] Probar con tu número
5. [ ] Dejar corriendo 24/7

---

## 13. Notas

- El token de Meta expira cada ~23 horas, hay que renovarlo
- Para producción 24/7, considerar un VPS (~$4/mes)
- Los comprobantes se guardan localmente en `data/comprobantes/`
- La base de datos es un archivo `.db` que se puede respaldar

---

*Documento creado para el proyecto de chatbot de rifas*
