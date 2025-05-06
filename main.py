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
import pygame as pg
import serial #conda install -k -c conda-forge pyserial
# -----------------------------------------------------------
# --- INITIALIZATIONS ---
# -----------------------------------------------------------

#  PARALLEL‑PORT SET‑UP  (works even on a machine with no LPT port)

try: 
    from psychopy import parallel #conda install -k -c conda-forge psychopy
    PORT_ADDRESS = 0xdff8 # Port address for parallel port (LPT1) /Confirm with Device Manager
    _port = parallel.ParallelPort(PORT_ADDRESS) # initialise the port once
    _port.setData(0) # keeps lines low at launch
    HAVE_PARALLEL = True
    print("[trigger] LPT initialised at 0x{:X}".format(PORT_ADDRESS))
except Exception as e:
    _port = None
    HAVE_PARALLEL = False
    print("[trigger] No parallel port available – running without hardware triggers\n", e)
    print("          (error was:", e, ")")
    
# SERIAL (NeoPixel) SET‑UP
SERIAL_PORT = 'COM8'          # ← your Arduino appears on COM8
BAUD_RATE   = 9600            # must match Serial.begin() in the sketch
try:
    neo_ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"[Neopixel] Serial opened on {SERIAL_PORT} @ {BAUD_RATE} baud")
except serial.SerialException as e:
    neo_ser = None            # run gracefully without LEDs if unplugged
    print("[Neopixel] Could not open serial port – LEDs disabled\n", e)
    
#--- constants / trigger map ---

TRIG_EXP_START   = 1        # experiment begins
TRIG_PHASE_BASE  = 10       # will add phase index (phase0 = 10, phase1 = 11…)
TRIG_KEY_MAP = {                # behavioural keys
    'd': 31,
    'f': 32,
    's': 33,
    't': 34,
    'right': 40
}
experiment_start_time = None # (log_event sets t = 0 *and* fires EXP_START)

# Path to images files
image_file1 = "images/Movidoc.png" # Movidoc letters
image_file2 = "images/Movidoc_logo.png" # Movidoc logo

# Where the timestamps of events will be saved
# LOGGING: keep file handle open the whole experiment
event_log = []  # List to store event logs

LOG_FIELDNAMES = ['elapsed_time_seconds', 'event_type',
                  'event_value', 'task_phase']

log_filename = f"event_log_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
log_fh = open(log_filename, 'w', newline='')               # stays open
log_writer = csv.DictWriter(log_fh, fieldnames=LOG_FIELDNAMES)
log_writer.writeheader()                                   # CSV header
log_fh.flush()                                             # force header to disk                                        # make sure header hits disk

# Color definition
color_cream = (255, 247, 239)
color_turquoise = (0, 144, 154)
color_olive = (180, 170, 5)
color_violet = (57, 47, 90)

# Initialisation Pygame
pg.init()
pg.mixer.init(frequency=44100, size=-16, channels=1) # Initialize the mixer for sound playback

screen_info = pg.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
window = pg.display.set_mode((0,0),pg.FULLSCREEN) # creates a win that matches the size of the entire screen

DEBUG = True # ← flip to False for real runs

# Phase 0 - Activité motrice de base
baselineButtonPress = []
key_press_count = 0 # Counter for button presses
KEY_TOTAL_REQUIRED = 10 if not DEBUG else 5 # Total number of button presses required
phase0_label = "Nombre d'appuis de la touche D restantes:"

# Phase 1 - EEG au repos
start_seq = [(880, 180), (1046, 180)]   # début : deux bips ascendants
end_seq   = [(440, 180), (330, 180)]    # fin  : deux bips descendants
REST_EYES_CLOSED_MS = 60_000 if not DEBUG else 5_000 # 1 minute = 60_000 countdown
REST_EYES_OPEN_MS   = 60_000 if not DEBUG else 5_000

# Phase 2 - Tics spontanés
SPONT_TICS_MS = 600_000 if not DEBUG else 10_000 # 10 minute = 600_000 countdown

# Phase 3  - Tics mimicking
mimicked_tic_count = 0 # Counter for button presses
MIMICKED_TOTAL_REQUIRED = 10 if not DEBUG else 5

