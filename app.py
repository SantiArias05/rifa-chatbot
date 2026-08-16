"""Servidor principal - Flask + Webhook + Admin."""
import logging
import requests
from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from pathlib import Path

from config import Config
from database import init_db, query, query_one, execute, get_active_rifa
from webhook import webhook_bp
from telegram import telegram

# Configurar logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Registrar blueprint del webhook
app.register_blueprint(webhook_bp)


@app.route("/")
def index():
    """Página principal."""
    return {
        "status": "running",
        "service": "Chatbot Rifas",
        "version": "2.0"
    }


@app.route("/health")
def health():
    """Health check."""
    return {"status": "healthy"}


# ---------- Panel Admin ----------

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Chatbot Rifas</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="30">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 20px; font-size: 28px; }
        .refresh-note { color: #aaa; text-align: center; font-size: 12px; margin-bottom: 20px; }
        
        .stats { display: flex; gap: 20px; margin-bottom: 30px; }
        .stat { 
            flex: 1; background: white; padding: 25px; border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: center;
        }
        .stat h3 { margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .stat .number { font-size: 48px; font-weight: bold; }
        .stat.disponibles .number { color: #3498db; }
        .stat.separadas .number { color: #f39c12; }
        .stat.vendidas .number { color: #27ae60; }
        
        .rifa-info { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;
        }
        .rifa-info h2 { margin: 0 0 10px 0; font-size: 24px; }
        .rifa-info p { margin: 5px 0; opacity: 0.9; }
        
        .seccion { background: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .seccion h2 { margin: 0 0 20px 0; color: #2c3e50; display: flex; align-items: center; gap: 10px; }
        .seccion h2 .count { 
            background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; 
        }
        .seccion.separadas h2 .count { background: #f39c12; }
        .seccion.vendidas h2 .count { background: #27ae60; }
        .seccion.disponibles h2 .count { background: #3498db; }
        
        .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 15px; }
        
        .card {
            border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px;
            transition: all 0.3s ease; background: white;
        }
        .card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        
        .card.separada { border-color: #f39c12; background: #fffbf0; }
        .card.vendida { border-color: #27ae60; background: #f0fff4; }
        .card.disponible { border-color: #3498db; background: #f0f8ff; }
        
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .card-header .boleta { font-size: 32px; font-weight: bold; color: #2c3e50; }
        .card-header .estado { 
            padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase;
        }
        .estado.separada { background: #f39c12; color: white; }
        .estado.vendida { background: #27ae60; color: white; }
        .estado.disponible { background: #3498db; color: white; }
        
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #888; font-size: 13px; }
        .info-value { color: #2c3e50; font-weight: 600; }
        
        .pago-info { 
            background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; 
            border-left: 4px solid #667eea;
        }
        .pago-info.abono { border-left-color: #f39c12; }
        .pago-info.completo { border-left-color: #27ae60; }
        
        .monto-grande { font-size: 26px; font-weight: bold; color: #2c3e50; }
        .monto-resta { color: #e74c3c; font-weight: bold; }
        
        .comprobante { 
            display: inline-block; background: #667eea; color: white; 
            padding: 8px 16px; border-radius: 6px; font-size: 13px; margin-top: 10px;
        }
        
        .acciones { display: flex; gap: 10px; margin-top: 15px; }
        .btn { 
            flex: 1; padding: 12px 20px; border: none; border-radius: 8px; 
            cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s;
        }
        .btn-approve { background: #27ae60; color: white; }
        .btn-approve:hover { background: #219a52; }
        .btn-reject { background: #e74c3c; color: white; }
        .btn-reject:hover { background: #c0392b; }
        .btn-whatsapp { background: #25d366; color: white; }
        .btn-whatsapp:hover { background: #20b655; }
        
        .empty { text-align: center; padding: 40px; color: #888; }
        
        /* Lista de disponibles */
        .disponibles-grid { display: flex; flex-wrap: wrap; gap: 8px; }
        .disp-num { 
            background: #e8f4f8; color: #3498db; padding: 8px 14px; 
            border-radius: 6px; font-weight: 600; font-size: 14px;
        }
        
        /* Modal */
        .modal {
            display: none; position: fixed; z-index: 1000; left: 0; top: 0;
            width: 100%; height: 100%; background-color: rgba(0,0,0,0.7);
        }
        .modal-content {
            background-color: white; margin: 5% auto; padding: 30px;
            border-radius: 15px; width: 90%; max-width: 600px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.5);
        }
        .modal-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #eee;
        }
        .modal-header h2 { margin: 0; color: #2c3e50; }
        .close-modal { font-size: 28px; font-weight: bold; color: #aaa; cursor: pointer; }
        .close-modal:hover { color: #333; }
        
        .detalle-seccion { margin-bottom: 20px; }
        .detalle-seccion h3 { 
            color: #667eea; margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase;
        }
        .detalle-row { 
            display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;
        }
        .detalle-row:last-child { border-bottom: none; }
        .detalle-label { color: #888; }
        .detalle-value { font-weight: 600; color: #2c3e50; }
        
        .transaccion-item {
            background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .transaccion-item.separacion { border-left-color: #f39c12; }
        .transaccion-item.pago { border-left-color: #27ae60; }
        
        .loading { text-align: center; padding: 40px; color: #888; }
        
        /* Historial */
        .historial { max-height: 300px; overflow-y: auto; }
        .hist-item { 
            display: flex; align-items: center; gap: 15px; padding: 12px; 
            border-bottom: 1px solid #eee;
        }
        .hist-item:last-child { border-bottom: none; }
        .hist-icon { font-size: 20px; }
        .hist-details { flex: 1; }
        .hist-details strong { color: #2c3e50; }
        .hist-details span { color: #888; font-size: 13px; }
        .hist-time { color: #aaa; font-size: 12px; }
        
        @media (max-width: 768px) {
            .stats { flex-direction: column; }
            .card-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Panel de Administracion - Chatbot Rifas</h1>
        <p class="refresh-note">Se actualiza automaticamente cada 30 segundos</p>

        <div class="stats">
            <div class="stat disponibles">
                <h3>Disponibles</h3>
                <div class="number">{{ disponibles }}</div>
            </div>
            <div class="stat separadas">
                <h3>Separadas (Abono)</h3>
                <div class="number">{{ separadas }}</div>
            </div>
            <div class="stat vendidas">
                <h3>Vendidas (Pagado)</h3>
                <div class="number">{{ vendidas }}</div>
            </div>
            </div>
  
        <!-- BOTON CREAR RIFA -->
        <div style="margin-bottom: 20px;">
            <button onclick="document.getElementById('modalCrearRifa').style.display='block'" 
                style="padding: 15px 30px; background: #9b59b6; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">
                + Crear Nueva Rifa
            </button>
        </div>
        
        <!-- PESTAÑAS DE RIFAS -->
        {% if rifas|length > 1 %}
        <div style="display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap;">
            {% for r in rifas %}
            <a href="/admin?rifa_id={{ r.id }}" 
                style="padding: 10px 20px; background: {% if r.id == rifa.id %}#667eea{% else %}#2d3748{% endif %}; color: white; text-decoration: none; border-radius: 8px 8px 0 0;">
                {{ r.nombre }} ({{ r.total_boletas }})
            </a>
            {% endfor %}
        </div>
        {% endif %}
 
        {% if rifa %}
        <div class="rifa-info">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2>{{ rifa.nombre }}</h2>
                    <p><strong>Precio:</strong> ${{ rifa.precio_boleta|default(0)|int }} | 
                       <strong>Total boletas:</strong> {{ rifa.total_boletas }} |
                       <strong>Sorteo:</strong> {{ rifa.fecha_sorteo or 'Por definir' }}</p>
                </div>
                <div style="display: flex; gap: 10px;">
                    {% if rifa.estado != 'finalizada' %}
                    <a href="/admin/finalizar-rifa?id={{ rifa.id }}" 
                        onclick="return confirm('¿Finalizar rifa {{ rifa.nombre }}? Ya no se podrán vender más boletas.')"
                        style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block;">
                        ✅ Finalizar Rifa
                    </a>
                    {% else %}
                    <span style="padding: 10px 20px; background: #7f8c8d; color: white; border-radius: 8px;">
                        🔒 Rifa Terminada
                    </span>
                    {% endif %}
                    <a href="/admin/eliminar-rifa?id={{ rifa.id }}" 
                        onclick="return confirm('¿Eliminar rifa {{ rifa.nombre }}? Esto no se puede deshacer.')"
                        style="padding: 10px 20px; background: #e74c3c; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block;">
                        🗑️ Eliminar
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
         
        <!-- ESTADÍSTICAS -->
        {% if rifa %}
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #3498db, #2980b9); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: bold;">{{ disponibles }}</div>
                <div style="font-size: 14px; opacity: 0.9;">Disponibles</div>
            </div>
            <div style="background: linear-gradient(135deg, #f39c12, #e67e22); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: bold;">{{ separadas }}</div>
                <div style="font-size: 14px; opacity: 0.9;">Separadas</div>
            </div>
            <div style="background: linear-gradient(135deg, #27ae60, #1e8449); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: bold;">{{ vendidas }}</div>
                <div style="font-size: 14px; opacity: 0.9;">Vendidas</div>
            </div>
            <div style="background: linear-gradient(135deg, #9b59b6, #8e44ad); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: bold;">${{ ganancias|int }}</div>
                <div style="font-size: 14px; opacity: 0.9;">Ganancias</div>
            </div>
        </div>
        {% endif %}
  
        <!-- BUSCADOR -->
        <div class="seccion">
            <form method="get" action="/admin" style="display: flex; gap: 10px;">
                <input type="text" name="buscar" placeholder="Buscar por numero, nombre o telefono..." 
                    value="{{ buscar or '' }}"
                    style="flex: 1; padding: 15px; border: 2px solid #667eea; border-radius: 8px; font-size: 18px;">
                <button type="submit" style="padding: 15px 30px; background: #667eea; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">Buscar</button>
                {% if buscar %}
                <a href="/admin" style="padding: 15px 20px; background: #e74c3c; color: white; border: none; border-radius: 8px; font-size: 16px; text-decoration: none; display: inline-block;">Limpiar</a>
                {% endif %}
            </form>
            {% if buscar %}
            <p style="margin: 10px 0 0 0; color: #667eea;">Resultados para: "{{ buscar }}" ({{ boletas|length }} encontradas)</p>
            {% endif %}
            
            <h2>BOLETAS <span id="contador-boletas" class="count">{{ boletas|length }}</span></h2>
            
            <table id="tabla-boletas" style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #667eea; color: white;">
                        <th style="padding: 12px; text-align: left;">Boleta</th>
                        <th style="padding: 12px; text-align: left;">Estado</th>
                        <th style="padding: 12px; text-align: left;">Cliente</th>
                        <th style="padding: 12px; text-align: left;">Telefono</th>
                        <th style="padding: 12px; text-align: left;">Fecha</th>
                        <th style="padding: 12px; text-align: left;">Accion</th>
                    </tr>
                </thead>
                <tbody>
                    {% for b in boletas %}
                    <tr data-estado="{{ b.estado }}" data-telefono="{{ b.cliente_telefono or '' }}" data-nombre="{{ b.cliente_nombre or '' }}" style="border-bottom: 1px solid #eee; {% if b.estado == 'reservada' %}background: #fffbf0;{% elif b.estado == 'vendida' %}background: #f0fff4;{% endif %}">
                        <td style="padding: 12px; font-weight: bold; font-size: 16px;">{{ b.numero }}</td>
                        <td style="padding: 12px;">
                            <span style="padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;
                                {% if b.estado == 'reservada' %}background: #f39c12; color: white;
                                {% elif b.estado == 'vendida' %}background: #27ae60; color: white;
                                {% else %}background: #3498db; color: white;{% endif %}">
                                {% if b.estado == 'reservada' %}RESERVADA{% elif b.estado == 'vendida' %}VENDIDA{% else %}DISPONIBLE{% endif %}
                            </span>
                        </td>
                        <td style="padding: 12px;">{{ b.cliente_nombre or '—' }}</td>
                        <td style="padding: 12px;">{{ b.cliente_telefono or '—' }}</td>
                        <td style="padding: 12px; font-size: 12px;">
                            {% if b.estado == 'vendida' and b.fecha_pago %}{{ b.fecha_pago[:10] }}
                            {% elif b.estado == 'reservada' and b.fecha_separacion %}{{ b.fecha_separacion[:10] }}
                            {% else %}—{% endif %}
                        </td>
                        <td style="padding: 12px;">
                            {% if b.estado == 'reservada' %}
                            <button onclick="aprobarBoleta('{{ b.numero }}')" style="background: #27ae60; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">APROBAR</button>
                            <button onclick="rechazarBoleta('{{ b.numero }}')" style="background: #e74c3c; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">RECHAZAR</button>
                            {% elif b.estado == 'vendida' and b.cliente_telefono %}
                            <a href="https://wa.me/{{ b.cliente_telefono|replace('+','') }}" target="_blank" style="background: #25d366; color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px;">WHATSAPP</a>
                            {% else %}
                            —
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- HISTORIAL -->
        {% if transacciones %}
        <div class="seccion">
            <h2>Historial Reciente</h2>
            <div class="historial">
                {% for t in transacciones %}
                <div class="hist-item">
                    <div class="hist-icon">
                        {% if t.tipo == 'separacion' %}📝
                        {% elif t.tipo == 'pago_confirmado' %}✅
                        {% elif t.tipo == 'cancelacion' %}❌
                        {% else %}📋{% endif %}
                    </div>
                    <div class="hist-details">
                        <strong>{{ t.numero or '—' }}</strong> - {{ t.detalle or t.tipo }}
                        <br><span>{{ t.nombre or '' }} {{ t.telefono or '' }}</span>
                    </div>
                    <div class="hist-time">{{ t.created_at[:16] if t.created_at else '' }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Modal para detalles de boleta -->
    <div id="modalBoleta" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitulo">Boleta</h2>
                <span class="close-modal" onclick="cerrarModal()">&times;</span>
            </div>
            <div id="modalBody">
                <div class="loading">Cargando...</div>
            </div>
        </div>
    </div>
    
    <!-- Modal para crear rifa -->
    <div id="modalCrearRifa" class="modal">
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h2>Crear Nueva Rifa</h2>
                <span class="close-modal" onclick="document.getElementById('modalCrearRifa').style.display='none'">&times;</span>
            </div>
            <div style="padding: 20px;">
                <form action="/admin/crear-rifa" method="POST">
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Nombre de la rifa:</label>
                        <input type="text" name="nombre" required 
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px;"
                            placeholder="Ej: Rifa Navidad 2024">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Precio por boleta ($):</label>
                        <input type="number" name="precio" required 
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px;"
                            placeholder="Ej: 20000">
                    </div>
                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <div style="flex: 1;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Desde:</label>
                            <input type="number" name="desde" required 
                                style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px;"
                                placeholder="Ej: 0" value="0">
                        </div>
                        <div style="flex: 1;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Hasta:</label>
                            <input type="number" name="hasta" required 
                                style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px;"
                                placeholder="Ej: 99" value="99">
                        </div>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Fecha del sorteo:</label>
                        <input type="date" name="fecha_sorteo" 
                            style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px;">
                    </div>
                    <button type="submit" 
                        style="width: 100%; padding: 15px; background: #9b59b6; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">
                        Crear Rifa
                    </button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
    function aprobar(numero) {
        event.stopPropagation();
        if (!confirm('Confirmar el pago de la boleta ' + numero + '?')) return;
        fetch('/admin/aprobar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({numero: numero})
        }).then(r => r.json()).then(d => {
            alert(d.message);
            location.reload();
        });
    }
    function rechazar(numero) {
        event.stopPropagation();
        if (!confirm('Rechazar la boleta ' + numero + '? Se liberara para otro cliente.')) return;
        fetch('/admin/rechazar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({numero: numero})
        }).then(r => r.json()).then(d => {
            alert(d.message);
            location.reload();
        });
    }
    
    function verBoleta(numero) {
        document.getElementById('modalBoleta').style.display = 'block';
        document.getElementById('modalTitulo').textContent = 'Boleta ' + numero;
        document.getElementById('modalBody').innerHTML = '<div class="loading">Cargando detalles...</div>';
        
        fetch('/admin/boleta/' + numero)
            .then(r => r.json())
            .then(data => {
                if (!data.success) {
                    document.getElementById('modalBody').innerHTML = '<p>' + data.message + '</p>';
                    return;
                }
                
                const b = data.boleta;
                const transacciones = data.transacciones || [];
                
                let html = '';
                
                // Estado y numero
                html += '<div class="detalle-seccion">';
                html += '<h3>Informacion</h3>';
                html += '<div class="detalle-row"><span class="detalle-label">Numero</span><span class="detalle-value">' + b.numero + '</span></div>';
                html += '<div class="detalle-row"><span class="detalle-label">Estado</span><span class="detalle-value" style="color: ' + (b.estado === 'vendida' ? '#27ae60' : '#f39c12') + '">' + b.estado.toUpperCase() + '</span></div>';
                html += '<div class="detalle-row"><span class="detalle-label">Precio</span><span class="detalle-value">$' + (b.precio || 0) + '</span></div>';
                html += '</div>';
                
                // Datos del cliente
                html += '<div class="detalle-seccion">';
                html += '<h3>Datos del Cliente</h3>';
                html += '<div class="detalle-row"><span class="detalle-label">Nombre</span><span class="detalle-value">' + (b.cliente_nombre || '—') + '</span></div>';
                html += '<div class="detalle-row"><span class="detalle-label">Telefono</span><span class="detalle-value">' + (b.cliente_telefono || '—') + '</span></div>';
                html += '</div>';
                
                // Informacion de pago
                if (b.estado === 'separada' || b.estado === 'vendida') {
                    html += '<div class="detalle-seccion">';
                    html += '<h3>Pago</h3>';
                    html += '<div class="detalle-row"><span class="detalle-label">Abono</span><span class="detalle-value">$' + (b.monto_separacion || 0) + '</span></div>';
                    html += '<div class="detalle-row"><span class="detalle-label">Resta</span><span class="detalle-value">$' + (b.monto_restante || 0) + '</span></div>';
                    html += '<div class="detalle-row"><span class="detalle-label">Fecha Separacion</span><span class="detalle-value">' + (b.fecha_separacion || '—') + '</span></div>';
                    if (b.fecha_pago) {
                        html += '<div class="detalle-row"><span class="detalle-label">Fecha Pago</span><span class="detalle-value">' + b.fecha_pago + '</span></div>';
                    }
                    if (b.comprobante_path) {
                        html += '<div class="detalle-row"><span class="detalle-label">Comprobante</span><span class="detalle-value">Si</span></div>';
                    }
                    html += '</div>';
                }
                
                // Historial de transacciones
                if (transacciones.length > 0) {
                    html += '<div class="detalle-seccion">';
                    html += '<h3>Historial</h3>';
                    transacciones.forEach(t => {
                        let icon = '📋';
                        let clase = '';
                        if (t.tipo === 'separacion') { icon = '📝'; clase = 'separacion'; }
                        if (t.tipo === 'pago_confirmado') { icon = '✅'; clase = 'pago'; }
                        if (t.tipo === 'cancelacion') { icon = '❌'; clase = ''; }
                        
                        html += '<div class="transaccion-item ' + clase + '">';
                        html += icon + ' <strong>' + t.tipo + '</strong> - ' + (t.detalle || '');
                        html += '<br><small style="color:#888">' + (t.created_at || '') + '</small>';
                        html += '</div>';
                    });
                    html += '</div>';
                }
                
                // Acciones
                if (b.estado === 'separada') {
                    html += '<div class="detalle-seccion">';
                    html += '<div class="acciones">';
                    html += '<button class="btn btn-approve" onclick="aprobar(\'' + b.numero + '\')">CONFIRMAR PAGO</button>';
                    html += '<button class="btn btn-reject" onclick="rechazar(\'' + b.numero + '\')">RECHAZAR</button>';
                    html += '</div>';
                    html += '</div>';
                }
                
                document.getElementById('modalBody').innerHTML = html;
            })
            .catch(err => {
                document.getElementById('modalBody').innerHTML = '<p>Error al cargar los datos</p>';
            });
    }
    
    function cerrarModal() {
        document.getElementById('modalBoleta').style.display = 'none';
    }
    
    // Cerrar modal al hacer click fuera
    window.onclick = function(event) {
        const modal = document.getElementById('modalBoleta');
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
    
    // Aprobar boleta desde la tabla
    function aprobarBoleta(numero) {
        if (!confirm('Aprobar la boleta ' + numero + '? Se notificara al cliente por WhatsApp.')) return;
        
        var rifaId = {{ rifa.id if rifa else 'null' }};
        
        fetch('/admin/aprobar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({numero: numero, rifa_id: rifaId})
        })
        .then(r => r.json())
        .then(d => {
            alert(d.message);
            setTimeout(() => location.reload(), 500);
        })
        .catch(err => {
            alert('Error al aprobar');
        });
    }
    
    // Rechazar boleta desde la tabla
    function rechazarBoleta(numero) {
        if (!confirm('Rechazar la boleta ' + numero + '? Se liberara para otro cliente.')) return;
        
        fetch('/admin/rechazar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({numero: numero})
        })
        .then(r => r.json())
        .then(d => {
            alert(d.message);
            setTimeout(() => location.reload(), 500);
        })
        .catch(err => {
            alert('Error al rechazar');
        });
    }
    
    // Crear nueva rifa
    var formCrearRifa = document.getElementById('formCrearRifa');
    if (formCrearRifa) {
        formCrearRifa.addEventListener('submit', function(e) {
            e.preventDefault();
            
            var nombre = document.querySelector('input[name="nombre"]').value;
            var precio = parseInt(document.querySelector('input[name="precio"]').value);
            var desde = parseInt(document.querySelector('input[name="desde"]').value);
            var hasta = parseInt(document.querySelector('input[name="hasta"]').value);
            var fecha_sorteo = document.querySelector('input[name="fecha_sorteo"]').value;
            
            var debugInfo = document.getElementById('debug-info');
            debugInfo.style.display = 'block';
            debugInfo.innerHTML = 'Enviando...<br>nombre: ' + nombre + '<br>precio: ' + precio + '<br>desde: ' + desde + '<br>hasta: ' + hasta;
            
            if (desde > hasta) {
                alert('El número "desde" debe ser menor o igual que "hasta"');
                return;
            }
            
            var data = {
                nombre: nombre,
                precio: precio,
                desde: desde,
                hasta: hasta,
                fecha_sorteo: fecha_sorteo
            };
            
            console.log('Enviando data:', data);
            
            fetch('/admin/crear-rifa', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(function(r) { 
                console.log('Status:', r.status); 
                return r.json(); 
            })
            .then(function(d) {
                console.log('Respuesta:', d);
                if (d.success) {
                    alert(d.message);
                    document.getElementById('modalCrearRifa').style.display = 'none';
                    location.reload();
                } else {
                    alert('Error: ' + d.message);
                }
            })
            .catch(function(err) {
                console.error('Error:', err);
                alert('Error al crear rifa: ' + err);
            });
        });
    } else {
        console.error('No se encontró el formulario formCrearRifa');
    }
    
    // Eliminar rifa
    function eliminarRifa(rifaId, rifaNombre) {
        if (!confirm('¿Estás seguro de eliminar la rifa "' + rifaNombre + '"? Esto eliminará todas las boletas asociadas.')) {
            return;
        }
        
        fetch('/admin/eliminar-rifa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({rifa_id: rifaId})
        })
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                alert(d.message);
                location.reload();
            } else {
                alert('Error: ' + d.message);
            }
        })
        .catch(err => {
            alert('Error al eliminar rifa');
        });
    }
    
    </script>
</body>
</html>
"""


@app.route("/admin")
def admin_panel():
    """Panel de administración web."""
    # Obtener parámetro de búsqueda
    buscar = request.args.get('buscar', '').strip()
    rifa_id_seleccionada = request.args.get('rifa_id', None)
    
    # Obtener todas las rifas
    rifas = query("SELECT * FROM rifas ORDER BY id DESC")
    
    # Si hay rifa_id en URL, usar esa; sino usar la activa
    if rifa_id_seleccionada:
        rifa = query_one("SELECT * FROM rifas WHERE id = ?", (rifa_id_seleccionada,))
    else:
        rifa = get_active_rifa()
    
    # Si ninguna rifa seleccionada, usar la primera
    if not rifa and rifas:
        rifa = rifas[0]
    
    # Si no hay rifas, igual renderizamos la página con datos vacíos
    # Las stats serán 0 si no hay rifa
    if not rifa:
        disp = {"c": 0}
        sep = {"c": 0}
        vend = {"c": 0}
        ganancias = {"total": 0}
        boletas = []
    else:
        # Stats
        disp = query_one(
            "SELECT COUNT(*) as c FROM boletas WHERE rifa_id = ? AND estado = 'disponible'",
            (rifa["id"],)
        )
        sep = query_one(
            "SELECT COUNT(*) as c FROM boletas WHERE rifa_id = ? AND estado = 'separada'",
            (rifa["id"],)
        )
        vend = query_one(
            "SELECT COUNT(*) as c FROM boletas WHERE rifa_id = ? AND estado = 'vendida'",
            (rifa["id"],)
        )
        
        # Calcular ganancias (solo de boletas vendidas)
        ganancias = query_one("""
            SELECT 
                COALESCE(SUM(precio), 0) as total
            FROM boletas 
            WHERE rifa_id = ? AND estado = 'vendida'
        """, (rifa["id"],))

        # Filtrar boletas si hay búsqueda
        if buscar:
            boletas = query("""
                SELECT 
                    b.numero, b.estado, b.precio, b.monto_separacion, b.monto_restante,
                    b.fecha_separacion, b.fecha_pago, b.updated_at,
                    c.nombre as cliente_nombre, c.telefono as cliente_telefono
                FROM boletas b
                LEFT JOIN clientes c ON b.cliente_id = c.id
                WHERE b.rifa_id = ?
                AND (b.numero LIKE ? OR c.nombre LIKE ? OR c.telefono LIKE ?)
                ORDER BY 
                    CASE b.estado 
                        WHEN 'separada' THEN 1 
                        WHEN 'vendida' THEN 2 
                        ELSE 3 
                    END,
                    b.numero
            """, (rifa["id"], f'%{buscar}%', f'%{buscar}%', f'%{buscar}%'))
        else:
            boletas = query("""
                SELECT 
                    b.numero, b.estado, b.precio, b.monto_separacion, b.monto_restante,
                    b.fecha_separacion, b.fecha_pago, b.updated_at,
                    c.nombre as cliente_nombre, c.telefono as cliente_telefono
                FROM boletas b
                LEFT JOIN clientes c ON b.cliente_id = c.id
                WHERE b.rifa_id = ?
                ORDER BY 
                    CASE b.estado 
                        WHEN 'separada' THEN 1 
                        WHEN 'vendida' THEN 2 
                        ELSE 3 
                    END,
                    b.numero
            """, (rifa["id"],))

    return render_template_string(
        ADMIN_TEMPLATE,
        rifa=rifa,
        rifas=rifas,
        disponibles=disp["c"],
        separadas=sep["c"],
        vendidas=vend["c"],
        ganancias=ganancias["total"] if ganancias else 0,
        boletas=boletas,
        buscar=buscar
    )


@app.route("/admin/aprobar", methods=["POST"])
def admin_aprobar():
    """Aprueba una boleta."""
    data = request.json
    numero = data.get("numero", "")
    rifa_id = data.get("rifa_id", None)

    # Usar rifa_id si se provee, sino usar la activa
    if rifa_id:
        rifa = query_one("SELECT * FROM rifas WHERE id = ?", (rifa_id,))
    else:
        rifa = get_active_rifa()
    
    if not rifa:
        return jsonify({"success": False, "message": "No hay rifa"})

    # Buscar boleta
    boleta = query_one(
        "SELECT * FROM boletas WHERE rifa_id = ? AND numero = ?",
        (rifa["id"], numero)
    )

    if not boleta:
        return jsonify({"success": False, "message": "Boleta no encontrada"})

    # Actualizar estado
    execute(
        """UPDATE boletas
           SET estado = 'vendida', fecha_pago = CURRENT_TIMESTAMP,
               monto_restante = 0, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (boleta["id"],)
    )

    # Registrar transacción
    execute(
        """INSERT INTO transacciones (boleta_id, rifa_id, tipo, detalle)
           VALUES (?, ?, 'pago_confirmado', 'Aprobado por admin')""",
        (boleta["id"], rifa["id"])
    )

    # Notificar al cliente por WhatsApp
    if boleta.get("cliente_id"):
        cliente = query_one("SELECT telefono, nombre FROM clientes WHERE id = ?", (boleta["cliente_id"],))
        if cliente and cliente.get("telefono"):
            from whatsapp import WhatsAppClient
            wa = WhatsAppClient()
            wa.enviar_mensaje(
                cliente["telefono"],
                f"¡Su pago ha sido confirmado! \n\n"
                f"Boleta: {numero}\n"
                f"¡Mucha suerte! 🍀"
            )

    # Notificar al admin por Telegram
    try:
        from telegram import telegram
        resultado = telegram.notificar_pago({
            "boletas": [numero],
            "nombre": cliente.get("nombre", "Sin nombre") if boleta.get("cliente_id") else "Sin nombre",
            "telefono": cliente.get("telefono", "") if boleta.get("cliente_id") else "",
            "monto": boleta.get("precio", 0),
            "tipo": "completo"
        })
        print(f"[APP] Notificación Telegram: {resultado}")
    except Exception as e:
        print(f"[APP] Error Telegram: {e}")

    return jsonify({"success": True, "message": f"Boleta {numero} aprobada y cliente notificado"})


@app.route("/admin/rechazar", methods=["POST"])
def admin_rechazar():
    """Rechaza una boleta."""
    data = request.json
    numero = data.get("numero", "")

    rifa = get_active_rifa()
    if not rifa:
        return jsonify({"success": False, "message": "No hay rifa activa"})

    # Buscar y liberar boleta
    execute(
        """UPDATE boletas
           SET estado = 'disponible', cliente_id = NULL, monto_separacion = 0,
               monto_restante = 0, updated_at = CURRENT_TIMESTAMP
           WHERE rifa_id = ? AND numero = ?""",
        (rifa["id"], numero)
    )

    return jsonify({"success": True, "message": f"Boleta {numero} rechazada y liberada"})


@app.route("/admin/boleta/<numero>")
def admin_ver_boleta(numero):
    """Ver detalles de una boleta específica."""
    rifa = get_active_rifa()
    if not rifa:
        return jsonify({"success": False, "message": "No hay rifa activa"})

    boleta = query_one("""
        SELECT b.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono
        FROM boletas b
        LEFT JOIN clientes c ON b.cliente_id = c.id
        WHERE b.rifa_id = ? AND b.numero = ?
    """, (rifa["id"], numero))

    if not boleta:
        return jsonify({"success": False, "message": "Boleta no encontrada"})

    # Historial de transacciones de esta boleta
    transacciones = query("""
        SELECT * FROM transacciones
        WHERE boleta_id = ?
        ORDER BY created_at DESC
    """, (boleta["id"],))

    return jsonify({
        "success": True,
        "boleta": boleta,
        "transacciones": transacciones
    })


# ---------- Jobs (tareas programadas) ----------

@app.route("/job/liberar-expiradas")
def job_liberar_expiradas():
    """Libera las separaciones expiradas."""
    from database import liberar_expiradas
    count = liberar_expiradas()
    return jsonify({"liberadas": count})


@app.route("/admin/crear-rifa", methods=["POST"])
def admin_crear_rifa():
    """Crea una nueva rifa con sus boletas."""
    try:
        # Aceptar JSON o formulario
        if request.is_json:
            data = request.json
            nombre = data.get("nombre", "").strip()
            precio = data.get("precio", 0)
            desde = data.get("desde", 0)
            hasta = data.get("hasta", 99)
            fecha_sorteo = data.get("fecha_sorteo", "")
        else:
            # Formulario tradicional
            nombre = request.form.get("nombre", "").strip()
            precio = int(request.form.get("precio", 0))
            desde = int(request.form.get("desde", 0))
            hasta = int(request.form.get("hasta", 99))
            fecha_sorteo = request.form.get("fecha_sorteo", "")
        
        if not nombre or precio <= 0:
            return jsonify({"success": False, "message": "Datos inválidos"})
        
        if desde < 0 or hasta > 9999 or desde > hasta:
            return jsonify({"success": False, "message": "Rango de números inválido"})
        
        cantidad = hasta - desde + 1
        
        # Crear la rifa
        rifa_id = execute("""
            INSERT INTO rifas (nombre, precio_boleta, total_boletas, fecha_sorteo, estado)
            VALUES (?, ?, ?, ?, 'activa')
        """, (nombre, precio, cantidad, fecha_sorteo))
        
        # Crear las boletas desde "desde" hasta "hasta"
        for i in range(desde, hasta + 1):
            numero = str(i).zfill(4)
            execute("""
                INSERT INTO boletas (rifa_id, numero, precio, estado)
                VALUES (?, ?, ?, 'disponible')
            """, (rifa_id, numero, precio))
        
        # Actualizar config rifa_activa_id
        execute("""
            INSERT OR REPLACE INTO config (clave, valor)
            VALUES ('rifa_activa_id', ?)
        """, (str(rifa_id),))
        
        # Si es JSON, responder con JSON; si no, redirigir
        if request.is_json:
            return jsonify({
                "success": True, 
                "message": f"Rifa '{nombre}' creada con boletas {str(desde).zfill(4)} a {str(hasta).zfill(4)} ({cantidad} boletas)"
            })
        else:
            return redirect("/admin?msg=ok")
        
    except Exception as e:
        if request.is_json:
            return jsonify({"success": False, "message": str(e)})
        else:
            return redirect("/admin?msg=error")


@app.route("/admin/eliminar-rifa", methods=["POST", "GET"])
def admin_eliminar_rifa():
    """Elimina una rifa y sus boletas."""
    try:
        # Aceptar POST (JSON) o GET con parametro
        if request.is_json:
            data = request.json
            rifa_id = data.get("rifa_id")
        else:
            rifa_id = request.args.get("id")
        
        if not rifa_id:
            if request.is_json:
                return jsonify({"success": False, "message": "ID de rifa requerido"})
            return redirect("/admin?msg=error")
        
        # Eliminar boletas primero
        execute("DELETE FROM boletas WHERE rifa_id = ?", (rifa_id,))
        
        # Eliminar rifa
        execute("DELETE FROM rifas WHERE id = ?", (rifa_id,))
        
        # Si era la activa, limpiar config
        config_actual = query_one("SELECT valor FROM config WHERE clave = 'rifa_activa_id'")
        if config_actual and str(config_actual["valor"]) == str(rifa_id):
            execute("DELETE FROM config WHERE clave = 'rifa_activa_id'")
        
        if request.is_json:
            return jsonify({
                "success": True, 
                "message": "Rifa eliminada correctamente"
            })
        else:
            return redirect("/admin?msg=deleted")
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/admin/finalizar-rifa", methods=["GET"])
def admin_finalizar_rifa():
    """Finaliza una rifa (la marca como terminada)."""
    try:
        rifa_id = request.args.get("id")
        
        if not rifa_id:
            return redirect("/admin?msg=error")
        
        # Marcar rifa como terminada
        execute("UPDATE rifas SET estado = 'finalizada' WHERE id = ?", (rifa_id,))
        
        return redirect("/admin?msg=finalizada")
        
    except Exception as e:
        return redirect("/admin?msg=error")


@app.route("/admin/estadisticas", methods=["GET"])
def admin_estadisticas():
    """Muestra estadísticas de la rifa actual."""
    try:
        rifa_id = request.args.get("rifa_id")
        
        # Obtener rifa
        if rifa_id:
            rifa = query_one("SELECT * FROM rifas WHERE id = ?", (rifa_id,))
        else:
            rifa = get_active_rifa()
        
        if not rifa:
            return redirect("/admin?msg=error")
        
        # Calcular estadísticas
        stats = query_one("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'disponible' THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN estado = 'separada' THEN 1 ELSE 0 END) as separadas,
                SUM(CASE WHEN estado = 'vendida' THEN 1 ELSE 0 END) as vendidas,
                SUM(CASE WHEN estado = 'vendida' THEN precio ELSE 0 END) as ganancias_vendidas,
                SUM(CASE WHEN estado = 'separada' THEN monto_separacion ELSE 0 END) as ganancias_separadas
            FROM boletas WHERE rifa_id = ?
        """, (rifa["id"],))
        
        # Calcular ganancias potenciales (todas las boletas)
        ganancias_maximas = rifa["precio_boleta"] * rifa["total_boletas"]
        
        return jsonify({
            "success": True,
            "rifa": {
                "nombre": rifa["nombre"],
                "precio": rifa["precio_boleta"],
                "total": rifa["total_boletas"]
            },
            "stats": {
                "disponibles": stats["disponibles"] or 0,
                "separadas": stats["separadas"] or 0,
                "vendidas": stats["vendidas"] or 0,
                "ganancias_vendidas": stats["ganancias_vendidas"] or 0,
                "ganancias_separadas": stats["ganancias_separadas"] or 0,
                "ganancias_totales": (stats["ganancias_vendidas"] or 0) + (stats["ganancias_separadas"] or 0),
                "ganancias_maximas": ganancias_maximas
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# ---------- Telegram Bot ----------
@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """Recibe callbacks de los botones de Telegram."""
    try:
        data = request.json
        
        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback.get("data", "")
            message = callback.get("message", {})
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            
            # Responder al callback
            from whatsapp import WhatsAppClient
            
            if callback_data.startswith("aprobar_"):
                numero = callback_data.replace("aprobar_", "")
                
                rifa = get_active_rifa()
                if rifa:
                    # Buscar boleta
                    boleta = query_one(
                        "SELECT * FROM boletas WHERE rifa_id = ? AND numero = ?",
                        (rifa["id"], numero)
                    )
                    
                    if boleta and boleta.get("cliente_id"):
                        # Actualizar estado
                        execute(
                            """UPDATE boletas
                               SET estado = 'vendida', fecha_pago = CURRENT_TIMESTAMP,
                                   updated_at = CURRENT_TIMESTAMP
                               WHERE id = ?""",
                            (boleta["id"],)
                        )
                        
                        # Notificar al cliente por WhatsApp
                        cliente = query_one("SELECT telefono, nombre FROM clientes WHERE id = ?", (boleta["cliente_id"],))
                        if cliente and cliente.get("telefono"):
                            wa = WhatsAppClient()
                            wa.enviar_mensaje(
                                cliente["telefono"],
                                f"¡Pago confirmado!\n\nBoleta: {numero}\n¡Mucha suerte! 🍀"
                            )
                        
                        # Responder en Telegram
                        respuesta = f"✅ Boleta {numero} APROBADA"
                    else:
                        respuesta = f"❌ Boleta {numero} no encontrada o ya procesada"
                else:
                    respuesta = "No hay rifa activa"
                    
            elif callback_data.startswith("rechazar_"):
                numero = callback_data.replace("rechazar_", "")
                
                rifa = get_active_rifa()
                if rifa:
                    execute(
                        """UPDATE boletas
                           SET estado = 'disponible', cliente_id = NULL,
                               updated_at = CURRENT_TIMESTAMP
                           WHERE rifa_id = ? AND numero = ?""",
                        (rifa["id"], numero)
                    )
                    respuesta = f"❌ Boleta {numero} RECHAZADA y liberada"
                else:
                    respuesta = "No hay rifa activa"
            else:
                respuesta = "Comando no reconocido"
            
            # Enviar respuesta al callback
            if chat_id:
                requests.post(
                    f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                    json={
                        "callback_query_id": callback.get("id"),
                        "text": respuesta,
                        "show_alert": True
                    }
                )
                
                # Actualizar el mensaje original
                requests.post(
                    f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/editMessageText",
                    json={
                        "chat_id": chat_id,
                        "message_id": message.get("message_id"),
                        "text": respuesta
                    }
                )
        
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Error en telegram webhook: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- Main ----------

if __name__ == "__main__":
    # Inicializar DB
    logger.info("Inicializando base de datos...")
    init_db()

    # Iniciar servidor
    logger.info(f"Iniciando servidor en http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
