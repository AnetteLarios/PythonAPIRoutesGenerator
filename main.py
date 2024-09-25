import json
import math
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

mapImage = Image.open("images/mapacucei.webp")

def load_json_file(archive_name):
    try:
        with open(archive_name, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Archivo {archive_name} no encontrado.")
        return {}
    except json.JSONDecodeError:
        print(f"Error al decodificar el archivo {archive_name}. Asegúrate de que el archivo no esté vacío y tenga un formato JSON válido.")
        return {}

def save_json_file(data, archive_name):
    with open(archive_name, 'w') as file:
        json.dump(data, file, indent=4)

coordenadas = load_json_file("coordinates.json")
rutas_predefinidas = load_json_file("rutas_predefinidas.json")

# Inicializar el archivo si está vacío
if not rutas_predefinidas:
    rutas_predefinidas = {}
    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")

def obtenerCoordenadas(nodo):
    return coordenadas.get(nodo, None)

def calcular_distancia(nodo1, nodo2):
    coord1 = obtenerCoordenadas(nodo1)
    coord2 = obtenerCoordenadas(nodo2)
    
    if coord1 and coord2:
        x1, y1 = coord1
        x2, y2 = coord2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return float('inf')  

def generar_grafo_con_pesos(coordenadas):
    grafo = {}
    nodos = list(coordenadas.keys())
    
    for nodo in nodos:
        grafo[nodo] = {}
        for otro_nodo in nodos:
            if nodo != otro_nodo:
                distancia = calcular_distancia(nodo, otro_nodo)
                if distancia != float('inf') and distancia < 1000:  # Limitar conexiones largas
                    grafo[nodo][otro_nodo] = distancia
    return grafo

def dijkstra(graph, start, end):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous_nodes = {node: None for node in graph}
    visited = set()

    while len(visited) < len(graph):
        current_node = min((node for node in graph if node not in visited), key=distances.get)
        visited.add(current_node)

        for neighbor, weight in graph[current_node].items():
            new_distance = distances[current_node] + weight
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
        if current_node == end:
            break
    
    path = []
    while end is not None:
        path.append(end)
        end = previous_nodes[end]
    path.reverse()

    return path

def es_nodo_principal(nodo):
    """
    Verifica si el nodo es un nodo principal.
    Un nodo principal es aquel que está compuesto únicamente de una letra mayúscula (con o sin número).
    """
    return nodo.isupper()

def completar_ruta_con_nodos_no_principales(graph, ruta, min_nodos=5):
    """
    Completa la ruta añadiendo nodos intermedios que ya existen en el archivo coordinates.json,
    asegurándose de que sean nodos no principales (no formados solo por una mayúscula).
    """
    # Si la ruta ya tiene el número mínimo de nodos, no hacer nada
    if len(ruta) >= min_nodos:
        return ruta

    # Lista de nodos disponibles en el grafo que no están en la ruta y no son principales
    nodos_disponibles = [nodo for nodo in graph if nodo not in ruta and not es_nodo_principal(nodo)]

    # Insertar nodos intermedios entre los nodos actuales para completar la ruta
    while len(ruta) < min_nodos and nodos_disponibles:
        mejor_nodo = None
        mejor_distancia = float('inf')

        # Buscar el nodo intermedio más eficiente para agregar entre dos nodos consecutivos de la ruta
        for i in range(len(ruta) - 1):
            nodo_actual = ruta[i]
            nodo_siguiente = ruta[i + 1]

            for nodo_intermedio in nodos_disponibles:
                distancia_actual = graph[nodo_actual].get(nodo_intermedio, float('inf')) + graph[nodo_intermedio].get(nodo_siguiente, float('inf'))

                if distancia_actual < mejor_distancia:
                    mejor_distancia = distancia_actual
                    mejor_nodo = nodo_intermedio

        # Si se encuentra un buen nodo, insertarlo en la posición óptima y removerlo de nodos disponibles
        if mejor_nodo:
            # Insertar el nodo justo antes del nodo siguiente
            for i in range(len(ruta) - 1):
                if graph[ruta[i]].get(mejor_nodo) and graph[mejor_nodo].get(ruta[i + 1]):
                    ruta.insert(i + 1, mejor_nodo)
                    nodos_disponibles.remove(mejor_nodo)
                    break

    return ruta

def ordenar_ruta_por_coordenadas(ruta):
    """
    Ordena la ruta basándose en las coordenadas (x, y) de los nodos, tratando de mantener
    una lógica espacial coherente. En este caso, ordenaremos por la coordenada 'x' y,
    en caso de empate, por 'y'.
    """
    return sorted(ruta, key=lambda nodo: obtenerCoordenadas(nodo))

def dibujar_ruta(ruta_optima, dibujador):
    coordenadas_ruta = []

    for nodo in ruta_optima:
        coord = obtenerCoordenadas(nodo)
        if coord:
            coordenadas_ruta.append(coord)
        else:
            print(f"Coordenadas no encontradas para nodo {nodo}")

    if len(coordenadas_ruta) < 2:
        print("No hay suficientes nodos para dibujar la ruta.")
        return

    for i in range(len(coordenadas_ruta) - 1):
        x1, y1 = coordenadas_ruta[i]
        x2, y2 = coordenadas_ruta[i + 1]
        
        dibujador.line([(x1, y1), (x2, y2)], fill="black", width=35)
        dibujador.line([(x1, y1), (x2, y2)], fill="yellow", width=25)

def guardar_ruta_predefinida(start, end, ruta):
    ruta_clave = f"{start}_{end}"
    rutas_predefinidas[ruta_clave] = ruta
    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")
    print(f"Ruta {ruta_clave} guardada en rutas_predefinidas.json")

def obtener_ruta_optima(start, end, graph):
    ruta_clave = f"{start}_{end}"
    
    if ruta_clave in rutas_predefinidas:
        print(f"Ruta {ruta_clave} encontrada en rutas predefinidas.")
        return rutas_predefinidas[ruta_clave]

    print(f"Calculando ruta óptima usando Dijkstra para {start} a {end}")
    ruta_optima = dijkstra(graph, start, end)
    
    # Asegurarse de que la ruta tenga al menos 5 nodos y que los intermedios no sean principales
    ruta_optima = completar_ruta_con_nodos_no_principales(graph, ruta_optima, min_nodos=5)
    
    # Ordenar la ruta por las coordenadas (x, y)
    ruta_optima = ordenar_ruta_por_coordenadas(ruta_optima)
    
    guardar_ruta_predefinida(start, end, ruta_optima)
    return ruta_optima

start_node = 'V2' 
end_node = 'R'    

graph = generar_grafo_con_pesos(coordenadas)
ruta_optima = obtener_ruta_optima(start_node, end_node, graph)

# Guardar el grafo con un identificador
graph_key = f"{start_node}_{end_node}"
graph_data = {graph_key: graph}
save_json_file(graph_data, "graph.json")

dibujador = ImageDraw.Draw(mapImage)
dibujar_ruta(ruta_optima, dibujador)

mapImage.save(f"{start_node}_{end_node}.webp")

print("Ruta óptima dibujada desde", start_node, "a", end_node, ":", ruta_optima)

save_json_file(graph, "graph.json")
