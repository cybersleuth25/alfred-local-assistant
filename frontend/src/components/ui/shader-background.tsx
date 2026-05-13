import { useEffect, useRef } from 'react';

interface ShaderBackgroundProps {
  state: "idle" | "listening" | "processing" | "speaking";
}

const ShaderBackground = ({ state }: ShaderBackgroundProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef(state);
  
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const vsSource = `
    attribute vec4 aVertexPosition;
    void main() {
      gl_Position = aVertexPosition;
    }
  `;

  // Minimal clean grid shader
  const fsSource = `
    precision highp float;
    uniform vec2 iResolution;
    uniform float iTime;
    uniform vec3 uColor;
    uniform float uIntensity;

    void main() {
      vec2 uv = gl_FragCoord.xy / iResolution.xy;
      
      // Center coordinates
      vec2 p = uv * 2.0 - 1.0;
      p.x *= iResolution.x / iResolution.y;

      // Subtle vignette
      float v = 1.0 - length(p) * 0.5;
      v = smoothstep(0.0, 1.0, v);

      // Dynamic grid
      vec2 grid = fract(uv * 40.0 + vec2(iTime * 0.1, iTime * 0.05));
      float lines = smoothstep(0.95, 1.0, grid.x) + smoothstep(0.95, 1.0, grid.y);
      lines = clamp(lines, 0.0, 1.0);

      // Soft radial glow based on state
      float glow = smoothstep(0.8, 0.0, length(p)) * uIntensity;

      vec3 finalColor = vec3(0.035, 0.035, 0.043); // bg-base #09090b

      // Add grid lines
      finalColor = mix(finalColor, vec3(0.1, 0.1, 0.1), lines * 0.5 * v);

      // Add state color glow
      finalColor += uColor * glow * 0.15;

      gl_FragColor = vec4(finalColor, 1.0);
    }
  `;

  useEffect(() => {
    const loadShader = (gl: WebGLRenderingContext, type: number, source: string) => {
      const shader = gl.createShader(type);
      if (!shader) return null;
      gl.shaderSource(shader, source);
      gl.compileShader(shader);

      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compile error: ', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    };

    const initShaderProgram = (gl: WebGLRenderingContext, vsSource: string, fsSource: string) => {
      const vertexShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
      const fragmentShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);

      if (!vertexShader || !fragmentShader) return null;

      const shaderProgram = gl.createProgram();
      if (!shaderProgram) return null;
      gl.attachShader(shaderProgram, vertexShader);
      gl.attachShader(shaderProgram, fragmentShader);
      gl.linkProgram(shaderProgram);

      if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
        console.error('Shader program link error: ', gl.getProgramInfoLog(shaderProgram));
        return null;
      }
      return shaderProgram;
    };

    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl');
    if (!gl) return;

    const shaderProgram = initShaderProgram(gl, vsSource, fsSource);
    if (!shaderProgram) return;

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = [
      -1.0, -1.0,
       1.0, -1.0,
      -1.0,  1.0,
       1.0,  1.0,
    ];
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);

    const programInfo = {
      program: shaderProgram,
      attribLocations: {
        vertexPosition: gl.getAttribLocation(shaderProgram, 'aVertexPosition'),
      },
      uniformLocations: {
        resolution: gl.getUniformLocation(shaderProgram, 'iResolution'),
        time: gl.getUniformLocation(shaderProgram, 'iTime'),
        color: gl.getUniformLocation(shaderProgram, 'uColor'),
        intensity: gl.getUniformLocation(shaderProgram, 'uIntensity'),
      },
    };

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // State Colors (RGB 0-1)
    // listening: cyan #14b8a6 -> 0.08, 0.72, 0.65
    // processing: amber #f59e0b -> 0.96, 0.62, 0.04
    // speaking: purple #8b5cf6 -> 0.55, 0.36, 0.96
    // idle: gray #71717a -> 0.44, 0.44, 0.48
    const PRESETS: Record<string, { r: number, g: number, b: number, intensity: number }> = {
      idle:       { r: 0.44, g: 0.44, b: 0.48, intensity: 0.1 },
      listening:  { r: 0.08, g: 0.72, b: 0.65, intensity: 0.8 },
      processing: { r: 0.96, g: 0.62, b: 0.04, intensity: 0.6 },
      speaking:   { r: 0.55, g: 0.36, b: 0.96, intensity: 0.9 },
    };

    const currentUniforms = {
      r: PRESETS.idle.r,
      g: PRESETS.idle.g,
      b: PRESETS.idle.b,
      intensity: PRESETS.idle.intensity
    };

    const startTime = Date.now();
    let animationFrameId: number;
    let lastTime = Date.now();
    
    const render = () => {
      const now = Date.now();
      const dt = (now - lastTime) / 1000;
      lastTime = now;
      const currentTime = (now - startTime) / 1000;

      const target = PRESETS[stateRef.current] || PRESETS.idle;
      const lerpSpeed = Math.min(4.0 * dt, 1.0);
      
      currentUniforms.r += (target.r - currentUniforms.r) * lerpSpeed;
      currentUniforms.g += (target.g - currentUniforms.g) * lerpSpeed;
      currentUniforms.b += (target.b - currentUniforms.b) * lerpSpeed;
      
      // Speaking pulse
      let targetIntensity = target.intensity;
      if (stateRef.current === "speaking") {
         const pulse = Math.sin(currentTime * 8.0) * 0.5 + 0.5;
         targetIntensity = 0.5 + pulse * 0.5;
      }
      
      currentUniforms.intensity += (targetIntensity - currentUniforms.intensity) * lerpSpeed;

      gl.clearColor(0.035, 0.035, 0.043, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(programInfo.program);

      gl.uniform2f(programInfo.uniformLocations.resolution, canvas.width, canvas.height);
      gl.uniform1f(programInfo.uniformLocations.time, currentTime);
      gl.uniform3f(programInfo.uniformLocations.color, currentUniforms.r, currentUniforms.g, currentUniforms.b);
      gl.uniform1f(programInfo.uniformLocations.intensity, currentUniforms.intensity);

      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
      gl.vertexAttribPointer(
        programInfo.attribLocations.vertexPosition,
        2,
        gl.FLOAT,
        false,
        0,
        0
      );
      gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, [vsSource, fsSource]);

  return (
    <canvas ref={canvasRef} className="absolute top-0 left-0 w-full h-full opacity-60" />
  );
};

export default ShaderBackground;
