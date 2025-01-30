import json
import math
import heapq
from PIL import Image, ImageDraw

# Si quieres Shapely, podrías usarlo (opcional):
# from shapely.geometry import Polygon, LineString

Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------
# 1. Cargar datos (coordinates, rangos_prohibidos, rutas_predefinidas)
# ---------------------------------------------------------------------
def load_json(filename):
    try:
        with open(filename,'r',encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No se encontró {filename}")
        return {}
    except json.JSONDecodeError:
        print(f"Error JSON en {filename}")
        return {}

def save_json(data, filename):
    with open(filename,'w',encoding='utf-8') as f:
        json.dump(data,f,indent=4)

coordenadas = load_json("coordinates.json")
rangos = load_json("rangos_prohibidos.json")
rutas_predef = load_json("rutas_predefinidas.json")
if not rutas_predef:
    rutas_predef={}
    save_json(rutas_predef,"rutas_predefinidas.json")

mapImage = Image.open("images/mapa.webp")

# ---------------------------------------------------------------------
# 2. Funciones para rangos prohibidos (rectángulos)
# ---------------------------------------------------------------------
def dentro_de_rangos(coord):
    x,y = coord
    for key, r in rangos.get("rangos_prohibidos",{}).items():
        if r["x_min"]<=x<=r["x_max"] and r["y_min"]<=y<=r["y_max"]:
            return True
    return False

def intersecta_recta(coord1,coord2):
    """Verifica si el segmento coord1->coord2
    cruza cualquiera de los rectángulos prohibidos."""
    if dentro_de_rangos(coord1) or dentro_de_rangos(coord2):
        return True
    x1,y1=coord1
    x2,y2=coord2

    # Función de colisión de segmentos
    def seg_intersect(a1,a2,b1,b2):
        def orient(p,q,r):
            val = (q[1]-p[1])*(r[0]-q[0]) - (q[0]-p[0])*(r[1]-q[1])
            if val==0:return 0
            return 1 if val>0 else 2
        def on_segment(p,q,r):
            return (min(p[0],r[0])<=q[0]<=max(p[0],r[0]) and
                    min(p[1],r[1])<=q[1]<=max(p[1],r[1]))
        o1=orient(a1,a2,b1)
        o2=orient(a1,a2,b2)
        o3=orient(b1,b2,a1)
        o4=orient(b1,b2,a2)
        if o1!=o2 and o3!=o4:
            return True
        if o1==0 and on_segment(a1,b1,a2):return True
        if o2==0 and on_segment(a1,b2,a2):return True
        if o3==0 and on_segment(b1,a1,b2):return True
        if o4==0 and on_segment(b1,a2,b2):return True
        return False

    for key,r in rangos.get("rangos_prohibidos",{}).items():
        rx1,rx2 = r["x_min"],r["x_max"]
        ry1,ry2 = r["y_min"],r["y_max"]

        # aristas del rect
        p1=(rx1,ry1); p2=(rx2,ry1)
        p3=(rx2,ry2); p4=(rx1,ry2)

        if (seg_intersect((x1,y1),(x2,y2), p1,p2) or
            seg_intersect((x1,y1),(x2,y2), p2,p3) or
            seg_intersect((x1,y1),(x2,y2), p3,p4) or
            seg_intersect((x1,y1),(x2,y2), p4,p1)):
            return True
    return False

# ---------------------------------------------------------------------
# 3. Grafo dinámico por umbral de distancia
# ---------------------------------------------------------------------
def get_coord(n):
    c=coordenadas.get(n,(None,None))
    return c

def dist(n1,n2):
    c1=get_coord(n1)
    c2=get_coord(n2)
    if None in c1 or None in c2:
        return float('inf')
    if dentro_de_rangos(c1) or dentro_de_rangos(c2):
        return float('inf')
    if intersecta_recta(c1,c2):
        return float('inf')
    dx=c2[0]-c1[0]
    dy=c2[1]-c1[1]
    return math.hypot(dx,dy)

def generar_grafo(umbral=600):
    nodos = list(coordenadas.keys())
    graph={}
    for n in nodos:
        graph[n]={}
    for i in range(len(nodos)):
        for j in range(i+1, len(nodos)):
            n1=nodos[i]
            n2=nodos[j]
            d=dist(n1,n2)
            if d<umbral and d!=float('inf'):
                graph[n1][n2]=d
                graph[n2][n1]=d
    return graph

# ---------------------------------------------------------------------
# 4. A*
# ---------------------------------------------------------------------
def heuristic(a,b):
    cA=get_coord(a)
    cB=get_coord(b)
    if None in cA or None in cB: return float('inf')
    dx=cB[0]-cA[0]
    dy=cB[1]-cA[1]
    return math.hypot(dx,dy)

def a_star(graph, start, end):
    if start not in graph or end not in graph: return []
    openSet=[]
    heapq.heappush(openSet,(0,start))
    came={}
    gScore={n: float('inf') for n in graph}
    fScore={n: float('inf') for n in graph}
    gScore[start]=0
    fScore[start]=heuristic(start,end)
    inOpen={n:False for n in graph}
    inOpen[start]=True

    while openSet:
        cf, current=heapq.heappop(openSet)
        inOpen[current]=False
        if current==end:
            return reconstruir_camino(came,current)
        if cf>fScore[current]:
            continue
        for neigh,w in graph[current].items():
            tmp=gScore[current]+w
            if tmp<gScore[neigh]:
                came[neigh]=current
                gScore[neigh]=tmp
                fScore[neigh]=tmp+heuristic(neigh,end)
                if not inOpen[neigh]:
                    heapq.heappush(openSet,(fScore[neigh],neigh))
                    inOpen[neigh]=True
    return []

def reconstruir_camino(came, actual):
    path=[actual]
    while actual in came:
        actual=came[actual]
        path.append(actual)
    path.reverse()
    return path

# ---------------------------------------------------------------------
# 5. Dibujar un trazo único (para que se vea "vectorial")
# ---------------------------------------------------------------------
def dibujar_ruta_unica(path, draw):
    coords_list = []
    for node in path:
        c = get_coord(node)
        print(f"{node} -> {c}")  # <--- Depuración

        # Revisa si c es (None, None) o si no tiene exactamente 2 elementos
        if not c or len(c)!=2 or None in c:
            print(f"¡Alerta! El nodo {node} no tiene coordenadas válidas en coordinates.json")
            continue

        # Asegúrate de convertir a int (o float)
        x, y = c
        coords_list.append((int(x), int(y)))

    if len(coords_list)<2:
        print("La ruta no tiene suficientes coordenadas para dibujar.")
        return

    # Trazar la línea
    draw.line(coords_list, fill="black", width=30)
    draw.line(coords_list, fill="yellow", width=20)


# ---------------------------------------------------------------------
# 6. Guardar / Ordenar / etc. (Opcional)
# ---------------------------------------------------------------------
def ordenar_ruta_por_coord(path):
    if len(path)<3: return path
    s=path[0]
    e=path[-1]
    mid=path[1:-1]
    mid_s=sorted(mid, key=lambda x: get_coord(x))
    return [s]+mid_s+[e]

def guardar_ruta_predefinida(start,end,path):
    k1=f"{start}_{end}"
    k2=f"{end}_{start}"
    rutas_predef[k1]=path
    rutas_predef[k2]=path[::-1]
    save_json(rutas_predef,"rutas_predefinidas.json")

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
if __name__=="__main__":
    # 1) Generar grafo con umbral
    graph=generar_grafo(umbral=600)
    
    # 2) Definir nodos de inicio y fin
    start_node="P"
    end_node="Biblioteca"
    
    print(f"Buscando ruta de {start_node} a {end_node}...")
    ruta=a_star(graph, start_node, end_node)
    
    if len(ruta)<2:
        print("No se encontró ruta :(")
    else:
        print("Ruta:", ruta)
        # Opcional: re-ordenar intermedio
        # ruta=ordenar_ruta_por_coord(ruta)
        # Guardar en predefinidas
        guardar_ruta_predefinida(start_node,end_node, ruta)
        # Dibujar
        dib=ImageDraw.Draw(mapImage)
        dibujar_ruta_unica(ruta, dib)
        # Guardar imagen final
        outname=f"new_routes/{start_node}_{end_node}.webp"
        mapImage.save(outname)
        print(f"¡Listo! Se guardó la ruta en {outname}")
