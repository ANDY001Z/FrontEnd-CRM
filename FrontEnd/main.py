from customtkinter import *
from ui.login import LoginPage
from ui.dashboard import VentanaDashboard # Import necesario para la transición

# Configuración inicial del tema y apariencia
set_appearance_mode("light")
set_default_color_theme("blue")

def open_dashboard_callback(user_name):
    """Oculta la ventana de Login y muestra la ventana del Dashboard."""
    app.withdraw() # Oculta la ventana principal (Login)
    # Crea y muestra la ventana del Dashboard
    VentanaDashboard(app, username=user_name)

if __name__ == "__main__":
    app = CTk()
    app.title("CRM XTART")
    app.geometry("1000x600")
    
    # Crea la vista de Login y le pasa la función de transición
    login_view = LoginPage(
        master=app,
        open_dashboard_callback=open_dashboard_callback
    )
    
    # Empaqueta la vista para que ocupe todo el espacio de la ventana principal
    login_view.pack(fill="both", expand=True)
    
    # Inicia el bucle principal de la aplicación
    app.mainloop()