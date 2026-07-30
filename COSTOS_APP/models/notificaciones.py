"""Notificaciones de Windows para avisar cuando termina una carga."""
from __future__ import annotations


def notificar(titulo: str, mensaje: str) -> None:
    """Muestra un toast de Windows. Si falla, no interrumpe la app."""
    try:
        from winotify import Notification, audio

        toast = Notification(
            app_id="COSTOS PUBLISTIK",
            title=titulo,
            msg=mensaje,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        return
    except Exception:
        pass

    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass
