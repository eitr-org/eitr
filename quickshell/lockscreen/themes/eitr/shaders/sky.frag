#version 440
// The night sky behind the aurora: a dense field of stars in three sizes and a
// Milky Way band crossing it diagonally, with dark dust lanes along its centre.
// It has no time input, so the scene graph draws it once and reuses the layer.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 size;
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
    for (int i = 0; i < 5; i++) { value += amplitude * noise(p); p *= 2.03; amplitude *= 0.5; }
    return value;
}

// One star at most per cell, at a random spot inside it; rarer cells hold brighter stars.
// `halo` adds a soft glow around the star, reaching about three times its radius.
vec3 stars(vec2 pixel, float cell, float rarity, float radius, float seed, float halo) {
    vec2 index = floor(pixel / cell);
    float chance = hash(index + seed);
    if (chance < rarity) return vec3(0.0);
    vec2 centre = (index + 0.15 + 0.7 * vec2(hash(index + seed + 7.1), hash(index + seed + 13.7))) * cell;
    float light = (chance - rarity) / (1.0 - rarity);
    float reach = length(pixel - centre);
    // Only the brighter half of these stars gets the halo.
    float glow = smoothstep(radius, 0.0, reach) + halo * step(0.5, light) * light * exp(-reach * reach / (radius * radius * 1.8));
    float tint = hash(index + seed + 29.3);
    vec3 color = tint < 0.12 ? vec3(1.0, 0.86, 0.7) : (tint < 0.3 ? vec3(0.78, 0.86, 1.0) : vec3(1.0));
    return color * glow * (0.35 + 0.65 * light);
}

void main() {
    vec2 pixel = qt_TexCoord0 * size;
    float aspect = size.x / max(size.y, 1.0);
    vec2 p = vec2(qt_TexCoord0.x * aspect, qt_TexCoord0.y);
    // The band runs from the upper left down toward the lower middle, as in a summer sky.
    vec2 along = normalize(vec2(0.55, 1.0));
    vec2 normal = vec2(-along.y, along.x);
    float across = dot(p - vec2(0.18 * aspect, 0.0), normal);
    across += 0.06 * (fbm(p * 2.0 + 4.0) - 0.5);
    float band = exp(-across * across / 0.045);
    float clouds = fbm(p * 3.2 + 1.7) * 0.6 + fbm(p * 9.0 + 5.3) * 0.4;
    float dust = smoothstep(0.5, 0.72, fbm(p * 6.0 + 11.0)) * exp(-across * across / 0.004);
    float milky = band * clouds * (1.0 - 0.75 * dust);
    vec3 color = vec3(0.66, 0.6, 0.82) * milky * 0.4;
    // Stars: many faint ones (denser inside the band), fewer medium, a few bright.
    float scale = max(size.y / 1080.0, 0.5);
    color += stars(pixel, 7.0 * scale, 0.92 - 0.14 * band, 1.1 * scale, 1.0, 0.0) * (0.6 + 0.4 * band);
    color += stars(pixel, 19.0 * scale, 0.88, 1.6 * scale, 2.0, 0.0);
    color += stars(pixel, 45.0 * scale, 0.78, 2.4 * scale, 3.0, 0.55) * 1.4;
    // Fainter toward the horizon, where the password field sits.
    color *= mix(0.45, 1.0, smoothstep(1.0, 0.45, qt_TexCoord0.y));
    color = min(color, vec3(1.0));
    fragColor = vec4(color, max(color.r, max(color.g, color.b))) * qt_Opacity;
}
