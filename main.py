from modelo.main import Modelo
from vista.main import Vista
from controlador.main import Controller



def main():
    model = Modelo()
    view = Vista()
    controller = Controller(model, view)
    controller.start()

if __name__ == "__main__":
    main()