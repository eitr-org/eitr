#version 440
// The website hero's northern lights (website/src/components/AuroraSky.astro),
// for the desktop's live wallpaper: three curtains with a lime fringe and green
// at the foot, magenta rising to violet, drifting on their own.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float time;
    float aspect;
    vec4 lime;
    vec4 green;
    vec4 magenta;
    vec4 violet;
};

float hash(vec2 p) {
    vec3 q = fract(vec3(p.xyx) * 0.1031);
    q += dot(q, q.yzx + 33.33);
    return fract((q.x + q.y) * q.z);
}

float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

float fbm(vec2 p) {
    float value = 0.0, amplitude = 0.5;
    for (int i = 0; i < 4; i++) { value += amplitude * noise(p); p *= 2.0; amplitude *= 0.5; }
    return value;
}

void main() {
    vec2 uv = vec2(qt_TexCoord0.x, 1.0 - qt_TexCoord0.y);
    vec3 color = vec3(0.0);
    for (int i = 0; i < 3; i++) {
        float layer = float(i);
        float x = uv.x * aspect + layer * 0.9;
        float curve = 0.56 + layer * 0.07 + 0.11 * sin(x * 1.2 + time * 0.045 * (1.0 + layer * 0.35)) + 0.08 * fbm(vec2(x * 1.4, time * 0.03 + layer));
        float rise = uv.y - curve;
        float curtain = exp(-max(-rise, 0.0) * 18.0) * exp(-max(rise, 0.0) * 3.4);
        float rays = 0.45 + 0.55 * fbm(vec2(x * 7.0, time * 0.06 + layer * 3.0));
        float height = clamp(rise / 0.18, 0.0, 1.0);
        float pink = mix(0.55, 1.0, smoothstep(0.3, 0.6, fbm(vec2(x * 0.9 + layer * 2.0, time * 0.012))));
        vec3 foot = mix(lime.rgb, green.rgb, smoothstep(0.0, 0.08, height));
        vec3 greenish = mix(foot, violet.rgb * 0.8, smoothstep(0.45, 1.0, height));
        vec3 pinkish = mix(mix(green.rgb, magenta.rgb, smoothstep(0.0, 0.3, height)), violet.rgb, smoothstep(0.55, 1.0, height));
        color += mix(greenish, pinkish, pink) * curtain * rays * (0.6 - layer * 0.12);
    }
    color *= smoothstep(0.0, 0.35, uv.y) * smoothstep(1.0, 0.75, uv.y);
    fragColor = vec4(color, max(color.r, max(color.g, color.b))) * qt_Opacity;
}
