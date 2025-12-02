from customtkinter import CTkFrame, CTkButton, CTkEntry, CTkLabel 
import tkinter.messagebox as tk_messagebox
import re 
from datetime import datetime # Necesario para la fecha de emisión

from components.data_table import DataTable
from components.modal_form import ModalForm 
from api import api_client

# --- FUNCIONES DE VALIDACIÓN ---
def validar_id_factura(valor):
    # Valida que el ID de factura no esté vacío.
    if not valor: return "El ID de factura es obligatorio.", False
    return "✅", True
def validar_id_entidad(valor):
    # Valida que el ID (Cliente/Comercial/Producto) sea un número positivo.
    if not valor: return "El ID es obligatorio.", False
    try:
        if int(valor) <= 0: return "Debe ser un número positivo.", False
        return "✅", True
    except ValueError: return "Debe ser un número entero.", False
def validar_total(valor):
    # Valida que el Total sea un número positivo y válido.
    if not valor: return "El Total es obligatorio.", False
    try:
        # Permite comas o puntos, pero el float lo normalizará
        total = float(str(valor).replace(',', '.')) 
        if total <= 0: return "El total debe ser positivo.", False
        return "✅", True
    except ValueError: return "Debe ser un número válido (decimales permitidos).", False

# --- VISTA COMPLETA CON CRUD DE FACTURAS ---

