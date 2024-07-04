import sys
import time
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QTabWidget, QMessageBox
)
from PyQt5.QtCore import QTimer, QTime
import winsound

# Función para reproducir sonido
def play_sound():
    winsound.Beep(1000, 3000)  # Beep(frequency, duration)

# Conexión a la base de datos SQLite
conn = sqlite3.connect('BD_ALARMA_POMODORO.db')
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute('''CREATE TABLE IF NOT EXISTS "tbl.Alarma" (
                   ID INTEGER PRIMARY KEY AUTOINCREMENT,
                   Hora_de_alarma TEXT,
                   Hora_de_registro TEXT DEFAULT CURRENT_TIMESTAMP,
                   tiempo_Transcurrido TEXT
               )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS "tbl.Temporizador" (
                   ID INTEGER PRIMARY KEY AUTOINCREMENT,
                   Temporizador INTEGER,
                   Fecha_Registro DATETIME DEFAULT CURRENT_TIMESTAMP
               )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS "tbl.Pomodoro" (
                   ID INTEGER PRIMARY KEY AUTOINCREMENT,
                   Hora_Inicio TEXT,
                   Hora_Fin_Pomodoro TEXT,
                   Hora_Inicio_Descanso TEXT,
                   Hora_Fin TEXT,
                   Fecha_Registro DATETIME DEFAULT CURRENT_TIMESTAMP
               )''')

conn.commit()


class Timer(QWidget):
    def __init__(self):
        super().__init__()

        self.time_left = 0
        self.running = False

        self.layout = QVBoxLayout()

        self.label = QLabel("Temporizador (segundos):")
        self.layout.addWidget(self.label)

        self.entry = QLineEdit()
        self.layout.addWidget(self.entry)

        self.time_label = QLabel("Tiempo Restante: 00:00:00")
        self.layout.addWidget(self.time_label)

        self.start_button = QPushButton("Iniciar")
        self.start_button.clicked.connect(self.start_timer)
        self.layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_timer)
        self.layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reiniciar")
        self.reset_button.clicked.connect(self.reset_timer)
        self.layout.addWidget(self.reset_button)

        self.exit_button = QPushButton("Salir")
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.setLayout(self.layout)

    def start_timer(self):
        try:
            self.time_left = int(self.entry.text())
            if not self.running:
                self.timer.start(1000)
                self.running = True
                self.record_timer_start()
        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor ingrese un número válido")

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.time_label.setText(f"Tiempo Restante: {self.format_time(self.time_left)}")
        elif self.time_left == 0:
            play_sound()
            QMessageBox.information(self, "Tiempo finalizado", "El temporizador ha terminado.")
            self.timer.stop()
            self.running = False
            self.record_timer_stop()

    def pause_timer(self):
        self.running = False
        self.timer.stop()

    def reset_timer(self):
        self.running = False
        self.timer.stop()
        self.time_left = 0
        self.time_label.setText("Tiempo Restante: 00:00:00")

    def record_timer_start(self):
        cursor.execute('''INSERT INTO "tbl.Temporizador" (Temporizador) VALUES (?)''', (self.entry.text(),))
        conn.commit()

    def record_timer_stop(self):
        cursor.execute('''UPDATE "tbl.Temporizador" SET Temporizador = ? WHERE ID = (SELECT MAX(ID) FROM "tbl.Temporizador")''', (self.entry.text(),))
        conn.commit()

    @staticmethod
    def format_time(seconds):
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02}:{mins:02}:{secs:02}"


class Alarm(QWidget):
    def __init__(self):
        super().__init__()

        self.alarm_time = None
        self.running = False

        self.layout = QVBoxLayout()

        self.label = QLabel("Alarma (HH:MM:SS):")
        self.layout.addWidget(self.label)

        self.entry = QLineEdit()
        self.layout.addWidget(self.entry)

        self.set_button = QPushButton("Establecer")
        self.set_button.clicked.connect(self.set_alarm)
        self.layout.addWidget(self.set_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_alarm)
        self.layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reiniciar")
        self.reset_button.clicked.connect(self.reset_alarm)
        self.layout.addWidget(self.reset_button)

        self.exit_button = QPushButton("Salir")
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alarm)

        self.setLayout(self.layout)

    def set_alarm(self):
        try:
            alarm_time_str = self.entry.text()
            self.alarm_time = QTime.fromString(alarm_time_str, "HH:mm:ss")
            if not self.running:
                self.timer.start(1000)
                self.running = True
                self.record_alarm_set()
        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor ingrese un tiempo válido (HH:MM:SS)")

    def check_alarm(self):
        if self.running:
            current_time = QTime.currentTime()
            if (current_time.hour(), current_time.minute(), current_time.second()) == \
                    (self.alarm_time.hour(), self.alarm_time.minute(), self.alarm_time.second()):
                play_sound()
                QMessageBox.information(self, "Alarma", "¡Es hora!")
                self.timer.stop()
                self.running = False
                self.record_alarm_triggered()

    def pause_alarm(self):
        self.running = False
        self.timer.stop()

    def reset_alarm(self):
        self.running = False
        self.timer.stop()
        self.alarm_time = None

    def record_alarm_set(self):
        cursor.execute('''INSERT INTO "tbl.Alarma" (Hora_de_alarma, Hora_de_registro) VALUES (?, ?)''',
                       (self.alarm_time.toString(), QTime.currentTime().toString()))
        conn.commit()

    def record_alarm_triggered(self):
        cursor.execute('''SELECT Hora_de_registro FROM "tbl.Alarma" WHERE ID = (SELECT MAX(ID) FROM "tbl.Alarma")''')
        hora_registro = cursor.fetchone()[0]
        hora_registro_time = QTime.fromString(hora_registro, "HH:mm:ss")
        tiempo_transcurrido = self.calculate_elapsed_time(hora_registro_time, QTime.currentTime())
        cursor.execute('''UPDATE "tbl.Alarma" SET tiempo_Transcurrido = ? WHERE ID = (SELECT MAX(ID) FROM "tbl.Alarma")''',
                       (tiempo_transcurrido,))
        conn.commit()

    @staticmethod
    def calculate_elapsed_time(start_time, end_time):
        elapsed_seconds = start_time.secsTo(end_time)
        elapsed_time = QTime(0, 0).addSecs(elapsed_seconds)
        return elapsed_time.toString("HH:mm:ss")


