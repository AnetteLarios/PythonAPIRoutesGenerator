import json
import math
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

mapImage = Image.open("images/mapa.webp")

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
rangos_prohibidos = load_json_file("rangos_prohibidos.json")  # Cargamos los rangos prohibidos desde un archivo

if not rutas_predefinidas:
    rutas_predefinidas = {}
    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")

def dentro_de_rangos_prohibidos(coordenada):
    """ Verifica si una coordenada está dentro de cualquier rango prohibido """
    x, y = coordenada
    # Itera sobre todos los rangos prohibidos dentro del diccionario
    for clave, rango in rangos_prohibidos.get("rangos_prohibidos", {}).items():
        if (rango["x_min"] <= x <= rango["x_max"] and
            rango["y_min"] <= y <= rango["y_max"]):
            return True
    return False

def cruzar_rango_prohibido(coord1, coord2):
    """ Verifica si una línea entre coord1 y coord2 cruza algún rango prohibido """
    x1, y1 = coord1
    x2, y2 = coord2

    # Itera sobre todos los rangos prohibidos dentro del diccionario
    for clave, rango in rangos_prohibidos.get("rangos_prohibidos", {}).items():
        # Coordenadas del rango prohibido
        rect_x_min, rect_x_max = rango["x_min"], rango["x_max"]
        rect_y_min, rect_y_max = rango["y_min"], rango["y_max"]
        
        # Chequear si alguno de los extremos está dentro del rango
        if dentro_de_rangos_prohibidos(coord1) or dentro_de_rangos_prohibidos(coord2):
            return True
        
        # Fórmula para determinar si la línea (x1, y1) - (x2, y2) intersecta los bordes del rectángulo
        def interseccion(p1, p2, q1, q2):
            """ Comprueba si dos segmentos de línea (p1, p2) y (q1, q2) se intersectan """
            def orientacion(a, b, c):
                """ Determina la orientación de tres puntos. """
                val = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
                if val == 0:
                    return 0  # Colineal
                elif val > 0:
                    return 1  # Sentido horario
                else:
                    return 2  # Sentido antihorario
            
            o1 = orientacion(p1, p2, q1)
            o2 = orientacion(p1, p2, q2)
            o3 = orientacion(q1, q2, p1)
            o4 = orientacion(q1, q2, p2)

            # General case
            if o1 != o2 and o3 != o4:
                return True

            # Casos especiales (colinealidad)
            if o1 == 0 and en_segmento(p1, p2, q1):
                return True
            if o2 == 0 and en_segmento(p1, p2, q2):
                return True
            if o3 == 0 and en_segmento(q1, q2, p1):
                return True
            if o4 == 0 and en_segmento(q1, q2, p2):
                return True

            return False

        def en_segmento(p, q, r):
            """ Comprueba si el punto q está en el segmento pr """
            if min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= max(p[1], r[1]):
                return True
            return False
        
        # Líneas de los bordes del rectángulo (rango prohibido)
        esquina1 = (rect_x_min, rect_y_min)
        esquina2 = (rect_x_max, rect_y_min)
        esquina3 = (rect_x_max, rect_y_max)
        esquina4 = (rect_x_min, rect_y_max)
        
        # Checar intersección con cada borde del rectángulo
        if (interseccion((x1, y1), (x2, y2), esquina1, esquina2) or
            interseccion((x1, y1), (x2, y2), esquina2, esquina3) or
            interseccion((x1, y1), (x2, y2), esquina3, esquina4) or
            interseccion((x1, y1), (x2, y2), esquina4, esquina1)):
            return True
    
    return False


def obtenerCoordenadas(nodo):
    return coordenadas.get(nodo, None)

def calcular_distancia(nodo1, nodo2):
    coord1 = obtenerCoordenadas(nodo1)
    coord2 = obtenerCoordenadas(nodo2)
    
    if coord1 and coord2:
        # Verificación adicional para evitar nodos dentro de rangos prohibidos o cruce de áreas prohibidas
        if dentro_de_rangos_prohibidos(coord1) or dentro_de_rangos_prohibidos(coord2) or cruzar_rango_prohibido(coord1, coord2):
            return float('inf')  # Asignar una distancia infinita si pasa por un área prohibida

        return math.sqrt((coord2[0] - coord1[0]) ** 2 + (coord2[1] - coord1[1]) ** 2)
    
    return float('inf')

def generar_grafo_con_pesos(coordenadas):
    grafo = {}
    nodos = list(coordenadas.keys())
    
    for nodo in nodos:
        grafo[nodo] = {}
        for otro_nodo in nodos:
            if nodo != otro_nodo:
                distancia = calcular_distancia(nodo, otro_nodo)
                if distancia != float('inf') and distancia < 1000:
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

# El resto del código sigue igual como antes...


def es_nodo_principal(nodo):
    return nodo.isupper()

