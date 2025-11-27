# wumpus_gui.py
# Mundo de Wumpus con interfaz en Tkinter.
# Agente optimizado + sistema de puntos + flecha y grito.

import tkinter as tk
import random

# Tamaño del mundo
GRID_SIZE = 10
CELL_SIZE = 40

# Límites para Wumpus y hoyos
MAX_WUMPUS = 5
MAX_PITS = 8
DEFAULT_WUMPUS = 1
DEFAULT_PITS = 6

# Sistema de puntos
MOVE_COST = -1          # cada movimiento cuesta 1 punto
DEATH_PENALTY = -50     # morir en hoyo o Wumpus
GOLD_REWARD = 100       # encontrar el oro
ARROW_COST = -5         # disparar la flecha cuesta puntos
KILL_REWARD = 30        # matar a un Wumpus
IMPOSSIBLE_PENALTY = -10  # declarar que es imposible


class WumpusWorldGUI:
    def __init__(self, root):
        self.root = root
        root.title("Mundo de Wumpus - Agente Pedro")

        # Canvas de la cuadrícula
        self.canvas = tk.Canvas(
            root,
            width=GRID_SIZE * CELL_SIZE,
            height=GRID_SIZE * CELL_SIZE,
            bg="white"
        )
        self.canvas.pack(side=tk.TOP, padx=10, pady=10)

        # Controles superiores
        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.TOP, pady=5)

        self.num_wumpus = DEFAULT_WUMPUS
        self.num_pits = DEFAULT_PITS

        self.wumpus_var = tk.IntVar(value=self.num_wumpus)
        self.pits_var = tk.IntVar(value=self.num_pits)

        tk.Label(control_frame, text="Wumpus (0-5):").grid(row=0, column=0, padx=3)
        self.wumpus_spin = tk.Spinbox(
            control_frame,
            from_=0,
            to=MAX_WUMPUS,
            width=3,
            textvariable=self.wumpus_var
        )
        self.wumpus_spin.grid(row=0, column=1, padx=3)

        tk.Label(control_frame, text="Hoyos (0-8):").grid(row=0, column=2, padx=3)
        self.pits_spin = tk.Spinbox(
            control_frame,
            from_=0,
            to=MAX_PITS,
            width=3,
            textvariable=self.pits_var
        )
        self.pits_spin.grid(row=0, column=3, padx=3)

        self.new_world_button = tk.Button(
            control_frame,
            text="Nuevo mundo",
            command=self.new_world,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold")
        )
        self.new_world_button.grid(row=0, column=4, padx=6)

        self.move_button = tk.Button(
            control_frame,
            text="Mover / siguiente paso",
            command=self.on_move_button,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold")
        )
        self.move_button.grid(row=0, column=5, padx=6)

        # Mensajes y puntos
        self.status_var = tk.StringVar()
        self.status_var.set("Elige la cantidad de Wumpus y hoyos y luego pulsa 'Nuevo mundo'.")
        self.status_label = tk.Label(root, textvariable=self.status_var,
                                     font=("Arial", 11))
        self.status_label.pack(side=tk.TOP, pady=3)
        self.score = 0
        self.score_label = tk.Label(
            root,
            text="Puntos: 0",
            font=("Arial", 11, "bold")
        )
        self.score_label.pack(side=tk.TOP, pady=(0, 5))

        self.arrow_label = tk.Label(
            root,
            text="Flecha: Disponible",
            font=("Arial", 10, "bold"),
            fg="#2E7D32"    # verde
        )
        self.arrow_label.pack(side=tk.TOP, pady=(0, 2))

        self.author_label = tk.Label(
            root,
            text="UMNG\nHecho por:\nNicolás Acevedo\nJuan Camilo Niño\nJuan Moreno",
            font=("Arial", 10),
            justify="left"
        )
        self.author_label.pack(side=tk.TOP, pady=(0, 5))

        # Estado del mundo y del agente
        self.world = None
        self.start_pos = (GRID_SIZE - 1, 0)
        self.agent_row = None
        self.agent_col = None
        self.alive = True
        self.has_gold = False
        self.impossible = False

        # Memoria entre intentos en el mismo mundo
        self.global_danger = set()

        # Conocimiento por intento
        self.visited = set()
        self.known_safe = set()
        self.known_danger = set()
        self.stench_info = {}
        self.breeze_info = {}
        self.possible_wumpus = set()
        self.possible_pits = set()

        # Para evitar bucles
        self.visit_count = {}
        self.prev_pos = None

        # Flecha
        self.has_arrow = True

    # ---------------------- UTILIDAD PUNTOS ---------------------- #
    def update_score_label(self):
        self.score_label.config(text=f"Puntos: {self.score}")

    # ---------------------- CREACIÓN DEL MUNDO ------------------- #
    def new_world(self):
        """Genera un mundo nuevo con los parámetros de la interfaz."""
        try:
            w = int(self.wumpus_var.get())
        except ValueError:
            w = DEFAULT_WUMPUS
        try:
            p = int(self.pits_var.get())
        except ValueError:
            p = DEFAULT_PITS

        w = max(0, min(MAX_WUMPUS, w))
        p = max(0, min(MAX_PITS, p))

        self.num_wumpus = w
        self.num_pits = p

        self.global_danger.clear()
        self.score = 0
        self.update_score_label()
        self.has_arrow = True
        self.update_arrow_label()

        self.generate_world()
        self.reset_agent()
        self.draw_world()
        self.status_var.set(
            f"Nuevo mundo con {self.num_wumpus} Wumpus y "
            f"{self.num_pits} hoyos. Pulsa 'Mover / siguiente paso'."
        )

    def generate_world(self):
        """Coloca oro, Wumpus, hoyos y percepciones."""
        self.world = [[{
            "wumpus": False,
            "pit": False,
            "gold": False,
            "stench": False,
            "breeze": False
        } for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        safe_zone = set(self.get_neighbors(self.start_pos))
        safe_zone.add(self.start_pos)

        # Oro
        while True:
            r = random.randrange(GRID_SIZE)
            c = random.randrange(GRID_SIZE)
            if (r, c) not in safe_zone:
                self.world[r][c]["gold"] = True
                self.gold_pos = (r, c)
                break

        # Wumpus
        placed = 0
        while placed < self.num_wumpus:
            r = random.randrange(GRID_SIZE)
            c = random.randrange(GRID_SIZE)
            if (r, c) in safe_zone:
                continue
            cell = self.world[r][c]
            if not any([cell["wumpus"], cell["pit"], cell["gold"]]):
                cell["wumpus"] = True
                placed += 1

        # Hoyos
        pits = 0
        while pits < self.num_pits:
            r = random.randrange(GRID_SIZE)
            c = random.randrange(GRID_SIZE)
            if (r, c) in safe_zone:
                continue
            cell = self.world[r][c]
            if not any([cell["wumpus"], cell["pit"], cell["gold"]]):
                cell["pit"] = True
                pits += 1

        # Hedor y brisa
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.world[r][c]["wumpus"]:
                    for nr, nc in self.get_neighbors((r, c)):
                        self.world[nr][nc]["stench"] = True
                if self.world[r][c]["pit"]:
                    for nr, nc in self.get_neighbors((r, c)):
                        self.world[nr][nc]["breeze"] = True

    # ----------------------- ESTADO DEL AGENTE ------------------- #
    def reset_agent(self):
        """Reinicia intento en el mismo mundo (mantiene memoria global)."""
        self.agent_row, self.agent_col = self.start_pos
        self.alive = True
        self.has_gold = False
        self.impossible = False

        self.visited = set()
        self.known_safe = {self.start_pos}
        self.known_danger = set(self.global_danger)
        self.stench_info = {}
        self.breeze_info = {}
        self.possible_wumpus = set()
        self.possible_pits = set()

        self.visit_count = {}
        self.prev_pos = None
        self.has_arrow = True   # nueva flecha para el nuevo intento
        self.has_arrow = True   # ya la tienes
        self.update_arrow_label()

        self.update_knowledge()
        self.draw_world()
        self.status_var.set(
            "Nuevo intento. El agente recuerda las casillas donde murió."
        )

    def update_arrow_label(self):
        if self.has_arrow:
            self.arrow_label.config(
                text="Flecha: Disponible",
                fg="#2E7D32"    # verde
            )
        else:
            self.arrow_label.config(
                text="Flecha: Usada",
                fg="#B71C1C"    # rojo
            )

    def get_neighbors(self, pos):
        r, c = pos
        neighbors = []
        if r > 0:
            neighbors.append((r - 1, c))
        if r < GRID_SIZE - 1:
            neighbors.append((r + 1, c))
        if c > 0:
            neighbors.append((r, c - 1))
        if c < GRID_SIZE - 1:
            neighbors.append((r, c + 1))
        return neighbors

    # ------------------------ BOTÓN PRINCIPAL --------------------- #
    def on_move_button(self):
        if self.world is None:
            self.status_var.set(
                "Primero elige cantidades y pulsa 'Nuevo mundo'."
            )
            return

        if (not self.alive) or self.has_gold or self.impossible:
            self.reset_agent()
            return

        self.agent_step()

    def agent_step(self):
        if not self.alive or self.has_gold or self.impossible:
            return

        current_pos = (self.agent_row, self.agent_col)

        # 1) Decisión de flecha (si hay un único vecino muy probable)
        if self.has_arrow:
            target = self.choose_shoot_target()
            if target is not None:
                self.shoot_arrow(target)
                return

        # 2) Si no dispara flecha, se mueve
        next_pos = self.choose_next_move()
        if next_pos is None:
            self.impossible = True
            self.score += IMPOSSIBLE_PENALTY
            self.update_score_label()
            self.status_var.set(
                "El agente no encuentra movimientos razonables: "
                "considera imposible llegar al oro."
            )
            return

        self.prev_pos = current_pos
        self.agent_row, self.agent_col = next_pos
        pos = (self.agent_row, self.agent_col)
        cell = self.world[self.agent_row][self.agent_col]

        # Coste del movimiento
        self.score += MOVE_COST
        self.update_score_label()

        # Muerte
        if cell["wumpus"] or cell["pit"]:
            self.alive = False
            self.global_danger.add(pos)
            self.known_danger.add(pos)
            peligro = "un Wumpus" if cell["wumpus"] else "un hoyo"
            self.score += DEATH_PENALTY
            self.update_score_label()
            self.status_var.set(
                f"Pedro cayó en {peligro} en {pos}. Muere, "
                "pero recordará esa casilla."
            )
            self.draw_world()
            return

        # Oro
        if cell["gold"]:
            self.has_gold = True
            self.score += GOLD_REWARD
            self.update_score_label()
            self.status_var.set(
                "¡Pedro encontró el oro! Pulsa el botón para reiniciar "
                "el intento en el mismo mundo."
            )
            self.update_knowledge()
            self.draw_world()
            return

        # Continúa vivo y sin oro
        self.update_knowledge()
        self.status_var.set(self.describe_perceptions(cell))
        self.draw_world()

    # --------------------- CONOCIMIENTO DEL AGENTE ---------------- #
    def update_knowledge(self):
        pos = (self.agent_row, self.agent_col)
        self.visited.add(pos)
        self.known_safe.add(pos)

        # Nº de veces que visita la casilla (para evitar bucles)
        self.visit_count[pos] = self.visit_count.get(pos, 0) + 1

        cell = self.world[self.agent_row][self.agent_col]
        stench = cell["stench"]
        breeze = cell["breeze"]

        neighbors = self.get_neighbors(pos)

        # Sin hedor ni brisa ⇒ vecinos seguros
        if not stench and not breeze:
            for n in neighbors:
                self.known_safe.add(n)

        # Info de hedor
        if stench:
            unknown_neighbors = [n for n in neighbors if n not in self.known_safe]
            if unknown_neighbors:
                self.stench_info[pos] = set(unknown_neighbors)

        # Info de brisa
        if breeze:
            unknown_neighbors = [n for n in neighbors if n not in self.known_safe]
            if unknown_neighbors:
                self.breeze_info[pos] = set(unknown_neighbors)

        # Posibles Wumpus (intersección)
        self.possible_wumpus = set()
        if self.stench_info:
            candidate_sets = list(self.stench_info.values())
            inter = candidate_sets[0].copy()
            for s in candidate_sets[1:]:
                inter &= s
            self.possible_wumpus = inter.difference(self.known_safe)

        # Posibles hoyos (intersección)
        self.possible_pits = set()
        if self.breeze_info:
            candidate_sets = list(self.breeze_info.values())
            inter = candidate_sets[0].copy()
            for s in candidate_sets[1:]:
                inter &= s
            self.possible_pits = inter.difference(self.known_safe)

    # --------------------- FLECHA Y GRITO ------------------------- #
    def choose_shoot_target(self):
        """Decide si vale la pena disparar flecha a un vecino."""
        if not self.has_arrow:
            return None
        current = (self.agent_row, self.agent_col)
        neighbors = self.get_neighbors(current)
        # Solo dispara si hay EXACTAMENTE un vecino muy sospechoso de Wumpus
        targets = [p for p in neighbors if p in self.possible_wumpus]
        if len(targets) == 1:
            return targets[0]
        return None

    def shoot_arrow(self, target):
        """Dispara la flecha en la dirección del vecino objetivo."""
        current = (self.agent_row, self.agent_col)
        dr = target[0] - current[0]
        dc = target[1] - current[1]

        r, c = current
        killed = False

        # Avanza en línea recta en esa dirección
        r += dr
        c += dc
        while 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            if self.world[r][c]["wumpus"]:
                self.world[r][c]["wumpus"] = False
                killed = True
                break
            r += dr
            c += dc

        self.has_arrow = False
        self.score += ARROW_COST
        if killed:
            self.score += KILL_REWARD
        self.update_score_label()
        self.update_arrow_label()

        self.score += ARROW_COST
        if killed:
            self.score += KILL_REWARD
        self.update_score_label()

        # Recalcular hedor del mapa
        self.recompute_stench()
        # Limpiar inferencias viejas (se reconstruyen con nuevas percepciones)
        self.stench_info.clear()
        self.possible_wumpus.clear()

        if killed:
            msg = "Pedro dispara una flecha... ¡Se escucha un grito! Un Wumpus ha muerto."
        else:
            msg = "Pedro dispara una flecha... No se escucha ningún grito."

        # Actualizar conocimiento en la casilla actual con la nueva situación
        self.update_knowledge()
        self.status_var.set(msg)
        self.draw_world()

    def recompute_stench(self):
        """Recalcula el hedor en todo el mapa a partir de los Wumpus vivos."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.world[r][c]["stench"] = False
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.world[r][c]["wumpus"]:
                    for nr, nc in self.get_neighbors((r, c)):
                        self.world[nr][nc]["stench"] = True

    # --------------------- ELECCIÓN DEL MOVIMIENTO --------------- #
    def choose_next_move(self):
        """Escoge la siguiente casilla a visitar (optimizada)."""
        current = (self.agent_row, self.agent_col)
        neighbors = self.get_neighbors(current)

        candidates = [p for p in neighbors if p not in self.known_danger]
        if not candidates:
            return None

        # 1. Vecinos seguros no visitados
        safe_unvisited = [
            p for p in candidates if p in self.known_safe and p not in self.visited
        ]
        if safe_unvisited:
            return random.choice(safe_unvisited)

        # 2. Vecinos seguros (minimizar nº de visitas y evitar rebote)
        safe_any = [p for p in candidates if p in self.known_safe]
        if safe_any:
            best_pos = None
            best_score = float("inf")
            for p in safe_any:
                visits = self.visit_count.get(p, 0)
                back_penalty = 2 if p == self.prev_pos else 0
                score = visits + back_penalty
                if score < best_score:
                    best_score = score
                    best_pos = p
            return best_pos

        # 3. Sin nada claramente seguro: minimizar riesgo + visitas
        best_pos = None
        best_score = float("inf")
        for p in candidates:
            score = 0
            if p in self.possible_wumpus:
                score += 3
            if p in self.possible_pits:
                score += 2
            if p not in self.visited:
                score -= 0.5
            if p == self.prev_pos:
                score += 2
            visits = self.visit_count.get(p, 0)
            score += 0.7 * visits
            if score < best_score:
                best_score = score
                best_pos = p
        return best_pos

    # --------------------------- UI / DIBUJO ---------------------- #
    def describe_perceptions(self, cell):
        msgs = []
        if cell["stench"]:
            msgs.append("hedor")
        if cell["breeze"]:
            msgs.append("brisa")

        if not msgs:
            return "La casilla actual es tranquila: sin hedor ni brisa."
        else:
            joined = " y ".join(msgs)
            return f"Pedro percibe {joined}. Debe moverse con cuidado."

    def draw_world(self):
        self.canvas.delete("all")

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                pos = (r, c)

                fill = "white"
                if pos in self.known_safe:
                    fill = "#E3F2FD"
                if pos in self.known_danger:
                    fill = "#FFEBEE"
                if pos == (self.agent_row, self.agent_col):
                    fill = "#BBDEFB"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill,
                    outline="#B0BEC5"
                )

                cell = self.world[r][c]

                # Oro
                if cell["gold"]:
                    self.canvas.create_oval(
                        x1 + 10, y1 + 10,
                        x2 - 10, y2 - 10,
                        fill="#FFD700",
                        outline="#F9A825"
                    )

                # Wumpus
                if cell["wumpus"]:
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text="W",
                        fill="#D32F2F",
                        font=("Arial", 14, "bold")
                    )

                # Hoyo
                if cell["pit"]:
                    self.canvas.create_oval(
                        x1 + 12, y1 + 12,
                        x2 - 12, y2 - 12,
                        fill="#263238"
                    )

                # Hedor / brisa
                text_offset_y = y1 + CELL_SIZE - 10
                small_texts = []
                if cell["stench"]:
                    small_texts.append(("H", "#388E3C"))
                if cell["breeze"]:
                    small_texts.append(("B", "#00796B"))

                if small_texts:
                    txt = " ".join(t[0] for t in small_texts)
                    color = small_texts[0][1] if len(small_texts) == 1 else "#5D4037"
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        text_offset_y,
                        text=txt,
                        fill=color,
                        font=("Arial", 9, "bold")
                    )

                # Casillas sospechosas
                if pos in self.possible_wumpus or pos in self.possible_pits:
                    self.canvas.create_text(
                        x1 + 8, y1 + 10,
                        text="?",
                        fill="#EF6C00",
                        font=("Arial", 10, "bold")
                    )

        # Agente
        ax1 = self.agent_col * CELL_SIZE + 8
        ay1 = self.agent_row * CELL_SIZE + 8
        ax2 = ax1 + CELL_SIZE - 16
        ay2 = ay1 + CELL_SIZE - 16

        self.canvas.create_oval(
            ax1, ay1, ax2, ay2,
            fill="#1976D2",
            outline="#0D47A1",
            width=2
        )
        self.canvas.create_text(
            (ax1 + ax2) // 2,
            (ay1 + ay2) // 2,
            text="P",
            fill="white",
            font=("Arial", 12, "bold")
        )
        self.arrow_label.pack(side=tk.TOP, pady=(0, 2))
        self.update_arrow_label()


if __name__ == "__main__":
    root = tk.Tk()
    app = WumpusWorldGUI(root)
    root.mainloop()