class Pomodoro(QWidget):
    def __init__(self):
        super().__init__()

        self.work_time = 25 * 60
        self.break_time = 5 * 60
        self.time_left = self.work_time
        self.running = False
        self.is_working = True

        self.layout = QVBoxLayout()

        self.label = QLabel("Pomodoro (Trabajo: 25min, Descanso: 5min)")
        self.layout.addWidget(self.label)

        self.time_label = QLabel("Tiempo Restante: 25:00")
        self.layout.addWidget(self.time_label)

        self.start_button = QPushButton("Iniciar")
        self.start_button.clicked.connect(self.start_pomodoro)
        self.layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_pomodoro)
        self.layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reiniciar")
        self.reset_button.clicked.connect(self.reset_pomodoro)
        self.layout.addWidget(self.reset_button)

        self.exit_button = QPushButton("Salir")
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_pomodoro)

        self.setLayout(self.layout)

    def start_pomodoro(self):
        if not self.running:
            self.timer.start(1000)
            self.running = True
            self.record_pomodoro_start()

    def update_pomodoro(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.time_label.setText(f"Tiempo Restante: {self.format_time(self.time_left)}")
        elif self.time_left == 0:
            play_sound()
            if self.is_working:
                self.record_pomodoro_work_end()
                QMessageBox.information(self, "Pomodoro", "¡Tiempo de descanso!")
                self.time_left = self.break_time
                self.is_working = False
                self.record_pomodoro_break_start()
            else:
                QMessageBox.information(self, "Pomodoro", "¡Tiempo de trabajo!")
                self.time_left = self.work_time
                self.is_working = True
                self.record_pomodoro_break_end()
                self.record_pomodoro_work_start()

    def pause_pomodoro(self):
        self.running = False
        self.timer.stop()

    def reset_pomodoro(self):
        self.running = False
        self.timer.stop()
        self.time_left = self.work_time
        self.is_working = True
        self.time_label.setText("Tiempo Restante: 25:00")

    def record_pomodoro_start(self):
        cursor.execute('''INSERT INTO "tbl.Pomodoro" (Hora_Inicio) VALUES (?)''',
                       (QTime.currentTime().toString(),))
        conn.commit()

    def record_pomodoro_work_end(self):
        cursor.execute('''UPDATE "tbl.Pomodoro" SET Hora_Fin_Pomodoro = ?
                           WHERE ID = (SELECT MAX(ID) FROM "tbl.Pomodoro")''',
                       (QTime.currentTime().toString(),))
        conn.commit()

    def record_pomodoro_break_start(self):
        cursor.execute('''UPDATE "tbl.Pomodoro" SET Hora_Inicio_Descanso = ?
                           WHERE ID = (SELECT MAX(ID) FROM "tbl.Pomodoro")''',
                       (QTime.currentTime().toString(),))
        conn.commit()

    def record_pomodoro_break_end(self):
        cursor.execute('''UPDATE "tbl.Pomodoro" SET Hora_Fin = ?
                           WHERE ID = (SELECT MAX(ID) FROM "tbl.Pomodoro")''',
                       (QTime.currentTime().toString(),))
        conn.commit()

    @staticmethod
    def format_time(seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02}:{secs:02}"



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Aplicación de Gestión de Tiempo")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        self.timer_tab = Timer()
        self.alarm_tab = Alarm()
        self.pomodoro_tab = Pomodoro()

        self.tab_widget.addTab(self.timer_tab, "Temporizador")
        self.tab_widget.addTab(self.alarm_tab, "Alarma")
        self.tab_widget.addTab(self.pomodoro_tab, "Pomodoro")

        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

    def closeEvent(self, event):
        conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
