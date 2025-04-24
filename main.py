###############################################################################
#                                                                             #
#                               Main: Movidoc Tic-Track task                   #
#                                                                             #
###############################################################################

# Author: @lizbethMG
# Date: April 2025
# Description:
# Version: 1.0 (or your version number)

# Phase 0: Baseline Motor Activity (Button Press)
# Phase 1: Resting State EEG
# Phase 2: Spontaneous Tics
# Phase 3: Mimicking Tics
# Phase 4: Tic Suppression

# Import necessary libraries
import os
import sys
import datetime
import time
import numpy as np
# from psychopy import parallel #conda install -k -c conda-forge psychopy
import pygame as pg

# --- Initializations ---

# Path to images files
image_file1 = "images/Movidoc.png" # Movidoc letters
image_file2 = "images/Movidoc_logo.png" # Movidoc logo

# Where the timestamps of events will be saved
experiment_log = []  # Utilisez la même liste pour tous les événements
log_filename = "experiment_log.csv" # Définissez le nom du fichier une seule fois

# Port parallel
# port = parallel.ParallelPort(0xdff8)
 
premonitoryUrges = [] # Phase 2
cuedTics = [] # Phase 3
selfInitiatedTics = [] # Phase 3
activeSuppression = [] # Phase 4
urgeDuringActiveSuppression =  [] # Phase 4

# Color definition
color_cream = (255, 247, 239)
color_turquoise = (0, 144, 154)
color_olive = (180, 170, 5)
color_violet = (57, 47, 90)

# Initialisation Pygame
pg.init()
screen_info = pg.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
window = pg.display.set_mode((0,0),pg.FULLSCREEN) # creates a win that matches the size of the entire screen
font = pg.font.SysFont('Arial', 40)

# Phase 0
baselineButtonPress = []
key_press_count = 0 # Counter for button presses
key_total_required = 5 # Total number of button presses required
phase0_label = "Nombre de pressions de bouton restants :"

# Phase 1
start_seq = [(880, 180), (1046, 180)]   # début : deux bips ascendants
end_seq   = [(440, 180), (330, 180)]    # fin  : deux bips descendants
duration_ms=10_000
font2 = pg.font.SysFont('Arial', 60)

# Phase 2
phase2_duration_ms = 10_000 # 1 minute = 60_000 countdown

# Phase 3 
phase3_label = "Nombre tic imités restants :"
mimicked_tic_count = 0 # Counter for button presses
mimicked_tic_total_required = 5 # Total number of button presses required

