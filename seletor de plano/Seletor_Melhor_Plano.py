import os
import csv
import ipywidgets as widgets
from IPython.display import display
from PIL import Image
import io  # Adicione esse import no início do script


# Caminho base
base_path = "you/data/set"

# Caminho para as camadas de multiplos focos
levels = ["F+45_embryo_dataset", "F+30_embryo_dataset", "F+15_embryo_dataset", "F0_embryo_dataset", "F-15_embryo_dataset", "F-30_embryo_dataset", "F-45_embryo_dataset"]

# Inicializando variáveis globais
protocols = []
images = []
current_protocol_index = 0
current_image_index = 0
current_level_index = 3  # Começa no nível 0
selected_focus = {}

# Caminho do arquivo CSV
csv_file = "selected_focus.csv"

# Carregar protocolos
def load_protocols():
    global protocols
    protocols = os.listdir(os.path.join(base_path, levels[0]))

# Carregar imagens
def load_images():
    global images
    protocol = protocols[current_protocol_index]
    path = os.path.join(base_path, levels[0], protocol)
    images = os.listdir(path)

# Salvar foco selecionado
def save_focus(button):
    protocol = protocols[current_protocol_index]
    focus_level = levels[current_level_index]
    selected_focus[protocol] = focus_level

    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Protocol", "Focus Level"])
        for key, value in selected_focus.items():
            writer.writerow([key, value])

    print(f"Protocolo {protocol} salvo com foco {focus_level}")


def update_image():
    protocol = protocols[current_protocol_index]
    image_name = images[current_image_index]
    image_path = os.path.join(base_path, levels[current_level_index], protocol, image_name)

    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((600, 600))

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        image_widget.value = buffer.getvalue()

        label.value = f"Protocolo: {protocol}<br>Nível: {levels[current_level_index]}<br>Imagem: {image_name}"
    except Exception as e:
        label.value = f"<b>Erro ao carregar imagem:</b> {image_name}<br>{str(e)}"

# Eventos para navegação
def next_image(button):
    global current_image_index
    current_image_index = (current_image_index + 1) % len(images)
    update_image()

def prev_image(button):
    global current_image_index
    current_image_index = (current_image_index - 1) % len(images)
    update_image()

def next_protocol(button):
    global current_protocol_index
    current_protocol_index = (current_protocol_index + 1) % len(protocols)
    load_images()
    update_image()

def prev_protocol(button):
    global current_protocol_index
    current_protocol_index = (current_protocol_index - 1) % len(protocols)
    load_images()
    update_image()

def next_focus(button):
    global current_level_index
    current_level_index = (current_level_index + 1) % len(levels)
    update_image()

def prev_focus(button):
    global current_level_index
    current_level_index = (current_level_index - 1) % len(levels)
    update_image()

# Interface Gráfica para Jupyter Notebook
image_widget = widgets.Image(format='jpeg', width=600, height=600)
label = widgets.HTML(value="")

save_button = widgets.Button(description="Salvar Foco")
save_button.on_click(save_focus)

next_image_button = widgets.Button(description="Próxima Imagem")
next_image_button.on_click(next_image)

prev_image_button = widgets.Button(description="Imagem Anterior")
prev_image_button.on_click(prev_image)

next_protocol_button = widgets.Button(description="Próximo Protocolo")
next_protocol_button.on_click(next_protocol)

prev_protocol_button = widgets.Button(description="Protocolo Anterior")
prev_protocol_button.on_click(prev_protocol)

next_focus_button = widgets.Button(description="Próximo Foco")
next_focus_button.on_click(next_focus)

prev_focus_button = widgets.Button(description="Foco Anterior")
prev_focus_button.on_click(prev_focus)

# Inicializar
load_protocols()
load_images()
update_image()

# Exibir interface
display(label)
display(image_widget)
display(widgets.HBox([prev_image_button, next_image_button]))
display(widgets.HBox([prev_protocol_button, next_protocol_button]))
display(widgets.HBox([prev_focus_button, next_focus_button]))
display(save_button)
