"""Escala nativa da janela no Windows, antes de iniciar o PPlay/SDL."""
import os
import sys


def preparar_escala_windows():
    """Evita que o Windows amplie só a janela e desloque o cursor na captura.

    Não muda a escala do desktop. Em IDEs que já definiram o DPI, a chamada
    pode ser recusada pelo Windows; preservamos a configuração do processo.
    """
    if sys.platform != 'win32' or os.environ.get('SDL_VIDEODRIVER') == 'dummy':
        return False
    import ctypes
    from ctypes import wintypes

    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        configurar = user32.SetProcessDpiAwarenessContext
        configurar.argtypes = [ctypes.c_void_p]
        configurar.restype = wintypes.BOOL
        return bool(configurar(ctypes.c_void_p(-4)))  # Per Monitor V2.
    except (AttributeError, OSError):
        return False
