import os
import re
import cv2
import csv
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
import numpy as np
import time

# Caminho para a pasta das marcações
labels_folder         = r"C:\labels"

# Caminho para o eixo 0
central_images_folder = r"C:\0"

# Caminhos das pastas com imagens dos filtros e profundidade
filter_folders = {
                  'F1': r"C:\ACHATAMENTO",
                  'F2': r"C:\RTF",
                  'F3': r"C:\+45",
                  'F4': r"C:\+30",
                  'F5': r"C:\+15",
                  'F6': r"C:\-15",
                  'F7': r"C:\-30",
                  'F8': r"C:\-45",
}

# Atualização: Apenas uma única classe chamada "Zigoto"
class_labels = {
    0: ("Zigoto", "Zigoto", (255, 0, 0)),  # Vermelho para marcações de zigoto
}

#Altura e largura padrão da marcação
WD = 0.2 
HD = 0.2

#Caminho onde salvar os novos labels
output_folder = labels_folder

# Verificar e preparar a pasta de saída
os.makedirs(output_folder, exist_ok=True)

plt.style.use('dark_background')

# Variável global para armazenar marcações persistentes
annotations = {}

# Variáveis globais
image_folder = central_images_folder  # Começa com as imagens originais

# Carregar imagens
def extract_protocol_and_run(filename):
    """Extrai o protocolo e o número do RUN do nome do arquivo."""
    match = re.search(r'(.+)_RUN(\d+)', filename)
    if match:
        protocol = match.group(1)
        run_number = int(match.group(2))  # Converte o número do RUN para inteiro
        return protocol, run_number
    return None, None

def list_sorted_files(folder_path):
    """Lista e ordena os arquivos de forma correta com base no protocolo e número do RUN."""
    files = [f for f in os.listdir(folder_path) if f.endswith(('.jpeg', '.jpg', '.png'))]
    
    # Agrupa arquivos por protocolo
    grouped_files = {}
    for file in files:
        protocol, run_number = extract_protocol_and_run(file)
        if protocol and run_number is not None:
            if protocol not in grouped_files:
                grouped_files[protocol] = []
            grouped_files[protocol].append((run_number, file))
    
    # Ordena arquivos dentro de cada protocolo
    sorted_files = []
    for protocol in sorted(grouped_files.keys()):
        grouped_files[protocol].sort()  # Ordena por número do RUN
        sorted_files.extend([file for _, file in grouped_files[protocol]])
    
    return sorted_files

# Substitua a linha original por essa:
image_files = list_sorted_files(image_folder)

if not image_files:
    raise ValueError("Nenhuma imagem encontrada na pasta especificada. Verifique o caminho e os arquivos.")

current_index = 0
markings = []



# Variáveis globais para movimentação
dragging = False
dragged_mark = None
start_x, start_y = None, None
motion_threshold = 10  # Tolerância mínima para movimento
show_annotations = True  # Estado da exibição das marcações

def save_current_annotations():
    """Salvar as marcações da imagem atual no dicionário global."""
    image_key = get_image_key(image_folder, image_files[current_index])
    annotations[image_key] = markings

def switch_to_original(event):
    """Muda para a base de imagens originais."""
    global image_folder, current_image
    image_folder = central_images_folder

    # Salvar as marcações atuais antes de trocar para as imagens originais
    save_current_annotations()

    # Carregar a imagem original e suas marcações
    current_image = load_image(current_index)
    display_image(current_image, ax, side_ax)
    print("Exibindo imagens originais.")

def delete_all_annotations(event):
    """Excluir todas as anotações da imagem atual."""
    global markings
    markings = []
    display_image(current_image, ax, side_ax)
    print("Todas as anotações foram excluídas.")

def switch_to_filter(filter_key):
    """Muda para a base de imagens do filtro especificado."""
    global image_folder, current_image
    image_folder = filter_folders[filter_key]

    # Salvar as marcações atuais antes de trocar de filtro
    save_current_annotations()

    # Atualizar a imagem e as marcações para o novo filtro
    current_image = load_image(current_index)
    display_image(current_image, ax, side_ax)
    print(f"Exibindo imagens do filtro: {filter_key}")

