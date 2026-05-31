#ifdef GL_ES
precision mediump float;
#endif

// Phong related variables
uniform sampler2D uSampler;
uniform vec3 uKd;
uniform vec3 uKs;
uniform vec3 uLightPos;
uniform vec3 uCameraPos;
uniform vec3 uLightIntensity;

varying highp vec2 vTextureCoord;
varying highp vec3 vFragPos;
varying highp vec3 vNormal;

// Shadow map related variables
#define NUM_SAMPLES 40
#define BLOCKER_SEARCH_NUM_SAMPLES NUM_SAMPLES
#define PCF_NUM_SAMPLES NUM_SAMPLES
#define NUM_RINGS 11

#define EPS 1e-3
#define PI 3.141592653589793
#define PI2 6.283185307179586
#define SHADOW_BIAS 0.004
#define BLOCKER_SEARCH_SIZE 0.0045
#define LIGHT_SIZE_UV 0.007
#define PCF_FILTER_SIZE 0.0035
#define PCSS_MIN_FILTER_SIZE 0.0008
#define PCSS_MAX_FILTER_SIZE 0.009

uniform sampler2D uShadowMap;

varying vec4 vPositionFromLight;
varying vec2 vScreenPos;

// Debug uniforms
uniform int uDebugShowShadowMap;
uniform int uDebugShowBlocker;

highp float rand_1to1(highp float x ) { 
  // -1 -1
  return fract(sin(x)*10000.0);
}

highp float rand_2to1(vec2 uv ) { 
  // 0 - 1
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract(sin(sn) * c);
}

float unpack(vec4 rgbaDepth) {
    const vec4 bitShift = vec4(1.0, 1.0/256.0, 1.0/(256.0*256.0), 1.0/(256.0*256.0*256.0));
    return dot(rgbaDepth, bitShift);
}

vec2 poissonDisk[NUM_SAMPLES];

void poissonDiskSamples( const in vec2 randomSeed ) {

  float ANGLE_STEP = PI2 * float( NUM_RINGS ) / float( NUM_SAMPLES );
  float INV_NUM_SAMPLES = 1.0 / float( NUM_SAMPLES );

  float angle = rand_2to1( randomSeed ) * PI2;
  float radius = INV_NUM_SAMPLES;
  float radiusStep = radius;

  for( int i = 0; i < NUM_SAMPLES; i ++ ) {
    poissonDisk[i] = vec2( cos( angle ), sin( angle ) ) * pow( radius, 0.75 );
    radius += radiusStep;
    angle += ANGLE_STEP;
  }
}

void uniformDiskSamples( const in vec2 randomSeed ) {

  float randNum = rand_2to1(randomSeed);
  float sampleX = rand_1to1( randNum ) ;
  float sampleY = rand_1to1( sampleX ) ;

  float angle = sampleX * PI2;
  float radius = sqrt(sampleY);

  for( int i = 0; i < NUM_SAMPLES; i ++ ) {
    poissonDisk[i] = vec2( radius * cos(angle) , radius * sin(angle)  );

    sampleX = rand_1to1( sampleY ) ;
    sampleY = rand_1to1( sampleX ) ;

    angle = sampleX * PI2;
    radius = sqrt(sampleY);
  }
}

float findBlocker( sampler2D shadowMap,  vec2 uv, float zReceiver ) {
  poissonDiskSamples(uv);

  float blockerDepthSum = 0.0;
  int blockerCount = 0;
  float bias = SHADOW_BIAS;

  for (int i = 0; i < BLOCKER_SEARCH_NUM_SAMPLES; i++) {
    vec2 sampleUV = uv + poissonDisk[i] * BLOCKER_SEARCH_SIZE;
    if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
      continue;
    }

    float closestDepth = unpack(texture2D(shadowMap, sampleUV));
    if (zReceiver - bias > closestDepth) {
      blockerDepthSum += closestDepth;
      blockerCount++;
    }
  }

  if (blockerCount == 0) {
    return -1.0;
  }

  return blockerDepthSum / float(blockerCount);
}

float PCFWithFilterSize(sampler2D shadowMap, vec4 coords, float filterSize) {
  vec3 projCoords = coords.xyz;

  if (projCoords.x < 0.0 || projCoords.x > 1.0 ||
      projCoords.y < 0.0 || projCoords.y > 1.0 ||
      projCoords.z < 0.0 || projCoords.z > 1.0) {
    return 1.0;
  }

  // Poisson 圆盘采样：生成围绕片元的 N 个偏移点
  poissonDiskSamples(projCoords.xy);

  float visibility = 0.0;
  float currentDepth = projCoords.z;
  float bias = SHADOW_BIAS;

  for (int i = 0; i < PCF_NUM_SAMPLES; i++) {
    vec2 offset = poissonDisk[i] * filterSize;
    vec2 sampleUV = projCoords.xy + offset;
    if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
      visibility += 1.0;
    } else {
      float closestDepth = unpack(texture2D(shadowMap, sampleUV));
      visibility += currentDepth - bias > closestDepth ? 0.0 : 1.0;
    }
  }

  // 取平均 → 0.0~1.0 之间的连续值，产生柔化过渡
  return visibility / float(PCF_NUM_SAMPLES);
}

float PCF(sampler2D shadowMap, vec4 coords) {
  return PCFWithFilterSize(shadowMap, coords, PCF_FILTER_SIZE);
}

