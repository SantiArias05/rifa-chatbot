"""Lógica del chatbot - Máquina de estados conversacional."""
import re
import random
import json
from datetime import datetime
from database import (
    query, query_one, execute, get_or_create_cliente,
    get_active_rifa, is_admin
)
from utils import messages
from telegram import telegram


class ChatBot:
    """Gestor de conversación con memoria."""

    def __init__(self):
        self.estados_validos = [
            'inicio', 'pidiendo_numero',
            'pidiendo_datos', 'pidiendo_comprobante',
            'procesando', 'completado', 'timeout'
        ]

    # ---------- gestión de sesión ----------

    def get_session(self, telefono: str) -> dict:
        """Obtiene o crea la sesión del cliente."""
        session = query_one(
            "SELECT * FROM sesiones_cliente WHERE telefono = ?",
            (telefono,)
        )
        if not session:
            # Crear nueva sesión
            rifa = get_active_rifa()
            rifa_id = rifa["id"] if rifa else None
            execute(
                """INSERT INTO sesiones_cliente (telefono, estado, rifa_id, contexto_json)
                   VALUES (?, 'inicio', ?, '{}')""",
                (telefono, rifa_id)
            )
            session = query_one(
                "SELECT * FROM sesiones_cliente WHERE telefono = ?",
                (telefono,)
            )
        return session

    def update_session(self, telefono: str, estado: str, contexto: dict = None):
        """Actualiza el estado y contexto de la sesión."""
        ctx_json = json.dumps(contexto) if contexto else "{}"
        execute(
            """UPDATE sesiones_cliente
               SET estado = ?, contexto_json = ?, last_activity = CURRENT_TIMESTAMP
               WHERE telefono = ?""",
            (estado, ctx_json, telefono)
        )

    def get_contexto(self, telefono: str) -> dict:
        """Obtiene el contexto de la sesión."""
        session = self.get_session(telefono)
        if session and session.get("contexto_json"):
            return json.loads(session["contexto_json"])
        return {}

    # ---------- memoria del cliente ----------

    def get_historial_cliente(self, telefono: str) -> dict:
        """Obtiene el historial del cliente."""
        return query_one(
            "SELECT * FROM historial_cliente WHERE telefono = ?",
            (telefono,)
        ) or {}

    def save_historial(self, telefono: str, nombre: str = None, datos: dict = None):
        """Guarda/actualiza el historial del cliente."""
        existente = self.get_historial_cliente(telefono)

        if existente:
            # Actualizar
            updates = ["updated_at = CURRENT_TIMESTAMP", "ultimo_mensaje = CURRENT_TIMESTAMP"]
            params = []

            if nombre:
                updates.append("nombre = ?")
                params.append(nombre)

            if datos:
                if "boletas_compradas" in datos:
                    updates.append("boletas_compradas = ?")
                    params.append(datos["boletas_compradas"])
                if "deuda_pendiente" in datos:
                    updates.append("deuda_pendiente = ?")
                    params.append(datos["deuda_pendiente"])

            params.append(telefono)
            execute(
                f"UPDATE historial_cliente SET {', '.join(updates)} WHERE telefono = ?",
                tuple(params)
            )
        else:
            # Crear
            execute(
                """INSERT INTO historial_cliente (telefono, nombre, ultimo_mensaje)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (telefono, nombre or "Sin nombre")
            )

    def guardar_mensaje(self, telefono: str, mensaje: str, tipo: str = "entrada"):
        """Guarda el mensaje en el historial de conversación."""
        execute(
            "INSERT INTO conversaciones (telefono, mensaje, tipo) VALUES (?, ?, ?)",
            (telefono, mensaje, tipo)
        )

    # ---------- lógica de procesamiento ----------

    def procesar(self, telefono: str, mensaje: str, es_admin: bool = False) -> str:
        """Procesa el mensaje y retorna la respuesta."""
        # Guardar mensaje en historial
        self.guardar_mensaje(telefono, mensaje, "entrada")

        # Si es admin, procesar comando
        if es_admin:
            return self.procesar_admin(telefono, mensaje)

        # Obtener sesión
        session = self.get_session(telefono)
        estado = session.get("estado", "inicio")
        contexto = json.loads(session.get("contexto_json", "{}"))

        # Revisar historial del cliente
        historial = self.get_historial_cliente(telefono)

        # Procesar según estado
        respuesta = self._procesar_por_estado(
            telefono, mensaje, estado, contexto, historial
        )

        # Guardar respuesta en historial
        self.guardar_mensaje(telefono, respuesta, "salida")

        return respuesta

    def _procesar_por_estado(
        self, telefono: str, mensaje: str, estado: str,
        contexto: dict, historial: dict
    ) -> str:
        """Procesa el mensaje según el estado actual."""

        # Normalizar mensaje
        msg = mensaje.strip().lower()

        # Comandos globales
        if msg in ["hola", "buenas", "buenos días", "buenas tardes", "buenas noches", "inicio", "start"]:
            return self._iniciar_conversacion(telefono)

        if msg in ["disponibles", "ver números", "numeros disponibles"]:
            return self._mostrar_disponibles(telefono)

        if msg in ["mis boletas", "mi compra", "mis tickets"]:
            return self._mostrar_boletas_cliente(telegrafo)

        if msg in ["ayuda", "help", "comandos"]:
            return messages.ayuda()

        # Flujo según estado
        if estado == "inicio":
            return self._estado_inicio(telefono, mensaje, contexto)

        elif estado == "pidiendo_numero":
            return self._estado_pidiendo_numero(telefono, mensaje, contexto)

        elif estado == "pidiendo_separacion":
            return self._estado_pidiendo_separacion(telefono, mensaje, contexto)

        elif estado == "pidiendo_datos":
            return self._estado_pidiendo_datos(telefono, mensaje, contexto)

        elif estado == "pidiendo_comprobante":
            return self._estado_pidiendo_comprobante(telefono, mensaje, contexto)

        elif estado == "separacion_pendiente":
            return self._estado_separacion_pendiente(telefono, mensaje, contexto)

        # Si no entiende, notificar al admin
        telegram.notificar_no_entiendo(telegrafo, mensaje)
        return messages.no_entiendo()

    # ---------- estados ----------

    def _iniciar_conversacion(self, telefono: str) -> str:
        """Inicia una nueva conversación."""
        # Obtener rifa activa
        rifa = get_active_rifa()
        if not rifa:
            return messages.rifa_no_activa()

        # Resetear sesión
        self.update_session(telefono, "pidiendo_numero", {"rifa_id": rifa["id"]})

        # Saludar con memoria
        historial = self.get_historial_cliente(telefono)
        if historial and historial.get("nombre"):
            nombre = historial["nombre"]
            return (
                f"¡Buenas, {nombre}! 👋\n\n"
                f"¿Tiene algún número en especial en mente?"
            )

        return messages.bienvenida(rifa["nombre"], rifa["precio_boleta"])

    def _estado_inicio(self, telefono: str, mensaje: str, contexto: dict) -> str:
        """Estado inicial - preguntar número."""
        return self._iniciar_conversacion(telefono)

    def _estado_pidiendo_numero(self, telefono: str, mensaje: str, contexto: dict) -> str:
        """El cliente indica qué número quiere."""
        # Extraer número de 4 dígitos
        numeros = re.findall(r'\b(\d{4})\b', mensaje)

        if numeros:
            numero = numeros[0]
            return self._verificar_y_proponer_numero(telefono, numero, contexto)

        # Si dice "disponibles" o similar
        msg = mensaje.strip().lower()
        if "disponibles" in msg or "ver" in msg or "muestrame" in msg or "dame" in msg:
            return self._mostrar_disponibles(telefono)

        # Si escribió un número en formato diferente
        if mensaje.strip().isdigit():
            numero = mensaje.strip()[:4].zfill(4)
            return self._verificar_y_proponer_numero(telefono, numero, contexto)

        # No entendió
        return (
            f"Por favor, indique el número de 4 dígitos que desea comprar.\n"
            f"O si lo prefiere, escriba *disponibles* para ver la lista."
        )

    def _verificar_y_proponer_numero(
        self, telefono: str, numero: str, contexto: dict
    ) -> str:
        """Verifica si el número está disponible."""
        rifa_id = contexto.get("rifa_id")
        if not rifa_id:
            return messages.rifa_no_activa()

        # Buscar boleta
        boleta = query_one(
            "SELECT * FROM boletas WHERE rifa_id = ? AND numero = ? AND estado = 'disponible'",
            (rifa_id, numero)
        )

        if boleta:
            # Disponible - pedir separación
            rifa = query_one("SELECT * FROM rifas WHERE id = ?", (rifa_id,))
            self.update_session(
                telefono, "pidiendo_separacion",
                {"rifa_id": rifa_id, "numero": numero, "precio": rifa["precio_boleta"],
                 "separacion_min": rifa["precio_separacion_min"]}
            )
            return messages.pedir_separacion(
                numero, rifa["precio_boleta"], rifa["precio_separacion_min"]
            )
        else:
            # No disponible - ofrecer cercanos
            return self._ofrecer_numeros_cercanos(telefono, numero, rifa_id)

    def _ofrecer_numeros_cercanos(
        self, telefono: str, numero: str, rifa_id: int
    ) -> str:
        """Ofrece números cercanos al solicitado."""
        # Buscar disponibles cerca del número
        num_int = int(numero)
        cercanos = []

        for offset in range(-5, 6):
            if offset == 0:
                continue
            candidate = str(num_int + offset).zfill(4)
            if int(candidate) >= 0 and int(candidate) <= 9999:
                disp = query_one(
                    "SELECT id FROM boletas WHERE rifa_id = ? AND numero = ? AND estado = 'disponible'",
                    (rifa_id, candidate)
                )
                if disp:
                    cercanos.append(candidate)

        if cercanos:
            self.update_session(
                telefono, "pidiendo_numero",
                {"rifa_id": rifa_id, "cercanos": cercanos}
            )
            return messages.oferta_numeros_cercanos(numero, cercanos)

        return "Lo siento, no hay números disponibles cerca de ese."

    def _mostrar_disponibles(self, telefono: str) -> str:
        """Muestra un random de 20 boletas disponibles."""
        rifa = get_active_rifa()
        if not rifa:
            return messages.rifa_no_activa()

        disponibles = query(
            "SELECT numero FROM boletas WHERE rifa_id = ? AND estado = 'disponible' ORDER BY RANDOM() LIMIT 20",
            (rifa["id"],)
        )

        numeros = [d["numero"] for d in disponibles]
        return messages.numeros_disponibles_aleatorios(numeros)

    def _estado_pidiendo_separacion(
        self, telefono: str, mensaje: str, contexto: dict
    ) -> str:
        """El cliente indica cuánto quiere separar."""
        # Extraer monto
        montos = re.findall(r'[\d,]+', mensaje.replace(".", "").replace(",", ""))
        if not montos:
            return "¿Cuánto desea separar? Indique el monto en números."

        monto = int(montos[0].replace(",", ""))

        # Validar mínimo
        separacion_min = contexto.get("separacion_min", 5000)
        if monto < separacion_min:
            return f"El monto mínimo para separar es ${separacion_min:,}. ¿Cuánto desea separar?"

        precio = contexto.get("precio", 0)
        resto = precio - monto

        # Guardar en contexto
        contexto["monto_separacion"] = monto
        contexto["monto_resta"] = resto

        # Obtener rifa para fecha
        rifa = query_one("SELECT * FROM rifas WHERE id = ?", (contexto["rifa_id"],))

        self.update_session(telefono, "pidiendo_datos", contexto)

        # Confirmar y pedir datos
        fecha = rifa["fecha_sorteo"] if rifa else "próximamente"
        return messages.confirmacion_separacion(
            contexto["numero"], monto, resto, fecha
        )

    def _estado_pidiendo_datos(
        self, telefono: str, mensaje: str, contexto: dict
    ) -> str:
        """El cliente envía nombre y teléfono."""
        # Guardar nombre
        nombre = mensaje.strip()
        contexto["nombre_cliente"] = nombre

        # Obtener o crear cliente
        cliente_id = get_or_create_cliente(telefono, nombre)

        # Actualizar historial
        self.save_historial(telefono, nombre)

        # Pedir comprobante
        self.update_session(telefono, "pidiendo_comprobante", contexto)

        # Enviar datos de pago (por ahora genéricos)
        datos_pago = {
            "banco": "Banco de Bogotá",
            "cuenta": "123456789",
            "tipo": "ahorros"
        }
        return messages.datos_pago(datos_pago)

    def _estado_pidiendo_comprobante(
        self, telefono: str, mensaje: str, contexto: dict
    ) -> str:
        """Espera el comprobante de pago."""
        # Aquí se maneja cuando llega la imagen
        # Por ahora solo confirmar recibo
        return messages.comprobante_recibido("abono")

    def _estado_separacion_pendiente(
        self, telefono: str, mensaje: str, contexto: dict
    ) -> str:
        """El cliente tiene una separación pendiente."""
        msg = mensaje.strip().lower()

        if msg in ["si", "sí", "dame", "envíame", "pagos", "datos"]:
            datos_pago = {
                "banco": "Banco de Bogotá",
                "cuenta": "123456789",
                "tipo": "ahorros"
            }
            return messages.datos_pago(datos_pago)

        return "¿Ya realizó el pago? Envíe el comprobante cuando lo tenga."

    def _mostrar_boletas_cliente(self, telefono: str) -> str:
        """Muestra las boletas del cliente."""
        cliente = query_one("SELECT id FROM clientes WHERE telefono = ?", (telefono,))
        if not cliente:
            return "No tiene boletas registradas."

        boletas = query(
            """SELECT numero, estado, monto_separacion
               FROM boletas
               WHERE cliente_id = ?
               ORDER BY created_at DESC""",
            (cliente["id"],)
        )

        if not boletas:
            return "No tiene boletas registradas."

        return messages.estado_cliente(boletas)

    # ---------- comandos admin ----------

    def procesar_admin(self, telefono: str, mensaje: str) -> str:
        """Procesa comandos de administrador."""
        msg = mensaje.strip().upper()

        # APROBAR
        if msg.startswith("APROBAR"):
            return self._cmd_aprobar(mensaje)

        # RECHAZAR
        if msg.startswith("RECHAZAR"):
            return self._cmd_rechazar(mensaje)

        # LISTA / VENTAS
        if msg in ["LISTA", "VENTAS"]:
            return self._cmd_lista()

        # DISPONIBLES
        if msg == "DISPONIBLES":
            return self._cmd_disponibles()

        return "Comando no reconocido. Use: APROBAR <num>, RECHAZAR <num>, LISTA, DISPONIBLES"

    def _cmd_aprobar(self, mensaje: str) -> str:
        """Aprueba el pago de una boleta."""
        numeros = re.findall(r'\b(\d{4})\b', mensaje)
        if not numeros:
            return "Indique el número de boleta: APROBAR 1234"

        numero = numeros[0]
        # Aquí iría la lógica de aprobación
        return f"Boleta {numero} aprobada ✓"

    def _cmd_rechazar(self, mensaje: str) -> str:
        """Rechaza el pago de una boleta."""
        numeros = re.findall(r'\b(\d{4})\b', mensaje)
        if not numeros:
            return "Indique el número de boleta: RECHAZAR 1234"

        numero = numeros[0]
        # Aquí iría la lógica de rechazo
        return f"Boleta {numero} rechazada"

    def _cmd_lista(self) -> str:
        """Lista las ventas."""
        boletas = query(
            """SELECT b.numero, c.nombre, b.estado, b.monto_separacion
               FROM boletas b
               LEFT JOIN clientes c ON b.cliente_id = c.id
               WHERE b.estado IN ('separada', 'vendida')
               ORDER BY b.updated_at DESC
               LIMIT 10"""
        )

        if not boletas:
            return "No hay ventas aún."

        msg = "📋 *Últimas ventas*\n\n"
        for b in boletas:
            estado = "✓" if b["estado"] == "vendida" else "⏳"
            msg += f"{estado} {b['numero']} - {b['nombre'] or 'Sin nombre'}\n"

        return msg

    def _cmd_disponibles(self) -> str:
        """Muestra cuántas disponibles."""
        rifa = get_active_rifa()
        if not rifa:
            return "No hay rifa activa."

        disp = query_one(
            "SELECT COUNT(*) as total FROM boletas WHERE rifa_id = ? AND estado = 'disponible'",
            (rifa["id"],)
        )

        return f"Disponibles: {disp['total']:,} de {rifa['total_boletas']:,}"


# Instancia global
bot = ChatBot()
