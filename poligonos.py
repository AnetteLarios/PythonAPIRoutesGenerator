import json
import math
import heapq  # Para la cola de prioridad en A*
from PIL import Image, ImageDraw

# ---- IMPORTANTE: Instala shapely antes (pip install shapely) ----
from shapely.geometry import Point, Polygon, LineString

Image.MAX_IMAGE_PIXELS = None

# Cargar la imagen del mapa
mapImage = Image.open("images/mapa.webp")


# ---------------------------------------------------------------------
#     FUNCIONES PARA CARGAR/GUARDAR JSON
# ---------------------------------------------------------------------
def load_json_file(archive_name):
    try:
        with open(archive_name, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Archivo {archive_name} no encontrado.")
        return {}
    except json.JSONDecodeError:
        print(f"Error al decodificar {archive_name}. Asegúrate de que no esté vacío y tenga formato JSON válido.")
        return {}

def save_json_file(data, archive_name):
    with open(archive_name, 'w') as file:
        json.dump(data, file, indent=4)


# ---------------------------------------------------------------------
#     CARGAR DATOS
# ---------------------------------------------------------------------
coordenadas = load_json_file("coordinates.json")
rutas_predefinidas = load_json_file("rutas_predefinidas.json")
rangos_data = load_json_file("rangos_prohibidos.json")

if not rutas_predefinidas:
    rutas_predefinidas = {}
    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")


# ---------------------------------------------------------------------
#     CREAR POLÍGONOS DE ÁREAS PROHIBIDAS CON SHAPELY
# ---------------------------------------------------------------------
rangos_poligonos = []  # Aquí guardaremos cada rectángulo convertido a Polygon

if "rangos_prohibidos" in rangos_data:
    for key, rango in rangos_data["rangos_prohibidos"].items():
        # Creamos un polígono rectangular con las esquinas definidas
        # por x_min, x_max, y_min, y_max
        poly = Polygon([
            (rango["x_min"], rango["y_min"]),
            (rango["x_max"], rango["y_min"]),
            (rango["x_max"], rango["y_max"]),
            (rango["x_min"], rango["y_max"])
        ])
        rangos_poligonos.append(poly)


# ---------------------------------------------------------------------
#     FUNCIONES PARA VERIFICAR ÁREAS PROHIBIDAS (USANDO SHAPELY)
# ---------------------------------------------------------------------
def dentro_de_rangos_prohibidos(coord):
    """
    Verifica si la coordenada (x, y) está dentro de
    alguno de los polígonos prohibidos de 'rangos_poligonos'.
    """
    punto = Point(coord[0], coord[1])
    for poligono in rangos_poligonos:
        if poligono.contains(punto):
            return True
    return False

def cruzar_rango_prohibido(coord1, coord2):
    """
    Verifica si la línea que une coord1 y coord2
    intersecta alguno de los polígonos prohibidos.
    """
    line = LineString([coord1, coord2])
    for poligono in rangos_poligonos:
        # .intersects() = True si el LineString toca o cruza el polígono
        if line.intersects(poligono):
            return True
    return False


# ---------------------------------------------------------------------
#     OBTENER COORDENADAS DE UN NODO
# ---------------------------------------------------------------------
def obtenerCoordenadas(nodo):
    """
    Devuelve la tupla (x, y) correspondiente al nodo en 'coordenadas.json'
    """
    return coordenadas.get(nodo, None)


# ---------------------------------------------------------------------
#     CALCULAR DISTANCIA ENTRE DOS NODOS (EUCLIDIANA)
# ---------------------------------------------------------------------
def calcular_distancia(nodo1, nodo2):
    """
    Retorna la distancia Euclidiana entre nodo1 y nodo2.
    Si cualquiera de los dos está en un polígono prohibido
    o la línea que los une lo cruza, retorna infinito.
    """
    c1 = obtenerCoordenadas(nodo1)
    c2 = obtenerCoordenadas(nodo2)
    if c1 and c2:
        if dentro_de_rangos_prohibidos(c1) or dentro_de_rangos_prohibidos(c2):
            return float('inf')
        if cruzar_rango_prohibido(c1, c2):
            return float('inf')
        # Distancia euclidiana
        dx = c2[0] - c1[0]
        dy = c2[1] - c1[1]
        return math.sqrt(dx*dx + dy*dy)
    return float('inf')


# ---------------------------------------------------------------------
#     GENERAR GRAFO CON PESOS
# ---------------------------------------------------------------------
def generar_grafo_con_pesos(coordenadas, umbral=1000):
    """
    Genera un grafo tipo dict: {
       nodo1: {nodo2: dist, nodo3: dist, ...},
       nodo2: {nodo1: dist, ...},
       ...
    }
    Solo genera arista si la distancia < umbral
    (para no crear conexiones demasiado lejanas).
    """
    graph = {}
    nodos = list(coordenadas.keys())

    for nodo in nodos:
        graph[nodo] = {}
        for otro_nodo in nodos:
            if nodo != otro_nodo:
                dist = calcular_distancia(nodo, otro_nodo)
                if dist != float('inf') and dist < umbral:
                    graph[nodo][otro_nodo] = dist
    return graph


# ---------------------------------------------------------------------
#     A* (BÚSQUEDA DE RUTA)
# ---------------------------------------------------------------------
def heuristic(nodo_actual, nodo_destino):
    """
    Heurística para A*.
    Usamos la distancia euclidiana entre las coordenadas de ambos nodos.
    """
    cA = obtenerCoordenadas(nodo_actual)
    cB = obtenerCoordenadas(nodo_destino)
    if not cA or not cB:
        return float('inf')
    dx = cB[0] - cA[0]
    dy = cB[1] - cA[1]
    return math.sqrt(dx*dx + dy*dy)

def a_star(graph, start, end):
    """
    Implementación del algoritmo A*.
    - graph: dict con nodos y adyacentes {nodo: {vecino: dist, ...}}
    - start: nodo inicial
    - end: nodo final
    Retorna la lista de nodos en el camino óptimo.
    """
    openSet = []
    heapq.heappush(openSet, (0, start))  # (fScore, nodo)
    
    cameFrom = {}
    gScore = {n: float('inf') for n in graph}
    fScore = {n: float('inf') for n in graph}

    gScore[start] = 0
    fScore[start] = heuristic(start, end)

    inOpenSet = {n: False for n in graph}
    inOpenSet[start] = True

    while openSet:
        current_f, current = heapq.heappop(openSet)
        inOpenSet[current] = False

        if current == end:
            return reconstruir_camino(cameFrom, current)

        if current_f > fScore[current]:
            continue

        # Explorar vecinos
        for neighbor, dist in graph[current].items():
            tentative_g = gScore[current] + dist
            if tentative_g < gScore[neighbor]:
                cameFrom[neighbor] = current
                gScore[neighbor] = tentative_g
                fScore[neighbor] = tentative_g + heuristic(neighbor, end)
                if not inOpenSet[neighbor]:
                    heapq.heappush(openSet, (fScore[neighbor], neighbor))
                    inOpenSet[neighbor] = True

    return []

def reconstruir_camino(cameFrom, current):
    """
    Reconstruye la ruta desde 'current' (end) hacia el start.
    """
    path = [current]
    while current in cameFrom:
        current = cameFrom[current]
        path.append(current)
    path.reverse()
    return path


# ---------------------------------------------------------------------
#     COMPLETAR RUTA CON NODOS SECUNDARIOS
# ---------------------------------------------------------------------
def es_nodo_principal(nodo):
    """
    Lógica opcional:
    Suponemos que un nodo principal está en mayúsculas, 
    o puedes definir tu criterio.
    """
    return nodo.isupper()

def completar_ruta_con_nodos_no_principales(graph, ruta, min_nodos=6):
    """
    Si la ruta tiene menos de min_nodos, inserta nodos "secundarios".
    Esto es la misma lógica de tu script original.
    """
    if len(ruta) >= min_nodos:
        return ruta

    nodos_disponibles = [
        n for n in graph
        if n not in ruta and not es_nodo_principal(n)
    ]

    while len(ruta) < min_nodos and nodos_disponibles:
        mejor_nodo = None
        mejor_distancia = float('inf')

        for i in range(len(ruta) - 1):
            nodo_actual = ruta[i]
            nodo_siguiente = ruta[i + 1]

            for nodo_intermedio in nodos_disponibles:
                # Verificar que la línea nodo_actual->nodo_intermedio->nodo_siguiente
                # no cruce zonas prohibidas
                cA = obtenerCoordenadas(nodo_actual)
                cB = obtenerCoordenadas(nodo_siguiente)
                cM = obtenerCoordenadas(nodo_intermedio)

                if (cA and cB and cM and
                    not cruzar_rango_prohibido(cA, cM) and
                    not cruzar_rango_prohibido(cM, cB)):

                    # Calcular la distancia si existe en el grafo
                    dist_actual = graph[nodo_actual].get(nodo_intermedio, float('inf'))
                    dist_actual += graph[nodo_intermedio].get(nodo_siguiente, float('inf'))

                    if dist_actual < mejor_distancia:
                        mejor_distancia = dist_actual
                        mejor_nodo = nodo_intermedio

        if mejor_nodo:
            # Insertar el nodo intermedio
            for i in range(len(ruta) - 1):
                if (mejor_nodo in graph[ruta[i]] and
                    mejor_nodo in graph[ruta[i+1]]):
                    ruta.insert(i + 1, mejor_nodo)
                    nodos_disponibles.remove(mejor_nodo)
                    break

    return ruta


# ---------------------------------------------------------------------
#     ORDENAR RUTA (OPCIONAL)
# ---------------------------------------------------------------------
def ordenar_ruta_por_coordenadas(ruta):
    """
    Simplemente un sorted() que ordena
    los nodos según sus (x, y).
    """
    return sorted(ruta, key=lambda n: obtenerCoordenadas(n) if obtenerCoordenadas(n) else (999999,999999))


# ---------------------------------------------------------------------
#     DIBUJAR RUTA EN EL MAPA
# ---------------------------------------------------------------------
def dibujar_ruta(ruta_optima, dibujador):
    coords_ruta = []
    for nodo in ruta_optima:
        coord = obtenerCoordenadas(nodo)
        if coord:
            coords_ruta.append(coord)
        else:
            print(f"Coordenadas no encontradas para nodo {nodo}.")

    if len(coords_ruta) < 2:
        print("No hay suficientes nodos para dibujar.")
        return

    # Trazar la ruta en negro y amarillo
    for i in range(len(coords_ruta) - 1):
        x1, y1 = coords_ruta[i]
        x2, y2 = coords_ruta[i + 1]
        dibujador.line([(x1, y1), (x2, y2)], fill="black", width=30)
        dibujador.line([(x1, y1), (x2, y2)], fill="yellow", width=20)


# ---------------------------------------------------------------------
#     GUARDAR RUTA PREDEFINIDA
# ---------------------------------------------------------------------
def guardar_ruta_predefinida(start, end, ruta):
    """
    Guarda la ruta en rutas_predefinidas.json (en ambas direcciones).
    """
    clave = f"{start}_{end}"
    clave_inversa = f"{end}_{start}"

    # Ordenar la ruta excepto el primer y último nodo
    ruta_ordenada = [start] + ordenar_ruta_por_coordenadas(ruta[1:-1]) + [end]

    rutas_predefinidas[clave] = ruta_ordenada
    rutas_predefinidas[clave_inversa] = list(reversed(ruta_ordenada))

    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")
    print(f"Ruta {clave} e inversa {clave_inversa} guardadas en rutas_predefinidas.json.")


# ---------------------------------------------------------------------
#     LÓGICA: CÁLCULO DE RUTA ÓPTIMA
# ---------------------------------------------------------------------
def calcular_numero_de_nodos(coord1, coord2, base_nodos=2, umbral_distancia=500,
                             incremento_nodos=0.5, factor_prohibido=1.2):
    """
    Cálculo dinámico del número de nodos intermedios deseados,
    basado en la distancia entre coord1 y coord2, y si se cruza área prohibida.
    """
    dist = math.dist(coord1, coord2)  # sqrt((x2-x1)^2 + (y2-y1)^2)
    nodos_adicionales = int(dist // umbral_distancia * incremento_nodos)
    total_nodos = base_nodos + nodos_adicionales

    # Si cruza un área prohibida directamente, aumentar factor
    line = LineString([coord1, coord2])
    for poligono in rangos_poligonos:
        if line.intersects(poligono):
            total_nodos = int(total_nodos * factor_prohibido)
            break

    return max(base_nodos, total_nodos)


def obtener_ruta_optima(start, end, graph):
    """
    - Si la ruta existe en 'rutas_predefinidas.json', la retorna.
    - Si no, la calcula con A*, la completa con nodos,
      y la guarda en 'rutas_predefinidas.json'.
    """
    clave = f"{start}_{end}"
    if clave in rutas_predefinidas:
        print(f"Ruta {clave} encontrada en rutas predefinidas.")
        return rutas_predefinidas[clave]

    print(f"Calculando ruta óptima (A*) de {start} a {end}...")
    path = a_star(graph, start, end)
    if not path or len(path) < 2:
        print("No se encontró ruta. Devolviendo ruta vacía.")
        return []

    # Si la ruta es muy corta, metemos nodos intermedios
    cStart = obtenerCoordenadas(start)
    cEnd = obtenerCoordenadas(end)
    if cStart and cEnd:
        min_nodos = calcular_numero_de_nodos(cStart, cEnd)
        path = completar_ruta_con_nodos_no_principales(graph, path, min_nodos=min_nodos)

    # Guardar la ruta
    guardar_ruta_predefinida(start, end, path)
    return rutas_predefinidas[clave]


# ---------------------------------------------------------------------
#     EJEMPLO DE USO
# ---------------------------------------------------------------------
if __name__ == "__main__":

    # Ejemplo: queremos la ruta entre nodos 'M' y 'K'
    start_node = "Biblioteca"
    end_node = "Q"

    # Crear el grafo
    graph = generar_grafo_con_pesos(coordenadas, umbral=1000)

    # Obtener ruta óptima con A*
    ruta_optima = obtener_ruta_optima(start_node, end_node, graph)

    # Dibujar en la imagen
    dibujador = ImageDraw.Draw(mapImage)
    dibujar_ruta(ruta_optima, dibujador)

    # Guardar la imagen con la ruta
    mapImage.save(f"poligonos/{start_node}_{end_node}.webp")
    mapImage.save(f"poligonos/{end_node}_{start_node}.webp")

    # Opcional: guardar el grafo en un JSON
    save_json_file(graph, "graph_shapely.json")

    print("Ruta óptima:", ruta_optima)
    print("¡Listo! Se guardó la ruta y la imagen.")
