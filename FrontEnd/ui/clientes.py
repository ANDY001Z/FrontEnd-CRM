from customtkinter import CTkFrame, CTkButton, CTkEntry, CTkFont
import tkinter.messagebox as tk_messagebox
import re
from api import api_client

# Importa componentes de tabla y modal
from components.data_table import DataTable
from components.modal_form import ModalForm 

# ====================================================================
# --- FUNCIONES DE VALIDACIÓN SIMPLIFICADAS ---
# ====================================================================

def validar_nombre_y_apellidos(valor):
    if not valor: return "Campo obligatorio.", False
    if len(valor) < 3: return "Mínimo 3 caracteres.", False
    return "✅", True

def validar_email(valor):
    if not valor: return "El email es obligatorio.", False
    if not re.match(r"[^@]+@[^@]+\.[^@]+", valor): return "Formato de email incorrecto.", False
    return "✅", True

def validar_edad(valor):
    if not valor: return "La edad es obligatoria.", False
    try:
        edad = int(valor)
        if not (18 <= edad <= 120): return "Edad debe ser entre 18 y 120.", False
        return "✅", True
    except ValueError:
        return "Debe ser un número entero.", False

def validar_telefono(valor):
    if not valor: return "El teléfono es obligatorio.", False
    if not re.match(r"[\d\s\-\.]{6,}", valor): return "Formato de teléfono incorrecto (mín. 6 dígitos).", False
    return "✅", True

def validar_direccion(valor):
    if not valor: return "La dirección es obligatoria.", False
    if len(valor) < 5: return "Dirección demasiado corta.", False
    return "✅", True


# ====================================================================
# --- VISTA COMPLETA CON CRUD DE CLIENTES ---
# ====================================================================

