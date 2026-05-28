import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import os

# --- CATÁLOGO DE CONTINGENCIA ---
# Puedes editar, añadir o quitar canales de esta lista cuando quieras.
CANALES = [
    {"nombre": "TVN", "url": "https://mdstrm.com/live-stream-playlist-v/555c9a91eb4886825b07ee7b.m3u8"},
    {"nombre": "T13", "url": "https://redirector.rudo.video/hls-video/10b92cafdf3646cbc1e727f3dc76863621a327fd/t13/t13.smil/playlist.m3u8"},
    {"nombre": "CHV", "url": "https://redirector.rudo.video/hls-video/10b92cafdf3646cbc1e727f3dc76863621a327fd/chv/chv.smil/playlist.m3u8"},
    {"nombre": "MEGA", "url": "https://unlimited1-cl-isp.dps.live/mega/mega.smil/playlist.m3u8"},
    {"nombre": "CNN CHILE", "url": "https://jireh-4-hls-video-cl-isp.dps.live/hls-video/lvcl5/cnn/cnn.smil/playlist.m3u8"},
    {"nombre": "24 HORAS", "url": "https://mdstrm.com/live-stream-playlist/689ba606ecfe7915e1f8f741.m3u8"},
    {"nombre": "[RESPALDO] BioBio TV", "url": "https://rudo.video/live/bbtv/playlist.m3u8"},
    {"nombre": "[RESPALDO] CDO Deportes", "url": "https://rudo.video/live/cdo2/playlist.m3u8"},
    {"nombre": "[RESPALDO] Canal 26 Noticias", "url": "https://live-am.canal26.com/hls/hd/main.m3u8"}
]

class MasterControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎛️ Master Control Sede")
        self.root.geometry("480x540")
        self.root.configure(bg="#0c0f12")
        self.root.resizable(False, False)
        
        # Estilos visuales Dark Mode Estilizados
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#0c0f12', foreground='#8b9bb0', font=('Arial', 11, 'bold'))
        style.configure('TCombobox', fieldbackground='#14191f', background='#1b222b', foreground='white')
        
        # Título
        title = tk.Label(root, text="CONTROL DE SEÑALES CENTRAL", bg="#0c0f12", fg="#ff4444", font=("Arial", 13, "bold"))
        title.pack(pady=15)
        
        self.dropdowns = {}
        frame_grid = tk.Frame(root, bg="#0c0f12")
        frame_grid.pack(pady=5, padx=20)
        
        nombres_canales = [c["nombre"] for c in CANALES]
        
        # Intentar cargar la configuración existente para no reiniciar desde cero
        config_previa = self.cargar_config_previa()

        # Generar los 6 controles
        for i in range(1, 7):
            frame_row = tk.Frame(frame_grid, bg="#0c0f12")
            frame_row.pack(fill='x', pady=6)
            
            lbl = ttk.Label(frame_row, text=f"Pantalla {i}:", width=12)
            lbl.pack(side='left')
            
            cb = ttk.Combobox(frame_row, values=nombres_canales, width=32, state="readonly")
            
            # Si existía una configuración previa para esta pantalla, la selecciona
            if str(i) in config_previa and config_previa[str(i)]["nombre"] in nombres_canales:
                idx = nombres_canales.index(config_previa[str(i)]["nombre"])
                cb.current(idx)
            else:
                cb.current(i-1 if i-1 < len(nombres_canales) else 0)
                
            cb.pack(side='left', padx=5)
            self.dropdowns[i] = cb

        # Botón de Acción Principal
        self.btn_push = tk.Button(
            root, 
            text="🔴 APLICAR Y SINCRONIZAR SEDE", 
            command=self.publicar_cambios,
            bg="#ff4444", 
            fg="white", 
            font=("Arial", 11, "bold"),
            activebackground="#cc3333",
            activeforeground="white",
            relief="flat",
            cursor="hand2"
        )
        self.btn_push.pack(pady=25, fill='x', padx=35, ipady=8)
        
        # Barra de estado inferior
        self.lbl_status = tk.Label(root, text="Conectado al repositorio • Listo", bg="#14191f", fg="#00e676", font=("Arial", 10, "italic"))
        self.lbl_status.pack(side="bottom", fill="x", ipady=5)

    def cargar_config_previa(self):
        if os.path.exists("live-config.json"):
            try:
                with open("live-config.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def publicar_cambios(self):
        self.lbl_status.config(text="Escribiendo configuración local...", fg="#ffaa00")
        self.root.update()
        
        # 1. Construir el nuevo JSON
        nuevo_estado = {}
        for i in range(1, 7):
            nombre_seleccionado = self.dropdowns[i].get()
            canal_obj = next(c for c in CANALES if c["nombre"] == nombre_seleccionado)
            nuevo_estado[str(i)] = {
                "nombre": canal_obj["nombre"],
                "url": canal_obj["url"]
            }
        
        # 2. Guardar el archivo JSON localmente
        try:
            with open("live-config.json", "w", encoding="utf-8") as f:
                json.dump(nuevo_estado, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
            return

        # 3. Empujar de forma automática e invisible hacia GitHub
        self.lbl_status.config(text="Subiendo actualizaciones a GitHub Pages...", fg="#ffaa00")
        self.root.update()
        
        try:
            # git add live-config.json
            subprocess.run(["git", "add", "live-config.json"], check=True, capture_output=True)
            # git commit
            subprocess.run(["git", "commit", "-m", "Master Control: Cambio manual de señales caídas"], check=True, capture_output=True)
            # git push
            subprocess.run(["git", "push"], check=True, capture_output=True)
            
            self.lbl_status.config(text="¡Sincronización Exitosa! GitHub está aplicando los cambios.", fg="#00e676")
            messagebox.showinfo("Éxito", "Las señales han sido cambiadas en el servidor.\nEn unos segundos los televisores captarán el cambio de forma automática.")
        except subprocess.CalledProcessError as e:
            self.lbl_status.config(text="Error de Sincronización", fg="#ff4444")
            err = e.stderr.decode('utf-8') if e.stderr else "Revisa la conexión o los permisos de Git."
            messagebox.showerror("Error de Git", f"No se pudo subir a GitHub automáticamente:\n\n{err}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MasterControlApp(root)
    root.mainloop()