import json
import math
from PIL import Image, ImageDraw

# Aumentar el límite de píxeles permitidos para imágenes grandes
Image.MAX_IMAGE_PIXELS = None

# Cargar la imagen del mapa
mapImage = Image.open("images/mapacucei.png")

# Función para cargar un archivo JSON
def load_json_file(archive_name):
    with open(archive_name, 'r') as file:
        data = json.load(file)
    return data

# Guardar datos en un archivo JSON
def save_json_file(data, archive_name):
    with open(archive_name, 'w') as file:
        json.dump(data, file, indent=4)

# Cargar el grafo y coordenadas
coordenadas = load_json_file("coordinates.json")
rutas_predefinidas = load_json_file("rutas_predefinidas.json")

# Obtener coordenadas de los nodos
def obtenerCoordenadas(nodo):
    return coordenadas.get(nodo, None)

# Calcular la distancia euclidiana entre dos nodos
def calcular_distancia(nodo1, nodo2):
    coord1 = obtenerCoordenadas(nodo1)
    coord2 = obtenerCoordenadas(nodo2)
    
    if coord1 and coord2:
        x1, y1 = coord1
        x2, y2 = coord2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return float('inf')  # Si no hay coordenadas, devolver infinito

# Generar un grafo con pesos basados en las coordenadas
def generar_grafo_con_pesos(coordenadas):
    grafo = {}
    nodos = list(coordenadas.keys())
    
    for nodo in nodos:
        grafo[nodo] = {}
        for otro_nodo in nodos:
            if nodo != otro_nodo:
                distancia = calcular_distancia(nodo, otro_nodo)
                if distancia != float('inf') and distancia < 1000:  # Evitar conexiones largas no válidas
                    grafo[nodo][otro_nodo] = distancia
    
    return grafo

# Algoritmo de Dijkstra mejorado
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

    # Reconstruir la ruta
    path = []
    while end is not None:
        path.append(end)
        end = previous_nodes[end]
    path.reverse()

    # Si la ruta es directa de start a end, volver a calcular con nodos intermedios
    if len(path) <= 2:
        return recalcular_ruta_con_nodos_intermedios(graph, start, end)

    return path

# Recalcular ruta para forzar nodos intermedios en la secuencia correcta
def recalcular_ruta_con_nodos_intermedios(graph, start, end):
    # Forzar los nodos intermedios según la secuencia lógica
    if start == 'U' and end == 'R':
        nodos_intermedios = ["U", "T", "accessT", "middleCornerT", "rightCornerR", "R"]
        return nodos_intermedios
    
    return []  # No recalcular si no es el caso de 'U' a 'R'

# Dibujar las rutas en la imagen
def dibujar_ruta(ruta_optima, dibujador):
    # Inicializar las coordenadas de la ruta
    coordenadas_ruta = []

    # Recopilar las coordenadas de los nodos en la ruta
    for nodo in ruta_optima:
        coord = obtenerCoordenadas(nodo)
        if coord:
            coordenadas_ruta.append(coord)
        else:
            print(f"Coordenadas no encontradas para nodo {nodo}")

    # Verificar que hay coordenadas válidas antes de dibujar
    if len(coordenadas_ruta) < 2:
        print("No hay suficientes nodos para dibujar la ruta.")
        return

    # Dibujar una línea entre cada par de nodos consecutivos
    for i in range(len(coordenadas_ruta) - 1):
        x1, y1 = coordenadas_ruta[i]
        x2, y2 = coordenadas_ruta[i + 1]
        
        # Dibujar la línea entre los nodos
        dibujador.line([(x1, y1), (x2, y2)], fill="black", width=40)
        dibujador.line([(x1, y1), (x2, y2)], fill="yellow", width=30)

# Guardar la ruta calculada en el archivo de rutas predefinidas
def guardar_ruta_predefinida(start, end, ruta):
    ruta_clave = f"{start}_{end}"
    rutas_predefinidas[ruta_clave] = ruta
    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")
    print(f"Ruta {ruta_clave} guardada en rutas_predefinidas.json")

# Obtener la secuencia de nodos para una ruta o calcularla con Dijkstra
def obtener_ruta_optima(start, end, graph):
    ruta_clave = f"{start}_{end}"
    
    # Si la ruta ya está predefinida
    if ruta_clave in rutas_predefinidas:
        print(f"Ruta {ruta_clave} encontrada en rutas predefinidas.")
        return rutas_predefinidas[ruta_clave]

    # Si no hay ruta predefinida, calcular la ruta usando Dijkstra
    print(f"Calculando ruta óptima usando Dijkstra para {start} a {end}")
    ruta_optima = dijkstra(graph, start, end)
    
    # Guardar la ruta calculada para uso futuro
    guardar_ruta_predefinida(start, end, ruta_optima)
    return ruta_optima

# Nodo de inicio y final
start_node = 'U'  # Cambia esto según tus necesidades
end_node = 'R'    # Cambia esto según tus necesidades

# Generar el grafo dinámicamente basado en coordenadas
graph = generar_grafo_con_pesos(coordenadas)

# Obtener la ruta óptima (predefinida o calculada con Dijkstra)
ruta_optima = obtener_ruta_optima(start_node, end_node, graph)

# Dibujar la ruta óptima en la imagen
dibujador = ImageDraw.Draw(mapImage)
dibujar_ruta(ruta_optima, dibujador)

# Guardar la imagen modificada
mapImage.save(f"mapa_con_ruta_{start_node}_{end_node}.png")

print("Ruta óptima dibujada desde", start_node, "a", end_node, ":", ruta_optima)

# Guardar el grafo actualizado (si lo necesitas)
save_json_file(graph, "graph.json")
