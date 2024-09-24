from PIL import Image, ImageDraw

# Cargar la imagen del mapa
mapImage = Image.open("images/mapacucei.png")

# Crear un dibujador
dibujador = ImageDraw.Draw(mapImage)

# Función para dibujar puntos
def dibujar_punto(coordenadas, radio=20, color="red"):
    x, y = coordenadas
    # Dibujar un círculo centrado en las coordenadas (x, y)
    dibujador.ellipse((x - radio, y - radio, x + radio, y + radio), fill=color)

# Lista de coordenadas de los puntos a dibujar
puntos = [
    (5800, 4800),  # Ejemplo: Coordenadas del punto U
    (5800, 5000),  # Ejemplo: Coordenadas del punto T
    (5500, 5500), # Ejemplo: Coordenadas del punto R
    (5800, 4800),
    (5800, 5000),
    (5800, 5100),
    (5775, 5100),
    (5500, 5500),
    (5775, 5500)
]

# Dibujar los puntos en la imagen
for punto in puntos:
    dibujar_punto(punto)

# Guardar la imagen modificada
mapImage.save("mapa_con_puntos.png")

