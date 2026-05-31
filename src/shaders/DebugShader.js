// Debug Quad Shader — renders shadow map overlay in bottom-right corner
const DebugShadowMapVertexShader = `
attribute vec2 aPosition;
attribute vec2 aTexCoord;
varying vec2 vTexCoord;

void main(void) {
  vTexCoord = aTexCoord;
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`;

const DebugShadowMapFragmentShader = `
#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D uShadowMap;
varying vec2 vTexCoord;

float unpack(vec4 rgbaDepth) {
    const vec4 bitShift = vec4(1.0, 1.0/256.0, 1.0/(256.0*256.0), 1.0/(256.0*256.0*256.0));
    return dot(rgbaDepth, bitShift);
}

void main(void) {
  // 黄色边框
  if (vTexCoord.x < 0.01 || vTexCoord.x > 0.99 || vTexCoord.y < 0.01 || vTexCoord.y > 0.99) {
    gl_FragColor = vec4(1.0, 1.0, 0.0, 1.0);
    return;
  }
  float depth = unpack(texture2D(uShadowMap, vTexCoord));
  gl_FragColor = vec4(vec3(depth), 1.0);
}
`;