# -----------------------------------------------------------
# --- Définition des Phases ---
# -----------------------------------------------------------
phase_configs = [
    {
        "id": "start_experiment", # Message initial
        "instruction": """Nous allons maintenant commencer l'expérience. \n
        Suivez attentivement les instructions qui apparaîtront à l'écran.\n 
        Appuyez sur la touche > pour continuer.""",
        "background_color": color_cream
    },
    {
        "id": "phase0", # Activité motrice de base - Instruction
        "instruction": """Veuillez appuyer sur n'importe quel touche avec votre index \n
        de la main non dominante 5 fois, à votre rythme. \n
        Appuyez sur la touche > pour démarrer.""",
        "background_color": color_cream
    },
    {
        "id": "phase0a", # Activité motrice de base - Countdown
        "instruction": """ Numbre de pressions de bouton restantes:  \n""",
        "background_color": color_turquoise
    },
    {
        "id": "phase1a", # EEG au repos, yeux fermées - Instruction
        "instruction": """Veuillez vous détendre.\n
        Vous allez passer 1 minute avec les yeux fermés, un ton vous indiquera le debut et la fin. \n
        N'essayez pas de provoquer ou de supprimer vos tics intentionnellement. \n
        Appuyez sur la touche > pour démarrer.
        """,
        "background_color": color_cream
    },
    {
        "id": "phase1b", # EEG au repos, yeux fermées
        "instruction": """ Fermez vous yeux, temps restant: \n""",
        "background_color": color_olive
    },
    {
        "id": "phase1c", # EEG au repos, yeux ouverts - Instruction
        "instruction": """Veuillez vous détendre.\n
        Veuillez regarder et fixer la croix à l'écran pendant 1 minute, 
        l'écran changera automatiquement à la fin\n
        N'essayez pas de provoquer ou de supprimer vos tics intentionnellement. \n,
         Appuyez sur la touche > pour démarrer.""",
        "background_color": color_cream
    },
    {
        "id": "phase1d", # EEG au repos, yeux ouverts - Countdown
        "instruction": """ Fermez vous yeux, temps restant: \n""",
        "background_color": color_olive
    },
    {
        "id": "phase2a", # Tics spontanés - Instruction
        "instruction": 
        """1. Asseyez-vous confortablement et détendez-vous.\n
        2. Laissez vos tics se manifester naturellement : ne les retenez pas, ne les provoquez pas.\n
        3. Dès que vous sentez une envie prémonitoire, appuyez sur la barre d’espace avec votre main dominante.""",
        "background_color": color_cream
    },
    {
        "id": "phase2b", # Tics spontanés
        "instruction": 
        """ Laissez vos tics se manifester naturellement""",
        "background_color": color_violet
    },    
    {
        "id": "phase3a", # Tics mimicking - Instruction
        "instruction": """
        1. Asseyez-vous confortablement et détendez-vous.\n
        2. Vous allez imiter, de façon volontaire, vos tics les plus fréquents et représentatifs.\n
        3. Lorsque vous êtes prêt à en imiter un : appuyez une fois sur la barre d’espace avec votre main dominante, puis exécutez le tic.\n
        4. Dès que l’imitation est terminée : appuyez à nouveau sur la barre d’espace.\n
        5. Répétez ce cycle jusqu’à avoir enregistré 10 tics imités.\n  
        6. Si un tic spontané survient, n’appuyez pas sur la barre d’espace\n
        Appuyez sur la touche > pour démarrer.""",   
        "background_color": color_cream
    },
    {
        "id": "phase3b", #Tics mimicking
        "instruction": 
        """ Imitation volontaire des tics – 10 répétitions""",
        "background_color": color_violet
    },  
    {
        "id": "phase4a", # Suppression des Tics
        "instruction": 
            """1. Asseyez-vous confortablement et détendez-vous.\n
            2. Veuillez essayer activement de supprimer ou retenir vos tics pendant 10 min.\n
            3. Dès que vous sentez une envie prémonitoire et que vous essayez de la supprimer, appuyez sur la barre d’espace avec votre main dominante.\n
            Appuyez sur la touche > pour démarrer.""",
        "background_color": color_cream
    },
    {
        "id": "phase4b", # Questionnaire sur la suppression des Tics
        "instruction": "Veuillez répondre aux questions suivants avec le clavier, en utilisant le clavier et numeros de 1 a 10. \n1. Parmis les tics que vous avez réussi à supprimer, quel a été le niveau d'intensité de besoin d'exprimer ces tics que vous avez résenti?.\nPar example, 1 equivaut a un nivel minimum de besoin de les exprimer\n10 equivaut a un nivel maximum de besoin de les exprimer\nQuand vous avez répondu, validez avec la touche d'entrée",
        "background_color": color_violet
    },
    {
        "id": "end_experiment", # Message initial
        "instruction": "FIN de l'éxperience. \nMerci de votre participation!.\nAppuyez sur Echap (Esc) pour quitter.",
        "background_color": color_cream
    }
]

