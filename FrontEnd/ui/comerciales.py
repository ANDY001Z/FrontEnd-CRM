from customtkinter import CTkFrame, CTkButton, CTkEntry, CTkLabel 
import tkinter.messagebox as tk_messagebox 
import re 
from typing import Optional, Dict, Any 

from components.data_table import DataTable
from components.modal_form import ModalForm 
from api import api_client

# --- FUNCIONES DE VALIDACIÓN ---
def validar_nombre(valor):
    if not valor: return "El nombre es obligatorio.", False
    if len(valor) < 3: return "El nombre debe tener al menos 3 caracteres.", False
    return "✅", True
def validar_email(valor):
    if not valor: return "El email es obligatorio.", False
    if not re.match(r"[^@]+@[^@]+\.[^@]+", valor): return "Formato de email incorrecto.", False
    return "✅", True
def validar_telefono(valor):
    if not valor: return "El teléfono es obligatorio.", False
    if not valor.isdigit() or len(valor) < 6: return "El teléfono debe ser solo números (min 6).", False
    return "✅", True

# --- VISTA COMPLETA CON CRUD DE COMERCIALES ---

class VistaComerciales(CTkFrame):
    # Frame que contiene la tabla de comerciales y los controles CRUD.
    def __init__(self, maestro, **kwargs):
        super().__init__(maestro, **kwargs)
        # Asegura que la tabla y controles se expandan
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        # Variables de estado para la selección/edición
        self.id_seleccionado: Optional[int] = None 
        self.comercial_en_edicion: Optional[Dict[str, Any]] = None 
        
        # Marco de control superior
        self.marco_control = CTkFrame(self, fg_color="transparent")
        self.marco_control.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="new")
        CTkEntry(self.marco_control, placeholder_text="Buscar comercial...").pack(side="left", padx=5)

        # Botones CRUD (Nuevo y Recargar)
        CTkButton(self.marco_control, text="Nuevo (C)", command=self._abrir_modal_crear_comercial).pack(side="right", padx=5)
        CTkButton(self.marco_control, text="Recargar", command=self.cargar_datos_comercial).pack(side="right", padx=5)

        # Inicialización de la Tabla de Datos
        columnas_comercial = ["comercial_id", "nombre", "email", "telefono", "rol", "username"] 
        self.tabla_datos = DataTable(self, columnas=columnas_comercial, al_seleccionar_item=self.al_seleccionar_fila)
        self.tabla_datos.grid(row=1, column=0, padx=10, pady=5, sticky="nsew") # La tabla se inserta aquí
        self.cargar_datos_comercial() # Llama a la carga inicial de datos
        
        # Marco de Acciones inferiores
        self.marco_accion = CTkFrame(self, fg_color="transparent")
        self.marco_accion.grid(row=2, column=0, padx=10, pady=5, sticky="se")
        
        # Botones Editar y Eliminar
        CTkButton(self.marco_accion, text="Editar (U)", command=self._abrir_modal_editar_comercial).pack(side="right", padx=5)
        CTkButton(self.marco_accion, text="Eliminar (D)", fg_color="red", command=self._confirmar_y_eliminar).pack(side="right", padx=5)
        
    def cargar_datos_comercial(self):
        # Carga datos de la API y actualiza la tabla.
        datos = api_client.obtener_comerciales()
        if datos is None:
              # Muestra error y vacía la tabla si la conexión falla.
              tk_messagebox.showerror("Error de Conexión", "No se pudieron obtener los comerciales. Verifique el servidor REST.")
              self.tabla_datos.actualizar_datos([]) 
        else:
              self.tabla_datos.actualizar_datos(datos)

    def al_seleccionar_fila(self, id_comercial):
        # Guarda el ID de la fila seleccionada, normalizándolo a entero.
        try:
            self.id_seleccionado = int(id_comercial)
        except (ValueError, TypeError):
            self.id_seleccionado = None
            
        print(f"CRUD R: Comercial seleccionado: ID {self.id_seleccionado}")
        
    def _get_comercial_fields(self):
        # Define la configuración de los campos del formulario modal.
        return [
            {'label': 'Nombre Completo:', 'validator': validar_nombre, 'key': 'nombre'},
            {'label': 'Email:', 'validator': validar_email, 'key': 'email'},
            {'label': 'Teléfono:', 'validator': validar_telefono, 'key': 'telefono'},
            {'label': 'Nombre de Usuario:', 'validator': validar_nombre, 'key': 'username'},
        ]
    
    # --- FUNCIONES DE CALLBACK ---

    def _abrir_modal_crear_comercial(self):
        # Abre el modal para crear un nuevo comercial.
        ModalForm(self.master, 
                  title="Crear Nuevo Comercial", 
                  fields_config=self._get_comercial_fields(), 
                  action_callback=self._crear_comercial_y_guardar)

    def _abrir_modal_editar_comercial(self):
        # Comprueba la selección, obtiene el comercial por ID de la API y abre el modal.
        if self.id_seleccionado is None:
            tk_messagebox.showwarning("Advertencia", "Selecciona un comercial de la tabla para editar.")
            return

        try:
            datos_api = api_client.obtener_comercial_por_id(self.id_seleccionado)
            
            if isinstance(datos_api, list) and len(datos_api) > 0:
                datos_actuales = datos_api[0]
            elif isinstance(datos_api, dict):
                datos_actuales = datos_api
            else:
                 raise Exception("Comercial no encontrado o formato de respuesta inválido.")
            
            self.comercial_en_edicion = datos_actuales

            ModalForm(self.master, 
                      title=f"Editar Comercial ID: {self.id_seleccionado}", 
                      fields_config=self._get_comercial_fields(), 
                      initial_data=datos_actuales, 
                      action_callback=self._actualizar_comercial_y_guardar)
            
        except Exception as e:
            tk_messagebox.showerror("Error", f"No se pudo cargar el comercial: {e}")


    def _crear_comercial_y_guardar(self, data):
        # POST /api/comerciales. Añade 'rol' y 'passwordHash' por defecto.
        try:
            # Añadir campos NOT NULL requeridos por la BD
            data['rol'] = "comercial" 
            data['passwordHash'] = "defaultpass123" 
            
            resultado = api_client.crear_comercial(data) 
            
            if resultado is not None and resultado is not False:
                tk_messagebox.showinfo("Éxito", f"Comercial '{data['nombre']}' creado correctamente.")
                self.cargar_datos_comercial() 
                return True
            else:
                tk_messagebox.showerror("Error de API", "El servidor rechazó la petición POST. Revise la consola.")
                return False
        except Exception as e:
            tk_messagebox.showerror("Error de API", f"Fallo al guardar el comercial: {e}")
            return False

    def _actualizar_comercial_y_guardar(self, data):
        # PUT /api/comerciales/{id}. Reenvía campos obligatorios (rol, hash) con datos previos.
        if not self.comercial_en_edicion:
            tk_messagebox.showerror("Error", "Error interno: Objeto de edición no cargado.")
            return False

        try:
            comercial_previo = self.comercial_en_edicion
            
            # 1. Objeto final con campos modificados
            data_final = {
                'nombre': data.get('nombre'),
                'email': data.get('email'),
                'telefono': data.get('telefono'),
                'username': data.get('username'),
            }
            
            # 2. Reenviar campos obligatorios NOT NULL
            data_final['rol'] = comercial_previo.get('rol')
            data_final['passwordHash'] = comercial_previo.get('passwordHash') 
            
            # 3. Incluir el ID para el ORM de Java
            data_final['comercialId'] = self.id_seleccionado
            
            if api_client.actualizar_comercial(self.id_seleccionado, data_final):
                tk_messagebox.showinfo("Éxito", f"Comercial ID {self.id_seleccionado} actualizado correctamente.")
                self.cargar_datos_comercial() 
                return True
            else:
                tk_messagebox.showerror("Error de API", "El servidor rechazó la petición PUT. Revise la consola.")
                return False
                
        except Exception as e:
            tk_messagebox.showerror("Error de API", f"Fallo al actualizar el comercial: {e}")
            return False

    def _confirmar_y_eliminar(self):
        # Pide confirmación y llama a la API para eliminar.
        if self.id_seleccionado is None:
            tk_messagebox.showwarning("Advertencia", "Selecciona un comercial para eliminar.")
            return

        confirmar = tk_messagebox.askyesno(
            title="Confirmar Eliminación", 
            message=f"¿Está seguro de que desea eliminar el comercial con ID: {self.id_seleccionado}?"
        )

        if confirmar:
            try:
                if api_client.eliminar_comercial(self.id_seleccionado):
                    tk_messagebox.showinfo("Éxito", f"Comercial ID {self.id_seleccionado} eliminado.")
                    self.id_seleccionado = None 
                    self.cargar_datos_comercial() 
                else:
                    tk_messagebox.showerror("Error de API", "El servidor rechazó la eliminación.")
            except Exception as e:
                tk_messagebox.showerror("Error", f"No se pudo eliminar el comercial. {e}")