#!/usr/bin/env python3
"""Identify the session's EGL renderer without an optional diagnostics package."""
import ctypes
import json
import os


def software_renderer(renderer, backend="", forced=""):
    """Classify driver names and explicit Qt/Mesa software choices."""
    name = renderer.casefold()
    return (backend.casefold() == "software" or forced.casefold() in {"1", "true", "yes"}
            or any(token in name for token in ("llvmpipe", "softpipe", "swrast", "software rasterizer", "lavapipe")))


def renderer_name():
    """Use the Wayland EGL display, respecting Mesa's device/driver environment."""
    egl = ctypes.CDLL('libEGL.so.1')
    gl = ctypes.CDLL('libGLESv2.so.2')
    pointer, integer = ctypes.c_void_p, ctypes.c_int
    egl.eglGetProcAddress.argtypes = [ctypes.c_char_p]
    egl.eglGetProcAddress.restype = pointer
    address = egl.eglGetProcAddress(b'eglGetPlatformDisplayEXT')
    if not address:
        raise RuntimeError('EGL platform display unavailable')
    get_display = ctypes.CFUNCTYPE(pointer, ctypes.c_uint, pointer, ctypes.POINTER(integer))(address)
    display = get_display(0x31D8, None, None)  # EGL_PLATFORM_WAYLAND_KHR
    signatures = {
        'eglInitialize': ([pointer, ctypes.POINTER(integer), ctypes.POINTER(integer)], ctypes.c_uint),
        'eglBindAPI': ([ctypes.c_uint], ctypes.c_uint),
        'eglChooseConfig': ([pointer, ctypes.POINTER(integer), ctypes.POINTER(pointer), integer, ctypes.POINTER(integer)], ctypes.c_uint),
        'eglCreateContext': ([pointer, pointer, pointer, ctypes.POINTER(integer)], pointer),
        'eglMakeCurrent': ([pointer, pointer, pointer, pointer], ctypes.c_uint),
        'eglDestroyContext': ([pointer, pointer], ctypes.c_uint),
        'eglTerminate': ([pointer], ctypes.c_uint),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(egl, name)
        function.argtypes, function.restype = arguments, result
    if not display or not egl.eglInitialize(display, None, None):
        raise RuntimeError('Wayland EGL unavailable')
    context = None
    try:
        if not egl.eglBindAPI(0x30A0):  # EGL_OPENGL_ES_API
            raise RuntimeError('EGL GLES unavailable')
        attributes = (integer * 3)(0x3040, 4, 0x3038)  # EGL_RENDERABLE_TYPE, ES2, NONE
        config, count = pointer(), integer()
        if not egl.eglChooseConfig(display, attributes, ctypes.byref(config), 1, ctypes.byref(count)) or count.value == 0:
            raise RuntimeError('EGL config unavailable')
        context = egl.eglCreateContext(display, config, None, (integer * 3)(0x3098, 2, 0x3038))
        if not context or not egl.eglMakeCurrent(display, None, None, context):
            raise RuntimeError('EGL context unavailable')
        gl.glGetString.argtypes, gl.glGetString.restype = [ctypes.c_uint], ctypes.c_char_p
        return (gl.glGetString(0x1F01) or b'').decode('utf-8', 'replace')  # GL_RENDERER
    finally:
        egl.eglMakeCurrent(display, None, None, None)
        if context:
            egl.eglDestroyContext(display, context)
        egl.eglTerminate(display)


def detect(probe=renderer_name, environment=None):
    environment = os.environ if environment is None else environment
    backend, forced = environment.get('QT_QUICK_BACKEND', ''), environment.get('LIBGL_ALWAYS_SOFTWARE', '')
    if software_renderer('', backend, forced):
        return {'software': True, 'detected': True}
    try:
        renderer = probe()
        if not renderer:
            raise RuntimeError('Empty renderer')
        return {'software': software_renderer(renderer), 'detected': True}
    except (OSError, RuntimeError):
        # Keep Hyprpaper's still frame until a renderer can be established.
        return {'software': True, 'detected': False}


if __name__ == '__main__':
    print(json.dumps(detect()))
