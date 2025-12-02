import requests
from datetime import datetime
from collections import defaultdict
from typing import Any

# ====================================================================
# --- 1. CONFIGURACIÓN E INTERRUPTOR GLOBAL DE DATOS ---
# ====================================================================

# INTERRUPTOR: Cambia a False cuando tu API REST esté lista para usar.
USAR_MOCK_DATA = False

# Base URL corregida (asume que tu servlet está en /crm-backend/api/login)
BASE_URL = "http://localhost:8080/crm-backend/api"

# --- GESTIÓN DE SESIÓN Y AUTENTICACIÓN ---
GLOBAL_SESSION = requests.Session()
GLOBAL_USER_INFO = {"logueado": False, "rol": None, "nombre": None}

# --- MOCK DATA GLOBAL (Se mantiene para la simulación de CRUD) ---
MOCK_COMERCIALES = [
    {"comercial_id": 1, "nombre": "Ana García", "email": "ana@xtart.com", "telefono": "601", "rol": "admin", "username": "ana"},
    {"comercial_id": 2, "nombre": "Juan Pérez", "email": "juan@xtart.com", "telefono": "602", "rol": "comercial", "username": "juan"},
    {"comercial_id": 3, "nombre": "Laura Soto", "email": "laura@xtart.com", "telefono": "603", "rol": "comercial", "username": "laura"},
]
MOCK_CLIENTES = [
    {"cliente_id": 1, "nombre": "Cliente Uno", "apellidos": "S.L.", "edad": 35, "email": "c1@e.com", "telefono": "911", "comercial_id": 1},
    {"cliente_id": 2, "nombre": "Cliente Dos", "apellidos": "S.A.", "edad": 40, "email": "c2@e.com", "telefono": "912", "comercial_id": 2},
    {"cliente_id": 3, "nombre": "Cliente Tres", "apellidos": "Corp.", "edad": 28, "email": "c3@e.com", "telefono": "913", "comercial_id": 1},
]
MOCK_FACTURAS_ESTADISTICAS = [
    {"factura_id": "F-001", "cliente_id": 1, "comercial_id": 1, "fecha_emision": "2025-01-05", "estado": "pagada", "total": "1500.00€"},
    {"factura_id": "F-002", "cliente_id": 2, "comercial_id": 2, "fecha_emision": "2025-01-15", "estado": "pendiente", "total": "500.50€"},
    {"factura_id": "F-003", "cliente_id": 3, "comercial_id": 1, "fecha_emision": "2025-01-25", "estado": "pagada", "total": "2500.00€"},
    {"factura_id": "F-004", "cliente_id": 1, "comercial_id": 1, "fecha_emision": "2025-02-01", "estado": "pagada", "total": "3000.00€"},
    {"factura_id": "F-008", "cliente_id": 2, "comercial_id": 2, "fecha_emision": "2025-03-20", "estado": "pagada", "total": "2500.00€"},
]
MOCK_SECCIONES = [ {"seccion_id": 1, "nombre": "Electrónica"}, {"seccion_id": 2, "nombre": "Hogar"}, ]
MOCK_PRODUCTOS = [ {"producto_id": 101, "nombre": "Laptop X1", "precio_base": "1200.00", "plazas_disponibles": 50, "seccion_id": 1}, {"producto_id": 102, "nombre": "Aspiradora V2", "precio_base": "300.00", "plazas_disponibles": 150, "seccion_id": 2}, ]


def _simular_obtener_entidad(entidad):
    if entidad == 'clientes': return MOCK_CLIENTES
    elif entidad == 'comerciales': return MOCK_COMERCIALES
    elif entidad == 'secciones': return MOCK_SECCIONES
    elif entidad == 'productos': return MOCK_PRODUCTOS
    elif entidad == 'facturas': return MOCK_FACTURAS_ESTADISTICAS
    return []

def _limpiar_total_factura(total_str):
    try: return float(str(total_str).replace('€', '').replace(',', ''))
    except ValueError: return 0.0
        
def _normalizar_datos_desde_api(datos: Any) -> Any:
    # Función para convertir claves de camelCase (Java) a snake_case (Python)
    if isinstance(datos, dict):
        new_dict = {}
        key_mapping = {
            'clienteId': 'cliente_id', 'comercialId': 'comercial_id', 'productoId': 'producto_id',
            'seccionId': 'seccion_id', 'facturaId': 'factura_id', 'passwordHash': 'password_hash',
            'fechaEmision': 'fecha_emision',
        }
        
        for key, value in datos.items():
            new_key = key_mapping.get(key, key)
            new_dict[new_key] = _normalizar_datos_desde_api(value)
        return new_dict
    elif isinstance(datos, list):
        return [_normalizar_datos_desde_api(item) for item in datos]
    return datos


