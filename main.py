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
import csv
import sys
import datetime
import time
import numpy as np
# from psychopy import parallel #conda install -k -c conda-forge psychopy
import pygame as pg
import os

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


# Phase 0
baselineButtonPress = []
key_press_count = 0 # Counter for button presses
key_total_required = 5 # Total number of button presses required
phase0_label = "Numbre de pressions de la touche D restantes:"

# Phase 1
start_seq = [(880, 180), (1046, 180)]   # début : deux bips ascendants
end_seq   = [(440, 180), (330, 180)]    # fin  : deux bips descendants
duration_ms=10_000


# Phase 2
phase2_duration_ms = 2_000 # 1 minute = 60_000 countdown

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
        "title_text" : "Début d'expérience",
        "instruction": """Nous allons maintenant commencer l'expérience. \n
        Suivez attentivement les instructions qui apparaîtront à l'écran.\n 
          \n
        Appuyez sur la touche ➡ pour continuer.""",
        "background_color": color_cream
    },
    {
        "id": "phase0", # Activité motrice de base - Instruction
        "title_text" : "Activité motrice de base",
        "instruction": """Veuillez appuyer sur sur touche "D" avec votre index \n
        de la main dominante 5 fois, à votre rythme. \n
          \n
        Appuyez sur la touche ➡ pour démarrer.""",
        "background_color": color_cream
    },
    {
        "id": "phase0a", # Activité motrice de base - Countdown
        "title_text" : "Activité motrice de base",
        "instruction": """ Numbre de pressions de la touche "D" restantes:  \n""",
        "background_color": color_turquoise
    },
    {
        "id": "phase1a", # EEG au repos, yeux fermées - Instruction
        "title_text" : "Période de repos - Yeux fermés",
        "instruction": """Veuillez vous détendre.\n
        Vous allez passer 1 minute les yeux fermés. \n
        Un signal sonore marquera le début et la fin de cette période.\n
        Important :\n
        N'essayez pas de provoquer ni de supprimer vos tics volontairement.\n
          \n
        Appuyez sur la touche ➡ pour démarrer.
        """,
        "background_color": color_cream
    },
    {
        "id": "phase1b", # EEG au repos, yeux fermées - Countdown
        "title_text" : "Période de repos — Yeux fermés",
        "instruction": """ Fermez vous yeux, temps restant: \n""",
        "background_color": color_olive
    },
    {
        "id": "phase1c", # EEG au repos, yeux ouverts - Instruction
        "title_text" : "Période de repos — Fixez la croix",
        "instruction": """Veuillez vous détendre.\n
        Veuillez regarder et fixer la croix à l'écran pendant 1 minute, 
        L'écran changera automatiquement à la fin\n
        Important : N'essayez pas de provoquer ni de supprimer vos tics volontairement.\n
        Appuyez sur la touche ➡ pour démarrer.
        """,
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
        "id": "phase2b", # Tics spontanés - Countdown
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
        "id": "phase3b", #Tics mimicking - Countdown
        "instruction": 
        """ Imitation volontaire des tics – 10 répétitions""",
        "background_color": color_violet
    },  
    {
        "id": "phase4a", # Suppression des Tics - Instruction
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
def display_instruction(window, phase_config):
    window.fill(phase_config.get("background_color", (0, 0, 0)))

    # Load images
    try:
        image1 = pg.image.load(image_file1).convert_alpha() # Movidoc letters
        image2 = pg.image.load(image_file2).convert_alpha() # Movidoc logo	
    except pg.error as e:
        print(f"Error loading image: {e}")
        return True # Continue to display text even if images fail

    # Resize image2
    new_width = window.get_width() // 20  # Control image size here
    aspect_ratio = image2.get_height() / image2.get_width()
    image2 = pg.transform.scale(image2, (new_width, int(new_width * aspect_ratio)))
    
    # Set spacing values (easy to adjust)
    spacing_after_image1 = 40
    spacing_after_title = 40
    spacing_after_image2 = 80
    line_spacing = 30  # space between instruction lines
    
    # Create title text
    font_title = pg.font.SysFont('Segoe UI Symbol', 36, bold=True)  
    title_text = phase_config.get("title_text", "")
    title_surface = font_title.render(title_text, True, color_olive)  
    
    # Start vertical position
    center_x = window.get_width() // 2
    current_y = 100  # Start 100px from the top (you can control this too)

    # Draw image1
    image1_rect = image1.get_rect(center=(center_x, current_y + image1.get_height() // 2))
    window.blit(image1, image1_rect)
    current_y = image1_rect.bottom + spacing_after_image1

    # Draw title
    title_rect = title_surface.get_rect(center=(center_x, current_y + title_surface.get_height() // 2))
    window.blit(title_surface, title_rect)
    current_y = title_rect.bottom + spacing_after_title

    # Draw image2
    image2_rect = image2.get_rect(center=(center_x, current_y + image2.get_height() // 2))
    window.blit(image2, image2_rect)
    current_y = image2_rect.bottom + spacing_after_image2

    # Display text below image 2
    """font = pg.font.SysFont("Segoe UI Symbol", 32)
    instruction_text = phase_config.get("instruction", "")
    messages = instruction_text.split('\n')
    for i, message in enumerate(messages):
        text_surface = font.render(message.strip(), True, color_violet)
        text_rect = text_surface.get_rect(center=(center_x, current_y + i * line_spacing)) 
        window.blit(text_surface, text_rect)"""
        
    # Display instruction text
    font = pg.font.SysFont("Segoe UI Symbol", 32)
    instruction_text = phase_config.get("instruction", "")
    messages = instruction_text.split('\n')

    # Margins
    left_margin = 100
    right_margin = window.get_width() - 100
    max_line_width = right_margin - left_margin

    # Display instruction text LEFT aligned
    font = pg.font.SysFont("Segoe UI Symbol", 32)
    instruction_text = phase_config.get("instruction", "")
    messages = instruction_text.split('\n')

    left_margin = 600  # <-- left margin (adjustable)

    for i, message in enumerate(messages):
        text_surface = font.render(message.strip(), True, color_violet)
        text_rect = text_surface.get_rect(topleft=(left_margin, current_y + i * line_spacing)) 
        window.blit(text_surface, text_rect)

    pg.display.flip()
    return True # Indicate that the display happened

def display_pushbutton_countdown(window, phase_config, current_count, total_required, label):
    window.fill(phase_config.get("background_color", (0, 0, 0)))

    font = pg.font.SysFont("Segoe UI Symbol", 48)
    label_surf = font.render(label, True, color_violet)
    label_rect = label_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2 - 120))
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
        
def display_minute_countdown(window, phase_config, duration, phase_id):
    
    play_tones(start_seq)
    log_event('information_display', 'tone_start', phase_id)                    

    start_ms   = pg.time.get_ticks()                   # 60 000 ms = 60 s
    running_cd = True

    while running_cd:
        now_ms     = pg.time.get_ticks()
        remaining  = max(0, duration - (now_ms - start_ms))
        secs_total = remaining // 1000
        mm_ss      = f"{secs_total // 60}:{secs_total % 60:02d}"

        # --- drawing ---
        font_main = pg.font.SysFont("Segoe UI Symbol", 32)
        font_title = pg.font.SysFont("Segoe UI Symbol", 28, bold=True)
        
        window.fill(phase_config.get("background_color", (0, 0, 0)))
        
        # Draw title at the top center
        title_text = "Gardez les yeux fermés jusqu'au deuxième signal sonore"
        title_surf = font_title.render(title_text, True, color_violet)
        title_rect = title_surf.get_rect(center=(window.get_width() // 2, 50))  # 50px from top
        window.blit(title_surf, title_rect)


        # Draw countdown timer in the center
        timer_surf = font_main.render(mm_ss, True, color_cream)
        timer_rect = timer_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
        window.blit(timer_surf, timer_rect)
        
        pg.display.flip()

        if remaining == 0:
            running_cd = False
        pg.time.delay(50)                   # ~20 fps

    play_tones(end_seq)
    log_event('information_display', 'tone_end', phase_id)
    # ---------- fin -------------
    pg.time.wait(400)                      # laisser jouer la dernière note

def display_cross_minute_countdown(window, phase_config):
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
        font = pg.font.SysFont("Segoe UI Symbol", 32)
        timer_surf = font.render(mm_ss, True, color_cream)
        timer_rect = timer_surf.get_rect(midtop=(window.get_width() // 2, 20))
        window.blit(timer_surf, timer_rect)

        # 2) gros “+” centré
        font2 = pg.font.SysFont("Segoe UI Symbol", 60)
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
  
def log_event(event_type, event_value, current_phase_id, filename="event_log.csv"):
    """
    Logs a key press event with a high-precision timestamp and the current task phase
    to a list and optionally saves the data to a CSV file.
    
    args:
        event_type (str): Type of event (e.g., 'keypress', 'instruction_display', etc.)
        event_value (str): Value associated with the event (e.g., righ_arrow_key, D_key, F_press, start_experiment, etc.)
        current_phase_id (str): ID of the current phase in the experiment
        filename (str, optional): Name of the CSV file to save the log. Defaults to "event_log.csv".
   
    """
    # Relative time since experiment started
    elapsed_time = time.perf_counter() - experiment_start_time
    
    event_log.append({
        'elapsed_time_seconds': round(elapsed_time, 6),
        'event_type': event_type,
        'event_value': event_value,
        'task_phase': current_phase_id
    })

    print(f"Event '{event_type}' - '{event_value}' at {elapsed_time:.6f}s in phase '{current_phase_id}'")

    save_event_log(filename)

def save_event_log( filename="keypress_log.csv"):
    """
    Saves the key press data to a CSV file. 

    """
    if not event_log:
        return

    file_exists = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = event_log[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(event_log[-1])
    except Exception as e:
        print(f"Error saving event log to '{filename}': {e}")
# -----------------------------------------------------------------
#  MAIN EXPERIMENTAL LOOP – sequential over phase_configs
# -----------------------------------------------------------------
keypress_data = []
current_phase_index = 0
running = True
event_log = []  # List to store event logs

experiment_start_time = time.perf_counter()  # Start time of the experiment

while running and current_phase_index < len(phase_configs):
    cfg = phase_configs[current_phase_index] 
    phase_id = cfg["id"]
    # ----------------  A) START-EXPERIMENT PHASE  -----------------
    if phase_id == "start_experiment":
        display_instruction(window, cfg)
        log_event('instruction_display', 'welcome_message', phase_id) 
        
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    log_event('key_press', pg.key.name(event.key), phase_id)
                    waiting_for_input = False  # Move to next phase ONLY when right arrow pressed
                else:
                    pass  # Ignore all other keys
        current_phase_index += 1 # Move to the next phase
        
    # ----------------  PHASE 0: BASELINE MOTOR ACTIVITY  -----------------       
    elif phase_id == "phase0": # Activité motrice de base - Instruction *OK*
        display_instruction(window, cfg) 
        log_event('instruction_display', 'instruction_message', phase_id) 
              
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RIGHT:
                        log_event('key_press', pg.key.name(event.key), phase_id)
                        waiting_for_input = False  # Move to next phase ONLY when right arrow pressed
                    else:
                        pass  # Ignore all other keys
        current_phase_index += 1 # Move to the next phase   
    
    elif phase_id == "phase0a": # Activité motrice de base - Countdown *OK*
        counting = True # Flag to indicate if we are counting button presses
        log_event('information_display', 'counter_starts', phase_id) 
        
        while counting and running:
            display_pushbutton_countdown(window, cfg, key_press_count, key_total_required, phase0_label) # Display the countdown
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_d:
                        log_event('key_press', pg.key.name(event.key), phase_id)
                        key_press_count += 1
                    else:
                        pass  # Ignore all other keys
                    if key_press_count > key_total_required:
                        counting = False # Stop counting when the required number of presses is reached
                        current_phase_index += 1 # Move to the next phase
                        
    # ---------------- PHASE 1: BASELINE MOTOR ACTIVITY  -----------------       
    elif phase_id == "phase1a": # EEG au repos, yeux fermées - Instruction *OK*
        display_instruction(window, cfg)
        log_event('instruction_display', 'instruction_message', phase_id) 
        
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RIGHT:
                        log_event('key_press', pg.key.name(event.key), phase_id)
                        waiting_for_input = False  # Move to next phase ONLY when right arrow pressed
                    else:
                        pass  # Ignore all other keys
        current_phase_index += 1 # Move to the next phase 
        
    elif phase_id == "phase1b":   # EEG au repos, yeux fermées - Countdown *OK*              
        display_minute_countdown(window, cfg, duration_ms, phase_id) # 1 minute countdown
        
        current_phase_index += 1 # Move to the next phase     
        
    elif phase_id == "phase1c":
        display_instruction(window, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_event(event, keypress_data, phase_id)
                    waiting_for_input = False
        current_phase_index += 1

    elif phase_id == "phase1d":                
        display_cross_minute_countdown(window, cfg) #  minute countdown
        current_phase_index += 1 # Move to the next phase  
    # ---------------- PHASE 2: SPONTANEOUS TICS  -----------------   
    elif phase_id == "phase2a":
        display_instruction(window, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_event(event, keypress_data, phase_id)
                    waiting_for_input = False
        current_phase_index += 1
    elif phase_id == "phase2b":                
        display_minute_countdown(window, cfg, phase2_duration_ms) # 1 minute countdown
        current_phase_index += 1 # Move to the next phase   
    # ---------------- PHASE 3: MIMICKING TICS  -----------------
    elif phase_id == "phase3a":
        display_instruction(window, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_event(event, keypress_data, phase_id)
                    waiting_for_input = False
        current_phase_index += 1
        
    elif phase_id == "phase3b":
        counting = True # Flag to indicate if we are counting button presses
        
        while counting and running:
            display_pushbutton_countdown(window, cfg, mimicked_tic_count, mimicked_tic_total_required, phase3_label) # Display the countdown
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    log_event(event, keypress_data, phase_id)
                    mimicked_tic_count += 1
                    if mimicked_tic_count > mimicked_tic_total_required:
                        counting = False # Stop counting when the required number of presses is reached
                        current_phase_index += 1 # Move to the next phase
    # ---------------- PHASE 4: TIC SUPRESSION  -----------------
    elif phase_id == "phase4a":
        display_instruction(window, cfg) 
        waiting_for_input = True
        while waiting_for_input and running:
            for event in pg.event.get():
                if event.type == pg.K_ESCAPE:
                    running = False
                if event.type == pg.KEYDOWN:
                    log_event(event, keypress_data, phase_id)
                    waiting_for_input = False
        current_phase_index += 1
    # ---------------- PHASE 5: QUESTIONS  -----------------
    
    # ---------------- B: END OF EXPERIMENT  -----------------                       
    elif phase_id == "end_experiment":
        display_instruction(window, cfg)
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