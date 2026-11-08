"""
LABORATORIO DE ANÁLISIS DE ALGORITMOS DE ORDENAMIENTO
Algoritmos: Insertion Sort, Merge Sort y Heap Sort.

Requisitos:
    pip install matplotlib

Ejecutar:
    python laboratorio_ordenamiento.py

Organización de la interfaz (menú lateral):
    - Inicio ............................ resumen y accesos rápidos.
    - Insertion / Merge / Heap Sort ..... ficha de cada algoritmo con pestañas:
          Historia | Características | Rendimiento O() | Pseudocódigo | Visualización
    - Laboratorio de pruebas ............ valida CADA algoritmo por separado
                                          (ordenamiento correcto + rendimiento
                                          experimental vs. teórico).
    - Comparación de gráficas ........... compara los tres algoritmos
                                          (comparaciones, movimientos, tiempo
                                          y pseudocódigo lado a lado).

Notas de medición:
    * Los algoritmos reciben COPIAS DE LOS MISMOS arreglos de prueba.
    * "Comparaciones" cuenta comparaciones entre valores del arreglo.
    * "Movimientos" cuenta escrituras realizadas en el arreglo.
    * El tiempo se mide sólo alrededor de la llamada al algoritmo.
    * Las pruebas corren en un hilo aparte: la ventana no se congela.
"""

import math
import queue
import random
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
# 1. ALGORITMOS CON CONTADORES (para el laboratorio)
# ============================================================

def insertion_sort(datos):
    arr = datos.copy()
    comparaciones = 0
    movimientos = 0

    for i in range(1, len(arr)):
        clave = arr[i]
        j = i - 1
        while j >= 0:
            comparaciones += 1
            if arr[j] > clave:
                arr[j + 1] = arr[j]
                movimientos += 1
                j -= 1
            else:
                break
        arr[j + 1] = clave
        movimientos += 1

    return arr, comparaciones, movimientos


def merge_sort(datos):
    comparaciones = 0
    movimientos = 0

    def ordenar(lista):
        nonlocal comparaciones, movimientos
        if len(lista) <= 1:
            return lista

        medio = len(lista) // 2
        izquierda = ordenar(lista[:medio])
        derecha = ordenar(lista[medio:])

        resultado = []
        i = j = 0
        while i < len(izquierda) and j < len(derecha):
            comparaciones += 1
            if izquierda[i] <= derecha[j]:      # <= mantiene la estabilidad
                resultado.append(izquierda[i])
                i += 1
            else:
                resultado.append(derecha[j])
                j += 1
            movimientos += 1

        while i < len(izquierda):
            resultado.append(izquierda[i])
            i += 1
            movimientos += 1
        while j < len(derecha):
            resultado.append(derecha[j])
            j += 1
            movimientos += 1
        return resultado

    ordenado = ordenar(datos.copy())
    return ordenado, comparaciones, movimientos