# ====================================================================
# --- 2. FUNCIÓN DE UTILIDAD CENTRAL (CONEXIÓN REAL) ---
# ====================================================================

def _manejar_peticion(metodo, endpoint, data = None, params = None):
    url = f"{BASE_URL}/{endpoint}"
    
    #  Lógica de MOCK total para el CRUD 
    if USAR_MOCK_DATA and metodo != 'GET':
          # Simulación de éxito para todas las operaciones de escritura/borrado
          return True
    if USAR_MOCK_DATA and metodo == 'GET':
          # Simulación de GETs
          entidad = endpoint.split('/')[0] # Extraer 'comerciales', 'clientes', etc.
          return _simular_obtener_entidad(entidad)
    
    #  Lógica REAL
    try:
        if metodo == 'GET':
            response = GLOBAL_SESSION.get(url, params=params)
        # ⚠️ Nota: Usamos 'json=data' para el CRUD, no 'data=data'.
        # Solo el login usa 'data='
        elif metodo == 'POST':
            response = GLOBAL_SESSION.post(url, json=data)
        elif metodo == 'PUT':
            response = GLOBAL_SESSION.put(url, json=data)
        elif metodo == 'DELETE':
            response = GLOBAL_SESSION.delete(url)
        else:
            raise ValueError(f"Método HTTP no soportado: {metodo}")
            
        response.raise_for_status()
        
        if response.text and response.status_code != 204:
            json_data = response.json()
            return _normalizar_datos_desde_api(json_data)
        
        return True
        
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response.text else "Detalle no disponible."
        print(f"ERROR HTTP {e.response.status_code} en {metodo} {url}: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR DE CONEXIÓN en {metodo} {url}: {e}")
        return None

# ====================================================================
# --- 3. AUTENTICACIÓN Y CRUD BASE ---
# ====================================================================

#  FUNCIÓN DE LOGIN QUE INTERACTUA CON LOGINSERVLET (/api/login)
def login_autenticacion(username, password):
    """
    Intenta autenticar al usuario usando el endpoint /api/login del Servlet.
    Devuelve datos de usuario (diccionario) si es exitoso, False si falla.
    """
    global GLOBAL_USER_INFO
    endpoint = "login"
    url = f"{BASE_URL}/{endpoint}"
    
    # :
    # 1. Creamos LOS DATOS PROPORCIONADOS  como diccionario
    datos_formulario = {"username": username, "password": password}
    
    GLOBAL_USER_INFO["logueado"] = False
    
    # --- MOCK DE LOGIN (Para desarrollo sin Java encendido) ---
    if USAR_MOCK_DATA:
        # 
        #Definimos las credenciales mock
        if (username.lower() == "admin" and password == "1234"):
            GLOBAL_USER_INFO["logueado"] = True
            GLOBAL_USER_INFO["rol"] = "admin"
            GLOBAL_USER_INFO["nombre"] = "Administrador"
            return {"username": username, "nombre": "Administrador", "rol": "admin"}
        return False
        
    # CONEXIÓN REAL AL SERVLET¡¡
    try:
        # Usamos 'data' para enviar form-urlencoded, compatible con request.getParameter()
        response = GLOBAL_SESSION.post(url, data=datos_formulario)
        
        if response.status_code == 200:
            # Esperamos: ROL,NOMBRE (ej: admin,David López)
            respuesta_texto = response.text
            if ',' in respuesta_texto:
                rol, nombre = respuesta_texto.split(',', 1)
                
                GLOBAL_USER_INFO["logueado"] = True
                GLOBAL_USER_INFO["rol"] = rol.lower()
                GLOBAL_USER_INFO["nombre"] = nombre.strip()
                
                return {"username": username, "nombre": nombre.strip(), "rol": rol.lower()}
        
        # Si falla es por 401 Unauthorized o 400 Bad Request
        return False
        
    except requests.exceptions.RequestException:
        # Falla de conexión
        return None
        
# -----------------------------------------------------------
# 4. COMERCIALES (/api/comerciales) 
# -----------------------------------------------------------

def obtener_comerciales():
    if USAR_MOCK_DATA: return _simular_obtener_entidad("comerciales")
    return _manejar_peticion('GET', 'comerciales') or []

def obtener_comercial_por_id(id):
    if USAR_MOCK_DATA: return next((c.copy() for c in MOCK_COMERCIALES if c['comercial_id'] == int(id)), None)
    return _manejar_peticion('GET', f'comerciales/{id}')

