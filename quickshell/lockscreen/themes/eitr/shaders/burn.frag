#version 440
// The lightning unlock: the lockscreen frame burns away like paper from the point
// the bolt struck. Inside a ragged, noisy circle it is gone (transparent, so the
// desktop shows); at the edge glow embers, and just ahead of them the frame chars.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 size;
    vec2 centre;
    float radius;
    float seed;
};
layout(binding = 1) uniform sampler2D source;

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
    for (int i = 0; i < 5; i++) { value += amplitude * noise(p); p *= 2.07; amplitude *= 0.5; }
    return value;
}

void main() {
    vec2 pixel = qt_TexCoord0 * size;
    vec4 frame = texture(source, qt_TexCoord0);
    float scale = max(size.y, 1.0);
    // The burn front: the circle's radius pushed in and out by noise, so it is ragged.
    float ragged = (fbm(pixel / scale * 7.0 + seed) - 0.5) * scale * 0.16;
    float beyond = length(pixel - centre) - (radius + ragged);
    if (beyond < 0.0) { fragColor = vec4(0.0); return; }
    float emberWidth = scale * 0.012, charWidth = scale * 0.07;
    // Glowing rim: hot yellow at the hole, red-orange further out, flickering grain.
    float rim = 1.0 - smoothstep(0.0, emberWidth, beyond);
    float grain = 0.7 + 0.3 * noise(pixel / scale * 120.0 + seed * 3.0);
    vec3 hot = mix(vec3(1.0, 0.45, 0.08), vec3(1.0, 0.88, 0.5), rim);
    // Charred band: the frame browns and blackens toward the rim.
    float charring = 1.0 - smoothstep(0.0, charWidth, beyond);
    vec3 burnt = mix(frame.rgb, frame.rgb * vec3(0.35, 0.22, 0.12), charring * 0.85);
    vec3 color = mix(burnt, hot * grain, rim);
    fragColor = vec4(color, 1.0) * qt_Opacity;
}
