
# Entrypoint that keeps the original app behavior/structure,
# but sources logic from organized modules.
from movidesk.ui_main import App

if __name__ == "__main__":
    App().mainloop()
