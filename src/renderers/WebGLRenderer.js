class WebGLRenderer {
    meshes = [];
    shadowMeshes = [];
    lights = [];

    constructor(gl, camera) {
        this.gl = gl;
        this.camera = camera;
        this._debugQuadReady = false;
    }

    addLight(light) {
        this.lights.push({
            entity: light,
            meshRender: new MeshRender(this.gl, light.mesh, light.mat)
        });
    }
    addMeshRender(mesh) { this.meshes.push(mesh); }
    addShadowMeshRender(mesh) { this.shadowMeshes.push(mesh); }

    // --- Debug Quad (bottom-right Shadow Map overlay) ---
    _setupDebugQuad() {
        if (this._debugQuadReady) return;
        const gl = this.gl;

        // Compile debug shader
        const debugShader = new Shader(gl,
            DebugShadowMapVertexShader,
            DebugShadowMapFragmentShader,
            { uniforms: ['uShadowMap'], attribs: ['aPosition', 'aTexCoord'] }
        );
        this._debugShader = debugShader;

        // Quad: NDC bottom-right 25%
        // pos(x,y) + texcoord(u,v) interleaved, 4 floats per vertex
        const vertices = new Float32Array([
            0.5, -0.5,  0.0, 1.0,  // top-left
            1.0, -0.5,  1.0, 1.0,  // top-right
            1.0, -1.0,  1.0, 0.0,  // bottom-right
            0.5, -1.0,  0.0, 0.0,  // bottom-left
        ]);
        const indices = new Uint16Array([0, 1, 2, 0, 2, 3]);

        this._debugQuadVBO = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, this._debugQuadVBO);
        gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER, null);

        this._debugQuadIBO = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this._debugQuadIBO);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);

        this._debugQuadReady = true;
    }

    _renderDebugShadowMap(fboTexture) {
        this._setupDebugQuad();
        const gl = this.gl;
        const prog = this._debugShader.program;

        gl.disable(gl.DEPTH_TEST);
        gl.useProgram(prog.glShaderProgram);

        // Bind interleaved vertex buffer: [x,y, u,v] × 4
        gl.bindBuffer(gl.ARRAY_BUFFER, this._debugQuadVBO);
        const FLOAT_SIZE = 4;
        const stride = 4 * FLOAT_SIZE;
        gl.vertexAttribPointer(prog.attribs.aPosition, 2, gl.FLOAT, false, stride, 0);
        gl.enableVertexAttribArray(prog.attribs.aPosition);
        gl.vertexAttribPointer(prog.attribs.aTexCoord, 2, gl.FLOAT, false, stride, 2 * FLOAT_SIZE);
        gl.enableVertexAttribArray(prog.attribs.aTexCoord);

        // Bind shadow map
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, fboTexture);
        gl.uniform1i(prog.uniforms.uShadowMap, 0);

        // Draw
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this._debugQuadIBO);
        gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);

        gl.bindBuffer(gl.ARRAY_BUFFER, null);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);
        gl.enable(gl.DEPTH_TEST);
    }

    render() {
        const gl = this.gl;

        gl.clearColor(0.0, 0.0, 0.0, 1.0); // Clear to black, fully opaque
        gl.clearDepth(1.0); // Clear everything
        gl.enable(gl.DEPTH_TEST); // Enable depth testing
        gl.depthFunc(gl.LEQUAL); // Near things obscure far things

        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        console.assert(this.lights.length != 0, "No light");
        console.assert(this.lights.length == 1, "Multiple lights");

        for (let l = 0; l < this.lights.length; l++) {
            // Draw light
            // TODO: Support all kinds of transform
            this.lights[l].meshRender.mesh.transform.translate = this.lights[l].entity.lightPos;
            this.lights[l].meshRender.draw(this.camera);

            // Shadow pass
            if (this.lights[l].entity.hasShadowMap == true) {
                gl.bindFramebuffer(gl.FRAMEBUFFER, this.lights[l].entity.fbo);
                gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
                for (let i = 0; i < this.shadowMeshes.length; i++) {
                    this.shadowMeshes[i].draw(this.camera);
                }
            }

            // Camera pass
            for (let i = 0; i < this.meshes.length; i++) {
                this.gl.useProgram(this.meshes[i].shader.program.glShaderProgram);
                this.gl.uniform3fv(this.meshes[i].shader.program.uniforms.uLightPos, this.lights[l].entity.lightPos);

                // Debug uniforms (from global state)
                if (this.meshes[i].shader.program.uniforms.uDebugShowBlocker) {
                    this.gl.uniform1i(this.meshes[i].shader.program.uniforms.uDebugShowBlocker, window.debugShowBlocker ? 1 : 0);
                }

                this.meshes[i].draw(this.camera);
            }
        }

        // --- Debug: Shadow Map overlay quad (independent quad, always on top) ---
        if (window.debugShowShadowMap && this.lights.length > 0 && this.lights[0].entity.fbo) {
            this._renderDebugShadowMap(this.lights[0].entity.fbo.texture);
        }
    }
}