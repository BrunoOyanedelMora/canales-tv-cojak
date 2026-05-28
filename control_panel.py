import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import os
import time

# --- CATÁLOGO DE CONTINGENCIA ---
CANALES = [
    {"nombre": "TVN", "url": "https://mdstrm.com/live-stream-playlist-v/555c9a91eb4886825b07ee7b.m3u8"},
    {"nombre": "T13", "url": "https://redirector.rudo.video/hls-video/10b92cafdf3646cbc1e727f3dc76863621a327fd/t13/t13.smil/playlist.m3u8"},
    {"nombre": "CHV", "url": "https://redirector.rudo.video/hls-video/10b92cafdf3646cbc1e727f3dc76863621a327fd/chv/chv.smil/playlist.m3u8"},
    {"nombre": "MEGA", "url": "https://unlimited1-cl-isp.dps.live/mega/mega.smil/playlist.m3u8"},
    {"nombre": "CNN CHILE", "url": "https://jireh-4-hls-video-cl-isp.dps.live/hls-video/lvcl5/cnn/cnn.smil/playlist.m3u8"},
    {"nombre": "24 HORAS", "url": "https://mdstrm.com/live-stream-playlist/689ba606ecfe7915e1f8f741.m3u8"},
    {"nombre": "[RESPALDO] BioBio TV", "url": "https://rudo.video/live/bbtv/playlist.m3u8"},
    {"nombre": "[RESPALDO] CDO Deportes", "url": "https://rudo.video/live/cdo2/playlist.m3u8"},
    {"nombre": "[RESPALDO] Canal 26", "url": "https://live-am.canal26.com/hls/hd/main.m3u8"}
]

class MasterControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎛️ Master Control Directo | Sede")
        self.root.geometry("640x580")
        self.root.configure(bg="#0c0f12")
        self.root.resizable(False, False)
        
        # Estado de triggers globales
        self.sync_trigger = "0"
        self.breaking_trigger = "0"
        self.blackout_trigger = False
        
        # Estilos visuales
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#0c0f12', foreground='#8b9bb0', font=('Arial', 10, 'bold'))
        style.configure('TCombobox', fieldbackground='#14191f', background='#1b222b', foreground='white')
        
        tk.Label(root, text="PANEL DE CONTROL DE SEÑALES", bg="#0c0f12", fg="#ff4444", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Tabla/Grid de pantallas
        frame_grid = tk.Frame(root, bg="#0c0f12")
        frame_grid.pack(pady=5, padx=15, fill="x")
        
        self.dropdowns = {}
        nombres_canales = [c["nombre"] for c in CANALES]
        config_previa = self.cargar_config_previa()
        
        # Crear filas con botones independientes por pantalla
        for i in range(1, 7):
            frame_row = tk.Frame(frame_grid, bg="#14191f", highlightbackground="#242f3d", highlightthickness=1)
            frame_row.pack(fill='x', pady=4, ipady=4)
            
            lbl = tk.Label(frame_row, text=f" PANTALLA {i}", bg="#14191f", fg="white", font=("Arial", 10, "bold"), width=11, anchor="w")
            lbl.pack(side='left', padx=5)
            
            cb = ttk.Combobox(frame_row, values=nombres_canales, width=24, state="readonly")
            if str(i) in config_previa and config_previa[str(i)]["nombre"] in nombres_canales:
                cb.current(nombres_canales.index(config_previa[str(i)]["nombre"]))
            else:
                cb.current(i-1 if i-1 < len(nombres_canales) else 0)
            cb.pack(side='left', padx=5)
            self.dropdowns[i] = cb
            
            # Botón Cambiar transmisión de ESTA pantalla
            btn_cambiar = tk.Button(frame_row, text="📺 Cambiar", bg="#242f3d", fg="white", font=("Arial", 9, "bold"),
                                    command=lambda idx=i: self.ejecutar_accion(accion="cambiar", slot=idx), relief="flat", width=9)
            btn_cambiar.pack(side='left', padx=4)
            
            # Botón Último Minuto (Maximizar esta pantalla desde la Mac)
            btn_break = tk.Button(frame_row, text="🚨 Alerta", bg="#3a1a1a", fg="#ff6666", font=("Arial", 9, "bold"),
                                  command=lambda idx=i: self.ejecutar_accion(accion="breaking", slot=idx), relief="flat", width=8)
            btn_break.pack(side='left', padx=4)

        # --- SECCIÓN DE FUNCIONES GENERALES/AVANZADAS ---
        lbl_ops = tk.Label(root, text="COMANDOS DE SINCRONIZACIÓN GLOBAL", bg="#0c0f12", fg="#8b9bb0", font=("Arial", 10, "bold"))
        lbl_ops.pack(pady=(15, 5))
        
        frame_global = tk.Frame(root, bg="#0c0f12")
        frame_global.pack(fill="x", padx=15)
        
        # FUNCIÓN: Forzar a que vayan al mismo tiempo (Remover Delay acumulado)
        btn_sync = tk.Button(frame_global, text="🔄 SINCRONIZAR TIEMPOS (EVITAR RETRASOS)", bg="#00e676", fg="#000",
                             font=("Arial", 10, "bold"), command=lambda: self.ejecutar_accion(accion="sync_tiempos"), relief="flat")
        btn_sync.pack(fill="x", pady=3, ipady=6)
        
        # FUNCIÓN ADICIONAL: Restaurar grilla / Quitar Alertas activas
        btn_clear = tk.Button(frame_global, text="🟢 RESTAURAR GRILLA NORMAL (6 PANTALLAS)", bg="#1b222b", fg="white",
                              font=("Arial", 10, "bold"), command=lambda: self.ejecutar_accion(accion="restaurar_grilla"), relief="flat")
        btn_clear.pack(fill="x", pady=3, ipady=4)

        # Barra de estado
        self.lbl_status = tk.Label(root, text="Listo • Esperando órdenes", bg="#14191f", fg="#00e676", font=("Arial", 10, "italic"))
        self.lbl_status.pack(side="bottom", fill="x", ipady=5)

    def cargar_config_previa(self):
        if os.path.exists("live-config.json"):
            try:
                with open("live-config.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sync_trigger = data.get("sync_trigger", "0")
                    self.breaking_trigger = str(data.get("breaking_trigger", "0"))
                    return data
            except: return {}
        return {}

    def ejecutar_accion(self, accion, slot=None):
        self.lbl_status.config(text="Procesando comando maestro...", fg="#ffaa00")
        self.root.update()
        
        # Re-armar el mapa base de canales según los dropdowns actuales
        nuevo_json = {}
        for i in range(1, 7):
            nombre_sel = self.dropdowns[i].get()
            canal_obj = next(c for c in CANALES if c["nombre"] == nombre_sel)
            nuevo_json[str(i)] = {"nombre": canal_obj["nombre"], "url": canal_obj["url"]}
        
        # Aplicar lógica según el botón presionado
        if accion == "cambiar":
            self.lbl_status.config(text=f"Cambiando Pantalla {slot}...")
        elif accion == "breaking":
            self.breaking_trigger = str(slot)
            self.lbl_status.config(text=f"Lanzando Alerta de Último Minuto en P{slot}!")
        elif accion == "restaurar_grilla":
            self.breaking_trigger = "0"
            self.lbl_status.config(text="Restaurando visualización general...")
        elif accion == "sync_tiempos":
            # Usamos el timestamp actual como un ID único. Las TVs al ver un ID nuevo refrescarán su buffer al "en vivo" real.
            self.sync_trigger = str(int(time.time()))
            self.lbl_status.config(text="Enviando pulso de sincronización de transmisión...")

        # Inyectar variables de control al JSON de GitHub
        nuevo_json["sync_trigger"] = self.sync_trigger
        nuevo_json["breaking_trigger"] = self.breaking_trigger

        # Guardar local y subir
        try:
            with open("live-config.json", "w", encoding="utf-8") as f:
                json.dump(nuevo_json, f, indent=4, ensure_ascii=False)
            
            # Subida veloz a GitHub deshabilitando reportes pesados en consola
            subprocess.run(["git", "add", "live-config.json"], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Master Control UX: {accion}"], check=True, capture_output=True)
            subprocess.run(["git", "push"], check=True, capture_output=True)
            
            self.lbl_status.config(text="¡Comando enviado con éxito a GitHub Pages!", fg="#00e676")
        except Exception as e:
            self.lbl_status.config(text="Error ejecutando comando", fg="#ff4444")
            messagebox.showerror("Error de Conexión / Git", f"No se pudo sincronizar el comando:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MasterControlApp(root)
    root.mainloop()