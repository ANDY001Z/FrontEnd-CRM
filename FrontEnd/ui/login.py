from customtkinter import *
from PIL import Image
import requests
import tkinter.messagebox as tk_messagebox
# Importar la configuración de la API desde api_client.py (PENDIENTE DE MOVER)

# --- CONFIGURACIÓN DE API 
BASE_URL = "http://localhost:8080/crm-backend/api"
COMERCIALES_ENDPOINT = f"{BASE_URL}/comerciales" 


class LoginPage(CTkFrame):
    """Frame que contiene la interfaz del Login."""

    def __init__(self, master, open_dashboard_callback, **kwargs):
        # Usamos el modo de apariencia definido globalmente en main.py
        super().__init__(master, **kwargs)
        self.master = master
        self.open_dashboard_callback = open_dashboard_callback
         
        # Configuración del FRAME (login)
        self.configure(fg_color="white") # Color de fondo del frame
        
        # Configuración de Grid: 2 columnas para el centrado
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)
        
        self._construir_interfaz()
        # Enlazar F1 a la ventana principal para que funcione siempre
        self.master.bind('<F1>', lambda event: self._abrir_ayuda())
    
    def _construir_interfaz(self):
        
        # 1. Columna de Imagen (Columna 0)
        self.bg_img = CTkImage(dark_image=Image.open("assets/b1.jpg"), size=(500, 500))
        bg_lab = CTkLabel(self, image=self.bg_img, text="")
        # Usamos sticky="nsew" para llenar el espacio
        bg_lab.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 2. Frame del Formulario (Columna 1)
        # El Frame principal tiene el color gris de fondo
        form_frame = CTkFrame(self, fg_color="#D9D9D9", corner_radius=20, width=300)
        # Usamos padx y pady más grandes para forzar un centrado visual
        form_frame.grid(row=0, column=1, padx=(10, 30), pady=115, sticky="nsew")

        # Frame interno para contener los widgets y centrar
        content_frame = CTkFrame(form_frame, fg_color="#D9D9D9")
        content_frame.pack(expand=True, padx=30, pady=30)
        content_frame.grid_columnconfigure(0, weight=1)

        # Llamada al método que construye los widgets internos
        self._construir_widgets_formulario(content_frame)

    def _construir_widgets_formulario(self, parent_frame):
        # Título
        title = CTkLabel(parent_frame, text="BIENVENIDO", text_color="black", font=("Roboto", 30, "bold"))
        title.grid(row=0, column=0, sticky="n", pady=10)

        # Campo Usuario
        entry_style = {"text_color": "white", "fg_color": "black", 
                        "placeholder_text_color": "white", "font": ("", 16, "bold"), 
                        "width": 250, "corner_radius": 15, "height": 45}

        self.usrname_entry = CTkEntry(parent_frame, placeholder_text="Usuario", **entry_style)
        self.usrname_entry.grid(row=1, column=0, sticky="ew", pady=(15, 5))

        # Campo Contraseña
        self.passwd_entry = CTkEntry(parent_frame, placeholder_text="Contraseña", show="*", **entry_style)
        self.passwd_entry.grid(row=2, column=0, sticky="ew", pady=(5, 20))

        # Contenedor para Botones (Login y Crear Cuenta)
        button_container = CTkFrame(parent_frame, fg_color="#D9D9D9")
        button_container.grid(row=3, column=0, sticky="ew")

        # Etiqueta "Crear Cuenta"
        cr_acc = CTkLabel(button_container, text="Crear Cuenta!", text_color="black", 
                            cursor="hand2", font=("", 15))
        cr_acc.pack(side="left")

        # Botón de Login
        self.l_btn = CTkButton(button_container, text="Login", font=("", 15, "bold"), 
                                height=40, width=80, fg_color="#0085FF", cursor="hand2",
                                corner_radius=15, command=self._handle_login)
        self.l_btn.pack(side="right")
        
    def _handle_login(self):
        """Maneja la lógica de validación de credenciales contra la API """
        username = self.usrname_entry.get()
        password = self.passwd_entry.get()

        if not username or not password:
            tk_messagebox.showerror(title="Error", message="Usuario y contraseña obligatorios.")
            return

        try:
            # 1. PETICIÓN GET al endpoint para obtener la lista de comerciales
            response = requests.get(COMERCIALES_ENDPOINT, timeout=3)
            response.raise_for_status() # Lanza HTTPError si el estado no es 2xx
            
            comerciales_list = response.json()
            login_successful = False

            # 2. Iterar y validar credenciales localmente (como en tu versión)
            for comercial in comerciales_list:
                api_username = comercial.get("username")
                api_password = comercial.get("passwordHash") # Se asume que la 'contraseña' es el hash
                
                if api_username == username and api_password == password:
                    nombre_comercial = comercial.get("nombre", username)
                    tk_messagebox.showinfo(title="Login Exitoso", message=f"Bienvenido, {nombre_comercial}.")
                    self.open_dashboard_callback(nombre_comercial)
                    login_successful = True
                    break
            
            if not login_successful:
                tk_messagebox.showerror(title="Error", message="Usuario o contraseña incorrectos.")

        except requests.exceptions.RequestException as e:
            # --- FALLBACK DE SIMULACIÓN (Servidor Java apagado o inaccesible) ---
            print(f"Error de conexión: {e}. Activando modo simulación.")
            
            if username == "admin" and password == "1234":
                nombre_simulado = "Administrador (Simulación)"
                tk_messagebox.showinfo(title="Modo Simulación Activo",
                                        message=f"Conexión fallida al servidor. Bienvenido, {nombre_simulado}.")
                self.open_dashboard_callback(nombre_simulado)
            else:
                # Mostrar el error de conexión real si no se usan las credenciales de simulación
                tk_messagebox.showerror(title="Error Fatal",
                                         message="No se pudo conectar al servidor. Intente más tarde.")
        
        finally:
            self.passwd_entry.delete(0, END) # Limpia la contraseña siempre

    def _abrir_ayuda(self):
        #Muestra la ayuda contextual (Requisito de F1).
        informacion_ayuda = ("GUÍA RÁPIDA - CRM XTART\n"
                              "• Puedes utilizar la tecla TAB para desplazarse mejor entre campos\n"
                              "• Pueds abrir la ayuda con el F1\n"
                              "• Para una simulacion, usar: usuario=admin, contraseña=1234")
        tk_messagebox.showinfo(title="Ayuda (F1)", message=informacion_ayuda)