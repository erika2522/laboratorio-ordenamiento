# Laboratorio de algoritmos de ordenamiento

Aplicación de escritorio (Python + Tkinter + Matplotlib) para estudiar, ejecutar, validar y comparar tres algoritmos de ordenamiento:

| Algoritmo | Promedio | Peor caso | Espacio | Estable |
|---|---|---|---|---|
| Insertion Sort | O(n²) | O(n²) | O(1) | Sí |
| Merge Sort | O(n log n) | O(n log n) | O(n) | Sí |
| Heap Sort | O(n log n) | O(n log n) | O(1) | No |

## Requisitos

```bash
pip install matplotlib
```

## Ejecución

```bash
python3 main.py
```

## Contenido de la aplicación

- **Ficha de cada algoritmo**, con pestañas de Historia, Características, Rendimiento O(), Pseudocódigo + Python y una animación paso a paso.
- **Laboratorio de pruebas**, que valida cada algoritmo por separado:
  - Ordenamiento correcto en todas las pruebas.
  - Rendimiento experimental frente al teórico: se calcula `c = comparaciones / f(n)`. Si `c` se mantiene casi constante al crecer `n`, el algoritmo crece como dice la teoría.
- **Comparación de gráficas**: resumen con ranking, gráficas de comparaciones, movimientos y tiempo, y el pseudocódigo de los tres lado a lado.

Todos los algoritmos se ejecutan sobre copias de los mismos arreglos de prueba (aleatorios, ordenados, en orden inverso o casi ordenados).