float PCSS(sampler2D shadowMap, vec4 coords){
  vec3 projCoords = coords.xyz;

  if (projCoords.x < 0.0 || projCoords.x > 1.0 ||
      projCoords.y < 0.0 || projCoords.y > 1.0 ||
      projCoords.z < 0.0 || projCoords.z > 1.0) {
    return 1.0;
  }

  // STEP 1: avgblocker depth
  float avgBlockerDepth = findBlocker(shadowMap, projCoords.xy, projCoords.z);
  if (avgBlockerDepth < 0.0) {
    return 1.0;
  }

  // STEP 2: penumbra size
  float penumbraRatio = (projCoords.z - avgBlockerDepth) / max(avgBlockerDepth, EPS);
  float filterSize = clamp(
    penumbraRatio * LIGHT_SIZE_UV,
    PCSS_MIN_FILTER_SIZE,
    PCSS_MAX_FILTER_SIZE
  );

  // STEP 3: filtering
  return PCFWithFilterSize(shadowMap, coords, filterSize);
}


float useShadowMap(sampler2D shadowMap, vec4 shadowCoord){
  vec3 projCoords = shadowCoord.xyz;

  if (projCoords.x < 0.0 || projCoords.x > 1.0 ||
      projCoords.y < 0.0 || projCoords.y > 1.0 ||
      projCoords.z < 0.0 || projCoords.z > 1.0) {
    return 1.0;
  }

  float closestDepth = unpack(texture2D(shadowMap, projCoords.xy));
  float currentDepth = projCoords.z;
  float bias = SHADOW_BIAS;

  return currentDepth - bias > closestDepth ? 0.0 : 1.0;
}

vec3 blinnPhong(float visibility) {
  vec3 color = texture2D(uSampler, vTextureCoord).rgb;
  color = pow(color, vec3(2.2));

  vec3 ambient = 0.05 * color;

  vec3 lightDir = normalize(uLightPos);
  vec3 normal = normalize(vNormal);
  float diff = max(dot(lightDir, normal), 0.0);
  vec3 light_atten_coff =
      uLightIntensity / pow(length(uLightPos - vFragPos), 2.0);
  vec3 diffuse = diff * light_atten_coff * color;

  vec3 viewDir = normalize(uCameraPos - vFragPos);
  vec3 halfDir = normalize((lightDir + viewDir));
  float spec = pow(max(dot(halfDir, normal), 0.0), 32.0);
  vec3 specular = uKs * light_atten_coff * spec;

  vec3 radiance = ambient + visibility * (diffuse + specular);
  vec3 phongColor = pow(radiance, vec3(1.0 / 2.2));
  return phongColor;
}

void main(void) {

  // === Shadow Map Debug Overlay (右下角小窗) ===
  if (uDebugShowShadowMap == 1) {
    vec2 screenUV = vScreenPos * 0.5 + 0.5;  // NDC [-1,1] → [0,1]
    if (screenUV.x > 0.75 && screenUV.y < 0.25) {
      vec2 debugUV = vec2(
        (screenUV.x - 0.75) / 0.25,
        screenUV.y / 0.25
      );
      // 黄色边框
      if (debugUV.x < 0.01 || debugUV.x > 0.99 || debugUV.y < 0.01 || debugUV.y > 0.99) {
        gl_FragColor = vec4(1.0, 1.0, 0.0, 1.0);
        return;
      }
      float depth = unpack(texture2D(uShadowMap, debugUV));
      gl_FragColor = vec4(vec3(depth), 1.0);
      return;
    }
  }

  // 透视除法
  vec3 shadowCoord = vPositionFromLight.xyz / vPositionFromLight.w;
  // vec3 shadowCoord = vPositionFromLight.xyz;
  // 归一化至 [0,1]
  shadowCoord = shadowCoord * 0.5 + 0.5;

  float visibility;
  // visibility = useShadowMap(uShadowMap, vec4(shadowCoord, 1.0));
  visibility = PCF(uShadowMap, vec4(shadowCoord, 1.0));
  // visibility = PCSS(uShadowMap, vec4(shadowCoord, 1.0));

  vec3 phongColor = blinnPhong(visibility);

  // === Blocker Search Debug ===
  if (uDebugShowBlocker == 1) {
    poissonDiskSamples(shadowCoord.xy);
    int blockerCount = 0;
    for (int i = 0; i < BLOCKER_SEARCH_NUM_SAMPLES; i++) {
      vec2 sampleUV = shadowCoord.xy + poissonDisk[i] * BLOCKER_SEARCH_SIZE;
      if (sampleUV.x >= 0.0 && sampleUV.x <= 1.0 && sampleUV.y >= 0.0 && sampleUV.y <= 1.0) {
        float d = unpack(texture2D(uShadowMap, sampleUV));
        if (shadowCoord.z - SHADOW_BIAS > d) blockerCount++;
      }
    }
    float blockerRatio = float(blockerCount) / float(BLOCKER_SEARCH_NUM_SAMPLES);
    // 绿色(无blocker) → 红色(全是blocker)
    vec3 debugColor = mix(vec3(0.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), blockerRatio);
    phongColor = phongColor * debugColor;
  }

  gl_FragColor = vec4(phongColor, 1.0);
  // gl_FragColor = vec4(phongColor, 1.0);
}