def heap_sort(datos):
    arr = datos.copy()
    comparaciones = 0
    movimientos = 0
    n = len(arr)

    def intercambiar(i, j):
        nonlocal movimientos
        arr[i], arr[j] = arr[j], arr[i]
        movimientos += 2            # dos posiciones reciben un valor

    def hundir(tamano, raiz):
        nonlocal comparaciones
        while True:                 # versión iterativa (sin recursión)
            mayor = raiz
            izquierdo = 2 * raiz + 1
            derecho = 2 * raiz + 2
            if izquierdo < tamano:
                comparaciones += 1
                if arr[izquierdo] > arr[mayor]:
                    mayor = izquierdo
            if derecho < tamano:
                comparaciones += 1
                if arr[derecho] > arr[mayor]:
                    mayor = derecho
            if mayor == raiz:
                return
            intercambiar(raiz, mayor)
            raiz = mayor

    for i in range(n // 2 - 1, -1, -1):     # 1) construir Max Heap
        hundir(n, i)
    for fin in range(n - 1, 0, -1):         # 2) extraer el máximo
        intercambiar(0, fin)
        hundir(fin, 0)

    return arr, comparaciones, movimientos


# ============================================================
# 2. ALGORITMOS PASO A PASO (para la animación)
#    Cada generador modifica la lista y emite eventos:
#    ("comp", índices) | ("mov", índices) | ("swap", (i, j))
# ============================================================

def insertion_pasos(a):
    for i in range(1, len(a)):
        clave = a[i]
        j = i - 1
        while j >= 0:
            yield ("comp", (j, j + 1))
            if a[j] > clave:
                a[j + 1] = a[j]
                yield ("mov", (j + 1,))
                j -= 1
            else:
                break
        a[j + 1] = clave
        yield ("mov", (j + 1,))


def merge_pasos(a):
    def ordenar(ini, fin):              # intervalo [ini, fin)
        if fin - ini <= 1:
            return
        medio = (ini + fin) // 2
        yield from ordenar(ini, medio)
        yield from ordenar(medio, fin)
        izq, der = a[ini:medio], a[medio:fin]
        i = j = 0
        k = ini
        while i < len(izq) and j < len(der):
            yield ("comp", (k, medio + j))
            if izq[i] <= der[j]:
                a[k] = izq[i]
                i += 1
            else:
                a[k] = der[j]
                j += 1
            yield ("mov", (k,))
            k += 1
        for valor in izq[i:] + der[j:]:
            a[k] = valor
            yield ("mov", (k,))
            k += 1
    yield from ordenar(0, len(a))


def heap_pasos(a):
    n = len(a)

    def hundir(tamano, raiz):
        while True:
            mayor = raiz
            iz, de = 2 * raiz + 1, 2 * raiz + 2
            if iz < tamano:
                yield ("comp", (iz, mayor))
                if a[iz] > a[mayor]:
                    mayor = iz
            if de < tamano:
                yield ("comp", (de, mayor))
                if a[de] > a[mayor]:
                    mayor = de
            if mayor == raiz:
                return
            a[raiz], a[mayor] = a[mayor], a[raiz]
            yield ("swap", (raiz, mayor))
            raiz = mayor

    for i in range(n // 2 - 1, -1, -1):
        yield from hundir(n, i)
    for fin in range(n - 1, 0, -1):
        a[0], a[fin] = a[fin], a[0]
        yield ("swap", (0, fin))
        yield from hundir(fin, 0)


ALGORITMOS = {
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Heap Sort": heap_sort,
}
PASOS = {
    "Insertion Sort": insertion_pasos,
    "Merge Sort": merge_pasos,
    "Heap Sort": heap_pasos,
}
COLORES = {
    "Insertion Sort": "#D1495B",
    "Merge Sort": "#2E86AB",
    "Heap Sort": "#3B9C6B",
}
TIPOS_DATOS = ["Aleatorios", "Ordenados", "Orden inverso", "Casi ordenados"]


def generar_datos(tipo, n):
    if tipo == "Ordenados":
        return list(range(1, n + 1))
    if tipo == "Orden inverso":
        return list(range(n, 0, -1))
    if tipo == "Casi ordenados":
        arr = list(range(1, n + 1))
        for _ in range(max(1, n // 20)):          # ~5 % de intercambios
            i, j = random.randrange(n), random.randrange(n)
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    return [random.randint(1, n * 10) for _ in range(n)]


# ------------------------------------------------------------
# Modelo teórico usado para validar el rendimiento
# ------------------------------------------------------------

def funcion_teorica(nombre, tipo):
    """Devuelve (f(n), etiqueta) del orden esperado de comparaciones."""
    if nombre == "Insertion Sort":
        if tipo == "Ordenados":
            return (lambda n: n), "O(n)"
        return (lambda n: n * n), "O(n²)"
    return (lambda n: n * math.log2(n)), "O(n log n)"


def evaluar_rendimiento(nombre, tipo, filas):
    """
    Calcula c = comparaciones / f(n) para cada tamaño.
    Si c se mantiene casi constante, el crecimiento experimental
    coincide con el orden teórico.
    """
    f, etiqueta = funcion_teorica(nombre, tipo)
    razones = [fila["comparaciones"] / f(fila["n"]) for fila in filas]
    utiles = [r for fila, r in zip(filas, razones) if fila["n"] >= 50]
    if len(utiles) < 3:
        return razones, None, 0.0, etiqueta
    variacion = (max(utiles) - min(utiles)) / max(utiles)
    return razones, variacion <= 0.30, variacion, etiqueta


# ============================================================
# 3. CONTENIDO TEÓRICO
# ============================================================

INFORMACION = {
    "Insertion Sort": {
        "resumen": "Inserta cada elemento en la posición que le corresponde "
                   "dentro de la parte ya ordenada.",
        "datos_clave": [
            ("Origen", "Método clásico; ya se discutía en 1946 (John Mauchly)"),
            ("Estrategia", "Incremental"),
            ("Estable", "Sí"),
            ("In-place", "Sí"),
        ],
        "historia": (
            "Insertion Sort es uno de los métodos de ordenamiento más antiguos. "
            "Su idea reproduce la forma en que una persona organiza cartas en la "
            "mano: toma una carta y la inserta en el lugar correcto entre las que "
            "ya están ordenadas. Ya aparecía en las primeras discusiones sobre "
            "ordenamiento por computadora a mediados de la década de 1940, y hoy "
            "se enseña por su sencillez. Además, algoritmos modernos como TimSort "
            "lo utilizan internamente para ordenar bloques pequeños."
        ),
        "caracteristicas": [
            "Construye progresivamente una sección ordenada a la izquierda.",
            "Es estable: conserva el orden relativo de elementos iguales.",
            "Ordena en el mismo arreglo (in-place), sin memoria extra.",
            "Es adaptativo: es muy rápido si los datos ya están casi ordenados.",
            "Es en línea (online): puede ordenar datos a medida que llegan.",
            "Es lento con arreglos grandes y desordenados (crecimiento cuadrático).",
        ],
        "complejidad": [
            ("Mejor caso", "O(n)", "Arreglo ya ordenado: una comparación por elemento"),
            ("Caso promedio", "O(n²)", "Datos en orden aleatorio"),
            ("Peor caso", "O(n²)", "Arreglo en orden inverso"),
            ("Espacio", "O(1)", "Memoria auxiliar constante"),
        ],
        "curva": "n²",
        "pseudocodigo": """INSERTION_SORT(A):
    para i desde 1 hasta n-1:
        clave = A[i]
        j = i - 1
        mientras j >= 0 y A[j] > clave:
            A[j + 1] = A[j]
            j = j - 1
        A[j + 1] = clave""",
        "python": """def insertion_sort(arr):
    for i in range(1, len(arr)):
        clave = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > clave:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = clave
    return arr""",
    },
    "Merge Sort": {
        "resumen": "Divide el arreglo en mitades, ordena cada mitad y "
                   "luego las mezcla en orden.",
        "datos_clave": [
            ("Origen", "John von Neumann, 1945"),
            ("Estrategia", "Divide y vencerás"),
            ("Estable", "Sí"),
            ("In-place", "No (usa O(n) de memoria)"),
        ],
        "historia": (
            "Merge Sort fue propuesto por John von Neumann en 1945. Es uno de los "
            "primeros algoritmos que aplicó la estrategia divide y vencerás: parte "
            "el problema en subproblemas más pequeños, los resuelve por separado y "
            "combina sus resultados. Por su rendimiento garantizado se usa para "
            "ordenar listas enlazadas y grandes volúmenes de datos en disco "
            "(ordenamiento externo), y es la base de TimSort, el algoritmo que usa "
            "Python en sorted()."
        ),
        "caracteristicas": [
            "Utiliza la estrategia divide y vencerás.",
            "Divide el arreglo en mitades hasta llegar a elementos individuales.",
            "Mezcla (merge) las mitades ya ordenadas en una sola lista.",
            "Es estable si, ante un empate, toma primero el elemento de la izquierda.",
            "Su rendimiento no depende del orden inicial de los datos.",
            "Necesita memoria auxiliar proporcional a n.",
        ],
        "complejidad": [
            ("Mejor caso", "O(n log n)", "Siempre divide y mezcla"),
            ("Caso promedio", "O(n log n)", "Rendimiento muy consistente"),
            ("Peor caso", "O(n log n)", "No se degrada"),
            ("Espacio", "O(n)", "Listas auxiliares para la mezcla"),
        ],
        "curva": "n log n",
        "pseudocodigo": """MERGE_SORT(A):
    si longitud(A) <= 1:
        retornar A
    medio = longitud(A) / 2
    izquierda = MERGE_SORT(A[0 .. medio-1])
    derecha   = MERGE_SORT(A[medio .. n-1])
    retornar MEZCLAR(izquierda, derecha)

MEZCLAR(I, D):
    R = lista vacía
    mientras I y D tengan elementos:
        si I[0] <= D[0]: mover I[0] a R
        si no:           mover D[0] a R
    agregar a R lo que quede de I y de D
    retornar R""",
        "python": """def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    medio = len(arr) // 2
    izq = merge_sort(arr[:medio])
    der = merge_sort(arr[medio:])
    return mezclar(izq, der)

def mezclar(izq, der):
    res, i, j = [], 0, 0
    while i < len(izq) and j < len(der):
        if izq[i] <= der[j]:
            res.append(izq[i]); i += 1
        else:
            res.append(der[j]); j += 1
    res.extend(izq[i:])
    res.extend(der[j:])
    return res""",
    },
    "Heap Sort": {
        "resumen": "Construye un Max Heap y extrae repetidamente el "
                   "elemento mayor.",
        "datos_clave": [
            ("Origen", "J. W. J. Williams, 1964 (mejorado por R. W. Floyd)"),
            ("Estrategia", "Selección con Heap"),
            ("Estable", "No"),
            ("In-place", "Sí"),
        ],
        "historia": (
            "Heap Sort fue publicado por J. W. J. Williams en 1964, junto con la "
            "estructura de datos Heap (montículo). Ese mismo año Robert W. Floyd "
            "propuso una forma más eficiente de construir el Heap en tiempo lineal. "
            "Un Heap es un árbol binario guardado dentro de un arreglo: los hijos "
            "del nodo i están en 2i+1 y 2i+2. Para ordenar de menor a mayor se "
            "construye un Max Heap y se mueve el máximo al final una y otra vez. "
            "Se usa en sistemas que necesitan un tiempo garantizado sin memoria extra."
        ),
        "caracteristicas": [
            "Utiliza un Max Heap: el mayor elemento siempre está en la raíz.",
            "Representa el árbol binario mediante índices de un arreglo.",
            "Garantiza O(n log n) en mejor, promedio y peor caso.",
            "Ordena en el mismo arreglo (in-place), memoria O(1).",
            "No es estable: elementos iguales pueden cambiar su orden relativo.",
            "En la práctica suele ser algo más lento que Merge Sort por el acceso a memoria.",
        ],
        "complejidad": [
            ("Mejor caso", "O(n log n)", "Construcción O(n) + n extracciones"),
            ("Caso promedio", "O(n log n)", "Crecimiento consistente"),
            ("Peor caso", "O(n log n)", "No presenta degradación cuadrática"),
            ("Espacio", "O(1)", "Ordena dentro del mismo arreglo"),
        ],
        "curva": "n log n",
        "pseudocodigo": """HEAP_SORT(A):
    para i desde n/2 - 1 hasta 0:
        HUNDIR(A, n, i)      // construir Max Heap
    para fin desde n-1 hasta 1:
        intercambiar A[0] con A[fin]
        HUNDIR(A, fin, 0)    // restaurar Heap

HUNDIR(A, tamaño, raíz):
    mayor = raíz
    izq = 2*raíz + 1 ;  der = 2*raíz + 2
    si izq < tamaño y A[izq] > A[mayor]: mayor = izq
    si der < tamaño y A[der] > A[mayor]: mayor = der
    si mayor != raíz:
        intercambiar A[raíz] con A[mayor]
        HUNDIR(A, tamaño, mayor)""",
        "python": """def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        hundir(arr, n, i)
    for fin in range(n - 1, 0, -1):
        arr[0], arr[fin] = arr[fin], arr[0]
        hundir(arr, fin, 0)
    return arr

def hundir(arr, tam, raiz):
    mayor = raiz
    izq, der = 2 * raiz + 1, 2 * raiz + 2
    if izq < tam and arr[izq] > arr[mayor]:
        mayor = izq
    if der < tam and arr[der] > arr[mayor]:
        mayor = der
    if mayor != raiz:
        arr[raiz], arr[mayor] = arr[mayor], arr[raiz]
        hundir(arr, tam, mayor)""",
    },
}


# ============================================================
# 4. COMPONENTES DE INTERFAZ
# ============================================================

FONDO = "#F3F6FA"
BLANCO = "#FFFFFF"
AZUL_OSCURO = "#173B57"
AZUL = "#28658A"
TEXTO = "#20384D"
GRIS = "#64798B"
ACENTO = "#DCEAF3"
BORDE = "#DCE5EB"
VERDE = "#2E7D4F"
NARANJA = "#B26A00"
ROJO = "#B3261E"


class AreaDesplazable(tk.Frame):
    """Marco con barra de desplazamiento vertical y rueda del ratón."""

    def __init__(self, parent):
        super().__init__(parent, bg=FONDO)
        self.canvas = tk.Canvas(self, bg=FONDO, highlightthickness=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = tk.Frame(self.canvas, bg=FONDO)
        self._ventana = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.interior.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._ventana, width=e.width))
        self.bind_all("<MouseWheel>", self._rueda)
        self.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        self.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))

    def _rueda(self, e):
        if isinstance(e.widget, tk.Text):
            return
        paso = -int(e.delta / 120) if abs(e.delta) >= 120 else -e.delta
        self.canvas.yview_scroll(paso * 2, "units")

    def limpiar(self):
        for w in self.interior.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0)


