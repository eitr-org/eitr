#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float flow;
    vec4 spectrum0;
    vec4 spectrum1;
    vec4 spectrum2;
    vec4 spectrum3;
    vec4 spectrum4;
    vec4 spectrum5;
    vec4 spectrum6;
};
layout(binding = 1) uniform sampler2D source;
vec3 spectrum(float position) {
    float segment = fract(position) * 6.0;
    if (segment < 1.0) return mix(spectrum0.rgb, spectrum1.rgb, segment);
    if (segment < 2.0) return mix(spectrum1.rgb, spectrum2.rgb, segment - 1.0);
    if (segment < 3.0) return mix(spectrum2.rgb, spectrum3.rgb, segment - 2.0);
    if (segment < 4.0) return mix(spectrum3.rgb, spectrum4.rgb, segment - 3.0);
    if (segment < 5.0) return mix(spectrum4.rgb, spectrum5.rgb, segment - 4.0);
    return mix(spectrum5.rgb, spectrum6.rgb, segment - 5.0);
}
void main() {
    vec2 uv = qt_TexCoord0;
    float alpha = texture(source, uv).a;
    vec3 color = spectrum(uv.x * 0.5 + flow);
    fragColor = vec4(color * alpha, alpha) * qt_Opacity;
}
