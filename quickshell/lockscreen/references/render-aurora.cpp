// Surfaceless reference renderer: execute the canonical GLSL without a desktop or QPA window.
#define GL_GLEXT_PROTOTYPES
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GL/gl.h>
#include <GL/glext.h>
#include <QColor>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QFile>
#include <QImage>
#include <array>
#include <iostream>
#include <stdexcept>
#include <sys/resource.h>
#include <vector>

static void require(bool condition, const char *message) {
    if (!condition) throw std::runtime_error(message);
}

static GLuint compile(GLenum type, const QByteArray &text) {
    const GLuint shader = glCreateShader(type);
    const char *source = text.constData();
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);
    GLint success = 0;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        std::array<char, 8192> log{};
        glGetShaderInfoLog(shader, log.size(), nullptr, log.data());
        throw std::runtime_error(log.data());
    }
    return shader;
}

static double cpuSeconds() {
    rusage usage{};
    getrusage(RUSAGE_SELF, &usage);
    return usage.ru_utime.tv_sec + usage.ru_utime.tv_usec / 1e6
         + usage.ru_stime.tv_sec + usage.ru_stime.tv_usec / 1e6;
}

int main(int argc, char **argv) {
    QCoreApplication application(argc, argv);
    try {
        require(argc == 12 || argc == 13, "Usage: render-aurora SOURCE OUTPUT WIDTH HEIGHT TIME OPACITY LIME GREEN MAGENTA VIOLET FRAMES [LIGHT_TINT]");
        const int width = QString(argv[3]).toInt(), height = QString(argv[4]).toInt();
        const int frames = QString(argv[11]).toInt();
        require(width > 0 && height > 0 && frames > 0, "Invalid render dimensions or frame count");
        EGLDisplay display = eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, nullptr);
        require(display != EGL_NO_DISPLAY, "No surfaceless EGL display");
        require(eglInitialize(display, nullptr, nullptr), "EGL initialization failed");
        require(eglBindAPI(EGL_OPENGL_API), "OpenGL API unavailable");
        const EGLint attributes[] = {EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
                                     EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE};
        EGLConfig config{};
        EGLint count = 0;
        require(eglChooseConfig(display, attributes, &config, 1, &count) && count, "No pbuffer EGL config");
        const EGLint contextAttributes[] = {EGL_CONTEXT_MAJOR_VERSION, 4, EGL_CONTEXT_MINOR_VERSION, 4,
                                           EGL_CONTEXT_OPENGL_PROFILE_MASK, EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT, EGL_NONE};
        EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, contextAttributes);
        require(context != EGL_NO_CONTEXT, "OpenGL 4.4 context unavailable");
        const EGLint surfaceAttributes[] = {EGL_WIDTH, 1, EGL_HEIGHT, 1, EGL_NONE};
        EGLSurface surface = eglCreatePbufferSurface(display, config, surfaceAttributes);
        require(surface != EGL_NO_SURFACE, "Pbuffer creation failed");
        require(eglMakeCurrent(display, surface, surface, context), "Cannot make EGL context current");
        QFile source(argv[1]);
        require(source.open(QIODevice::ReadOnly), "Cannot read canonical shader");
        const QByteArray vertex = R"(#version 440
layout(location = 0) out vec2 qt_TexCoord0;
void main() {
    vec2 positions[3] = vec2[3](vec2(-1,-1), vec2(3,-1), vec2(-1,3));
    vec2 position = positions[gl_VertexID];
    qt_TexCoord0 = vec2((position.x + 1.0) * 0.5, (1.0 - position.y) * 0.5);
    gl_Position = vec4(position, 0, 1);
})";
        GLuint program = glCreateProgram();
        glAttachShader(program, compile(GL_VERTEX_SHADER, vertex));
        glAttachShader(program, compile(GL_FRAGMENT_SHADER, source.readAll()));
        glLinkProgram(program);
        GLint linked = 0;
        glGetProgramiv(program, GL_LINK_STATUS, &linked);
        require(linked, "Shader link failed");
        glUseProgram(program);
        GLuint texture = 0, framebuffer = 0, vertexArray = 0, buffer = 0;
        glGenTextures(1, &texture);
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        glGenFramebuffers(1, &framebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0);
        require(glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE, "Incomplete framebuffer");
        glGenVertexArrays(1, &vertexArray);
        glBindVertexArray(vertexArray);
        std::array<float, 36> uniforms{};
        for (int diagonal = 0; diagonal < 4; diagonal++) uniforms[diagonal * 5] = 1;
        uniforms[16] = QString(argv[6]).toFloat();
        uniforms[17] = QString(argv[5]).toFloat();
        uniforms[18] = float(width) / height;
        for (int colorIndex = 0; colorIndex < 4; colorIndex++) {
            QColor color(argv[7 + colorIndex]);
            require(color.isValid(), "Invalid shader palette color");
            uniforms[20 + colorIndex * 4] = color.redF();
            uniforms[21 + colorIndex * 4] = color.greenF();
            uniforms[22 + colorIndex * 4] = color.blueF();
            uniforms[23 + colorIndex * 4] = color.alphaF();
        }
        glGenBuffers(1, &buffer);
        glBindBuffer(GL_UNIFORM_BUFFER, buffer);
        glBufferData(GL_UNIFORM_BUFFER, sizeof(uniforms), uniforms.data(), GL_DYNAMIC_DRAW);
        glBindBufferBase(GL_UNIFORM_BUFFER, 0, buffer);
        glViewport(0, 0, width, height);
        glDisable(GL_BLEND);
        glDrawArrays(GL_TRIANGLES, 0, 3);
        glFinish();
        const double beforeCpu = cpuSeconds();
        QElapsedTimer elapsed;
        elapsed.start();
        for (int frame = 0; frame < frames; frame++) {
            uniforms[17] = QString(argv[5]).toFloat() + frame * 0.5f;
            glBufferSubData(GL_UNIFORM_BUFFER, 0, sizeof(uniforms), uniforms.data());
            glDrawArrays(GL_TRIANGLES, 0, 3);
            glFinish();
        }
        const double milliseconds = elapsed.nsecsElapsed() / 1e6 / frames;
        const double cpuPerFrame = (cpuSeconds() - beforeCpu) / frames;
        std::vector<unsigned char> pixels(size_t(width) * height * 4);
        glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
        require(glGetError() == GL_NO_ERROR, "OpenGL rendering failed");
        QImage image(pixels.data(), width, height, QImage::Format_RGBA8888_Premultiplied);
        QImage output = image.flipped(Qt::Vertical);
        if (argc == 13) {
            const QColor pigment = QColor(argv[12]).darker(180);
            for (int row = 0; row < output.height(); row++) {
                auto *pixels = output.scanLine(row);
                for (int column = 0; column < output.width(); column++) {
                    const int alpha = pixels[column * 4 + 3];
                    pixels[column * 4] = (pigment.red() * alpha + 127) / 255;
                    pixels[column * 4 + 1] = (pigment.green() * alpha + 127) / 255;
                    pixels[column * 4 + 2] = (pigment.blue() * alpha + 127) / 255;
                }
            }
        }
        require(output.save(argv[2]), "Cannot save shader reference");
        std::cout << "renderer=" << glGetString(GL_RENDERER) << " width=" << width << " height=" << height
                  << " ms_per_frame=" << milliseconds << " cpu_seconds_per_frame=" << cpuPerFrame
                  << " core_percent_at_2fps=" << cpuPerFrame * 200 << '\n';
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        eglDestroySurface(display, surface);
        eglDestroyContext(display, context);
        eglTerminate(display);
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
