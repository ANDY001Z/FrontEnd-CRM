import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from customtkinter import CTkFrame

# Importaciones del API (Funciones de obtención de datos)
from api.api_client import get_ingresos_mensuales, get_ranking_comerciales, get_invoice_counts

# =================================================================
# 1. CONFIGURACIÓN DE ESTILOS (Tema Claro y Colores Limpios)
# =================================================================
CARD_COLOR = "#FFFFFF" # Fondo de las tarjetas (Blanco)
TEXT_COLOR_DARK = "#0D0D0D" # Texto oscuro para fondo claro
LINE_COLORS = ["#0085FF", "#FF7F50", "#3CB371", "#7B68EE"] # Azules y complementarios
GRID_COLOR = "#DDDDDD" # Líneas de la cuadrícula suaves

plt.rcParams.update({
    "figure.facecolor": CARD_COLOR,
    "axes.facecolor": CARD_COLOR,
    "axes.edgecolor": GRID_COLOR,
    "axes.labelcolor": TEXT_COLOR_DARK,
    "xtick.color": TEXT_COLOR_DARK,
    "ytick.color": TEXT_COLOR_DARK,
    "grid.color": GRID_COLOR,
    "grid.linestyle": "-",
    "font.size": 9
})

# =================================================================
# 2. CLASE MODULAR DE LA VISTA
# =================================================================
class VistaDashboard(CTkFrame):
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configuración de Grid: 3 columnas, 3 filas
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(0, weight=1) # Fila superior (KPI Grande)
        self.grid_rowconfigure(1, weight=2) # Fila media (Línea)
        self.grid_rowconfigure(2, weight=2) # Fila inferior (Barras y Donut)

        # --- 1. LLAMADA A LA API Y PROCESAMIENTO DE DATOS ---
        periodos, ingresos = get_ingresos_mensuales()
        ranking = get_ranking_comerciales()
        conteo_facturas = get_invoice_counts() 
        
        nombres = [d['nombre'] for d in ranking]
        valores = [d['ingresos'] for d in ranking]
        total_ingresos = sum(ingresos)

        # --- 2. CONFIGURACIÓN DE GRÁFICOS Y KPIS ---
        
        # Fila 0: KPI Grande (Total de Ingresos)
        self._add_kpi_card(self, total_ingresos, 0, 0, 3)

        # Fila 1: Ingresos Mensuales (Ocupa 3 columnas)
        chart_func_line = lambda: self.create_top_chart(periodos, ingresos)
        self._add_chart_to_dashboard(self, chart_func_line, 1, 0, 3, "📈 Evolución de Ingresos Mensuales (€)", None, None)
        
        # Fila 2: Ranking (Barras) y Estado de Facturas (Donut)
        chart_func_bar = lambda: self.create_bar_chart(nombres, valores)
        self._add_chart_to_dashboard(self, chart_func_bar, 2, 0, 2, "📊 Ranking Comercial por Ingresos", "Total facturado por cada comercial.", None)
        
        chart_func_donut = lambda: self.create_invoice_status_pie(conteo_facturas)
        self._add_chart_to_dashboard(self, chart_func_donut, 2, 2, 1, "📑 Estado de Facturas", "Distribución Pagadas vs. Pendientes.", None)


    # --- Métodos de Layout ---

    def _add_kpi_card(self, parent_frame, total_ingresos, row, col, span):
        # Tarjeta para mostrar un KPI clave (Ingresos Totales).
        kpi_frame = ctk.CTkFrame(parent_frame, fg_color=LINE_COLORS[0], corner_radius=10)
        kpi_frame.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=5, pady=5)
        kpi_frame.grid_columnconfigure(0, weight=1)
        kpi_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(kpi_frame, 
                     text="INGRESOS TOTALES NETOS", 
                     text_color="white", 
                     font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="nw", padx=20, pady=(15, 0))

        ctk.CTkLabel(kpi_frame, 
                     text=f"{total_ingresos:,.2f} €", 
                     text_color="white", 
                     font=ctk.CTkFont(size=40, weight="bold")
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))


    def _add_chart_to_dashboard(self, parent_frame, chart_function, row, column, columnspan, title_text, text_above, text_below):
        # Contenedor para los gráficos (tarjeta blanca)
        container = ctk.CTkFrame(parent_frame, fg_color=CARD_COLOR, corner_radius=10, border_color=GRID_COLOR, border_width=1)
        container.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=5, pady=5)
        container.grid_columnconfigure(0, weight=1)
        
        current_row = 0
        PAD_X_INNER = 15
        
        # Título principal del gráfico
        label = ctk.CTkLabel(container, text=title_text, text_color=TEXT_COLOR_DARK, font=ctk.CTkFont(size=14, weight="bold"))
        label.grid(row=current_row, column=0, sticky="w", padx=PAD_X_INNER, pady=(15, 5))
        current_row += 1

        # Frame contenedor para el widget Matplotlib
        chart_frame = ctk.CTkFrame(container, fg_color="transparent")
        chart_frame.grid(row=current_row, column=0, sticky="nsew", padx=5, pady=5)
        container.grid_rowconfigure(current_row, weight=1) 
        current_row += 1
        
        # Inserta el gráfico
        self._create_matplotlib_widget(chart_frame, chart_function())

        # Etiqueta de texto inferior (si existe)
        if text_above or text_below:
            info_text = text_above if text_above else text_below
            label = ctk.CTkLabel(container, text=info_text, text_color=GRID_COLOR, wraplength=450, font=ctk.CTkFont(size=10))
            label.grid(row=current_row, column=0, sticky="w", padx=PAD_X_INNER, pady=(0, 10))
            current_row += 1

    
    def _create_matplotlib_widget(self, parent_frame, fig):
        # Configura y empaqueta el widget Matplotlib.
        fig.patch.set_alpha(0.0)
        canvas_widget = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas_widget.draw()
        widget = canvas_widget.get_tk_widget()
        
        widget.pack(fill="both", expand=True, padx=0, pady=0)


    # =================================================================
    # 4. FUNCIONES DE MATPLOTLIB (Tres gráficos clave)
    # =================================================================
    
    def create_invoice_status_pie(self, conteo_facturas):
        # Gráfico Donut de estado de facturas.
        fig, ax = plt.subplots(figsize=(1, 1))
        
        labels = ['Pagadas', 'Pendientes', 'Canceladas']
        sizes = [conteo_facturas['pagada'], conteo_facturas['pendiente'], conteo_facturas['cancelada']]
        colors = [LINE_COLORS[2], LINE_COLORS[1], LINE_COLORS[3]] # Verde, Naranja, Púrpura
        
        labels_filt = [labels[i] for i, size in enumerate(sizes) if size > 0]
        sizes_filt = [size for size in sizes if size > 0]
        colors_filt = [colors[i] for i, size in enumerate(sizes) if size > 0]
        
        if not sizes_filt: 
            ax.text(0.5, 0.5, 'Sin Datos', ha='center', va='center', color=TEXT_COLOR_DARK)
            return fig
            
        ax.pie(sizes_filt, labels=None, colors=colors_filt, autopct='%1.1f%%', startangle=90,
               wedgeprops={'edgecolor': CARD_COLOR, 'linewidth': 3}, pctdistance=0.85)

        # Círculo central (Donut)
        centre_circle = plt.Circle((0,0), 0.65, fc=CARD_COLOR)
        ax.add_artist(centre_circle)
        ax.axis('equal')
        ax.legend(labels_filt, loc="center", bbox_to_anchor=(0.5, 0.5), fontsize=8, frameon=False)
        
        fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        return fig
    
    def create_top_chart(self, periodos, ingresos):
        # Gráfico de línea de Ingresos Mensuales.
        fig, ax = plt.subplots(figsize=(1, 1))
        if not ingresos: 
            ax.text(0.5, 0.5, 'Sin Datos', ha='center', va='center', color=TEXT_COLOR_DARK)
            return fig
        
        x_indices = np.arange(len(periodos))
        
        # Trazado de línea azul
        ax.plot(x_indices, ingresos, color=LINE_COLORS[0], linewidth=2.5, marker='o', markersize=5)
        
        # Configuración de ejes
        ax.set_xticks(x_indices)
        ax.set_xticklabels(periodos, rotation=30, ha='right', color=TEXT_COLOR_DARK)
        ax.tick_params(axis='y', length=0) # Oculta las marcas del eje Y
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Oculta spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(GRID_COLOR)
        
        fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.2)
        return fig
    
    def create_bar_chart(self, nombres, valores):
        # Gráfico de barras de Ingresos por Comercial (Ranking).
        fig, ax = plt.subplots(figsize=(1, 1))
        if not valores: 
            ax.text(0.5, 0.5, 'Sin Datos', ha='center', va='center', color=TEXT_COLOR_DARK)
            return fig
        
        categorias = np.arange(len(nombres))
        colores_barras = [LINE_COLORS[0]] * len(nombres) # Usar color primario
        
        # Trazado de barras
        ax.bar(categorias, valores, color=colores_barras, edgecolor=CARD_COLOR, linewidth=1)
        
        # Configuración de ejes
        ax.set_xticks(categorias)
        ax.set_xticklabels(nombres, rotation=45, ha='right', color=TEXT_COLOR_DARK)
        ax.tick_params(axis='y', length=0) # Oculta las marcas del eje Y
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Oculta spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(GRID_COLOR)
        
        fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.3)
        return fig