class VistaClientes(CTkFrame):
    # Frame que contiene la tabla de clientes y los controles CRUD.
    
    def __init__(self, maestro, **kwargs):
        super().__init__(maestro, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        # La fila 1 (tabla) debe expandirse
        self.grid_rowconfigure(1, weight=1) 
        
        # Variables de estado para la selección
        self.id_seleccionado = None
        self.cliente_en_edicion = None
        self.valor_celda_seleccionada = None

        self._inicializar_controles()
        self.cargar_datos_cliente()
        
    def _inicializar_controles(self):
        # Define el layout, input de búsqueda y botones.
        
        self.marco_control = CTkFrame(self, fg_color="transparent")
        self.marco_control.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="new")
        self.marco_control.grid_columnconfigure(0, weight=1)
        
        # Input de búsqueda (claro por defecto)
        CTkEntry(self.marco_control, 
                  placeholder_text="Buscar cliente...",
                  width=200, 
                  corner_radius=10 
        ).pack(side="left", padx=5)

        # Botones CRUD (Nuevo y Recargar)
        CTkButton(self.marco_control, text="Nuevo (C)", command=self._abrir_modal_crear_cliente).pack(side="right", padx=5)
        CTkButton(self.marco_control, text="Recargar", command=self.cargar_datos_cliente).pack(side="right", padx=5)

        # Inicialización de la Tabla de Datos
        columnas_cliente = ["cliente_id", "nombre", "apellidos", "edad", "email", "telefono", "direccion", "comercial_id"]
        self.tabla_datos = DataTable(self, columnas=columnas_cliente, al_seleccionar_item=self.al_seleccionar_fila)
        self.tabla_datos.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Marco de Acciones inferiores (Editar/Eliminar)
        self.marco_accion = CTkFrame(self, fg_color="transparent")
        self.marco_accion.grid(row=2, column=0, padx=10, pady=5, sticky="se")
        
        CTkButton(self.marco_accion, text="Editar (U)", command=self._abrir_modal_editar_cliente).pack(side="right", padx=5)
        CTkButton(self.marco_accion, text="Eliminar (D)", fg_color="red", command=self._confirmar_y_eliminar).pack(side="right", padx=5)
        
    # --- FUNCIONES DE LECTURA Y SELECCIÓN ---

    def cargar_datos_cliente(self):
        # Llama a la API para obtener y actualizar la tabla con los clientes.
        datos = api_client.obtener_clientes()
        if datos is None:
              tk_messagebox.showerror("Error de Conexión", "No se pudieron obtener los clientes. Verifique el servidor REST.")
              self.tabla_datos.actualizar_datos([])
        else:
              self.tabla_datos.actualizar_datos(datos)

    def al_seleccionar_fila(self, id_cliente):
        # Guarda el ID y el valor de la fila seleccionada.
        self.valor_celda_seleccionada = id_cliente
        
        try:
            self.id_seleccionado = int(id_cliente)
        except (ValueError, TypeError):
            self.id_seleccionado = None
            
        print(f"CRUD R: Cliente seleccionado: ID {self.id_seleccionado}")

    def _get_cliente_fields(self):
        # Define la configuración de los campos para el ModalForm.
        return [
            {'label': 'Nombre:', 'validator': validar_nombre_y_apellidos, 'key': 'nombre'},
            {'label': 'Apellidos:', 'validator': validar_nombre_y_apellidos, 'key': 'apellidos'},
            {'label': 'Email:', 'validator': validar_email, 'key': 'email'},
            {'label': 'Edad:', 'validator': validar_edad, 'key': 'edad'},
            {'label': 'Teléfono:', 'validator': validar_telefono, 'key': 'telefono'},
            {'label': 'Dirección:', 'validator': validar_direccion, 'key': 'direccion'},
        ]
        
    #   FUNCIONES CRUD (por funcionalidad) ---

    def _abrir_modal_crear_cliente(self):
        # Abre el modal para crear un cliente nuevo.
        ModalForm(self.master,
                  title="Crear Nuevo Cliente",
                  fields_config=self._get_cliente_fields(),
                  action_callback=self._crear_cliente_y_guardar)

    def _abrir_modal_editar_cliente(self):
        # Abre el modal de edición, busca el cliente por ID (o nombre como parche).
        if self.id_seleccionado is None and not self.valor_celda_seleccionada:
            tk_messagebox.showwarning("Advertencia", "Selecciona un cliente de la tabla para editar.")
            return

        try:
            # Lógica de búsqueda simplificada
            datos_api_lista = api_client.obtener_clientes()
            datos_actuales = None
            id_buscado = self.id_seleccionado
            
            if isinstance(datos_api_lista, list):
                if id_buscado is not None:
                    for cliente in datos_api_lista:
                        if cliente.get('cliente_id') == id_buscado:
                            datos_actuales = cliente
                            break
                
                if datos_actuales is None and self.valor_celda_seleccionada:
                    # Búsqueda por nombre (por si falla el ID)
                    nombre_o_texto_buscado = self.valor_celda_seleccionada
                    for cliente in datos_api_lista:
                        if cliente.get('nombre') == nombre_o_texto_buscado:
                            datos_actuales = cliente
                            self.id_seleccionado = cliente.get('cliente_id') # Actualiza ID
                            break

                if datos_actuales is None:
                    raise Exception(f"Cliente no encontrado en la lista de la API.")
            
            elif isinstance(datos_api_lista, dict):
                datos_actuales = datos_api_lista
            
            else:
                  raise Exception(f"API devolvió un formato no reconocido.")
            
            self.cliente_en_edicion = datos_actuales
            
            ModalForm(self.master,
                      title=f"Editar Cliente ID: {self.id_seleccionado}",
                      fields_config=self._get_cliente_fields(),
                      initial_data=datos_actuales,
                      action_callback=self._actualizar_cliente_y_guardar)
            
        except Exception as e:
            tk_messagebox.showerror("Error", f"No se pudo cargar el cliente: {e}")


    def _crear_cliente_y_guardar(self, data):
        # POST /api/clientes. Añade campos obligatorios (auth/FK) antes de enviar.
        try:
            # 1. Autenticación (Obligatorios para la API)
            data['username'] = data['email']
            data['passwordHash'] = "password123"

            # 2. Clave Foránea Comercial (Asignación por defecto)
            data['comercial'] = { "comercialId": 1 }
            
            # 3. Limpieza (evitar enviar IDs innecesarios)
            if 'comercial_id' in data:
                del data['comercial_id']

            resultado = api_client.crear_cliente(data)
            
            if resultado is not None and resultado is not False:
                tk_messagebox.showinfo("Éxito", f"Cliente '{data['nombre']}' CREADO en la BD.")
                self.cargar_datos_cliente()
                return True
            else:
                tk_messagebox.showerror("Error de API", "La API REST no pudo crear el cliente. Revise la consola.")
                return False

        except Exception as e:
            tk_messagebox.showerror("Error de Aplicación", f"Fallo interno al preparar el cliente: {e}")
            return False

    def _actualizar_cliente_y_guardar(self, data):
        # PUT /api/clientes/{id}. Reenvía campos obligatorios (auth/FK) con los datos previos.
        if not self.cliente_en_edicion:
              tk_messagebox.showerror("Error", "Error interno: El cliente no fue cargado para edición.")
              return False
        try:
            cliente_previo = self.cliente_en_edicion
            
            # 1. Crear diccionario final con datos editables
            data_final = {
                'nombre': data.get('nombre'),
                'apellidos': data.get('apellidos'),
                'edad': int(data.get('edad')),
                'email': data.get('email'),
                'telefono': data.get('telefono'),
                'direccion': data.get('direccion'), 
            }
            
            # 2. Reenviar campos NOT NULL (auth/FKs). ESTA ES LA CORRECCIÓN CRÍTICA.
            # Forzamos un valor por defecto si el servidor falló al cargarlo (si es None)
            data_final['username'] = cliente_previo.get('username') or data.get('email')
            data_final['passwordHash'] = cliente_previo.get('password_hash') or "password123" 
            
            comercial_data = cliente_previo.get('comercial')
            if comercial_data and isinstance(comercial_data, dict):
                data_final['comercial'] = {
                    "comercialId": comercial_data.get('comercial_id')
                }
            # Si el cliente previo NO tenía la FK completa, la asignamos por defecto
            elif not data_final.get('comercial'):
                  data_final['comercial'] = { "comercialId": 1 }
            
            # Incluye el ID para la actualización en Java/JPA
            if cliente_previo.get('cliente_id') is not None:
                data_final['clienteId'] = cliente_previo.get('cliente_id')
                
            if api_client.actualizar_cliente(self.id_seleccionado, data_final):
                tk_messagebox.showinfo("Éxito", f"Cliente ID {self.id_seleccionado} actualizado.")
                self.cargar_datos_cliente()
                return True
            else:
                tk_messagebox.showerror("Error de API", "Fallo al actualizar. El servidor rechazó la petición.")
                return False
                
        except Exception as e:
            tk_messagebox.showerror("Error de API", f"Fallo al actualizar el cliente: {e}")
            return False
            
    def _confirmar_y_eliminar(self):
        # Pide confirmación y llama a la API para eliminar el cliente seleccionado.
        if self.id_seleccionado is None:
            tk_messagebox.showwarning("Advertencia", "Selecciona un cliente para eliminar.")
            return

        confirmar = tk_messagebox.askyesno(
            title="Confirmar Eliminación",
            message=f"¿Está seguro de que desea eliminar el cliente con ID: {self.id_seleccionado}?"
        )

        if confirmar:
            try:
                if api_client.eliminar_cliente(self.id_seleccionado):
                    tk_messagebox.showinfo("Éxito", f"Cliente ID {self.id_seleccionado} eliminado.")
                    self.id_seleccionado = None
                    self.cargar_datos_cliente()
                else:
                    tk_messagebox.showerror("Error de API", "El servidor rechazó la eliminación.")
            except Exception as e:
                tk_messagebox.showerror("Error", f"No se pudo eliminar el cliente. {e}")