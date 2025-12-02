from customtkinter import CTkFrame, CTkEntry, CTkLabel, StringVar

class ValidateEntry(CTkFrame):
    # Componente de campo de entrada con validación visual en tiempo real.
    def __init__(self, maestro, texto_etiqueta="Campo", validador=None, initial_value="", **kwargs): 
        super().__init__(maestro, **kwargs)
        
        self.validador = validador
        self.__es_valido = False # Estado de validez privado
        
        # Inicializa StringVar con el valor inicial
        self.var_entrada = StringVar(value=initial_value) 
        
        self.grid_columnconfigure(0, weight=1)
        
        # Etiqueta del campo
        CTkLabel(self, text=texto_etiqueta).grid(row=0, column=0, sticky="w", padx=5)
        
        # Campo de entrada enlazado a StringVar
        self.entrada = CTkEntry(self, textvariable=self.var_entrada, width=300) 
        self.entrada.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        # Enlaza la función de validación al evento de escritura/cambio
        self.var_entrada.trace_add("write", self._al_cambiar_entrada) 
        
        # Etiqueta para mostrar el feedback (mensaje de error o éxito)
        self.etiqueta_feedback = CTkLabel(self, text="", text_color="red")
        self.etiqueta_feedback.grid(row=2, column=0, sticky="w", padx=5)
        
        # Ejecuta la validación inicial (importante para el modo Edición)
        self._al_cambiar_entrada() 

    def _al_cambiar_entrada(self, *args):
        # Función llamada en cada pulsación de tecla para validar el contenido.
        valor = self.var_entrada.get()
        
        if self.validador:
            mensaje, es_valido = self.validador(valor)
            self.__es_valido = es_valido
            
            self.etiqueta_feedback.configure(text=mensaje)
            
            # Cambia el color del borde si no es válido
            if self.__es_valido or not valor:
                self.entrada.configure(border_color="#909090") # Color neutral/por defecto
            else:
                self.entrada.configure(border_color="red") # Marcar error

    def obtener_valor(self):
        # Devuelve el valor actual del campo de entrada.
        return self.var_entrada.get()

    @property 
    def es_valido(self):
        # Propiedad para obtener el estado de validez (fuerza una validación final).
        self._al_cambiar_entrada() 
        return self.__es_valido
    
    @es_valido.setter
    def es_valido(self, value):
        # Setter (utilizado raramente, pero necesario para la propiedad).
        self.__es_valido = value