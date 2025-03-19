import tkinter as tk
from tkinter import Canvas, messagebox, Toplevel
from PIL import Image, ImageTk
import cv2
import face_recognition
import face_recognition_models
import numpy as np
import os
from datetime import datetime
import threading
import queue
from pymongo import MongoClient
from twilio.rest import Client
from dotenv import load_dotenv

#cargar environment file
load_dotenv()

#load env vars
client = MongoClient(os.getenv("MONGOCLIENT"))
db = client[os.getenv("NAME_BD")]
alumnos_collection = db[os.getenv("ALUMNOS_COLLECTION")]
asistencia_collection = db[os.getenv("ASISTENCIA_COLLECTION")]
client.server_info()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHTS_NUMBER")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

KNOWN_FACES_DIR = os.getenv("DIR_FACES")
#load env vars

def resize_image(image_path, size=(120, 120)):
    image = Image.open(image_path)
    image = image.resize(size, Image.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    return photo

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_main_screen(root):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = Canvas(root, width=1600, height=900, bg="white", highlightthickness=0)
    canvas.pack()

    background_image = resize_image("imagenes/fondo.png", size=(1600, 900))
    if background_image:
        canvas.create_image(0, 0, anchor="nw", image=background_image)
        canvas.background_image = background_image

    logo1 = resize_image("imagenes/LOGO_SEMS.png", size=(200, 200))
    if logo1:
        canvas.create_image(50, 50, anchor="nw", image=logo1)
        canvas.logo1 = logo1

    logo2 = resize_image("imagenes/LOGO_SEP.png", size=(200, 200))
    if logo2:
        canvas.create_image(1350, 50, anchor="ne", image=logo2)
        canvas.logo2 = logo2

    logo3 = resize_image("imagenes/LOGO_DEGETI.png", size=(200, 200))
    if logo3:
        canvas.create_image(50, 750, anchor="sw", image=logo3)
        canvas.logo3 = logo3

    logo4 = resize_image("imagenes/LOGO_CBTIS179.png", size=(200, 200))
    if logo4:
        canvas.create_image(1350, 750, anchor="se", image=logo4)
        canvas.logo4 = logo4

    canvas.create_rectangle(5, 5, 1595, 895, outline="#D4AF37", width=5)

    canvas.create_text(
        800, 250,
        text="BIENVENIDO AL SISTEMA",
        fill="#b89234",
        font=("Impact", 60),
        justify="center"
    )

    register_button = tk.Button(root, text="REGISTRAR ALUMNO", bg="#b08948", fg="white", font=("Arial", 16, "bold"),
                                command=lambda: show_register_screen(root))
    register_button.place(x=530, y=720, width=500, height=70)

    recognize_button = tk.Button(root, text="INICIAR RECONOCIMIENTO", bg="#b08948", fg="white",
                                 font=("Arial", 16, "bold"),
                                 command=lambda: start_recognition(root))
    recognize_button.place(x=530, y=620, width=500, height=70)

    canvas.images = [img for img in [background_image, logo1, logo2, logo3, logo4] if img]

def show_register_screen(root):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = Canvas(root, width=1600, height=900, bg="white", highlightthickness=0)
    canvas.pack()

    background_image = resize_image("imagenes/fondo.png", size=(1600, 900))
    if background_image:
        canvas.create_image(0, 0, anchor="nw", image=background_image)
        canvas.background_image = background_image

    logo1 = resize_image("imagenes/LOGO_SEMS.png", size=(200, 200))
    if logo1:
        canvas.create_image(50, 50, anchor="nw", image=logo1)
        canvas.logo1 = logo1

    logo2 = resize_image("imagenes/LOGO_SEP.png", size=(200, 200))
    if logo2:
        canvas.create_image(1350, 50, anchor="ne", image=logo2)
        canvas.logo2 = logo2

    logo3 = resize_image("imagenes/LOGO_DEGETI.png", size=(200, 200))
    if logo3:
        canvas.create_image(50, 750, anchor="sw", image=logo3)
        canvas.logo3 = logo3

    logo4 = resize_image("imagenes/LOGO_CBTIS179.png", size=(200, 200))
    if logo4:
        canvas.create_image(1350, 750, anchor="se", image=logo4)
        canvas.logo4 = logo4

    canvas.create_rectangle(5, 5, 1595, 895, outline="#D4AF37", width=5)

    canvas.create_text(
        790, 200,
        text="REGISTRAR DATOS DEL ALUMNO",
        fill="#b89234",
        font=("Impact", 40)
    )

    labels = ["Nombre del Alumno", "Semestre", "Número de Control", "Número del Tutor"]
    y_positions = [300, 400, 500, 600]
    entries = {}

    for i, label in enumerate(labels):
        canvas.create_text(600, y_positions[i], text=label, fill="black", font=("Arial", 18, "bold"), anchor="e")
        entry = tk.Entry(root, font=("Arial", 16), bd=2, relief="groove")
        entry.place(x=620, y=y_positions[i] - 15, width=400, height=40)
        entries[label.lower().replace(" ", "_")] = entry

    def save_data_and_capture_face():
        student_data = {
            "nombre": entries["nombre_del_alumno"].get().strip(),
            "semestre": entries["semestre"].get().strip(),
            "numero_control": entries["número_de_control"].get().strip(),
            "numero_tutor": entries["número_del_tutor"].get().strip(),
        }
        if not all(student_data.values()):
            messagebox.showwarning("Advertencia", "Por favor completa todos los campos")
            return
        result = alumnos_collection.update_one(
            {"numero_control": student_data["numero_control"]},
            {"$set": student_data},
            upsert=True
        )
        capture_face(root, student_data["numero_control"])

    register_button = tk.Button(root, text="GUARDAR DATOS Y CAPTURAR ROSTRO", bg="#b08948", fg="white",
                                font=("Arial", 16, "bold"),
                                command=save_data_and_capture_face)
    register_button.place(x=530, y=720, width=500, height=70)

    canvas.images = [img for img in [background_image, logo1, logo2, logo3, logo4] if img]

def capture_face(root, numero_control):
    capture_window = Toplevel(root)
    center_window(capture_window, 640, 480)
    capture_window.title("Capturar Rostro")

    video_label = tk.Label(capture_window)
    video_label.pack()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Error", "No se pudo abrir la cámara")
        capture_window.destroy()
        return

    def update_video():
        ret, frame = cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.image = imgtk
            video_label.configure(image=imgtk)
        capture_window.after(33, update_video)

    def save_face_and_close():
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "No se pudo capturar la imagen")
            return
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if len(face_locations) != 1:
            messagebox.showerror("Error", "Debe haber exactamente un rostro en la imagen")
            return
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not face_encodings:
            messagebox.showerror("Error", "No se pudo generar el encoding facial")
            return
        encoding = face_encodings[0]
        if len(encoding) != 128:
            messagebox.showerror("Error", f"Encoding inválido: longitud esperada 128, obtenida {len(encoding)}")
            return
        filename = os.path.join(KNOWN_FACES_DIR, f"{numero_control}.jpg")
        cv2.imwrite(filename, frame)
        result = alumnos_collection.update_one(
            {"numero_control": numero_control},
            {"$set": {"face_encoding": encoding.tolist()}},
            upsert=True
        )
        messagebox.showinfo("Éxito", f"Rostro guardado como {filename}")
        cap.release()
        capture_window.destroy()
        show_main_screen(root)

    save_button = tk.Button(capture_window, text="GUARDAR ROSTRO", bg="#3498DB", fg="white", font=("Arial", 12, "bold"),
                            command=save_face_and_close)
    save_button.pack(pady=10)

    update_video()