class VistaFacturas(CTkFrame):
    # Frame que contiene la tabla de Facturas y los controles CRUD.
    def __init__(self, maestro, **kwargs):
        super().__init__(maestro, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        self.id_seleccionado = None 
        # Almacena el objeto completo de la factura para la actualización (PUT).
        self.factura_en_edicion = None

        self.marco_control = CTkFrame(self, fg_color="transparent")
        self.marco_control.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="new")
        CTkEntry(self.marco_control, placeholder_text="Buscar factura...").pack(side="left", padx=5)

        # Botones CRUD (Nuevo y Recargar)
        CTkButton(self.marco_control, text="Nuevo (C)", command=self._abrir_modal_crear_factura).pack(side="right", padx=5)
        CTkButton(self.marco_control, text="Recargar", command=self.cargar_datos_factura).pack(side="right", padx=5)

        # Inicialización de la Tabla de Datos
        columnas_factura = ["factura_id", "cliente_id", "comercial_id", "fecha_emision", "estado", "total"]
        self.tabla_datos = DataTable(self, columnas=columnas_factura, al_seleccionar_item=self.al_seleccionar_fila)
        self.tabla_datos.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        self.cargar_datos_factura()
        
        # Marco de Acciones inferiores (Editar y Eliminar)
        self.marco_accion = CTkFrame(self, fg_color="transparent")
        self.marco_accion.grid(row=2, column=0, padx=10, pady=5, sticky="se")
        
        # Botón de Edición (UPDATE)
        CTkButton(self.marco_accion, text="Editar (U)", command=self._abrir_modal_editar_factura).pack(side="right", padx=5)
        
        # Botón de Eliminar (DELETE)
        CTkButton(self.marco_accion, text="Eliminar (D)", fg_color="red", command=self._confirmar_y_eliminar).pack(side="right", padx=5)
        
    def cargar_datos_factura(self):
        # Carga datos de la API y actualiza la tabla.
        datos = api_client.obtener_facturas()
        if datos is None:
              tk_messagebox.showerror("Error de Conexión", "No se pudieron obtener las facturas. Verifique el servidor REST.")
              self.tabla_datos.actualizar_datos([])
        else:
              self.tabla_datos.actualizar_datos(datos)

    def al_seleccionar_fila(self, id_factura):
        # Guarda el ID de la fila seleccionada (debe ser string/VARCHAR).
        self.id_seleccionado = str(id_factura) 
        print(f"CRUD R: Factura seleccionada: ID {self.id_seleccionado}")
        
    def _get_factura_fields(self, is_edit=False):
        # Define la configuración de campos para Crear y Editar Factura.
        fields = [
            {'label': 'ID Cliente:', 'validator': validar_id_entidad, 'key': 'cliente_id'},
            {'label': 'ID Comercial:', 'validator': validar_id_entidad, 'key': 'comercial_id'},
            {'label': 'Total (€):', 'validator': validar_total, 'key': 'total'},
        ]
        
        if not is_edit:
            # Pedimos ID de factura (VARCHAR) y ID de Producto (FK NOT NULL) al crear
            fields.insert(0, {'label': 'ID Factura:', 'validator': validar_id_factura, 'key': 'factura_id'})
            fields.insert(3, {'label': 'ID Producto:', 'validator': validar_id_entidad, 'key': 'producto_id'})
            
        return fields

    def _abrir_modal_crear_factura(self):
        # Abre el modal para crear una nueva factura.
        ModalForm(self.master, 
                  title="Crear Nueva Factura", 
                  fields_config=self._get_factura_fields(is_edit=False), 
                  action_callback=self._crear_factura_y_guardar)

    def _abrir_modal_editar_factura(self):
        # Obtiene la factura por ID y abre el modal.
        if self.id_seleccionado is None:
            tk_messagebox.showwarning("Advertencia", "Selecciona una factura de la tabla para editar.")
            return

        try:
            # 1. Obtener datos de la factura seleccionada de la API
            datos_api = api_client.obtener_factura_por_id(self.id_seleccionado)
            
            if isinstance(datos_api, list) and len(datos_api) > 0:
                datos_actuales = datos_api[0]
            elif isinstance(datos_api, dict):
                datos_actuales = datos_api
            else:
                 raise Exception("Factura no encontrada o formato de respuesta inválido.")
            
            # Guardamos el objeto completo para reenviar campos obligatorios en el PUT
            self.factura_en_edicion = datos_actuales

            # 2. Abrir el modal con datos pre-cargados
            ModalForm(self.master, 
                      title=f"Editar Factura ID: {self.id_seleccionado}", 
                      fields_config=self._get_factura_fields(is_edit=True), 
                      initial_data=datos_actuales, 
                      action_callback=self._actualizar_factura_y_guardar)
            
        except Exception as e:
            tk_messagebox.showerror("Error", f"No se pudo cargar la factura: {e}")


    def _crear_factura_y_guardar(self, data):
        # Lógica para POST /api/facturas. Asigna estado y fecha de emisión por defecto.
        try:
            # Asignar campos NOT NULL requeridos por la BD
            data['estado'] = 'pendiente' 
            # Usar formato YYYY-MM-DD para la fecha
            data['fecha_emision'] = datetime.now().strftime("%Y-%m-%d")
            
            # El resto de campos ya vienen del formulario.
            
            resultado = api_client.crear_factura(data) 
            
            if resultado is not None and resultado is not False:
                tk_messagebox.showinfo("Éxito", f"Factura '{data['factura_id']}' creada correctamente.")
                self.cargar_datos_factura() 
                return True
            else:
                tk_messagebox.showerror("Error de API", "El servidor rechazó la petición POST. Revise la consola.")
                return False
        except Exception as e:
            tk_messagebox.showerror("Error de API", f"Fallo al guardar la factura: {e}")
            return False

    def _actualizar_factura_y_guardar(self, data):
        # Lógica para PUT /api/facturas/{id}. Reenvía campos obligatorios.
        if not self.factura_en_edicion:
            tk_messagebox.showerror("Error", "Error interno: Objeto de edición no cargado.")
            return False

        try:
            factura_previo = self.factura_en_edicion
            
            # 1. Crear el objeto final con los campos modificados del formulario
            data_final = {
                'cliente_id': int(data.get('cliente_id')),
                'comercial_id': int(data.get('comercial_id')),
                'total': float(data.get('total')),
            }
            
            # 2. Reenviar campos obligatorios NOT NULL (ID, producto, fecha, estado)
            data_final['factura_id'] = factura_previo.get('factura_id')
            data_final['producto_id'] = factura_previo.get('producto_id')
            data_final['fecha_emision'] = factura_previo.get('fecha_emision')
            data_final['estado'] = factura_previo.get('estado')
            
            if api_client.actualizar_factura(self.id_seleccionado, data_final):
                tk_messagebox.showinfo("Éxito", f"Factura ID {self.id_seleccionado} actualizada correctamente.")
                self.cargar_datos_factura() 
                return True
            else:
                tk_messagebox.showerror("Error de API", "El servidor rechazó la petición PUT. Revise la consola.")
                return False
                
        except Exception as e:
            tk_messagebox.showerror("Error de API", f"Fallo al actualizar la factura: {e}")
            return False

    def _confirmar_y_eliminar(self):
        # Pide confirmación y llama a la API para eliminar.
        if self.id_seleccionado is None:
            tk_messagebox.showwarning("Advertencia", "Selecciona una factura de la tabla para eliminar.")
            return

        confirmar = tk_messagebox.askyesno(
            title="Confirmar Eliminación", 
            message=f"¿Está seguro de que desea eliminar la factura con ID: {self.id_seleccionado}?"
        )

        if confirmar:
            try:
                if api_client.eliminar_factura(self.id_seleccionado):
                    tk_messagebox.showinfo("Éxito", f"Factura ID {self.id_seleccionado} eliminada.")
                    self.id_seleccionado = None 
                    self.cargar_datos_factura() 
                else:
                    tk_messagebox.showerror("Error de API", "El servidor rechazó la eliminación. Revise la consola.")
            except Exception as e:
                tk_messagebox.showerror("Error", f"No se pudo eliminar la factura. {e}")