# -----------------------------------------------------------------
# --- Fonctions d'Affichage Spécifiques aux Phases ---
# -----------------------------------------------------------------
def display_instruction(window, font, phase_config):
    window.fill(phase_config.get("background_color", (0, 0, 0)))

    # Load images
    try:
        image1 = pg.image.load(image_file1).convert_alpha()
        image2 = pg.image.load(image_file2).convert_alpha()
    except pg.error as e:
        print(f"Error loading image: {e}")
        return True # Continue to display text even if images fail

    # Resize image2
    new_width = window.get_width() // 6
    aspect_ratio = image2.get_height() / image2.get_width()
    new_height = int(new_width * aspect_ratio)
    image2 = pg.transform.scale(image2, (new_width, new_height))

    # Get image dimensions and positions
    image1_y_offset = 100  # Adjust this value to lower the image (increase to lower)
    image1_rect = image1.get_rect(center=(window.get_width() // 2, image1.get_height() // 2 + image1_y_offset))
    image2_rect = image2.get_rect(center=(window.get_width() // 2, window.get_height() // 2))

    # Blit (draw) images
    window.blit(image1, image1_rect)
    window.blit(image2, image2_rect)

    # Display text below image 2
    instruction_text = phase_config.get("instruction", "")
    messages = instruction_text.split('\n')
    text_y_start = image2_rect.bottom + 100 # Start text below image 2 with some spacing
    for i, message in enumerate(messages):
        text_surface = font.render(message, True, color_violet)
        text_rect = text_surface.get_rect(center=(window.get_width() // 2, text_y_start + i * 40)) # Adjust vertical spacing
        window.blit(text_surface, text_rect)

    pg.display.flip()
    return True # Indicate that the display happened

def display_pushbutton_countdown(window, font, phase_config, current_count, total_required, label):
    window.fill(phase_config.get("background_color", (0, 0, 0)))

    label_surf = font.render(label, True, color_violet)
    label_rect = label_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2 - 60))
    window.blit(label_surf, label_rect)
    # Format countdown (e.g., "3/5")
    countdown_text = f"{current_count}/{total_required}"
    text_surface = font.render(countdown_text, True, color_cream)
    text_rect = text_surface.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
    
    # Draw text
    window.blit(text_surface, text_rect)
    pg.display.flip()
    return True # Indicate that the display happened

def play_tones(sequence, *, volume=0.5, sample_rate=44100, gap_ms=30):
    """
    sequence = [(freq1, dur1_ms), (freq2, dur2_ms), ...]
    Chaque note est générée (sinusoïde 16-bit) puis lue aussitôt.
    """
    if not pg.mixer.get_init():
        pg.mixer.init(frequency=sample_rate, size=-16, channels=1)

    for freq, dur in sequence:
        # Génération du sinus en mémoire
        t = np.arange(int(sample_rate * dur / 1000))
        samples = (
            np.sin(2 * np.pi * freq * t / sample_rate) * (2**15 - 1)
        ).astype(np.int16)

        snd = pg.mixer.Sound(buffer=samples)
        snd.set_volume(volume)
        snd.play()

        pg.time.wait(dur + gap_ms)   # laisse la note se terminer + petit blanc
        
def display_minute_countdown(window, font, phase_config, duration):
    
    play_tones(start_seq)                   

    start_ms   = pg.time.get_ticks()                   # 60 000 ms = 60 s
    running_cd = True

    while running_cd:
        now_ms     = pg.time.get_ticks()
        remaining  = max(0, duration - (now_ms - start_ms))
        secs_total = remaining // 1000
        mm_ss      = f"{secs_total // 60}:{secs_total % 60:02d}"

        # --- dessin ---
        window.fill(phase_config.get("background_color", (0, 0, 0)))
        surf = font.render(mm_ss, True, color_cream)
        rect = surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
        window.blit(surf, rect)
        pg.display.flip()

        if remaining == 0:
            running_cd = False
        pg.time.delay(50)                   # ~20 fps

    play_tones(end_seq)                    # ---------- fin -------------
    pg.time.wait(400)                      # laisser jouer la dernière note

def display_cross_minute_countdown(window, font, phase_config):
    """
    • Affiche un “+” géant au centre et le décompte mm:ss en haut.
    • Les séquences start_seq / end_seq jouent au début et à la fin.
    • duration_ms peut être raccourci (10_000 ms pour test, 60_000 ms prod).
    """
    play_tones(start_seq)
    
    start_ms   = pg.time.get_ticks()
    running_cd = True

    while running_cd:
        now_ms     = pg.time.get_ticks()
        remaining  = max(0, duration_ms - (now_ms - start_ms))
        secs_total = remaining // 1000
        mm_ss      = f"{secs_total // 60}:{secs_total % 60:02d}"

        # -- dessin --
        window.fill(phase_config.get("background_color", (0, 0, 0)))

        # 1) petit compte à rebours en haut
        timer_surf = font.render(mm_ss, True, color_cream)
        timer_rect = timer_surf.get_rect(midtop=(window.get_width() // 2, 20))
        window.blit(timer_surf, timer_rect)

        # 2) gros “+” centré
        plus_surf = font2.render("+", True, color_cream)
        plus_rect = plus_surf.get_rect(center=(window.get_width() // 2,
                                               window.get_height() // 2))
        window.blit(plus_surf, plus_rect)

        pg.display.flip()

        # fin du compte à rebours
        if remaining == 0:
            running_cd = False

        pg.time.delay(50)   # ~20 fps

    # ----- bips de fin -----
    play_tones(end_seq)
    pg.time.wait(400)       # laisse jouer le dernier bip
  
def log_keypress(event, keypress_data, current_phase_id, filename="keypress_log.csv"):
    """
    Logs a key press event with a high-precision timestamp and the current task phase
    to a list and optionally saves the data to a CSV file.

    Args:
        event (pygame.event.Event): The pygame.KEYDOWN event object.
        keypress_data (list): A list to store the key press data (dictionaries).
        current_phase_id (str): The ID of the current task phase.
        filename (str, optional): The name of the CSV file to save to.
                                     Defaults to "keypress_log.csv".
    """
    timestamp_seconds = time.perf_counter()
    key_pressed = pg.key.name(event.key)
    timestamp_datetime = datetime.datetime.now().isoformat()

    # Store the timestamp, key press, and current phase
    keypress_data.append({
        'timestamp_seconds': timestamp_seconds,
        'key': key_pressed,
        'timestamp_datetime': timestamp_datetime,
        'task_phase': current_phase_id  # Added task phase
    })

    print(f"Key '{key_pressed}' pressed at {timestamp_seconds:.6f} seconds in phase '{current_phase_id}'")

    # Optionally, save to CSV after each key press
    save_keypress_log(keypress_data, filename)

def save_keypress_log(keypress_data, filename="keypress_log.csv"):
    """
    Saves the key press data to a CSV file. Includes the 'task_phase' field.

    Args:
        keypress_data (list): A list of dictionaries containing key press information.
        filename (str, optional): The name of the CSV file to save to.
                                     Defaults to "keypress_log.csv".
    """
    if not keypress_data:
        return

    file_exists = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = keypress_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(keypress_data[-1])
    except Exception as e:
        print(f"Error saving keypress log to '{filename}': {e}")

def log_event(event_name, event_data, log_data_list, filename="experiment_log.csv"):
    """
    Logs a specific event (e.g., phase start) with a high-precision timestamp
    and associated data to a list and optionally saves it to a CSV file.

    Args:
        event_name (str): The name of the event (e.g., "phase_start", "stimulus_onset").
        event_data (dict): A dictionary containing data specific to this event
                           (e.g., {'phase_id': 'start_experiment'}).
        log_data_list (list): A list to store the event data (dictionaries).
        filename (str, optional): The name of the CSV file to save to.
                                     Defaults to "experiment_log.csv".
    """
    timestamp_seconds = time.perf_counter()
    timestamp_datetime = datetime.datetime.now().isoformat()

    log_entry = {
        'timestamp_seconds': timestamp_seconds,
        'timestamp_datetime': timestamp_datetime,
        'event': event_name,
        **event_data  # Include event-specific data by unpacking the dictionary
    }

    log_data_list.append(log_entry)
    print(f"Event '{event_name}' logged at {timestamp_seconds:.6f} seconds with data: {event_data}")

    save_log_data(log_data_list, filename)

def save_log_data(log_data_list, filename="experiment_log.csv"):
    """
    Saves the logged event data to a CSV file.

    Args:
        log_data_list (list): A list of dictionaries containing event information.
        filename (str, optional): The name of the CSV file to save to.
                                     Defaults to "experiment_log.csv".
    """
    if not log_data_list:
        return

    file_exists = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = log_data_list[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(log_data_list[-1])
    except Exception as e:
        print(f"Error saving log data to '{filename}': {e}")

# -----------------------------------------------------------------
#  MAIN EXPERIMENTAL LOOP – sequential over phase_configs
# -----------------------------------------------------------------
keypress_data = []
current_phase_index = 0
running = True

while running and current_phase_index < len(phase_configs):
    cfg = phase_configs[current_phase_index] 
    phase_id = cfg["id"]
    # ----------------  A) START-EXPERIMENT PHASE  -----------------
    if phase_id == "start_experiment":
        display_instruction(window, font, cfg) 
        
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False # Move to the next phase on any key press
        current_phase_index += 1 # Move to the next phase
    # ----------------  PHASE 0: BASELINE MOTOR ACTIVITY  -----------------       
    elif phase_id == "phase0":
        display_instruction(window, font, cfg)       
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False # Move to the next phase on any key press
        current_phase_index += 1 # Move to the next phase   
    
    elif phase_id == "phase0a":
        counting = True # Flag to indicate if we are counting button presses
        
        while counting and running:
            display_pushbutton_countdown(window, font, cfg, key_press_count, key_total_required, phase0_label) # Display the countdown
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, phase_id)
                    key_press_count += 1
                    if key_press_count > key_total_required:
                        counting = False # Stop counting when the required number of presses is reached
                        current_phase_index += 1 # Move to the next phase
    # ---------------- PHASE 1: BASELINE MOTOR ACTIVITY  -----------------       
    elif phase_id == "phase1a":
        display_instruction(window, font, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False
        current_phase_index += 1 # Move to the next phase 
        
    elif phase_id == "phase1b":                
        display_minute_countdown(window, font, cfg, duration_ms) # 1 minute countdown
        current_phase_index += 1 # Move to the next phase     
        
    elif phase_id == "phase1c":
        display_instruction(window, font, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False
        current_phase_index += 1

    elif phase_id == "phase1d":                
        display_cross_minute_countdown(window, font2, cfg) #  minute countdown
        current_phase_index += 1 # Move to the next phase  
    # ---------------- PHASE 2: SPONTANEOUS TICS  -----------------   
    elif phase_id == "phase2a":
        display_instruction(window, font, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False
        current_phase_index += 1
    elif phase_id == "phase2b":                
        display_minute_countdown(window, font, cfg, phase2_duration_ms) # 1 minute countdown
        current_phase_index += 1 # Move to the next phase   
    # ---------------- PHASE 3: MIMICKING TICS  -----------------
    elif phase_id == "phase3a":
        display_instruction(window, font, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False
        current_phase_index += 1
        
    elif phase_id == "phase3b":
        counting = True # Flag to indicate if we are counting button presses
        
        while counting and running:
            display_pushbutton_countdown(window, font, cfg, mimicked_tic_count, mimicked_tic_total_required, phase3_label) # Display the countdown
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, phase_id)
                    mimicked_tic_count += 1
                    if mimicked_tic_count > mimicked_tic_total_required:
                        counting = False # Stop counting when the required number of presses is reached
                        current_phase_index += 1 # Move to the next phase
    # ---------------- PHASE 4: TIC SUPRESSION  -----------------
    elif phase_id == "phase4a":
        display_instruction(window, font, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_keypress(event, keypress_data, 'current_phase_id')
                    waiting_for_input = False
        current_phase_index += 1
    # ---------------- PHASE 5: QUESTIONS  -----------------
    
    # ---------------- B: END OF EXPERIMENT  -----------------                       
    elif phase_id == "end_experiment":
        display_instruction(window, font, cfg)
        waiting_for_exit = True
        while waiting_for_exit and running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                    waiting_for_exit = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
                        waiting_for_exit = False
                    # You might want to add logic for other keys if the experiment can restart

      
    else:
        print(f"Unknown phase ID: {phase_id}")
        current_phase_index += 1 # Avoid infinite loop

    

pg.quit()

print("\nFinal keypress data:")
for data in keypress_data:
    print(data)
    
sys.exit()