def start_recognition(root):
    recognition_window = Toplevel(root)
    center_window(recognition_window, 640, 480)
    recognition_window.title("Reconocimiento Facial")

    video_label = tk.Label(recognition_window)
    video_label.pack()

    status_label = tk.Label(recognition_window, text="Estado: Listo", bg="#34495E", fg="white", font=("Arial", 12))
    status_label.pack(fill="x", side="bottom")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Error", "No se pudo abrir la cámara")
        recognition_window.destroy()
        return

    frame_queue = queue.Queue(maxsize=1)
    known_face_encodings, known_face_names = load_known_faces()
    if not known_face_encodings:
        messagebox.showwarning("Advertencia", "No hay rostros conocidos registrados")
        recognition_window.destroy()
        return

    attendances_registered = set()
    frame_counter = 0

    def process_video_thread():
        nonlocal frame_counter
        while recognition_window.winfo_exists():
            ret, frame = cap.read()
            if not ret:
                status_label.config(text="Estado: Error al capturar cuadro")
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if frame_counter % 5 == 0:
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    name = "Desconocido"
                    if known_face_encodings:
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        if any(matches):
                            best_match_index = np.argmin(face_distances)
                            name = known_face_names[best_match_index]
                        else:
                            continue

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

                    if name != "Desconocido" and name not in attendances_registered:
                        register_attendance(name)
                        attendances_registered.add(name)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            try:
                frame_queue.put_nowait(imgtk)
            except queue.Full:
                pass
            frame_counter += 1

    def update_gui():
        if recognition_window.winfo_exists():
            try:
                imgtk = frame_queue.get_nowait()
                video_label.image = imgtk
                video_label.configure(image=imgtk)
            except queue.Empty:
                pass
            recognition_window.after(33, update_gui)

    def register_attendance(nombre):
        ahora = datetime.now()
        result = asistencia_collection.insert_one({
            "nombre": nombre,
            "fecha": ahora
        })
        status_label.config(text=f"Estado: Asistencia registrada para {nombre}")

        alumno = alumnos_collection.find_one({"nombre": nombre})
        if alumno and "numero_tutor" in alumno:
            numero_tutor = alumno["numero_tutor"]
            if not numero_tutor.startswith("+"):
                numero_tutor = f"+52{numero_tutor.lstrip('0')}"
            mensaje = f"Hola, se ha registrado la asistencia de {nombre} el {ahora.strftime('%d/%m/%Y a las %H:%M:%S')}."
            response = twilio_client.messages.create(
                body=mensaje,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=f"whatsapp:{numero_tutor}"
            )
            status_label.config(text=f"Estado: Mensaje enviado a {numero_tutor}")
        else:
            status_label.config(text=f"Estado: No se encontró tutor para {nombre}")

    threading.Thread(target=process_video_thread, daemon=True).start()
    update_gui()

    recognition_window.protocol("WM_DELETE_WINDOW", lambda: on_closing_recognition(recognition_window, cap))

def load_known_faces():
    known_face_encodings = []
    known_face_names = []
    alumnos = alumnos_collection.find({"face_encoding": {"$exists": True}})
    for alumno in alumnos:
        encoding = alumno.get("face_encoding")
        nombre = alumno.get("nombre", "Sin nombre")
        numero_control = alumno.get("numero_control", "Sin número")
        if encoding:
            encoding_array = np.array(encoding, dtype=np.float64)
            if len(encoding_array) == 128:
                known_face_encodings.append(encoding_array)
                known_face_names.append(nombre)
            else:
                continue
        else:
            continue
    return known_face_encodings, known_face_names

def on_closing_recognition(window, cap):
    cap.release()
    window.destroy()

if __name__ == "__main__":
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
    root = tk.Tk()
    root.title("Sistema de Reconocimiento Electrónico Facial X")
    center_window(root, 1600, 900)
    show_main_screen(root)
    root.mainloop()