def completar_ruta_con_nodos_no_principales(graph, ruta, min_nodos=6):
    if len(ruta) >= min_nodos:
        return ruta

    nodos_disponibles = [nodo for nodo in graph if nodo not in ruta and not es_nodo_principal(nodo)]

    while len(ruta) < min_nodos and nodos_disponibles:
        mejor_nodo = None
        mejor_distancia = float('inf')

        for i in range(len(ruta) - 1):
            nodo_actual = ruta[i]
            nodo_siguiente = ruta[i + 1]

            for nodo_intermedio in nodos_disponibles:
                # Verificamos que no se cruce un rango prohibido
                if (not cruzar_rango_prohibido(obtenerCoordenadas(nodo_actual), obtenerCoordenadas(nodo_intermedio)) and
                    not cruzar_rango_prohibido(obtenerCoordenadas(nodo_intermedio), obtenerCoordenadas(nodo_siguiente))):

                    # Calculamos la distancia actual con el nodo intermedio
                    distancia_actual = (graph[nodo_actual].get(nodo_intermedio, float('inf')) + 
                                        graph[nodo_intermedio].get(nodo_siguiente, float('inf')))

                    if distancia_actual < mejor_distancia:
                        mejor_distancia = distancia_actual
                        mejor_nodo = nodo_intermedio

        if mejor_nodo:
            for i in range(len(ruta) - 1):
                if (graph[ruta[i]].get(mejor_nodo) and 
                    graph[mejor_nodo].get(ruta[i + 1]) and
                    not cruzar_rango_prohibido(obtenerCoordenadas(ruta[i]), obtenerCoordenadas(mejor_nodo)) and
                    not cruzar_rango_prohibido(obtenerCoordenadas(mejor_nodo), obtenerCoordenadas(ruta[i + 1]))):
                    
                    ruta.insert(i + 1, mejor_nodo)
                    nodos_disponibles.remove(mejor_nodo)
                    break

    return ruta

def ordenar_ruta_por_coordenadas(ruta):
    coordenadas_ruta = [obtenerCoordenadas(nodo) for nodo in ruta]
    
    # Ordenamos la ruta basándonos en la proximidad entre los nodos
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
        
        dibujador.line([(x1, y1), (x2, y2)], fill="black", width=30)
        dibujador.line([(x1, y1), (x2, y2)], fill="yellow", width=20)

def guardar_ruta_predefinida(start, end, ruta):
    ruta_clave = f"{start}_{end}"
    ruta_clave_inversa = f"{end}_{start}"
    
    # Ordenar la ruta original (inicio -> destino)
    ruta_ordenada = [start] + ordenar_ruta_por_coordenadas(ruta[1:-1]) + [end]
    
    # Guardar la ruta original
    rutas_predefinidas[ruta_clave] = ruta_ordenada
    
    # Guardar la ruta inversa (destino -> inicio)
    ruta_ordenada_inversa = ruta_ordenada[::-1]  # Simplemente invertimos la lista
    rutas_predefinidas[ruta_clave_inversa] = ruta_ordenada_inversa
    
    # Guardar ambas rutas en el archivo
    save_json_file(rutas_predefinidas, "rutas_predefinidas.json")
    
    print(f"Ruta {ruta_clave} guardada en rutas_predefinidas.json en orden correcto.")
    print(f"Ruta inversa {ruta_clave_inversa} guardada en rutas_predefinidas.json.")


def calcular_numero_de_nodos(coord1, coord2, base_nodos=2, umbral_distancia=500, incremento_nodos=0.5, factor_prohibido=1.2):
    """
    Calcula el número de nodos necesarios en función de la distancia y si cruza áreas prohibidas.
    - base_nodos: Número base mínimo de nodos (reducido a 2).
    - umbral_distancia: Distancia umbral a partir de la cual se agregan más nodos (aumentado a 500).
    - incremento_nodos: Número de nodos adicionales por cada vez que se supera el umbral (muy reducido a 0.5).
    - factor_prohibido: Factor multiplicador si la ruta cruza rangos prohibidos (reducido a 1.2).
    """
    # Calcular la distancia euclidiana entre las coordenadas
    distancia = math.sqrt((coord2[0] - coord1[0]) ** 2 + (coord2[1] - coord1[1]) ** 2)
    
    # Agregar nodos adicionales solo si la distancia es mayor al umbral
    nodos_adicionales = (distancia // umbral_distancia) * incremento_nodos
    
    # Número total de nodos
    numero_de_nodos = base_nodos + int(nodos_adicionales)

    # Si la ruta cruza rangos prohibidos, aplicamos el factor de penalización, más reducido
    if cruzar_rango_prohibido(coord1, coord2):
        numero_de_nodos *= factor_prohibido

    # Devolvemos el número de nodos, siempre asegurando que sea mayor o igual a base_nodos
    return max(base_nodos, int(numero_de_nodos))



def obtener_ruta_optima(start, end, graph):
    ruta_clave = f"{start}_{end}"
    
    if ruta_clave in rutas_predefinidas:
        print(f"Ruta {ruta_clave} encontrada en rutas predefinidas.")
        return rutas_predefinidas[ruta_clave]

    print(f"Calculando ruta óptima usando Dijkstra para {start} a {end}")
    ruta_optima = dijkstra(graph, start, end)
    
    # Obtener las coordenadas de los nodos de inicio y fin
    coord_start = obtenerCoordenadas(start)
    coord_end = obtenerCoordenadas(end)

    if coord_start and coord_end:
        # Calcular dinámicamente el número de nodos mínimos necesarios
        min_nodos = calcular_numero_de_nodos(coord_start, coord_end)

        # Completar la ruta con nodos intermedios
        ruta_optima = completar_ruta_con_nodos_no_principales(graph, ruta_optima, min_nodos=min_nodos)
    
    # Guardar la ruta predefinida
    guardar_ruta_predefinida(start, end, ruta_optima)
    
    return rutas_predefinidas[ruta_clave]

#Aquí se seleccionan el nodo de inicio y el nodo final 
start_node = 'S' 
end_node = 'V'    
graph = generar_grafo_con_pesos(coordenadas)
ruta_optima = obtener_ruta_optima(start_node, end_node, graph)

dibujador = ImageDraw.Draw(mapImage)
dibujar_ruta(ruta_optima, dibujador)

mapImage.save(f"routes_generated/{start_node}_{end_node}.webp")
mapImage.save(f"routes_generated/{end_node}_{start_node}.webp")

print("Ruta óptima dibujada desde", start_node, "a", end_node, ":", ruta_optima)

save_json_file(graph, "graph.json")