def tarjeta(parent, titulo=None, padx=0, pady=7):
    """Tarjeta blanca con borde; devuelve el marco interior."""
    card = tk.Frame(parent, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1)
    card.pack(fill="x", padx=padx, pady=pady)
    if titulo:
        tk.Label(card, text=titulo, bg=BLANCO, fg=AZUL_OSCURO,
                 font=("Arial", 12, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
    cuerpo = tk.Frame(card, bg=BLANCO)
    cuerpo.pack(fill="both", expand=True, padx=16, pady=(0, 14))
    return cuerpo


def boton(parent, texto, comando, primario=True, **kw):
    return tk.Button(parent, text=texto, command=comando,
                     bg=AZUL if primario else "#E5EEF4",
                     fg="white" if primario else AZUL_OSCURO,
                     activebackground=AZUL_OSCURO if primario else ACENTO,
                     activeforeground="white" if primario else AZUL_OSCURO,
                     relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
                     font=("Arial", 10, "bold"), **kw)


def bloque_codigo(parent, titulo, codigo, alto=18, ajustar=False):
    panel = tk.Frame(parent, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1)
    tk.Label(panel, text=titulo, bg=BLANCO, fg=AZUL_OSCURO,
             font=("Arial", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
    tam = 9 if ajustar else 10                      # versión compacta
    txt = tk.Text(panel, height=alto, wrap="none", font=("Consolas", tam),
                  bg="#F7F9FB", fg="#24445C", relief="flat", padx=10, pady=10)
    barra_x = ttk.Scrollbar(panel, orient="horizontal", command=txt.xview)
    txt.configure(xscrollcommand=barra_x.set)
    barra_x.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
    txt.pack(fill="both", expand=True, padx=10, pady=(0, 2))
    txt.insert("1.0", codigo)
    # Resaltado sencillo de palabras clave
    claves = ["para", "mientras", "si", "si no", "retornar", "desde", "hasta",
              "def", "for", "while", "if", "else", "return", "in", "and"]
    txt.tag_configure("clave", foreground="#8A2BB0", font=("Consolas", tam, "bold"))
    txt.tag_configure("comentario", foreground="#7A8B99")
    for palabra in claves:
        inicio = "1.0"
        while True:
            pos = txt.search(r"\m" + palabra + r"\M", inicio, "end", regexp=True)
            if not pos:
                break
            fin = f"{pos}+{len(palabra)}c"
            txt.tag_add("clave", pos, fin)
            inicio = fin
    inicio = "1.0"
    while True:
        pos = txt.search("//", inicio, "end")
        if not pos:
            break
        txt.tag_add("comentario", pos, f"{pos} lineend")
        inicio = f"{pos} lineend"
    txt.config(state="disabled")
    return panel


def incrustar_figura(parent, fig, **pack):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(highlightthickness=0)
    widget.pack(**(pack or {"fill": "x", "pady": 6}))
    return canvas


class Visualizador(tk.Frame):
    """Animación paso a paso del algoritmo con barras."""

    def __init__(self, parent, nombre):
        super().__init__(parent, bg=BLANCO)
        self.nombre = nombre
        self.color = COLORES[nombre]
        self._job = None
        self.corriendo = False

        controles = tk.Frame(self, bg=BLANCO)
        controles.pack(fill="x", pady=(0, 8))
        tk.Label(controles, text="Datos:", bg=BLANCO, fg=TEXTO).pack(side="left")
        self.tipo = tk.StringVar(value="Aleatorios")
        cb = ttk.Combobox(controles, textvariable=self.tipo, values=TIPOS_DATOS,
                          state="readonly", width=14)
        cb.pack(side="left", padx=(4, 12))
        cb.bind("<<ComboboxSelected>>", lambda e: self.nuevo())

        tk.Label(controles, text="Elementos:", bg=BLANCO, fg=TEXTO).pack(side="left")
        self.n = tk.IntVar(value=30)
        ttk.Spinbox(controles, from_=8, to=80, textvariable=self.n, width=5,
                    command=self.nuevo).pack(side="left", padx=(4, 12))

        tk.Label(controles, text="Velocidad:", bg=BLANCO, fg=TEXTO).pack(side="left")
        self.velocidad = tk.IntVar(value=60)
        ttk.Scale(controles, from_=1, to=100, variable=self.velocidad,
                  length=130).pack(side="left", padx=(4, 12))

        self.b_play = boton(controles, "▶  Iniciar", self.alternar)
        self.b_play.pack(side="left", padx=3)
        boton(controles, "⏭  Paso", self.un_paso, primario=False).pack(side="left", padx=3)
        boton(controles, "↺  Nuevo arreglo", self.nuevo, primario=False).pack(side="left", padx=3)

        self.lienzo = tk.Canvas(self, height=280, bg="#F7F9FB", highlightthickness=0)
        self.lienzo.pack(fill="x")
        self.lienzo.bind("<Configure>", lambda e: self.dibujar())

        info = tk.Frame(self, bg=BLANCO)
        info.pack(fill="x", pady=(8, 0))
        self.lbl_comp = tk.Label(info, bg=BLANCO, fg=TEXTO, font=("Arial", 10, "bold"))
        self.lbl_comp.pack(side="left", padx=(0, 20))
        self.lbl_mov = tk.Label(info, bg=BLANCO, fg=TEXTO, font=("Arial", 10, "bold"))
        self.lbl_mov.pack(side="left", padx=(0, 20))
        self.lbl_estado = tk.Label(info, bg=BLANCO, fg=GRIS)
        self.lbl_estado.pack(side="left")
        leyenda = tk.Frame(info, bg=BLANCO)
        leyenda.pack(side="right")
        for txt_, col in [("Comparando", "#F2A541"), ("Escribiendo", "#D1495B"),
                          ("Ordenado", "#3B9C6B")]:
            tk.Label(leyenda, text="■", fg=col, bg=BLANCO).pack(side="left")
            tk.Label(leyenda, text=txt_ + "   ", fg=GRIS, bg=BLANCO).pack(side="left")

        self.bind("<Destroy>", lambda e: self._cancelar())
        self.nuevo()

    def _cancelar(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def nuevo(self):
        self._cancelar()
        self.corriendo = False
        self.b_play.config(text="▶  Iniciar")
        try:
            n = max(8, min(80, int(self.n.get())))
        except (tk.TclError, ValueError):
            n = 30
        self.arr = generar_datos(self.tipo.get(), n)
        if self.tipo.get() == "Aleatorios":
            self.arr = [random.randint(1, 100) for _ in range(n)]
        self.pasos = PASOS[self.nombre](self.arr)
        self.comp = self.mov = 0
        self.resaltar, self.tipo_evento, self.terminado = (), None, False
        self.lbl_estado.config(text="Listo. Pulsa Iniciar o Paso.")
        self._actualizar_contadores()
        self.dibujar()

    def alternar(self):
        if self.terminado:
            self.nuevo()
        self.corriendo = not self.corriendo
        self.b_play.config(text="⏸  Pausar" if self.corriendo else "▶  Continuar")
        if self.corriendo:
            self._bucle()

    def _bucle(self):
        if not self.corriendo:
            return
        self.un_paso()
        if not self.terminado:
            espera = int(400 - 3.95 * self.velocidad.get())
            self._job = self.after(max(1, espera), self._bucle)

    def un_paso(self):
        if self.terminado:
            return
        try:
            tipo, indices = next(self.pasos)
        except StopIteration:
            self.terminado, self.corriendo, self.resaltar = True, False, ()
            self.b_play.config(text="▶  Repetir")
            ok = self.arr == sorted(self.arr)
            self.lbl_estado.config(text="✔ Arreglo ordenado correctamente" if ok
                                   else "✘ Error en el ordenamiento",
                                   fg=VERDE if ok else ROJO)
            self.dibujar()
            return
        if tipo == "comp":
            self.comp += 1
        else:
            self.mov += 2 if tipo == "swap" else 1
        self.tipo_evento, self.resaltar = tipo, indices
        self.lbl_estado.config(text="Comparando posiciones " + ", ".join(map(str, indices))
                               if tipo == "comp" else
                               "Escribiendo en posición " + ", ".join(map(str, indices)),
                               fg=GRIS)
        self._actualizar_contadores()
        self.dibujar()

    def _actualizar_contadores(self):
        self.lbl_comp.config(text=f"Comparaciones: {self.comp}")
        self.lbl_mov.config(text=f"Movimientos: {self.mov}")

    def dibujar(self):
        c = self.lienzo
        c.delete("all")
        ancho = max(c.winfo_width(), 400)
        alto = max(c.winfo_height(), 200)
        n = len(self.arr)
        maximo = max(self.arr) if self.arr else 1
        w = (ancho - 20) / n
        for i, v in enumerate(self.arr):
            if self.terminado:
                color = "#3B9C6B"
            elif i in self.resaltar:
                color = "#F2A541" if self.tipo_evento == "comp" else "#D1495B"
            else:
                color = "#9DB4C6"
            x0 = 10 + i * w
            y0 = alto - 10 - (v / maximo) * (alto - 30)
            c.create_rectangle(x0 + 1, y0, x0 + w - 1, alto - 10, fill=color, outline="")
            if w > 18:
                c.create_text(x0 + w / 2, y0 - 7, text=str(v), fill=GRIS,
                              font=("Arial", 7))


# ============================================================
# 5. APLICACIÓN PRINCIPAL
# ============================================================

class Laboratorio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Laboratorio de algoritmos de ordenamiento")
        self.geometry("1400x880")
        self.minsize(1100, 700)
        self.configure(bg=FONDO)

        # resultados[nombre] = {"tipo": str, "rep": int, "filas": [...]}
        self.resultados = {}
        self.ejecutando = False
        self.cola = queue.Queue()
        self.botones_nav = {}
        self._activo = None

        self._configurar_estilos()
        self._construir_estructura()
        self.mostrar_inicio()

    # ---------------- estructura general ----------------

    def _configurar_estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=FONDO)
        s.configure("TLabel", background=FONDO, foreground=TEXTO, font=("Arial", 10))
        s.configure("TNotebook", background=FONDO, borderwidth=0)
        s.configure("TNotebook.Tab", padding=(16, 8), font=("Arial", 10, "bold"),
                    background="#E5EEF4", foreground=GRIS)
        s.map("TNotebook.Tab", background=[("selected", BLANCO)],
              foreground=[("selected", AZUL_OSCURO)])
        s.configure("Treeview", rowheight=28, font=("Arial", 10))
        s.configure("Treeview.Heading", font=("Arial", 10, "bold"),
                    background="#E5EEF4", foreground=AZUL_OSCURO)
        s.configure("TCheckbutton", background=BLANCO, font=("Arial", 10))
        s.configure("Horizontal.TProgressbar", troughcolor="#E5EEF4", background=AZUL)

    def _construir_estructura(self):
        encabezado = tk.Frame(self, bg=AZUL_OSCURO, height=80)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text="LABORATORIO DE ORDENAMIENTO", bg=AZUL_OSCURO,
                 fg="white", font=("Arial", 20, "bold")).pack(anchor="w", padx=24, pady=(14, 0))
        tk.Label(encabezado, text="Insertion Sort  ·  Merge Sort  ·  Heap Sort  —  "
                 "explora, ejecuta, valida y compara",
                 bg=AZUL_OSCURO, fg="#D9E8F2", font=("Arial", 10)).pack(anchor="w", padx=25)

        self.estado = tk.StringVar(value="Listo")
        tk.Label(self, textvariable=self.estado, anchor="w", bg="#E8EEF3", fg=GRIS,
                 padx=15, pady=5).pack(side="bottom", fill="x")

        cuerpo = tk.Frame(self, bg=FONDO)
        cuerpo.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(cuerpo, bg=BLANCO, width=250,
                                highlightbackground=BORDE, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._seccion_menu("GENERAL")
        self._nav("inicio", "⌂   Inicio", self.mostrar_inicio)

        self._seccion_menu("ALGORITMOS")
        for nombre in ALGORITMOS:
            self._nav(nombre, "●   " + nombre, lambda n=nombre: self.mostrar_ficha(n),
                      color=COLORES[nombre])

        self._seccion_menu("ANÁLISIS")
        self._nav("lab", "▦   Laboratorio de pruebas", self.mostrar_laboratorio)
        self._nav("comp", "▥   Comparación de gráficas", self.mostrar_comparacion)

        tk.Label(self.sidebar, text="Cada ficha incluye: historia,\ncaracterísticas, "
                 "rendimiento O(),\npseudocódigo y animación.",
                 bg=BLANCO, fg=GRIS, justify="left", font=("Arial", 8)).pack(
                     side="bottom", anchor="w", padx=18, pady=14)

        self.scroll = AreaDesplazable(cuerpo)
        self.scroll.pack(side="left", fill="both", expand=True)
        self.area = self.scroll.interior

    def _seccion_menu(self, texto):
        tk.Label(self.sidebar, text=texto, bg=BLANCO, fg=GRIS,
                 font=("Arial", 8, "bold")).pack(anchor="w", padx=18, pady=(18, 4))

    def _nav(self, clave, texto, comando, color=None):
        b = tk.Button(self.sidebar, text=texto, command=comando, anchor="w",
                      bg=BLANCO, fg=color or TEXTO, activebackground=ACENTO,
                      relief="flat", bd=0, padx=18, pady=9,
                      font=("Arial", 10, "bold"), cursor="hand2")
        b.pack(fill="x", padx=8, pady=1)
        b.bind("<Enter>", lambda e: b.config(bg=ACENTO) if b.cget("bg") == BLANCO else None)
        b.bind("<Leave>", lambda e: b.config(bg=BLANCO) if b.cget("bg") == ACENTO
               and self._activo != clave else None)
        self.botones_nav[clave] = b

    def _activar(self, clave):
        self._activo = clave
        for k, b in self.botones_nav.items():
            b.config(bg=ACENTO if k == clave else BLANCO)

    def _nueva_pagina(self, clave, titulo, subtitulo=""):
        self._activar(clave)
        self.scroll.limpiar()
        cont = tk.Frame(self.area, bg=FONDO)
        cont.pack(fill="both", expand=True, padx=26, pady=(18, 24))
        tk.Label(cont, text=titulo, bg=FONDO, fg=AZUL_OSCURO,
                 font=("Arial", 21, "bold")).pack(anchor="w")
        if subtitulo:
            tk.Label(cont, text=subtitulo, bg=FONDO, fg=GRIS,
                     font=("Arial", 10)).pack(anchor="w", pady=(2, 12))
        return cont

    # ---------------- página de inicio ----------------

    def mostrar_inicio(self):
        cont = self._nueva_pagina("inicio", "Bienvenido al laboratorio",
                                  "Elige un algoritmo para estudiarlo o ve directo a las pruebas.")

        fila = tk.Frame(cont, bg=FONDO)
        fila.pack(fill="x", pady=6)
        for col, nombre in enumerate(ALGORITMOS):
            fila.columnconfigure(col, weight=1, uniform="a")
            card = tk.Frame(fila, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))
            tk.Frame(card, bg=COLORES[nombre], height=6).pack(fill="x")
            tk.Label(card, text=nombre, bg=BLANCO, fg=AZUL_OSCURO,
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
            info = INFORMACION[nombre]
            tk.Label(card, text=info["resumen"], bg=BLANCO, fg=TEXTO, wraplength=300,
                     justify="left").pack(anchor="w", padx=16)
            orden = info["complejidad"][1][1]
            tk.Label(card, text=f"Caso promedio: {orden}", bg=BLANCO, fg=COLORES[nombre],
                     font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=8)
            bts = tk.Frame(card, bg=BLANCO)
            bts.pack(anchor="w", padx=16, pady=(0, 14))
            boton(bts, "Ver ficha", lambda n=nombre: self.mostrar_ficha(n)).pack(side="left")
            boton(bts, "Animación", lambda n=nombre: self.mostrar_ficha(n, 4),
                  primario=False).pack(side="left", padx=6)

        pasos = tarjeta(cont, "¿Cómo usar el laboratorio?")
        for i, (t, d) in enumerate([
            ("Estudia", "Abre cada algoritmo en el menú: historia, características, "
                        "rendimiento O() y pseudocódigo."),
            ("Observa", "En la pestaña Visualización mira el algoritmo ordenar paso a paso."),
            ("Valida", "En Laboratorio de pruebas ejecuta cada algoritmo y verifica que "
                       "ordene bien y que crezca como dice la teoría."),
            ("Compara", "En Comparación de gráficas mira los tres algoritmos juntos."),
        ], start=1):
            f = tk.Frame(pasos, bg=BLANCO)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=str(i), bg=AZUL, fg="white", width=3,
                     font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(f, text=f"  {t}: ", bg=BLANCO, fg=AZUL_OSCURO,
                     font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(f, text=d, bg=BLANCO, fg=TEXTO).pack(side="left")

        bts = tk.Frame(cont, bg=FONDO)
        bts.pack(anchor="w", pady=10)
        boton(bts, "IR AL LABORATORIO DE PRUEBAS", self.mostrar_laboratorio).pack(side="left")
        boton(bts, "VER COMPARACIÓN", self.mostrar_comparacion, primario=False).pack(
            side="left", padx=8)
        self.estado.set("Inicio")

    # ---------------- ficha de cada algoritmo ----------------

    def mostrar_ficha(self, nombre, pestana=0):
        info = INFORMACION[nombre]
        cont = self._nueva_pagina(nombre, nombre, info["resumen"])

        nb = ttk.Notebook(cont)
        nb.pack(fill="both", expand=True, pady=4)

        # --- Historia ---
        t1 = tk.Frame(nb, bg=FONDO)
        nb.add(t1, text="  Historia  ")
        datos = tk.Frame(t1, bg=FONDO)
        datos.pack(fill="x", pady=(10, 0))
        for col, (k, v) in enumerate(info["datos_clave"]):
            datos.columnconfigure(col, weight=1, uniform="d")
            c = tk.Frame(datos, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1)
            c.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))
            tk.Label(c, text=k.upper(), bg=BLANCO, fg=GRIS,
                     font=("Arial", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
            tk.Label(c, text=v, bg=BLANCO, fg=COLORES[nombre], wraplength=230,
                     justify="left", font=("Arial", 11, "bold")).pack(
                         anchor="w", padx=12, pady=(2, 10))
        cuerpo = tarjeta(t1, "Historia y origen")
        tk.Label(cuerpo, text=info["historia"], bg=BLANCO, fg=TEXTO, justify="left",
                 wraplength=950, font=("Arial", 11)).pack(anchor="w")

        # --- Características ---
        t2 = tk.Frame(nb, bg=FONDO)
        nb.add(t2, text="  Características  ")
        cuerpo = tarjeta(t2, "Características principales", pady=(10, 7))
        for c in info["caracteristicas"]:
            f = tk.Frame(cuerpo, bg=BLANCO)
            f.pack(fill="x", pady=3)
            tk.Label(f, text="✔", bg=BLANCO, fg=COLORES[nombre],
                     font=("Arial", 11, "bold")).pack(side="left", anchor="n")
            tk.Label(f, text=c, bg=BLANCO, fg=TEXTO, wraplength=900, justify="left",
                     font=("Arial", 11)).pack(side="left", padx=8)

        # --- Rendimiento O() ---
        t3 = tk.Frame(nb, bg=FONDO)
        nb.add(t3, text="  Rendimiento O()  ")
        cuerpo = tarjeta(t3, "Análisis de complejidad", pady=(10, 7))
        tabla = ttk.Treeview(cuerpo, columns=("caso", "orden", "desc"),
                             show="headings", height=4)
        for col, txt, ancho in [("caso", "Caso", 160), ("orden", "Orden", 140),
                                ("desc", "Explicación", 520)]:
            tabla.heading(col, text=txt)
            tabla.column(col, width=ancho, anchor="w" if col == "desc" else "center")
        for fila in info["complejidad"]:
            tabla.insert("", "end", values=fila)
        tabla.pack(fill="x")

        cuerpo = tarjeta(t3, "¿Cómo crece el costo?")
        fig = Figure(figsize=(9, 3.2), dpi=95)
        ax = fig.add_subplot(111)
        ns = list(range(2, 65))
        curvas = {"n": [n for n in ns], "n log n": [n * math.log2(n) for n in ns],
                  "n²": [n * n for n in ns]}
        for etiqueta, ys in curvas.items():
            propia = etiqueta == info["curva"]
            ax.plot(ns, ys, label=f"O({etiqueta})" + ("  ← este algoritmo" if propia else ""),
                    linewidth=3 if propia else 1.3,
                    color=COLORES[nombre] if propia else "#9DB4C6",
                    linestyle="-" if propia else "--")
        ax.set_xlabel("Cantidad de elementos (n)")
        ax.set_ylabel("Operaciones")
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        incrustar_figura(cuerpo, fig)
        tk.Label(cuerpo, text="La notación Big O describe cómo crece el número de "
                 "operaciones cuando aumenta n; no es un tiempo exacto en segundos.",
                 bg=BLANCO, fg=GRIS, wraplength=950, justify="left").pack(anchor="w")

        # --- Pseudocódigo ---
        t4 = tk.Frame(nb, bg=FONDO)
        nb.add(t4, text="  Pseudocódigo  ")
        bloque = tk.Frame(t4, bg=FONDO)
        bloque.pack(fill="both", expand=True, pady=10)
        bloque.columnconfigure(0, weight=1, uniform="c")
        bloque.columnconfigure(1, weight=1, uniform="c")
        bloque_codigo(bloque, "Pseudocódigo", info["pseudocodigo"]).grid(
            row=0, column=0, sticky="nsew", padx=(0, 5))
        bloque_codigo(bloque, "Implementación en Python", info["python"]).grid(
            row=0, column=1, sticky="nsew", padx=(5, 0))

        # --- Visualización ---
        t5 = tk.Frame(nb, bg=FONDO)
        nb.add(t5, text="  ▶ Visualización  ")
        cuerpo = tarjeta(t5, "Animación paso a paso", pady=(10, 7))
        Visualizador(cuerpo, nombre).pack(fill="x")

        nb.select(pestana)

        nav = tk.Frame(cont, bg=FONDO)
        nav.pack(fill="x", pady=10)
        tk.Label(nav, text="Ver otro algoritmo:", bg=FONDO, fg=GRIS).pack(side="left")
        for otro in ALGORITMOS:
            if otro != nombre:
                boton(nav, otro, lambda o=otro: self.mostrar_ficha(o, nb.index("current")),
                      primario=False).pack(side="left", padx=4)
        boton(nav, "Probar en el laboratorio →",
              lambda: self.mostrar_laboratorio(preseleccion=nombre)).pack(side="right")
        self.estado.set(f"Ficha de {nombre}")

    # ---------------- laboratorio de pruebas ----------------

    def mostrar_laboratorio(self, preseleccion=None):
        cont = self._nueva_pagina(
            "lab", "Laboratorio de pruebas",
            "Ejecuta cada algoritmo por separado y verifica la calidad: que ordene "
            "correctamente y que su rendimiento coincida con la teoría.")

        cfg = tarjeta(cont, "Parámetros de ejecución")
        fila1 = tk.Frame(cfg, bg=BLANCO)
        fila1.pack(fill="x", pady=4)

        self.n_var = tk.StringVar(value="2000")
        self.rep_var = tk.StringVar(value="5")
        self.tipo_var = tk.StringVar(value="Aleatorios")

        def campo(parent, texto, widget_fn):
            f = tk.Frame(parent, bg=BLANCO)
            f.pack(side="left", padx=(0, 22))
            tk.Label(f, text=texto, bg=BLANCO, fg=GRIS, font=("Arial", 9, "bold")).pack(anchor="w")
            widget_fn(f).pack(anchor="w", pady=2)

        campo(fila1, "TAMAÑO MÁXIMO (n)", lambda p: ttk.Spinbox(
            p, from_=60, to=20000, increment=500, textvariable=self.n_var, width=10))
        campo(fila1, "REPETICIONES", lambda p: ttk.Spinbox(
            p, from_=1, to=30, textvariable=self.rep_var, width=6))
        campo(fila1, "TIPO DE DATOS", lambda p: ttk.Combobox(
            p, textvariable=self.tipo_var, values=TIPOS_DATOS, state="readonly", width=16))

        def checks(p):
            f = tk.Frame(p, bg=BLANCO)
            self.sel_vars = {}
            for nombre in ALGORITMOS:
                v = tk.BooleanVar(value=(preseleccion is None or preseleccion == nombre))
                self.sel_vars[nombre] = v
                tk.Checkbutton(f, text=nombre, variable=v, bg=BLANCO, fg=COLORES[nombre],
                               activebackground=BLANCO, selectcolor=BLANCO,
                               font=("Arial", 10, "bold")).pack(side="left", padx=(0, 8))
            return f
        campo(fila1, "ALGORITMOS A PROBAR", checks)

        fila2 = tk.Frame(cfg, bg=BLANCO)
        fila2.pack(fill="x", pady=(10, 0))
        self.b_ejecutar = boton(fila2, "▶  EJECUTAR PRUEBAS", self.ejecutar_pruebas)
        self.b_ejecutar.pack(side="left")
        self.progreso = ttk.Progressbar(fila2, length=320, mode="determinate")
        self.progreso.pack(side="left", padx=14)
        self.lbl_progreso = tk.Label(fila2, text="", bg=BLANCO, fg=GRIS)
        self.lbl_progreso.pack(side="left")
        tk.Label(cfg, text="Se prueban 6 tamaños desde n/6 hasta n. Consejo: Insertion Sort "
                 "con más de 5.000 datos desordenados puede tardar bastante.",
                 bg=BLANCO, fg=GRIS, font=("Arial", 9)).pack(anchor="w", pady=(8, 0))

        self.resultado_frame = tk.Frame(cont, bg=FONDO)
        self.resultado_frame.pack(fill="both", expand=True)

        if self.ejecutando:
            self.b_ejecutar.config(state="disabled")
        visibles = {k: v for k, v in self.resultados.items()
                    if preseleccion is None or k == preseleccion}
        if visibles:
            self._dibujar_resultados(visibles)
        else:
            c = tarjeta(self.resultado_frame, "Resultados y validación")
            tk.Label(c, text="Aún no hay resultados. Configura los parámetros y pulsa "
                     "EJECUTAR PRUEBAS.", bg=BLANCO, fg=GRIS).pack(anchor="w")
        self.estado.set("Laboratorio de pruebas")

    def ejecutar_pruebas(self):
        if self.ejecutando:
            return
        try:
            n = int(self.n_var.get())
            rep = int(self.rep_var.get())
            if not 60 <= n <= 20000:
                raise ValueError("El tamaño máximo debe estar entre 60 y 20.000.")
            if not 1 <= rep <= 30:
                raise ValueError("Las repeticiones deben estar entre 1 y 30.")
        except ValueError as e:
            msg = str(e) if "debe" in str(e) else "Escribe números enteros válidos."
            messagebox.showerror("Parámetros inválidos", msg)
            return

        nombres = [k for k, v in self.sel_vars.items() if v.get()]
        if not nombres:
            messagebox.showwarning("Sin algoritmos", "Selecciona al menos un algoritmo.")
            return
        tipo = self.tipo_var.get()
        if ("Insertion Sort" in nombres and tipo != "Ordenados" and n * n * rep > 5000 ** 2 * 5):
            if not messagebox.askyesno(
                    "Prueba larga",
                    "Insertion Sort es O(n²): con estos parámetros puede tardar varios "
                    "minutos.\n\n¿Deseas continuar?"):
                return

        tamanos = sorted(set(max(2, round(n * i / 6)) for i in range(1, 7)))
        self.ejecutando = True
        self.b_ejecutar.config(state="disabled")
        self.progreso.config(value=0, maximum=len(nombres) * len(tamanos) * rep)
        self.estado.set("Ejecutando pruebas en segundo plano...")
        hilo = threading.Thread(target=self._trabajador,
                                args=(nombres, tamanos, rep, tipo), daemon=True)
        hilo.start()
        self.after(80, self._revisar_cola)

    def _trabajador(self, nombres, tamanos, rep, tipo):
        """Se ejecuta en otro hilo: NO toca widgets, sólo envía mensajes a la cola."""
        try:
            # Mismos arreglos de prueba para todos los algoritmos
            juegos = {tam: [generar_datos(tipo, tam) for _ in range(rep)] for tam in tamanos}
            nuevos, hechos = {}, 0
            for nombre in nombres:
                funcion = ALGORITMOS[nombre]
                filas = []
                for tam in tamanos:
                    tc = tm = tt = 0.0
                    correctos = 0
                    for datos in juegos[tam]:
                        inicio = time.perf_counter()
                        ordenado, comp, mov = funcion(datos)
                        tt += time.perf_counter() - inicio
                        if ordenado == sorted(datos) and len(ordenado) == len(datos):
                            correctos += 1
                        tc += comp
                        tm += mov
                        hechos += 1
                        self.cola.put(("progreso", hechos, f"{nombre} · n = {tam:,}"))
                    filas.append({"n": tam, "comparaciones": tc / rep,
                                  "movimientos": tm / rep, "tiempo": tt / rep,
                                  "correctos": correctos, "pruebas": rep})
                nuevos[nombre] = {"tipo": tipo, "rep": rep, "filas": filas}
            self.cola.put(("fin", nuevos))
        except Exception as e:                       # noqa: BLE001
            self.cola.put(("error", str(e)))

    def _revisar_cola(self):
        try:
            while True:
                msg = self.cola.get_nowait()
                if msg[0] == "progreso":
                    if self._widget_vivo("progreso"):
                        self.progreso.config(value=msg[1])
                        self.lbl_progreso.config(text=msg[2])
                elif msg[0] == "fin":
                    self.ejecutando = False
                    self.resultados.update(msg[1])
                    if self._widget_vivo("resultado_frame"):
                        self.b_ejecutar.config(state="normal")
                        self.lbl_progreso.config(text="Completado ✔")
                        self._dibujar_resultados(msg[1])
                    self.estado.set("Pruebas finalizadas. Revisa la validación de cada "
                                    "algoritmo o abre Comparación de gráficas.")
                    return
                elif msg[0] == "error":
                    self.ejecutando = False
                    if self._widget_vivo("b_ejecutar"):
                        self.b_ejecutar.config(state="normal")
                    messagebox.showerror("Error", msg[1])
                    return
        except queue.Empty:
            pass
        self.after(80, self._revisar_cola)

    def _widget_vivo(self, attr):
        w = getattr(self, attr, None)
        try:
            return w is not None and w.winfo_exists()
        except tk.TclError:
            return False

    def _dibujar_resultados(self, resultados):
        for w in self.resultado_frame.winfo_children():
            w.destroy()
        tk.Label(self.resultado_frame, text="Validación individual de cada algoritmo",
                 bg=FONDO, fg=AZUL_OSCURO, font=("Arial", 15, "bold")).pack(
                     anchor="w", pady=(12, 2))
        for nombre, datos in resultados.items():
            self._tarjeta_resultado(nombre, datos)

    def _tarjeta_resultado(self, nombre, datos):
        filas, tipo, rep = datos["filas"], datos["tipo"], datos["rep"]
        razones, coherente, variacion, etiqueta = evaluar_rendimiento(nombre, tipo, filas)
        total_ok = sum(f["correctos"] for f in filas)
        total = sum(f["pruebas"] for f in filas)

        card = tk.Frame(self.resultado_frame, bg=BLANCO,
                        highlightbackground=BORDE, highlightthickness=1)
        card.pack(fill="x", pady=8)
        tk.Frame(card, bg=COLORES[nombre], height=5).pack(fill="x")
        cab = tk.Frame(card, bg=BLANCO)
        cab.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(cab, text=nombre, bg=BLANCO, fg=AZUL_OSCURO,
                 font=("Arial", 14, "bold")).pack(side="left")
        tk.Label(cab, text=f"   Datos: {tipo}  ·  {rep} repeticiones por tamaño",
                 bg=BLANCO, fg=GRIS).pack(side="left")

        # Insignias de validación
        ins = tk.Frame(card, bg=BLANCO)
        ins.pack(fill="x", padx=16, pady=4)

        def insignia(texto, color):
            tk.Label(ins, text=texto, bg=color, fg="white", padx=10, pady=4,
                     font=("Arial", 9, "bold")).pack(side="left", padx=(0, 8))

        insignia(f"✔ Ordenamiento correcto: {total_ok}/{total} pruebas" if total_ok == total
                 else f"✘ Falló en {total - total_ok} de {total} pruebas",
                 VERDE if total_ok == total else ROJO)
        if coherente is None:
            insignia("ⓘ n muy pequeño para evaluar el crecimiento", GRIS)
        elif coherente:
            insignia(f"✔ Rendimiento coherente con {etiqueta} (variación de c: "
                     f"{variacion:.0%})", VERDE)
        else:
            insignia(f"⚠ Rendimiento se aleja de {etiqueta} (variación de c: "
                     f"{variacion:.0%})", NARANJA)

        tk.Label(card, text=f"Criterio: si c = comparaciones / f(n) se mantiene casi "
                 f"constante al crecer n (variación ≤ 30 %), el algoritmo crece como "
                 f"{etiqueta}.", bg=BLANCO, fg=GRIS, font=("Arial", 9)).pack(
                     anchor="w", padx=16, pady=(2, 6))

        # Tabla detallada por tamaño
        cols = ("n", "comp", "mov", "tiempo", "c", "valid")
        tabla = ttk.Treeview(card, columns=cols, show="headings", height=len(filas))
        for col, txt, ancho in [("n", "n", 90), ("comp", "Comparaciones prom.", 170),
                                ("mov", "Movimientos prom.", 170),
                                ("tiempo", "Tiempo prom. (ms)", 150),
                                ("c", f"c = comp / {etiqueta[2:-1]}", 160),
                                ("valid", "Validación", 120)]:
            tabla.heading(col, text=txt)
            tabla.column(col, width=ancho, anchor="center")
        tabla.tag_configure("mal", foreground=ROJO)
        for f, r in zip(filas, razones):
            ok = f["correctos"] == f["pruebas"]
            tabla.insert("", "end", tags=() if ok else ("mal",), values=(
                f"{f['n']:,}", f"{f['comparaciones']:,.0f}", f"{f['movimientos']:,.0f}",
                f"{f['tiempo'] * 1000:,.3f}", f"{r:.3f}",
                "✔ Correcto" if ok else "✘ Error"))
        tabla.pack(fill="x", padx=16, pady=4)

        # Gráficas: experimental vs teórico  +  constante c
        fig = Figure(figsize=(10, 2.9), dpi=92)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        f_teo, _ = funcion_teorica(nombre, tipo)
        xs = [f["n"] for f in filas]
        ys = [f["comparaciones"] for f in filas]
        c_med = sum(razones) / len(razones)
        ax1.plot(xs, ys, marker="o", linewidth=2.2, color=COLORES[nombre],
                 label="Experimental")
        ax1.plot(xs, [c_med * f_teo(x) for x in xs], linestyle="--", color="#555",
                 label=f"Teórico  {c_med:.2f}·{etiqueta[2:-1]}")
        ax1.set_title("Comparaciones: experimental vs. teórico", fontsize=10)
        ax1.set_xlabel("n")
        ax1.grid(alpha=0.25)
        ax1.legend(fontsize=8)
        ax2.plot(xs, razones, marker="s", color=COLORES[nombre])
        ax2.axhline(c_med, linestyle=":", color="#555")
        ax2.set_ylim(0, max(razones) * 1.4 if max(razones) > 0 else 1)
        ax2.set_title("Constante c (debe ser casi horizontal)", fontsize=10)
        ax2.set_xlabel("n")
        ax2.grid(alpha=0.25)
        fig.tight_layout()
        incrustar_figura(card, fig, fill="x", padx=10, pady=(4, 12))

    # ---------------- comparación de gráficas ----------------

    def mostrar_comparacion(self):
        cont = self._nueva_pagina(
            "comp", "Comparación de gráficas",
            "Compara los resultados experimentales de los algoritmos y su pseudocódigo.")

        nb = ttk.Notebook(cont)
        nb.pack(fill="both", expand=True, pady=4)

        if not self.resultados:
            t = tk.Frame(nb, bg=FONDO)
            nb.add(t, text="  Gráficas  ")
            c = tarjeta(t, "Todavía no hay resultados", pady=(10, 7))
            tk.Label(c, text="Primero ejecuta pruebas en el Laboratorio de pruebas "
                     "(idealmente con los tres algoritmos y el mismo tipo de datos).",
                     bg=BLANCO, fg=GRIS).pack(anchor="w")
            boton(c, "Ir al laboratorio", self.mostrar_laboratorio).pack(anchor="w", pady=8)
        else:
            self._pestanas_graficas(nb)

        # Pseudocódigo lado a lado (siempre disponible)
        t = tk.Frame(nb, bg=FONDO)
        nb.add(t, text="  Pseudocódigo comparado  ")
        bloque = tk.Frame(t, bg=FONDO)
        bloque.pack(fill="both", expand=True, pady=10)
        for col, nombre in enumerate(ALGORITMOS):
            bloque.columnconfigure(col, weight=1, uniform="p")
            panel = bloque_codigo(bloque, nombre, INFORMACION[nombre]["pseudocodigo"], alto=22,
                                   ajustar=True)
            tk.Frame(panel, bg=COLORES[nombre], height=4).pack(fill="x", side="top",
                                                                before=panel.winfo_children()[0])
            panel.grid(row=0, column=col, sticky="nsew", padx=4)
        resumen = tarjeta(t, "Diferencias clave")
        tabla = ttk.Treeview(resumen, columns=("alg", "estr", "prom", "peor", "esp", "est"),
                             show="headings", height=3)
        for col, txt in [("alg", "Algoritmo"), ("estr", "Estrategia"), ("prom", "Promedio"),
                         ("peor", "Peor caso"), ("esp", "Espacio"), ("est", "Estable")]:
            tabla.heading(col, text=txt)
            tabla.column(col, anchor="center", width=150)
        for nombre, info in INFORMACION.items():
            dk = dict(info["datos_clave"])
            tabla.insert("", "end", values=(nombre, dk["Estrategia"], info["complejidad"][1][1],
                                            info["complejidad"][2][1], info["complejidad"][3][1],
                                            dk["Estable"]))
        tabla.pack(fill="x")
        self.estado.set("Comparación de gráficas")

    def _pestanas_graficas(self, nb):
        tipos = {d["tipo"] for d in self.resultados.values()}
        aviso = ("" if len(tipos) == 1 else
                 "  ⚠ Los algoritmos se probaron con tipos de datos distintos; "
                 "para una comparación justa ejecútalos juntos.")

        # Resumen
        t = tk.Frame(nb, bg=FONDO)
        nb.add(t, text="  Resumen  ")
        c = tarjeta(t, "Resultados con el tamaño más grande probado", pady=(10, 7))
        if aviso:
            tk.Label(c, text=aviso, bg=BLANCO, fg=NARANJA).pack(anchor="w", pady=(0, 6))
        tabla = ttk.Treeview(c, columns=("alg", "tipo", "n", "comp", "mov", "t", "pos"),
                             show="headings", height=len(self.resultados))
        for col, txt, w in [("alg", "Algoritmo", 140), ("tipo", "Datos", 120), ("n", "n", 80),
                            ("comp", "Comparaciones", 140), ("mov", "Movimientos", 140),
                            ("t", "Tiempo (ms)", 120), ("pos", "Puesto por tiempo", 140)]:
            tabla.heading(col, text=txt)
            tabla.column(col, width=w, anchor="center")
        orden = sorted(self.resultados, key=lambda k: self.resultados[k]["filas"][-1]["tiempo"])
        medallas = ["🥇 1.º", "🥈 2.º", "🥉 3.º"]
        for nombre in orden:
            d = self.resultados[nombre]
            r = d["filas"][-1]
            tabla.insert("", "end", values=(
                nombre, d["tipo"], f"{r['n']:,}", f"{r['comparaciones']:,.0f}",
                f"{r['movimientos']:,.0f}", f"{r['tiempo'] * 1000:,.3f}",
                medallas[orden.index(nombre)]))
        tabla.pack(fill="x")

        # Una pestaña por métrica, con opción de escala logarítmica
        for clave, titulo, ylabel, factor in [
                ("comparaciones", "Comparaciones", "Promedio de comparaciones", 1),
                ("movimientos", "Movimientos", "Promedio de movimientos", 1),
                ("tiempo", "Tiempo", "Milisegundos", 1000)]:
            t = tk.Frame(nb, bg=FONDO)
            nb.add(t, text=f"  {titulo}  ")
            self._grafica_comparativa(t, clave, titulo, ylabel, factor, aviso)

    def _grafica_comparativa(self, parent, clave, titulo, ylabel, factor, aviso):
        c = tarjeta(parent, f"{titulo} según el tamaño de la entrada", pady=(10, 7))
        if aviso:
            tk.Label(c, text=aviso, bg=BLANCO, fg=NARANJA).pack(anchor="w")
        fig = Figure(figsize=(10, 4.6), dpi=95)
        ax = fig.add_subplot(111)
        for nombre, d in self.resultados.items():
            ax.plot([f["n"] for f in d["filas"]], [f[clave] * factor for f in d["filas"]],
                    marker="o", linewidth=2.2, color=COLORES[nombre], label=nombre)
        ax.set_xlabel("Cantidad de elementos (n)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        canvas = incrustar_figura(c, fig)

        log = tk.BooleanVar(value=False)

        def cambiar_escala():
            ax.set_yscale("log" if log.get() else "linear")
            canvas.draw()
        ttk.Checkbutton(c, text="Escala logarítmica en el eje Y (útil cuando una curva "
                        "aplasta a las demás)", variable=log,
                        command=cambiar_escala).pack(anchor="w")


if __name__ == "__main__":
    app = Laboratorio()
    app.mainloop()