def load_image(index):
    """Carregar imagem e marcações."""
    global markings
    image_path = os.path.join(image_folder, image_files[index])
    
    # Gerar o caminho do arquivo de marcação
    image_name_without_ext = os.path.splitext(image_files[index])[0]  # Remove a extensão do arquivo de imagem
    label_path = os.path.join(labels_folder, image_name_without_ext + '.txt')

    # Mensagem de depuração para mostrar onde o código está procurando o arquivo .txt
    print(f"Procurando arquivo de marcação em: {label_path}")

    # Carregar imagem
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Não foi possível carregar a imagem: {image_path}")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Carregar marcações do dicionário, se existirem
    image_key = get_image_key(image_folder, image_files[index])
    if image_key in annotations:
        markings = annotations[image_key]
    else:
        markings = []
        if os.path.exists(label_path):  # Verificar se o arquivo de marcação existe
            print(f"Arquivo de marcação encontrado: {label_path}")
            with open(label_path, 'r') as file:
                for line in file:
                    # Ler a linha e dividir os valores
                    values = line.split()

                    # Verificar o número de colunas
                    if len(values) == 6:
                        # Se houver 6 colunas, leia todas (incluindo conf)
                        class_id, x_center, y_center, width, height, conf = map(float, values)
                    elif len(values) == 5:
                        # Se houver 5 colunas, leia apenas as 5 primeiras (ignorando conf)
                        class_id, x_center, y_center, width, height = map(float, values)
                    else:
                        raise ValueError(f"Número inválido de colunas na linha: {line}")

                    markings.append([int(class_id), x_center, y_center, width, height])
        else:
            print(f"Arquivo de marcação NÃO encontrado: {label_path}")

    return image

def display_image(image, ax, side_ax):
    """Exibir imagem com ou sem marcações."""
    ax.clear()
    h, w, _ = image.shape
    ax.imshow(image)
    ax.set_title(f"Imagem {current_index + 1}/{len(image_files)}")
    
    if show_annotations:
        for mark in markings:
            class_id, x_center, y_center, width, height = mark
            x1 = int((x_center - width / 2) * w)
            y1 = int((y_center - height / 2) * h)
            x2 = int((x_center + width / 2) * w)
            y2 = int((y_center + height / 2) * h)
            label, _, color = class_labels[class_id]
            rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1, edgecolor=np.array(color) / 255, fill=False, lw=1)
            ax.add_patch(rect)
            ax.text(x1, y1 - 15, label, color=np.array(color) / 255, fontsize=10, fontweight='bold',
                    verticalalignment='top', horizontalalignment='left')
    
    add_side_list(side_ax)
    plt.draw()

def add_side_list(side_ax):
    """Adicionar lista lateral com as marcações."""
    side_ax.clear()
    side_ax.axis("off")
    side_ax.set_title("Marcações", fontsize=12, weight="bold", loc="left")
    
    for i, mark in enumerate(markings):
        class_id, x_center, y_center, _, _ = mark
        label, description, color = class_labels[class_id]
        text = f"{label} ({description}): ({x_center:.2f}, {y_center:.2f})"
        side_ax.text(0, 1 - i * 0.05, text, color=np.array(color) / 255, fontsize=10, verticalalignment="top")
    
    plt.draw()

def toggle_annotations(event):
    global show_annotations
    show_annotations = not show_annotations
    display_image(current_image, ax, side_ax)
    print("Marcações", "exibidas" if show_annotations else "ocultadas")

def on_mouse_press(event):
    """Detectar início do clique."""
    global dragging, dragged_mark, start_x, start_y

    # Verificar se o clique foi dentro do eixo da imagem (ax)
    if event.inaxes != ax:
        return  # Clique fora da imagem, ignorar

    x, y = event.xdata, event.ydata
    if x is None or y is None:
        return

    start_x, start_y = x, y
    h, w, _ = current_image.shape

    # Clique direito: excluir marcação
    if event.button == 3:
        for mark in markings:
            class_id, x_center, y_center, width, height = mark
            x1 = (x_center - width / 2) * w
            y1 = (y_center - height / 2) * h
            x2 = (x_center + width / 2) * w
            y2 = (y_center + height / 2) * h

            if x1 <= x <= x2 and y1 <= y <= y2:
                markings.remove(mark)
                display_image(current_image, ax, side_ax)
                return

    # Clique esquerdo: criar nova marcação da classe 0
    if event.button == 1:
        if markings:
            _, _, _, width, height = markings[-1]
        else:
            width, height = WD, HD  # Tamanho padrão

        x_center = x / w
        y_center = y / h

        markings.append([0, x_center, y_center, width, height])
        display_image(current_image, ax, side_ax)
        return

    # Verificar se clicou em uma marcação para movimentação
    for mark in markings:
        class_id, x_center, y_center, width, height = mark
        x1 = (x_center - width / 2) * w
        y1 = (y_center - height / 2) * h
        x2 = (x_center + width / 2) * w
        y2 = (y_center + height / 2) * h

        if x1 <= x <= x2 and y1 <= y <= y2:
            dragged_mark = mark
            dragging = True
            return