def crear_comercial(datos):
    if USAR_MOCK_DATA: return True
    return _manejar_peticion('POST', 'comerciales', data=datos)

def actualizar_comercial(id, datos):
    if USAR_MOCK_DATA: return True
    return _manejar_peticion('PUT', f'comerciales/{id}', data=datos)

def eliminar_comercial(id):
    if USAR_MOCK_DATA: return True
    return _manejar_peticion('DELETE', f'comerciales/{id}') is True

# --------------------------------------------------------------------
# 5. CLIENTES (/api/clientes)
# --------------------------------------------------------------------

def obtener_clientes(comercial_id = None):
    if USAR_MOCK_DATA and comercial_id is None: return _simular_obtener_entidad("clientes")
    params = {'comercialId': comercial_id} if comercial_id is not None else None
    return _manejar_peticion('GET', 'clientes', params=params) or []

def obtener_cliente_por_id(id):
    if USAR_MOCK_DATA:
        id_buscado = int(id)
        return next((c.copy() for c in MOCK_CLIENTES if c['cliente_id'] == id_buscado), None)
    return _manejar_peticion('GET', f'clientes/{id}')

def crear_cliente(datos):
    if USAR_MOCK_DATA: return True # Simulación de creación
    return _manejar_peticion('POST', 'clientes', data=datos)

def actualizar_cliente(id, datos):
    if USAR_MOCK_DATA: return True # Simulación de actualización
    return _manejar_peticion('PUT', f'clientes/{id}', data=datos)

def eliminar_cliente(id):
    if USAR_MOCK_DATA: return True # Simulación de eliminación
    return _manejar_peticion('DELETE', f'clientes/{id}') is True

# --------------------------------------------------------------------
# 6. SECCIONES (/api/secciones)
# --------------------------------------------------------------------

def obtener_secciones():
    if USAR_MOCK_DATA: return _simular_obtener_entidad("secciones")
    return _manejar_peticion('GET', 'secciones') or []

def obtener_seccion_por_id(id):
    if USAR_MOCK_DATA: return next((s.copy() for s in MOCK_SECCIONES if s['seccion_id'] == int(id)), None)
    return _manejar_peticion('GET', f'secciones/{id}')

def crear_seccion(datos):
    if USAR_MOCK_DATA: return True # Simulación de creación
    return _manejar_peticion('POST', 'secciones', data=datos)

def actualizar_seccion(id, datos):
    if USAR_MOCK_DATA: return True # Simulación de actualización
    return _manejar_peticion('PUT', f'secciones/{id}', data=datos)

def eliminar_seccion(id):
    if USAR_MOCK_DATA: return True # Simulación de eliminación
    return _manejar_peticion('DELETE', f'secciones/{id}') is True

# --------------------------------------------------------------------
# 7. PRODUCTOS (/api/productos)
# --------------------------------------------------------------------

def obtener_productos(seccion_id = None):
    if USAR_MOCK_DATA and seccion_id is None: return _simular_obtener_entidad("productos")
    params = {'seccionId': seccion_id} if seccion_id is not None else None
    return _manejar_peticion('GET', 'productos', params=params) or []

def obtener_producto_por_id(id):
    if USAR_MOCK_DATA: return next((p.copy() for p in MOCK_PRODUCTOS if p['producto_id'] == int(id)), None)
    return _manejar_peticion('GET', f'productos/{id}')

def crear_producto(datos):
    if USAR_MOCK_DATA: return True # Simulación de creación
    return _manejar_peticion('POST', 'productos', data=datos)

def actualizar_producto(id, datos):
    if USAR_MOCK_DATA: return True # Simulación de actualización
    return _manejar_peticion('PUT', f'productos/{id}', data=datos)

def eliminar_producto(id):
    if USAR_MOCK_DATA: return True # Simulación de eliminación
    return _manejar_peticion('DELETE', f'productos/{id}') is True

# --------------------------------------------------------------------
# 8. FACTURAS (/api/facturas)
# --------------------------------------------------------------------

def obtener_facturas(cliente_id = None, comercial_id = None):
    if USAR_MOCK_DATA and cliente_id is None and comercial_id is None: return _simular_obtener_entidad("facturas")
    params = {}
    if cliente_id is not None: params['clienteId'] = cliente_id
    if comercial_id is not None: params['comercialId'] = comercial_id
    return _manejar_peticion('GET', 'facturas', params=params) or []

def obtener_factura_por_id(id):
    if USAR_MOCK_DATA: return next((f.copy() for f in MOCK_FACTURAS_ESTADISTICAS if f['factura_id'] == str(id)), None)
    return _manejar_peticion('GET', f'facturas/{id}')

