"""
================================================================================
GEOMETRY DASH NEAT AI - Sistema de Entrenamiento
================================================================================

Descripción:
    Sistema de inteligencia artificial para jugar Geometry Dash usando
    algoritmos neuroevolutivos NEAT (NeuroEvolution of Augmenting Topologies).
    
    Lee el estado del juego desde un log generado por un mod de Geode (C++)
    y entrena redes neuronales para controlar el salto del jugador.

Autores:
    - Juan Camilo Niño
    - Juan Moreno
    - Nicolas Acevedo

Arquitectura:
    - C++ (Geode Mod): Extrae estado del juego → gd_ai_log_temp.log
    - Python (NEAT): Lee log → Red neuronal → Control de teclado
    - Matrix Vision: 15 sensores (3 alturas x 5 distancias)
    - Inputs: 19 (4 físicos + 15 de visión)
    - Output: 1 (saltar/no saltar)

Uso:
    python gd_neat_ai_refactored.py

Continuar desde checkpoint:
    Descomentar líneas 289-299 y cambiar el número de generación
================================================================================
"""

import neat
import time
import keyboard
import os
import sys
import random
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
LOG_PATH = r"D:\SteamLibrary\steamapps\common\Geometry Dash\geode\logs\gd_ai_log_temp.log"
GENERATIONS = 300

IMMUNITY_WINDOW = 0.2
STUCK_THRESHOLD = 150
READ_RETRY_DELAY = 0.0005

# ============================================================================
# ESTRUCTURAS DE DATOS
# ============================================================================
class EventType(Enum):
    NONE = 0
    STATE = 1
    DEATH = 2
    WIN = 3

@dataclass
class GameState:
    x: float
    y: float
    vely: float
    ground: bool
    matrix: list[float]
    timestamp: float

