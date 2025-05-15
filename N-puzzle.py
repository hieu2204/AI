import heapq
import time
import random
import tkinter as tk
from tkinter import messagebox
import threading

class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("N-Puzzle")
        self.SIZE = 80
        self.N = 3
        self.state = []
        self.goal = ""
        self.init_state = []
        self.steps = 0
        self.start_time = None
        self.timer_running = False
        self.manhattan_cache = {}  # Cache cho heuristic

        self.canvas = tk.Canvas(root)
        self.canvas.pack()

        self.info_label = tk.Label(root, text="", font=("Arial", 12))
        self.info_label.pack()

        size_frame = tk.Frame(root)
        size_frame.pack(pady=5)
        for n in [3, 4, 5]:
            tk.Button(size_frame, text=f"{n}x{n}", command=lambda n=n: self.set_size(n)).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Shuffle", command=self.shuffle).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Solve", command=self.auto_solve).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)

        self.set_size(3)
        self.canvas.bind("<Button-1>", self.click_tile)
        self.root.bind("<Key>", self.key_press)
        self.update_timer()

    def set_size(self, n):
        self.N = n
        self.SIZE = 80 if n <= 4 else 60
        self.canvas.config(width=self.N * self.SIZE, height=self.N * self.SIZE)  # Set canvas size dynamically
        self.goal = tuple(range(1, n * n)) + (0,)
        self.manhattan_cache.clear()  # Xóa cache khi thay đổi kích thước
        self.shuffle()

    def draw(self):
        self.canvas.delete("all")
        for i, tile in enumerate(self.state):
            x, y = divmod(i, self.N)
            if tile == 0:
                continue
            x1, y1 = y * self.SIZE, x * self.SIZE
            x2, y2 = x1 + self.SIZE, y1 + self.SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="black")
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=str(tile), font=("Arial", 18 if self.N <= 4 else 14, "bold"))

    def shuffle(self):
        self.state = list(self.goal)
        self.init_state = list(self.goal)
        if self.N == 3:
            shuffle_steps = random.randint(30, 50)  # Increased difficulty for 3x3
        elif self.N == 4:
            shuffle_steps = random.randint(40, 60)  # Increased difficulty for 4x4
        else:  # 5x5
            shuffle_steps = random.randint(50, 80)  # Increased difficulty for 5x5
        for _ in range(shuffle_steps):
            neighbors = self.neighbors(self.state)
            self.state = list(random.choice(neighbors))
        self.init_state = self.state[:]
        self.steps = 0
        self.start_time = time.time()
        self.timer_running = True
        self.draw()
        self.update_info()

    def reset(self):
        self.state = self.init_state[:]
        self.steps = 0
        self.start_time = time.time()
        self.timer_running = True
        self.draw()
        self.update_info()

    def update_info(self):
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        self.info_label.config(text=f"Bước: {self.steps} | Thời gian: {elapsed}s")

    def update_timer(self):
        if self.timer_running:
            self.update_info()
        self.root.after(1000, self.update_timer)

    def click_tile(self, event):
        col, row = event.x // self.SIZE, event.y // self.SIZE
        idx = row * self.N + col
        self.try_move(idx)

    def key_press(self, event):
        idx = self.state.index(0)
        x, y = divmod(idx, self.N)
        dx, dy = 0, 0
        if event.keysym == "Up" and x < self.N - 1: dx = 1
        if event.keysym == "Down" and x > 0: dx = -1
        if event.keysym == "Left" and y < self.N - 1: dy = 1
        if event.keysym == "Right" and y > 0: dy = -1
        nx, ny = x + dx, y + dy
        if 0 <= nx < self.N and 0 <= ny < self.N:
            nidx = nx * self.N + ny
            self.try_move(nidx)

    def try_move(self, idx):
        zero_idx = self.state.index(0)
        zx, zy = divmod(zero_idx, self.N)
        tx, ty = divmod(idx, self.N)
        if abs(zx - tx) + abs(zy - ty) == 1:
            self.state[zero_idx], self.state[idx] = self.state[idx], self.state[zero_idx]
            self.steps += 1
            self.draw()
            self.update_info()
            if tuple(self.state) == self.goal:
                self.timer_running = False
                messagebox.showinfo("Chúc mừng!", f"Hoàn thành sau {self.steps} bước!")

    def is_solvable(self, state):
        inv = 0
        flat = [x for x in state if x != 0]
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                if flat[i] > flat[j]:
                    inv += 1
        if self.N % 2 == 1:
            return inv % 2 == 0
        else:
            row = self.N - (state.index(0) // self.N)
            return (inv + row) % 2 == 0

    def manhattan(self, state):
        if state in self.manhattan_cache:
            return self.manhattan_cache[state]
        total = 0
        for i, tile in enumerate(state):
            if tile == 0:
                continue
            x, y = divmod(i, self.N)
            gx, gy = divmod(tile - 1, self.N)
            total += abs(x - gx) + abs(y - gy)
        # Thêm Linear Conflict cho hàng
        for i in range(self.N):
            row = state[i * self.N:(i + 1) * self.N]
            for j in range(self.N - 1):
                for k in range(j + 1, self.N):
                    if row[j] == 0 or row[k] == 0:
                        continue
                    gj, gk = divmod(row[j] - 1, self.N)[1], divmod(row[k] - 1, self.N)[1]
                    if gj > gk and j < k and row[j] < row[k]:
                        total += 2
        # Thêm Linear Conflict cho cột
        for j in range(self.N):
            col = [state[i * self.N + j] for i in range(self.N)]
            for i in range(self.N - 1):
                for k in range(i + 1, self.N):
                    if col[i] == 0 or col[k] == 0:
                        continue
                    gi, gk = divmod(col[i] - 1, self.N)[0], divmod(col[k] - 1, self.N)[0]
                    if gi > gk and i < k and col[i] < col[k]:
                        total += 2
        self.manhattan_cache[state] = total
        return total

    def neighbors(self, state):
        idx = state.index(0)
        x, y = divmod(idx, self.N)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        result = []
        for dx, dy in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                nidx = nx * self.N + ny
                new_state = list(state)
                new_state[idx], new_state[nidx] = new_state[nidx], new_state[idx]
                result.append(tuple(new_state))
        return result

    def ida_star(self, state):
        node_count = 0
        max_nodes = 2_000_000  # Increased node limit
        def search(path, g, threshold, visited):
            nonlocal node_count
            node_count += 1
            if node_count > max_nodes or g > 50:  # Increased depth limit
                return float('inf')
            curr = path[-1]
            f = g + self.manhattan(curr)
            if f > threshold:
                return f
            if curr == self.goal:
                return -1
            min_threshold = float('inf')
            for neighbor in self.neighbors(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    t = search(path, g + 1, threshold, visited)
                    if t == -1:
                        return -1
                    if t < min_threshold:
                        min_threshold = t
                    path.pop()
                    visited.remove(neighbor)
            return min_threshold

        threshold = self.manhattan(state)
        path = [state]
        visited = set()
        visited.add(state)
        start = time.time()
        while True:
            if time.time() - start > 5:  # Thoát sau 5 giây
                return None
            t = search(path, 0, threshold, visited)
            if t == -1:
                return path
            if t == float('inf'):
                return None
            threshold = t

    def auto_solve(self):
        def run_solver():
            self.info_label.config(text="Đang giải...")
            path = self.ida_star(tuple(self.state))
            self.info_label.config(text="")
            if not path:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", "Puzzle quá khó, thử lại!"))
                self.shuffle()
                return
            def animate(i=0):
                if i >= len(path):
                    self.timer_running = False
                    messagebox.showinfo("Xong!", "Đã giải xong puzzle!")
                    return
                self.state = list(path[i])
                self.steps = i
                self.draw()
                self.update_info()
                self.root.after(200, animate, i + 1)  # Slower animation (200ms)
            self.start_time = time.time()
            self.timer_running = True
            self.root.after(0, animate)
        threading.Thread(target=run_solver, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()