def on_mouse_release(event):
    """Detectar término do clique ou arraste."""
    global dragging, dragged_mark, start_x, start_y
    x, y = event.xdata, event.ydata
    if x is None or y is None:
        return

    h, w, _ = current_image.shape
    dragging = False

    if dragged_mark is not None and start_x is not None and start_y is not None:
        distance = np.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)
        # Se houver movimento suficiente, atualize a posição da marcação
        if distance >= motion_threshold:
            dragged_mark[1] = x / w
            dragged_mark[2] = y / h

    dragged_mark = None
    display_image(current_image, ax, side_ax)

def save_annotations(event):
    """Salvar marcações no formato YOLO."""
    label_path = os.path.join(output_folder, os.path.splitext(image_files[current_index])[0] + '.txt')
    with open(label_path, 'w') as file:
        for mark in markings:
            file.write(" ".join(map(str, mark)) + '\n')
    print(f"Anotações salvas em: {label_path}")

def save_image(event):
    """Salvar as marcações e ir para a próxima imagem."""
    global current_index, current_image
    save_annotations(event)
    current_index = (current_index + 1) % len(image_files)
    current_image = load_image(current_index)
    display_image(current_image, ax, side_ax)

def previous_image(event):
    """Voltar para a imagem anterior."""
    global current_index, current_image
    current_index = (current_index - 1) % len(image_files)
    current_image = load_image(current_index)
    display_image(current_image, ax, side_ax)

def next_image(event):
    """Ir para a próxima imagem."""
    global current_index, current_image
    current_index = (current_index + 1) % len(image_files)
    current_image = load_image(current_index)
    display_image(current_image, ax, side_ax)

def go_to_specific_image(event):
    """Ir para uma imagem específica inserida pelo usuário."""
    global current_index, current_image
    try:
        index = int(input(f"Digite o número da imagem (1 a {len(image_files)}): ")) - 1
        if 0 <= index < len(image_files):
            current_index = index
            current_image = load_image(current_index)
            display_image(current_image, ax, side_ax)
        else:
            print(f"Índice inválido. Escolha entre 1 e {len(image_files)}.")
    except ValueError:
        print("Entrada inválida. Por favor, insira um número válido.")

def get_image_key(folder, filename):
    """Gerar uma chave única para o dicionário de anotações."""
    return f"{folder}\\{filename}"

def repeat_last_annotations(event):
    """Repete as marcações da última imagem, salva e avança para a próxima."""
    global markings, current_index, current_image

    if current_index == 0:
        print("Esta é a primeira imagem, não há marcações anteriores para repetir.")
        return

    # Obter o nome do arquivo da última imagem
    previous_image_name = os.path.splitext(image_files[current_index - 1])[0]
    previous_label_path = os.path.join(labels_folder, previous_image_name + '.txt')

    # Verificar se há um arquivo de marcação na última imagem
    if os.path.exists(previous_label_path):
        new_markings = []
        with open(previous_label_path, 'r') as file:
            for line in file:
                values = line.split()
                if len(values) == 6:
                    class_id, x_center, y_center, width, height, conf = map(float, values)
                elif len(values) == 5:
                    class_id, x_center, y_center, width, height = map(float, values)
                else:
                    print(f"Ignorando linha inválida: {line}")
                    continue
                new_markings.append([int(class_id), x_center, y_center, width, height])

        markings = new_markings.copy()
        print(f"Repetidas {len(markings)} marcações da última imagem.")
        save_annotations(event)
        next_image(event)
    else:
        print("Nenhuma marcação encontrada na última imagem.")

# Carregar a primeira imagem
current_image = load_image(current_index)

# Configurar interface gráfica
fig, (ax, side_ax) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [3, 1]})
plt.subplots_adjust(bottom=0.2)
fig.patch.set_facecolor('black')  # Fundo da aplicação preto
display_image(current_image, ax, side_ax)

# Botões
axprev = plt.axes([0.05, 0.5, 0.1, 0.075], facecolor='dimgray')
axnext = plt.axes([0.05, 0.7, 0.1, 0.075], facecolor='dimgray')
axsave = plt.axes([0.45, 0.05, 0.1, 0.075], facecolor='dimgray')
axgoto = plt.axes([0.25, 0.05, 0.1, 0.075], facecolor='dimgray')
axdelete = plt.axes([0.05, 0.05, 0.1, 0.075], facecolor='dimgray')
axrepeat = plt.axes([0.70, 0.05, 0.1, 0.075], facecolor='dimgray')
ax_toggle = plt.axes([0.85, 0.05, 0.1, 0.075], facecolor='dimgray')