class SafeLogReader:
    """Lee el log con detección de cambios por mtime."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._last_content = ""
        self._last_mtime = 0.0
        
    def read_raw(self) -> Optional[str]:
        if not os.path.exists(self.filepath):
            return None
        
        try:
            current_mtime = os.path.getmtime(self.filepath)
            if current_mtime == self._last_mtime:
                return None
            
            self._last_mtime = current_mtime
            
            for attempt in range(3):
                try:
                    with open(self.filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    if not lines:
                        return None
                    
                    content = lines[-1].strip()
                    
                    if content != self._last_content:
                        self._last_content = content
                        return content
                    
                    return None
                    
                except (PermissionError, OSError):
                    if attempt < 2:
                        time.sleep(READ_RETRY_DELAY)
                    continue
                    
        except:
            return None
            
        return None

class GameStateParser:
    """Parsea el protocolo del log: STATE|X|Y|Vel|G|Matrix o DEATH/WIN."""
    
    @staticmethod
    def parse(line: str) -> Tuple[EventType, Optional[GameState]]:
        if not line:
            return EventType.NONE, None
        
        if line == 'DEATH':
            return EventType.DEATH, None
        elif line == 'WIN':
            return EventType.WIN, None
        
        parts = line.split('|')
        if parts[0] == 'STATE' and len(parts) >= 6:
            try:
                state = GameState(
                    x=float(parts[1]),
                    y=float(parts[2]),
                    vely=float(parts[3]),
                    ground=int(parts[4]) == 1,
                    matrix=[float(v) for v in parts[5].strip(',').split(',') if v],
                    timestamp=time.time()
                )
                return EventType.STATE, state
                
            except (ValueError, IndexError):
                return EventType.NONE, None
        
        return EventType.NONE, None

# ============================================================================
# LÓGICA DE SINCRONIZACIÓN
# ============================================================================
class LevelSession:
    """Maneja un intento de nivel con handshake y tracking."""
    
    attempt_counter = 0  # Contador global de intentos
    
    def __init__(self, reader: SafeLogReader, parser: GameStateParser, genome_id: int):
        self.reader = reader
        self.parser = parser
        self.genome_id = genome_id
        
        LevelSession.attempt_counter += 1
        self.attempt_id = LevelSession.attempt_counter
        
        self.start_time = None
        self.start_x = None
        self.max_x = 0.0
        self.frames_stuck = 0
        
    def wait_for_reset(self) -> bool:
        """Espera spawn inmediato - sin detectar DEATH."""
        
        # Solo esperar a que X sea pequeño (jugador en spawn)
        while True:
            raw = self.reader.read_raw()
            if raw:
                event, state = self.parser.parse(raw)
                
                if event == EventType.STATE and state:
                    if state.x <= 150:
                        return True
        
        return True
    
    def run(self, net: neat.nn.FeedForwardNetwork) -> float:
        """Ejecuta un intento completo del nivel."""
        self.start_time = time.time()
        death_seen = False
        valid_attempt = False
        
        while True:
            raw = self.reader.read_raw()
            if not raw:
                continue
            
            event, state = self.parser.parse(raw)
            elapsed = time.time() - self.start_time
            
            if event == EventType.DEATH:
                if elapsed < IMMUNITY_WINDOW:
                    continue
                death_seen = True
                break
            
            if event == EventType.WIN:
                self.max_x += 50000
                valid_attempt = True
                break
            
            if event == EventType.STATE and state:
                # Marcar que empezamos a recibir datos válidos
                if not valid_attempt and state.x > 10:
                    valid_attempt = True
                
                if self.start_x is None:
                    self.start_x = state.x
                    self.max_x = state.x
                
                if state.x > self.max_x + 0.5:
                    self.max_x = state.x
                    self.frames_stuck = 0
                else:
                    self.frames_stuck += 1
                
                if self.frames_stuck > STUCK_THRESHOLD:
                    valid_attempt = True
                    break
                
                inputs = self._build_inputs(state)
                output = net.activate(inputs)
                
                if output[0] > 0.5:
                    keyboard.press('space')
                else:
                    keyboard.release('space')
        
        keyboard.release('space')
        
        # Solo esperar si fue un intento válido y murió
        if death_seen and valid_attempt:
            time.sleep(0.08)
        
        if self.start_x is None or not valid_attempt:
            return 0.0
        
        distance = self.max_x - self.start_x
        percentage = min((distance / 10000.0) * 100, 100)
        fitness = (distance * distance) / 100.0
        
        sys.stdout.write(f"D:{distance:.0f}({percentage:.1f}%) ")
        sys.stdout.flush()
        
        return fitness
    
    def _build_inputs(self, state: GameState) -> list[float]:
        """Construye vector de 19 inputs: 4 físicos + 15 de visión."""
        inputs = []
        
        inputs.append((state.y - 105.0) / 100.0)
        inputs.append(state.vely / 20.0)
        inputs.append(1.0 if state.ground else 0.0)
        inputs.append(1.0)
        
        matrix = state.matrix[:15]
        while len(matrix) < 15:
            matrix.append(0.0)
        
        inputs.extend(matrix)
        
        return inputs

# ============================================================================
# INTEGRACIÓN CON NEAT
# ============================================================================
def evaluate_genome(genome_id: int, genome: neat.DefaultGenome, 
                   config: neat.Config) -> float:
    """Evalúa un genoma ejecutando un intento en el nivel."""
    
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    reader = SafeLogReader(LOG_PATH)
    parser = GameStateParser()
    
    # Reiniciar nivel
    keyboard.release('space')
    keyboard.press_and_release('r')
    time.sleep(0.05)
    
    # Limpiar caché del reader para evitar datos viejos
    reader._last_content = ""
    reader._last_mtime = 0.0
    
    session = LevelSession(reader, parser, genome_id)
    
    if not session.wait_for_reset():
        return 0.0
    
    fitness = session.run(net)
    
    return fitness

def eval_genomes(genomes, config):
    """Callback NEAT para evaluar generación."""
    for genome_id, genome in genomes:
        sys.stdout.write(f"G{genome_id:2d}:")
        genome.fitness = evaluate_genome(genome_id, genome, config)
    
    print()

class GenerationReporter(neat.reporting.BaseReporter):
    """Reporter para checkpoint por generación."""
    
    def __init__(self):
        self.generation = 0
    
    def post_evaluate(self, config, population, species, best_genome):
        self.generation += 1
        
        best_distance = (best_genome.fitness * 100) ** 0.5
        best_percentage = min((best_distance / 10000.0) * 100, 100)
        
        import pickle
        filename = f'checkpoint_gen_{self.generation}.pkl'
        
        with open(filename, 'wb') as f:
            data = {
                'generation': self.generation,
                'population': population,
                'species_set': species,
                'rndstate': random.getstate(),
                'best_genome': best_genome,
                'best_fitness': best_genome.fitness,
                'best_distance': best_distance,
                'best_percentage': best_percentage
            }
            pickle.dump(data, f)
        
        print(f"💾 Gen{self.generation} → Best:{best_distance:.0f}u ({best_percentage:.1f}%) Fit:{best_genome.fitness:.0f}")

# ============================================================================
# MAIN
# ============================================================================
def run():
    sys.stdout.reconfigure(encoding='utf-8')
    
    if not os.path.exists(LOG_PATH):
        print(f"❌ Log no encontrado: {LOG_PATH}")
        return
    
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    
    if not os.path.exists(config_path):
        print(f"❌ config.txt no encontrado")
        return
    
    config = neat.Config(
        neat.DefaultGenome, 
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet, 
        neat.DefaultStagnation,
        config_path
    )
    
    # ========================================================================
    # CONTINUAR DESDE CHECKPOINT
    # ========================================================================
    checkpoint_file = 'checkpoint_gen_1.pkl'
    import pickle
    with open(checkpoint_file, 'rb') as f:
        data = pickle.load(f)
        p = neat.Population(config)
        p.population = data['population']
        p.species = data['species_set']
        random.setstate(data['rndstate'])
        p.generation = data['generation']
        print(f"🔄 Continuando desde Gen {p.generation}")
    # ========================================================================
    
    # CREAR POBLACIÓN NUEVA (comentar si usas checkpoint)
    # p = neat.Population(config)
    
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    p.add_reporter(GenerationReporter())
    
    print("="*60)
    print(" 🎮 GEOMETRY DASH NEAT AI")
    print("="*60)
    print(f" 📁 Log: {os.path.basename(LOG_PATH)}")
    print(f" 🧬 Generaciones: {GENERATIONS}")
    print(f" 👥 Población: {config.pop_size}")
    print("="*60 + "\n")
    
    winner = p.run(eval_genomes, GENERATIONS)
    
    import pickle
    winner_path = 'winner_genome.pkl'
    
    winner_distance = (winner.fitness * 100) ** 0.5
    winner_percentage = min((winner_distance / 10000.0) * 100, 100)
    
    with open(winner_path, 'wb') as f:
        pickle.dump({
            'genome': winner,
            'fitness': winner.fitness,
            'distance': winner_distance,
            'percentage': winner_percentage
        }, f)
    
    print("\n" + "="*60)
    print(f" ✅ COMPLETADO!")
    print(f" 💾 {winner_path}")
    print(f" 🏆 {winner_distance:.0f}u ({winner_percentage:.1f}%) Fit:{winner.fitness:.0f}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run()