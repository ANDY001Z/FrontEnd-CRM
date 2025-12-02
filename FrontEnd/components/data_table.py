from customtkinter import CTkFrame, CTkScrollbar 
from tkinter import ttk 
import tkinter as tk

class DataTable(CTkFrame):
    # Componente reutilizable para mostrar datos tabulares (Requisito DataTabel).
    def __init__(self, maestro, columnas, al_seleccionar_item=None, **kwargs):
        super().__init__(maestro, **kwargs)
        self.columnas = columnas
        self.al_seleccionar_item = al_seleccionar_item
        self.datos = []
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # La tabla debe expandirse

        self._crear_vista_tabla()

    def _crear_vista_tabla(self):
        # Configura el Frame contenedor y el Treeview
        self.marco_tabla = CTkFrame(self)
        self.marco_tabla.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.marco_tabla.grid_rowconfigure(0, weight=1)
        self.marco_tabla.grid_columnconfigure(0, weight=1)

        # Inicializa Treeview con las columnas definidas
        self.arbol = ttk.Treeview(self.marco_tabla, columns=self.columnas, show='headings')
        
        # Configura las cabeceras y comandos de ordenación
        for col in self.columnas:
            self.arbol.heading(col, text=col.replace('_', ' ').title(), 
                               command=lambda c=col: self._ordenar_datos(c))
            self.arbol.column(col, width=150, anchor=tk.W)

        # Configura la barra de desplazamiento y la enlaza al Treeview
        self.barra_desplazamiento = CTkScrollbar(self.marco_tabla, command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=self.barra_desplazamiento.set)

        # Empaqueta la tabla y la barra de desplazamiento
        self.barra_desplazamiento.grid(row=0, column=1, sticky="ns")
        self.arbol.grid(row=0, column=0, sticky="nsew")

        # Conecta el evento de selección al método handler
        self.arbol.bind('<<TreeviewSelect>>', self._al_seleccionar)

    def _al_seleccionar(self, evento):
        # Maneja la selección de fila y devuelve el ID (primera columna).
        item_seleccionado = self.arbol.focus()
        if item_seleccionado and self.al_seleccionar_item:
            valores = self.arbol.item(item_seleccionado, 'values')
            
            # Devuelve el valor de la primera columna (ID), forzado a string.
            if valores:
                self.al_seleccionar_item(str(valores[0])) 

    def actualizar_datos(self, nuevos_datos):
        # Limpia la tabla y la rellena con los nuevos datos.
        self.datos = nuevos_datos
        for item in self.arbol.get_children():
            self.arbol.delete(item)

        for item in self.datos:
            # Inserta solo los valores que coinciden con las columnas
            valores_a_insertar = [item.get(col, "") for col in self.columnas]
            self.arbol.insert('', tk.END, values=valores_a_insertar)

    def _ordenar_datos(self, columna):
        # Función placeholder para ordenar datos (requerido en DataTabel).
        print(f"Ordenando la tabla por columna: {columna}")
        pass