# Botões adicionais para os filtros
ax_filtered1 = plt.axes([0.6, 0.9, 0.075, 0.075], facecolor='dimgray')
ax_filtered2 = plt.axes([0.6, 0.8, 0.075, 0.075], facecolor='dimgray')
ax_filtered3 = plt.axes([0.6, 0.7, 0.075, 0.075], facecolor='dimgray')
ax_filtered4 = plt.axes([0.6, 0.6, 0.075, 0.075], facecolor='dimgray')
ax_filtered5 = plt.axes([0.6, 0.5, 0.075, 0.075], facecolor='dimgray')
ax_original  = plt.axes([0.6, 0.4, 0.075, 0.075], facecolor='dimgray')
ax_filtered6 = plt.axes([0.6, 0.3, 0.075, 0.075], facecolor='dimgray')
ax_filtered7 = plt.axes([0.6, 0.2, 0.075, 0.075], facecolor='dimgray')
ax_filtered8 = plt.axes([0.6, 0.1, 0.075, 0.075], facecolor='dimgray')

btn_delete = Button(axdelete, 'Excluir Tudo', color='dimgray', hovercolor='gray')
btn_prev = Button(axprev, 'Anterior', color='dimgray', hovercolor='gray')
btn_next = Button(axnext, 'Próxima', color='dimgray', hovercolor='gray')
btn_save = Button(axsave, 'Salvar + próxima', color='dimgray', hovercolor='gray')
btn_goto = Button(axgoto, 'Ir para', color='dimgray', hovercolor='gray')
btn_repeat = Button(axrepeat, 'Repetir último', color='dimgray', hovercolor='gray')
btn_filtered1 = Button(ax_filtered1, 'ACT', color='dimgray', hovercolor='gray')
btn_filtered2 = Button(ax_filtered2, 'RTF', color='dimgray', hovercolor='gray')
btn_filtered3 = Button(ax_filtered3, '+45', color='dimgray', hovercolor='gray')
btn_filtered4 = Button(ax_filtered4, '+30', color='dimgray', hovercolor='gray')
btn_filtered5 = Button(ax_filtered5, '+15', color='dimgray', hovercolor='gray')
btn_original  = Button(ax_original,   '0', color='dimgray', hovercolor='gray')
btn_filtered6 = Button(ax_filtered6, '-15', color='dimgray', hovercolor='gray')
btn_filtered7 = Button(ax_filtered7, '-30', color='dimgray', hovercolor='gray')
btn_filtered8 = Button(ax_filtered8, '-45', color='dimgray', hovercolor='gray')
btn_toggle = Button(ax_toggle, 'Mostrar/Ocultar', color='dimgray', hovercolor='gray')

btn_prev.label.set_color('white')
btn_next.label.set_color('white')
btn_save.label.set_color('white')
btn_goto.label.set_color('white')
btn_delete.label.set_color('white')
btn_repeat.label.set_color('white')
btn_filtered1.label.set_color('white')
btn_filtered2.label.set_color('white')
btn_filtered3.label.set_color('white')
btn_filtered4.label.set_color('white')
btn_filtered5.label.set_color('white')
btn_original.label.set_color('white')
btn_filtered6.label.set_color('white')
btn_filtered7.label.set_color('white')
btn_filtered8.label.set_color('white')
btn_toggle.label.set_color('white')

btn_prev.on_clicked(previous_image)
btn_next.on_clicked(next_image)
btn_save.on_clicked(save_image)
btn_goto.on_clicked(go_to_specific_image)
btn_original.on_clicked(switch_to_original)
btn_delete.on_clicked(delete_all_annotations)
btn_repeat.on_clicked(repeat_last_annotations)
btn_toggle.on_clicked(toggle_annotations)  # Mostrar/Ocultar marcações

# Criar botões para cada filtro
btn_filtered1.on_clicked(lambda event: switch_to_filter('F1'))
btn_filtered2.on_clicked(lambda event: switch_to_filter('F2'))
btn_filtered3.on_clicked(lambda event: switch_to_filter('F3'))
btn_filtered4.on_clicked(lambda event: switch_to_filter('F4'))
btn_filtered5.on_clicked(lambda event: switch_to_filter('F5'))
btn_filtered6.on_clicked(lambda event: switch_to_filter('F6'))
btn_filtered7.on_clicked(lambda event: switch_to_filter('F7'))
btn_filtered8.on_clicked(lambda event: switch_to_filter('F8'))

# Conectar eventos do mouse
cid_press = fig.canvas.mpl_connect('button_press_event', on_mouse_press)
cid_release = fig.canvas.mpl_connect('button_release_event', on_mouse_release)

plt.show()