# Phase 4  - Tics supression
SUPPRESSION_MS = 600_000 if not DEBUG else 10_000 
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
        de la main dominante, à votre rythme. \n
          \n
        Appuyez sur la touche ➡ pour commencer.""",
        "background_color": color_cream
    },
    {
        "id": "phase0a", # Activité motrice de base - Countdown
        "title_text" : "Activité motrice de base",
        "instruction": """ Nombre d'appuis de la touche "D" restantes:  \n""",
        "background_color": color_turquoise
    },
    {
        "id": "phase1a", # EEG au repos, yeux fermées - Instruction
        "title_text" : "Période de repos - Yeux fermés",
        "instruction": """Veuillez vous détendre.\n
        Vous allez passer quelques instants les yeux fermés. \n
        Un signal sonore marquera le début et la fin de cette période.\n
        Important : N'essayez pas de provoquer ni de supprimer vos tics volontairement.\n
          \n
        Appuyez sur la touche ➡ pour commencer.
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
        "instruction": """
        Veuillez vous détendre.\n
        Veuillez regarder et fixer la croix à l'écran pendant quelques instants.\n, 
        l'écran changera automatiquement à la fin.\n
        Important : N'essayez pas de provoquer ni de supprimer vos tics volontairement.\n
        Appuyez sur la touche ➡ pour commencer.
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
        "title_text" : "Tics spontanés",
        "instruction": """
        Veuillez vous détendre.\n
        Laissez vos tics se manifester naturellement pendant quelques minutes.\n
        Ne les retenez pas et ne les provoquez pas. \n
        - Appuyez sur la touche D dès que vous sentez une envie prémonitoire (D pour début).
        - Appuyez sur la touche F dès que le tic est terminé (F pour fin).\n
        Utilisez votre main dominante et l’index pour appuyer sur les touches.\n
        \n
        Appuyez sur la touche ➡ pour commencer.
        
        """,
        "background_color": color_cream
    },
    {
        "id": "phase2b", # Tics spontanés - Countdown
        "title_text" : """Laissez vos tics se manifester naturellement.\n
        Appuyez sur D pour marquer le début.\n
        Appuyez sur F pour marquer la fin.""",
        "instruction": 
        """ Laissez vos tics se manifester naturellement""",
        "background_color": color_violet
    },    
    {
        "id": "phase3a", # Tics mimicking - Instruction
        "title_text" : "Tics spontanés",
        "instruction": """
        Veuillez vous détendre.\n
        Vous allez imiter 10 fois vos tics les plus fréquents.\n
        1. Quand vous êtes prêt : appuyez sur D (début) et exécutez le tic.\n
        2. À la fin : appuyez sur F (fin).\n
        3. Répétez jusqu'à le nombre de tics indiqués.\n  
        Si un tic spontané survient, appuyez sur T pour le signaler (tic).\n
        \n
        Appuyez sur la touche ➡ pour commencer.
        """,   
        "background_color": color_cream
    },
    {
        "id": "phase3b", #Tics mimicking - Countdown
        "title_text" : """ 
        Imitation volontaire des tics, plusieurs répétitions \n
        Appuyez sur D pour marquer le début.\n
        Appuyez sur F pour marquer la fin. \n
        Appuyez sur T pour marquer un tic spontané.
        """,
        "background_color": color_turquoise
    },  
    {
        "id": "phase4a", # Suppression des Tics - Instruction
        "instruction": 
            """Veuillez vous détendre.\n
            Vous allez essayer activement de supprimer ou retenir vos tics pendant quelques minutes.\n
            - Appuyez sur S pour signaler une intention de tic supprimée.\n
            - Appuyez sur T pour signaler un tic spontané que vous n’avez pas réussi à supprimer.\n
            \n
            Appuyez sur la touche ➡ pour commencer.""",
        "background_color": color_cream
    },
    {
        "id": "phase4b", # Suppression des Tics
        "title_text" : """ 
        Suppression volontaire des tics \n
        Appuyez sur S pour marquer un tic supprimé.\n
        Appuyez sur T pour marquer un tic spontané.
        """,
        "background_color": color_turquoise
    },  
    {
        "id": "end_experiment", # Message initial
        "title_text" : "Fin de l'expérience",
        "instruction": """
        Merci d'avoir participé à cette expérience.\n
        Veuillez patienter l'arrivé de l'éxperimentateur.  \n
        """,
        "background_color": color_cream
    }
]

# -----------------------------------------------------------------
# --- Functionsc/ Helpers  ---
# -----------------------------------------------------------------
def send_led(cmd: str):
    """Send a single text command to the Arduino, terminated by \\n."""
    if neo_ser and neo_ser.is_open:
        try:
            neo_ser.write((cmd + '\n').encode('ascii'))
        except serial.SerialException:
            pass   # ignore runtime cable disconnects

