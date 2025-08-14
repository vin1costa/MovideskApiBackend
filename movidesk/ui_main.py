
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox

from .config_store import load_config, save_config
from .security import verify_password, hash_password, is_hashed
from .api_client import apontar_horas
from .i18n import TEXTS as T

config = load_config()

class App(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title(T["app_title"])
        self.geometry("560x560")
        self.resizable(False, False)

        self.current_user = None

        self.page_container = tb.Frame(self, padding=10)
        self.page_container.pack(fill=BOTH, expand=True)

        self.login_page = LoginPage(self.page_container, self.do_login, self.toggle_theme)
        self.main_page  = MainPage(self.page_container, self.do_logoff, self.open_admin, self.toggle_theme)
        self.show_page(self.login_page)

    def show_page(self, page):
        for child in self.page_container.winfo_children():
            child.pack_forget()
        page.pack(fill=BOTH, expand=True)

    def do_login(self, usuario: str):
        self.current_user = usuario
        self.main_page.set_user(usuario)
        self.show_page(self.main_page)

    def do_logoff(self):
        self.current_user = None
        self.main_page.clear_fields()
        self.show_page(self.login_page)

    def open_admin(self):
        AdminWindow(self, on_change=lambda: self.main_page.refresh_admin_state())

    def toggle_theme(self):
        atual = self.style.theme.name
        self.style.theme_use("darkly" if atual != "darkly" else "flatly")

class LoginPage(tb.Frame):
    def __init__(self, master, on_login, on_toggle_theme):
        super().__init__(master)
        self.on_login = on_login
        self.on_toggle_theme = on_toggle_theme
        self._showing = False

        title = tb.Label(self, text=T["login_title"], font=("Segoe UI", 16, "bold"))
        title.pack(pady=(10, 20))

        form = tb.Frame(self); form.pack()

        row1 = tb.Frame(form); row1.pack(pady=6, fill=X)
        tb.Label(row1, text=T["user_label"], width=14, anchor="w").pack(side=LEFT)
        self.user_entry = tb.Entry(row1, width=28)
        self.user_entry.pack(side=LEFT)

        row2 = tb.Frame(form); row2.pack(pady=6, fill=X)
        tb.Label(row2, text=T["pass_label"], width=14, anchor="w").pack(side=LEFT)
        self.pass_entry = tb.Entry(row2, width=28, show="*")
        self.pass_entry.pack(side=LEFT)
        self.toggle_btn = tb.Button(row2, text=T["show_pass"], bootstyle=SECONDARY, command=self._toggle_password, width=14)
        self.toggle_btn.pack(side=LEFT, padx=6)

        actions = tb.Frame(self); actions.pack(pady=16)
        tb.Button(actions, text=T["login_btn"], bootstyle=SUCCESS, command=self.login).pack(side=LEFT, padx=5)
        tb.Button(actions, text=T["theme_btn"], bootstyle=INFO, command=self.on_toggle_theme).pack(side=LEFT, padx=5)

        self.user_entry.focus_set()

    def _toggle_password(self):
        self._showing = not self._showing
        self.pass_entry.config(show="" if self._showing else "*")
        self.toggle_btn.config(text=T["hide_pass"] if self._showing else T["show_pass"])

    def login(self):
        usuario = self.user_entry.get().strip()
        senha = self.pass_entry.get().strip()
        user = config.get("usuarios", {}).get(usuario)
        if user and verify_password(user.get("senha", ""), senha):
            self.on_login(usuario)
        else:
            messagebox.showerror(T["err"], T["invalid_login"])

class MainPage(tb.Frame):
    def __init__(self, master, on_logoff, on_open_admin, on_toggle_theme):
        super().__init__(master)
        self.on_logoff = on_logoff
        self.on_open_admin = on_open_admin
        self.on_toggle_theme = on_toggle_theme
        self.usuario_logado = None

        top = tb.Frame(self); top.pack(fill=X, pady=(5, 15))
        self.user_lbl = tb.Label(top, text=T["logged_as"].format(user="-"), font=("Segoe UI", 12, "bold"))
        self.user_lbl.pack(side=LEFT)

        tb.Button(top, text=T["theme_btn"], bootstyle=INFO, command=self.on_toggle_theme).pack(side=RIGHT, padx=4)
        tb.Button(top, text=T["logoff_btn"], bootstyle=DANGER, command=self.on_logoff).pack(side=RIGHT, padx=4)
        self.btn_admin = tb.Button(top, text=T["admin_btn"], bootstyle=SECONDARY, command=self.on_open_admin)
        self.btn_admin.pack(side=RIGHT, padx=4)

        card = tb.Labelframe(self, text=T["card_title"], padding=12)
        card.pack(fill=X, padx=4)

        self.ticket_id = self._row(card, T["ticket_label"])
        self.descricao = self._row(card, T["desc_label"])
        self.data      = self._row(card, T["date_label"])
        self.hora_ini  = self._row(card, T["start_label"])
        self.hora_fim  = self._row(card, T["end_label"])

        self.submit_btn = tb.Button(self, text=T["submit_btn"], bootstyle=SUCCESS, command=self._apontar)
        self.submit_btn.pack(pady=18)

        foot = tb.Label(self, text=T["footer"], bootstyle="secondary")
        foot.pack(side=BOTTOM, pady=6)

        self.refresh_admin_state()

    def _row(self, parent, label_text):
        row = tb.Frame(parent); row.pack(fill=X, pady=6)
        tb.Label(row, text=label_text, width=20, anchor="w").pack(side=LEFT)
        entry = tb.Entry(row); entry.pack(side=LEFT, fill=X, expand=True)
        return entry

    def set_user(self, usuario):
        self.usuario_logado = usuario
        self.user_lbl.config(text=T["logged_as"].format(user=usuario))
        self.refresh_admin_state()

    def refresh_admin_state(self):
        is_admin = False
        if self.usuario_logado and self.usuario_logado in config["usuarios"]:
            is_admin = bool(config["usuarios"][self.usuario_logado].get("admin", False))
        if is_admin:
            self.btn_admin.pack(side=RIGHT, padx=4)
        else:
            self.btn_admin.forget()

    def clear_fields(self):
        for e in [self.ticket_id, self.descricao, self.data, self.hora_ini, self.hora_fim]:
            e.delete(0, END)

    def _set_loading(self, loading: bool):
        if loading:
            self.submit_btn.config(state=DISABLED, text=T["submitting_btn"])
        else:
            self.submit_btn.config(state=NORMAL, text=T["submit_btn"])

    def _apontar(self):
        if not self.usuario_logado:
            messagebox.showerror(T["err"], T["no_user"]); return
        dados = config["usuarios"].get(self.usuario_logado, {})
        agent_id = dados.get("agent_id")
        if not agent_id:
            messagebox.showerror(T["err"], T["no_agent"]); return

        self._set_loading(True)
        try:
            ok = apontar_horas(
                config,
                self.ticket_id.get().strip(),
                self.descricao.get().strip(),
                self.data.get().strip(),
                self.hora_ini.get().strip(),
                self.hora_fim.get().strip(),
                agent_id,
                T
            )
            if ok:
                messagebox.showinfo(T["ok"], T["apontamento_ok"])
        except Exception as e:
            # Show friendly message if available
            msg = getattr(e, "user_message", str(e))
            messagebox.showerror(T["err"], msg)
        finally:
            self._set_loading(False)

class AdminWindow(tb.Toplevel):
    def __init__(self, master, on_change=None):
        super().__init__(master)
        self.title(T["admin_title"])
        self.geometry("640x500")
        self.resizable(False, False)
        self.on_change = on_change

        tb.Label(self, text=T["users_list"], font=("Segoe UI", 10, "bold")).pack(pady=(10, 6))
        cols = ("nome", "agent_id", "admin")
        self.tree = tb.Treeview(self, columns=cols, show="headings", height=10, bootstyle=INFO)
        self.tree.heading("nome", text="Nome")
        self.tree.heading("agent_id", text="Agent ID")
        self.tree.heading("admin", text="Admin")
        self.tree.column("nome", width=260)
        self.tree.column("agent_id", width=160)
        self.tree.column("admin", width=80, anchor=CENTER)
        self.tree.pack(fill=X, padx=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        form = tb.Labelframe(self, text=T["form_title"], padding=10)
        form.pack(fill=X, padx=10, pady=10)

        self.nome_e  = self._row(form, T["name_label"], width=38)
        self.senha_e = self._row(form, T["pass_label"], show="*", width=38)
        self.agent_e = self._row(form, T["agent_label"], width=38)

        chk_frame = tb.Frame(form); chk_frame.pack(fill=X, pady=4)
        self.admin_var = tk.BooleanVar(value=False)
        tb.Checkbutton(chk_frame, text=T["admin_check"], variable=self.admin_var).pack(side=LEFT)

        # Botões de ação dentro do formulário
        actions = tb.Frame(form); actions.pack(pady=6)
        tb.Button(actions, text=T["save_btn"], bootstyle=SUCCESS, command=self._salvar).pack(side=LEFT, padx=5)
        tb.Button(actions, text=T["remove_btn"], bootstyle=DANGER, command=self._remover).pack(side=LEFT, padx=5)
        tb.Button(actions, text=T["close_btn"], bootstyle=SECONDARY, command=self.destroy).pack(side=LEFT, padx=5)

        self._load_tree()

    def _row(self, parent, label, show=None, width=30):
        row = tb.Frame(parent); row.pack(fill=X, pady=4)
        tb.Label(row, text=label, width=18, anchor="w").pack(side=LEFT)
        e = tb.Entry(row, width=width, show=show if show else None)
        e.pack(side=LEFT)
        return e

    def _load_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for nome, dados in sorted(config["usuarios"].items()):
            self.tree.insert("", END, values=(nome, dados.get("agent_id", ""), "Sim" if dados.get("admin") else "Não"))

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel: return
        nome, agent, admin_str = self.tree.item(sel[0], "values")
        self.nome_e.delete(0, END); self.nome_e.insert(0, nome)
        self.senha_e.delete(0, END)
        self.agent_e.delete(0, END); self.agent_e.insert(0, agent)
        self.admin_var.set(admin_str == "Sim")

    def _salvar(self):
        nome = self.nome_e.get().strip()
        senha = self.senha_e.get().strip()
        agent = self.agent_e.get().strip()
        is_admin = self.admin_var.get()

        if not nome:
            messagebox.showerror(T["err"], T["inform_name"]); return
        if nome == "admin" and not is_admin:
            messagebox.showerror(T["err"], T["admin_must"]); return

        # Keep existing password if empty
        if nome in config["usuarios"] and not senha:
            senha = config["usuarios"][nome]["senha"]
        if not senha:
            messagebox.showerror(T["err"], T["inform_pass"]); return

        # Hash if needed
        if not isinstance(senha, str) or not senha:
            messagebox.showerror(T["err"], T["inform_pass"]); return
        if not senha.startswith("sha256$"):
            senha = hash_password(senha)

        config["usuarios"][nome] = {"senha": senha, "agent_id": agent, "admin": is_admin}
        save_config(config)
        self._load_tree()
        if self.on_change: self.on_change()
        messagebox.showinfo(T["ok"], T["user_saved"])

    def _remover(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror(T["err"], T["select_user"]); return
        nome, *_ = self.tree.item(sel[0], "values")
        if nome == "admin":
            messagebox.showerror(T["err"], T["no_remove_admin"]); return
        if messagebox.askyesno(T["ok"], T["confirm_remove"].format(name=nome)):
            config["usuarios"].pop(nome, None)
            save_config(config)
            self._load_tree()
            if self.on_change: self.on_change()
            messagebox.showinfo(T["ok"], T["user_removed"])