def crear_factura(datos):
    if USAR_MOCK_DATA: return True # Simulación de creación
    return _manejar_peticion('POST', 'facturas', data=datos)

def actualizar_factura(id, datos):
    if USAR_MOCK_DATA: return True # Simulación de actualización
    return _manejar_peticion('PUT', f'facturas/{id}', data=datos)

def eliminar_factura(id):
    if USAR_MOCK_DATA: return True # Simulación de eliminación
    return _manejar_peticion('DELETE', f'facturas/{id}') is True

# --------------------------------------------------------------------
# 9 y 10. INFORMES Y ESTADÍSTICAS
# --------------------------------------------------------------------
# Funciones que usan la API real o MOCK para el dashboard.

def arrancar_informe(tipo):
    if USAR_MOCK_DATA: return True # Simulación
    if tipo not in ['clientes', 'facturas', 'completo']: return None
    return _manejar_peticion('GET', f'informes/{tipo}')

def obtener_estadisticas_api():
    if USAR_MOCK_DATA: return {'peticionesTotales': 100, 'fallos': 5} # Simulación
    return _manejar_peticion('GET', 'estadisticas')

def exportar_estadisticas(nombre_archivo = None):
    if USAR_MOCK_DATA: return True # Simulación
    params = {'file': nombre_archivo} if nombre_archivo else None
    return _manejar_peticion('POST', 'estadisticas', params=params) is True

def resetear_estadisticas():
    if USAR_MOCK_DATA: return True # Simulación
    return _manejar_peticion('DELETE', f'estadisticas') is True

# --- Funciones de Dashboard ---

def obtener_facturas_para_estadisticas(): return obtener_facturas()
def obtener_comerciales_para_estadisticas(): return obtener_comerciales()

def get_invoice_counts():
    facturas = obtener_facturas_para_estadisticas()
    counts = defaultdict(int)
    for factura in facturas: counts[factura.get('estado', 'desconocido')] += 1
    return {'pagada': counts.get('pagada', 0), 'pendiente': counts.get('pendiente', 0), 'cancelada': counts.get('cancelada', 0)}

def get_ingresos_mensuales():
    facturas = obtener_facturas_para_estadisticas()
    ingresos_por_mes = defaultdict(float)
    for factura in facturas:
        total = _limpiar_total_factura(str(factura.get('total', '0.00€')))
        fecha_str = factura.get('fecha_emision')
        if fecha_str and total > 0:
            try:
                # Usar split('T') para manejar el formato DE JAVA
                fecha_dt = datetime.strptime(fecha_str.split('T')[0], "%Y-%m-%d")
                mes = fecha_dt.strftime("%b %Y")
                ingresos_por_mes[mes] += total
            except: continue
    periodos_ordenados = sorted(ingresos_por_mes.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
    valores = [ingresos_por_mes[p] for p in periodos_ordenados]
    return periodos_ordenados, valores

def get_ranking_comerciales():
    comerciales = obtener_comerciales_para_estadisticas()
    facturas = obtener_facturas_para_estadisticas()
    nombres_comerciales = {c['comercial_id']: c['nombre'] for c in comerciales if 'comercial_id' in c}
    ingresos_por_id = defaultdict(float)
    for factura in facturas:
        comercial_id = factura.get('comercial_id')
        total = _limpiar_total_factura(str(factura.get('total', '0.00€')))
        if comercial_id in nombres_comerciales and total > 0:
            ingresos_por_id[comercial_id] += total
    ranking = []
    for c in comerciales:
        c_id = c.get('comercial_id')
        total = ingresos_por_id.get(c_id, 0.0)
        ranking.append({"nombre": c.get('nombre', "Desconocido"), "ingresos": total})
    ranking.sort(key=lambda x: x['ingresos'], reverse=True)
    return ranking

# FUNCIÓN: CLIENTES POR COMERCIAL PARA ESTADISTICASS
def get_clientes_por_comercial():
    comerciales = obtener_comerciales_para_estadisticas()
    clientes = obtener_clientes()

    clientes_count_por_id = defaultdict(int)
    for cliente in clientes:
        comercial_id = cliente.get('comercial_id')
        if comercial_id:
            clientes_count_por_id[comercial_id] += 1

    ranking_clientes = []
    for c in comerciales:
        c_id = c.get('comercial_id')
        count = clientes_count_por_id.get(c_id, 0)
        ranking_clientes.append({"nombre": c.get('nombre', "Desconocido"), "clientes": count})
    
    ranking_clientes.sort(key=lambda x: x['clientes'], reverse=True)
    return ranking_clientes