def send_trigger(code, pulse_ms = 5):
    """Pulse `code` on the LPT lines; silently no‑op if no port."""
    if not HAVE_PARALLEL:
        print(f"[trigger] (mock) {code} (no LPT port)")
        return
    _port.setData(code)
    pg.time.wait(pulse_ms)      # needs ≥2 ms for actiCHamp, 5 ms is safe
    _port.setData(0)
    print(f"[trigger] Sent {code}  ({pulse_ms} ms)")

def trigger_phase_start(phase_idx):
    """
    ➊ Fire a TTL pulse on the parallel port (10 + phase_idx)
    ➋ Tell the NeoPixel rings which phase we entered
       • phases 0‑4  → send '0'‑'4'
       • any later   → send '0'‑'4' again (you can expand later)
    """
    send_trigger(TRIG_PHASE_BASE + phase_idx)
    # ------- LED command -------
    if   phase_idx == 0: send_led('0')
    elif phase_idx == 1: send_led('1')
    elif phase_idx == 2: send_led('2')
    elif phase_idx == 3: send_led('3')
    elif phase_idx == 4: send_led('4')
    # phase 5+ all reuse colours 0‑4 – tweak if you want more colours

        
def log_event(event_type, event_value, current_phase_id):
    """ ────────────────────────────────────────────────────────────────
    Centralised logger
      • Aligns the software clock (t = 0) with the first EXP_START
        hardware trigger.
      • Sends additional TTL pulses for key presses.
      • Writes one CSV row and flushes immediately.
      • Keeps an in‑memory copy in `event_log`.
    ────────────────────────────────────────────────────────────────
    """
    
    # --------------------------------------------------------------
    # 1 · Establish common t = 0 and fire EXP_START once
    # --------------------------------------------------------------
    global experiment_start_time      # defined at module level
    
    if experiment_start_time is None:  # first ever event!
        experiment_start_time = time.perf_counter()
        send_trigger(TRIG_EXP_START)   # 5 ms pulse on the LPT

    # --------------------------------------------------------------
    # 2 · Optionally fire a key‑specific trigger (D / F / S / T)
    # --------------------------------------------------------------
    if event_type == 'key_press':
        trig = TRIG_KEY_MAP.get(event_value.lower())   # returns None if key not mapped
        if trig is not None:
            send_trigger(trig)
    
    # --------------------------------------------------------------
    # 3 · Compute elapsed time for the CSV row
    # --------------------------------------------------------------
    elapsed_time = time.perf_counter() - experiment_start_time

    # --------------------------------------------------------------
    # 4 · Write the row to the open CSV and flush
    # --------------------------------------------------------------
    row = {
        'elapsed_time_seconds': round(elapsed_time, 6),
        'event_type'         : event_type,
        'event_value'        : event_value,
        'task_phase'         : current_phase_id
    }
    log_writer.writerow(row)
    log_fh.flush()                      # make sure it’s on disk
    event_log.append(row)               # optional RAM copy

    # --------------------------------------------------------------
    # 5 · Console echo (useful in DEBUG mode)
    # --------------------------------------------------------------
    print(f"{row['elapsed_time_seconds']:>9.3f}s  "
          f"{event_type:<18} {event_value}  ({current_phase_id})")
    
def display_instruction(window, phase_config):
    # Fonts
    font_title = pg.font.SysFont('Segoe UI Symbol', 36, bold=True)
    font_text = pg.font.SysFont("Segoe UI Symbol", 32)

    # Colors
    bg_color = phase_config.get("background_color", (0, 0, 0))

    # Margins & spacing
    image_margin_top = 50
    side_margin = 60
    title_margin_top = 60
    text_margin_top = 80
    text_line_spacing = 30
    text_left_margin = 100

    window.fill(bg_color)

    # Load images
    try:
        image1 = pg.image.load(image_file1).convert_alpha()  # Movidoc center
        image2 = pg.image.load(image_file2).convert_alpha()  # Logo right
    except pg.error as e:
        print(f"Error loading image: {e}")
        return True

    # Resize logo (image2)
    new_width = window.get_width() // 20
    aspect_ratio = image2.get_height() / image2.get_width()
    image2 = pg.transform.scale(image2, (new_width, int(new_width * aspect_ratio)))

    # Draw image1 (Movidoc) centered at top
    image1_rect = image1.get_rect(midtop=(window.get_width() // 2, image_margin_top))
    window.blit(image1, image1_rect)

    # Draw image2 (logo) top-right
    image2_rect = image2.get_rect(topright=(window.get_width() - side_margin, image_margin_top))
    window.blit(image2, image2_rect)

    # Draw title below the tallest image
    top_images_bottom = max(image1_rect.bottom, image2_rect.bottom)
    title_text = phase_config.get("title_text", "")
    title_surf = font_title.render(title_text, True, color_olive)
    title_rect = title_surf.get_rect(center=(window.get_width() // 2, top_images_bottom + title_margin_top))
    window.blit(title_surf, title_rect)

    # Instruction text
    instruction_text = phase_config.get("instruction", "")
    messages = instruction_text.split('\n')
    current_y = title_rect.bottom + text_margin_top

    for i, message in enumerate(messages):
        message = message.strip()
        if not message:
            continue
        text_surface = font_text.render(message, True, color_violet)
        text_rect = text_surface.get_rect(topleft=(text_left_margin, current_y + i * text_line_spacing))
        window.blit(text_surface, text_rect)

    pg.display.flip()
    return True

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
    sequence = [(freq_hz, dur_ms), ...]
    Generates each sine tone once and plays it immediately.
    """
    for freq, dur in sequence:
        t = np.arange(int(sample_rate * dur / 1000))
        samples = (np.sin(2 * np.pi * freq * t / sample_rate) * (2**15 - 1)
                  ).astype(np.int16)

        snd = pg.mixer.Sound(buffer=samples)
        snd.set_volume(volume)
        snd.play()

        pg.time.wait(dur + gap_ms)  # leave a short gap before next tone
        
def display_minute_countdown(window, phase_config, duration_ms, phase_id):
    
    play_tones(start_seq)
    log_event('information_display', 'tone_start', phase_id)                    

    start_ms   = pg.time.get_ticks()                   # 60 000 ms = 60 s
    running_cd = True

    while running_cd:
        now_ms     = pg.time.get_ticks()
        remaining  = max(0, duration_ms - (now_ms - start_ms))
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
    pg.time.wait(50)                      # laisser jouer la dernière note

def display_cross_minute_countdown(window, phase_config, duration_ms, phase_id):
    """
    • Affiche un “+” géant au centre et le décompte mm:ss en haut.
    • Les séquences start_seq / end_seq jouent au début et à la fin.
    • duration_ms peut être raccourci (10_000 ms pour test, 60_000 ms prod).
    """
    play_tones(start_seq)
    log_event('information_display', 'tone_start', phase_id)  
    
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
    log_event('information_display', 'tone_end', phase_id)  
    pg.time.wait(50)       # laisse jouer le dernier bip

def display_tic_tagging_timer(window, phase_config, duration, phase_id):
    play_tones(start_seq)
    log_event('information_display', 'tone_start', phase_id)

    start_ms = pg.time.get_ticks()
    running = True

    font_main = pg.font.SysFont("Segoe UI Symbol", 48)
    font_title = pg.font.SysFont("Segoe UI Symbol", 20, )
    font_feedback = pg.font.SysFont("Segoe UI Symbol", 26)

    feedback_text = ""
    feedback_color = None
    feedback_timer_start = 0
    feedback_duration = 500  # ms

    bg_color = phase_config.get("background_color", (0, 0, 0))

    while running:
        now_ms = pg.time.get_ticks()
        elapsed = now_ms - start_ms
        remaining = max(0, duration - elapsed)
        secs_total = remaining // 1000
        mm_ss = f"{secs_total // 60}:{secs_total % 60:02d}"

        # --- Event handling ---
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_d:
                    log_event("key_press", "D", phase_id)
                    feedback_text = "Début marqué"
                    feedback_color = color_turquoise
                    feedback_timer_start = now_ms
                elif event.key == pg.K_f:
                    log_event("key_press", "F", phase_id)
                    feedback_text = "Fin marquée"
                    feedback_color = color_olive
                    feedback_timer_start = now_ms

        # --- Drawing ---
        window.fill(bg_color)

        # Draw multi-line title from phase_config["title_text"]
        title_text = phase_config.get("title_text", "")
        title_lines = title_text.strip().split('\n')

        line_spacing = 20
        start_y = 50  # Distance from top

        for i, line in enumerate(title_lines):
            line = line.strip()
            if not line:
                continue
            title_surf = font_title.render(line, True, color_cream)
            title_rect = title_surf.get_rect(center=(window.get_width() // 2, start_y + i * line_spacing))
            window.blit(title_surf, title_rect)

        # Draw countdown lower on screen
        timer_y = window.get_height() // 2 + 60
        timer_surf = font_main.render(mm_ss, True, color_cream)
        timer_rect = timer_surf.get_rect(center=(window.get_width() // 2, timer_y))
        window.blit(timer_surf, timer_rect)

        # Feedback message below timer
        if feedback_text and now_ms - feedback_timer_start < feedback_duration:
            fb_surf = font_feedback.render(feedback_text, True, feedback_color)
            fb_rect = fb_surf.get_rect(center=(window.get_width() // 2, timer_rect.bottom + 40))
            window.blit(fb_surf, fb_rect)

        pg.display.flip()

        if remaining == 0:
            running = False
        pg.time.delay(30)

    play_tones(end_seq)
    log_event('information_display', 'tone_end', phase_id)
    pg.time.wait(50)

def display_mimicked_tics_phase(window, phase_config, phase_id, mimicked_tic_total_required):
    # Fonts
    font_title = pg.font.SysFont("Segoe UI Symbol", 20)
    font_counter = pg.font.SysFont("Segoe UI Symbol", 48)
    font_feedback = pg.font.SysFont("Segoe UI Symbol", 26)

    # Background color
    bg_color = phase_config.get("background_color", (0, 0, 0))

    # Feedback settings
    feedback_text = ""
    feedback_color = None
    feedback_start_time = 0
    feedback_duration = 500  # ms

    # State
    mimicked_tic_count = 0
    awaiting_f = False  # Only count D-F pairs
    running = True

    while running:
        now_ms = pg.time.get_ticks()

        # --- Event handling ---
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return  # exit early

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_d:
                    log_event("key_press", "D", phase_id)
                    feedback_text = "Début marqué"
                    feedback_color = color_violet
                    feedback_start_time = now_ms
                    awaiting_f = True
                elif event.key == pg.K_f:
                    log_event("key_press", "F", phase_id)
                    feedback_text = "Fin marquée"
                    feedback_color = color_olive
                    feedback_start_time = now_ms
                    if awaiting_f:
                        mimicked_tic_count += 1
                        awaiting_f = False
                        log_event("tic_mimicked_count", str(mimicked_tic_count), phase_id)
                elif event.key == pg.K_t:
                    log_event("key_press", "T", phase_id)
                    feedback_text = "Tic spontané enregistré"
                    feedback_color = color_cream
                    feedback_start_time = now_ms

        # --- Drawing ---
        window.fill(bg_color)

        # Draw instruction title (multi-line support)
        title_text = phase_config.get("title_text", "")
        lines = title_text.strip().split('\n')
        
        line_spacing = 20
        for i, line in enumerate(lines):
            surf = font_title.render(line.strip(), True, color_cream)
            rect = surf.get_rect(center=(window.get_width() // 2, 50 + i * line_spacing))
            window.blit(surf, rect)

        # Draw counter (center)
        counter_text = f"{mimicked_tic_count} / {mimicked_tic_total_required}"
        counter_surf = font_counter.render(counter_text, True, color_cream)
        counter_rect = counter_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
        window.blit(counter_surf, counter_rect)

        # Show feedback below counter
        if feedback_text and now_ms - feedback_start_time < feedback_duration:
            fb_surf = font_feedback.render(feedback_text, True, feedback_color)
            fb_rect = fb_surf.get_rect(center=(window.get_width() // 2, counter_rect.bottom + 40))
            window.blit(fb_surf, fb_rect)

        pg.display.flip()
        pg.time.delay(30)

        # End phase when all mimicked tics are completed
        if mimicked_tic_count >= mimicked_tic_total_required:
            running = False

    # Small pause at the end
    pg.time.wait(50)

def display_suppression_phase(window, phase_config, phase_id, duration_ms):
    # Fonts
    font_title = pg.font.SysFont("Segoe UI Symbol", 20)
    font_main = pg.font.SysFont("Segoe UI Symbol", 48)
    font_feedback = pg.font.SysFont("Segoe UI Symbol", 26)

    bg_color = phase_config.get("background_color", (0, 0, 0))

    # Feedback
    feedback_text = ""
    feedback_color = None
    feedback_start_time = 0
    feedback_duration = 500  # ms

    # Counters
    suppressed_count = 0
    spontaneous_count = 0

    start_time = pg.time.get_ticks()
    running = True

    while running:
        now = pg.time.get_ticks()
        elapsed = now - start_time
        remaining = max(0, duration_ms - elapsed)
        mm_ss = f"{(remaining // 1000) // 60}:{(remaining // 1000) % 60:02d}"

        # --- Event handling ---
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    log_event("key_press", "s", phase_id)
                    suppressed_count += 1
                    feedback_text = "Tic supprimé"
                    feedback_color = color_violet
                    feedback_start_time = now
                elif event.key == pg.K_t:
                    log_event("key_press", "t", phase_id)
                    spontaneous_count += 1
                    feedback_text = "Tic spontané"
                    feedback_color = color_turquoise
                    feedback_start_time = now

        # --- Drawing ---
        window.fill(bg_color)

        # Title
        title_text = phase_config.get("title_text", "")
        lines = title_text.strip().split('\n')
        line_spacing = 36
        for i, line in enumerate(lines):
            surf = font_title.render(line.strip(), True, color_cream)
            rect = surf.get_rect(center=(window.get_width() // 2, 50 + i * line_spacing))
            window.blit(surf, rect)

        # Countdown
        timer_surf = font_main.render(mm_ss, True, color_cream)
        timer_rect = timer_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2 - 50))
        window.blit(timer_surf, timer_rect)

        # Counters
        counter_text = f"Supprimés : {suppressed_count}   |   Spontanés : {spontaneous_count}"
        counter_surf = font_feedback.render(counter_text, True, color_cream)
        counter_rect = counter_surf.get_rect(center=(window.get_width() // 2, timer_rect.bottom + 40))
        window.blit(counter_surf, counter_rect)

        # Feedback (if visible)
        if feedback_text and now - feedback_start_time < feedback_duration:
            fb_surf = font_feedback.render(feedback_text, True, feedback_color)
            fb_rect = fb_surf.get_rect(center=(window.get_width() // 2, counter_rect.bottom + 40))
            window.blit(fb_surf, fb_rect)

        pg.display.flip()
        pg.time.delay(30)

        if remaining <= 0:
            running = False

    pg.time.wait(50)
    log_event("information_display", "suppression_phase_end", phase_id)

def wait_for_key_press(target_key, phase_id):
    """
    Waits for the user to press a specific key.
    Returns True if the key was pressed, False if the window was closed.
    """
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False  # signals to stop the experiment
            if event.type == pg.KEYDOWN:
                if event.key == target_key:
                    log_event('key_press', pg.key.name(event.key), phase_id)
                    return True
                else:
                    pass  # ignore other keys
# -----------------------------------------------------------------
#  MAIN EXPERIMENTAL LOOP – sequential over phase_configs
# -----------------------------------------------------------------
current_phase_index = 0
running = True

while running and current_phase_index < len(phase_configs):
    cfg = phase_configs[current_phase_index] 
    phase_id = cfg["id"]
      
    # ----------------  A) START-EXPERIMENT PHASE  -----------------
    if phase_id == "start_experiment": # *ok*
        display_instruction(window, cfg)
        send_led('START')          # <‑‑ lights green once
        log_event('instruction_display', 'welcome_message', phase_id)             
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press
        current_phase_index += 1 # Move to the next phase
        
    # ----------------  PHASE 0: BASELINE MOTOR ACTIVITY  -----------------       
    elif phase_id == "phase0": # Activité motrice de base - Instruction  *ok*
        
        display_instruction(window, cfg) 
        log_event('instruction_display', 'instruction_message', phase_id)
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press
        current_phase_index += 1 # Move to the next phase   
    
    elif phase_id == "phase0a": # Activité motrice de base - Countdown *ok*
        trigger_phase_start(0)           # 10
        key_press_count = 0 # Reset key press count
        counting = True # Flag to indicate if we are counting button presses
        log_event('information_display', 'counter_starts', phase_id) 
        
        while counting and running:
            display_pushbutton_countdown(window, cfg, key_press_count, KEY_TOTAL_REQUIRED, phase0_label) # Display the countdown
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_d:
                        log_event('key_press', pg.key.name(event.key), phase_id)
                        key_press_count += 1
                    else:
                        pass  # Ignore all other keys
                    if key_press_count >= KEY_TOTAL_REQUIRED:
                        counting = False # Stop counting when the required number of presses is reached
                        current_phase_index += 1 # Move to the next phase
                        
    # ---------------- PHASE 1: BASELINE MOTOR ACTIVITY  -----------------       
    elif phase_id == "phase1a": # EEG au repos, yeux fermées - Instruction *OK*
        trigger_phase_start(1)           # 11
        display_instruction(window, cfg)
        log_event('instruction_display', 'instruction_message', phase_id) 
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press      
        current_phase_index += 1 # Move to the next phase
        
    elif phase_id == "phase1b":   # EEG au repos, yeux fermées - Countdown *OK*              
        trigger_phase_start(2)           # 12
        display_minute_countdown(window, cfg, REST_EYES_CLOSED_MS, phase_id) # 1 minute countdown
        current_phase_index += 1 # Move to the next phase   
        
    elif phase_id == "phase1c": # EEG au repos, yeux ouverts - Instruction *OK*
        trigger_phase_start(3)           # 13
        display_instruction(window, cfg)
        log_event('instruction_display', 'instruction_message', phase_id)
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press 
        current_phase_index += 1

    elif phase_id == "phase1d": # EEG au repos, yeux ouverts - Countdown   *OK*            
        trigger_phase_start(4)           # 14
        display_cross_minute_countdown(window, cfg, REST_EYES_OPEN_MS, phase_id) #  minute countdown
        current_phase_index += 1 # Move to the next phase 
         
    # ---------------- PHASE 2: SPONTANEOUS TICS  -----------------   
    elif phase_id == "phase2a": # Tics spontanés - Instruction *OK* 
        trigger_phase_start(5)           # 15
        display_instruction(window, cfg)
        log_event('instruction_display', 'instruction_message', phase_id)
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press     
        current_phase_index += 1
        
    elif phase_id == "phase2b":  # Tics spontanés              
        trigger_phase_start(6)           # 16
        display_tic_tagging_timer(window, cfg, SPONT_TICS_MS , phase_id)
        current_phase_index += 1 # Move to the next phase 
        
    # ---------------- PHASE 3: MIMICKING TICS  -----------------
    elif phase_id == "phase3a": # Tics mimicking - Instruction *OK* 
        trigger_phase_start(7)           # 17
        display_instruction(window, cfg) 
        log_event('instruction_display', 'instruction_message', phase_id)     
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press
        current_phase_index += 1
        
    elif phase_id == "phase3b": # Tics mimicking 
       trigger_phase_start(8)           # 18
       display_mimicked_tics_phase(window, cfg, phase_id, MIMICKED_TOTAL_REQUIRED)
       current_phase_index += 1 # Move to the next phase 
       
    # ---------------- PHASE 4: TIC SUPRESSION  -----------------
    elif phase_id == "phase4a": # Suppression des Tics - Instruction
        trigger_phase_start(9)           # 19
        display_instruction(window, cfg) 
        log_event('instruction_display', 'instruction_message', phase_id)  
        running = wait_for_key_press(pg.K_RIGHT, phase_id) # Wait for right arrow key press
        current_phase_index += 1
        
    elif phase_id == "phase4b":
        trigger_phase_start(10)           # 20
        start_time = pg.time.get_ticks() # Start time for the countdown
        display_suppression_phase(window, cfg, phase_id, SUPPRESSION_MS)
        current_phase_index += 1 # Move to the next phase 
         
    # ---------------- B: END OF EXPERIMENT  -----------------                       
    elif phase_id == "end_experiment":
        trigger_phase_start(11)           # 21
        display_instruction(window, cfg)
        log_event('instruction_display', 'instruction_message', phase_id)  
       
        waiting_for_exit = True
        while waiting_for_exit and running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                    waiting_for_exit = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        send_led('STOP')           #  <‑‑ lights red
                        log_event("key_press", "End of experiment", phase_id)
                        running = False
                        waiting_for_exit = False
                        
    else:
        print(f"Unknown phase ID: {phase_id}")
        current_phase_index += 1 # Avoid infinite loop

if neo_ser and neo_ser.is_open:
    send_led('STOP')           # <‑‑ lights red for 3 s, then clears
    neo_ser.close()

if HAVE_PARALLEL:
    _port.setData(0) # Close the parallel port if it was opened
    del _port # Clean up the port object
    
   
pg.quit()
log_fh.close() # Close the log file
sys.exit()