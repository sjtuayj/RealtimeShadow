class WebGLRenderer {
    meshes = [];
    shadowMeshes = [];  // shadowMeshes[lightIndex] = [...]
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
    addShadowMeshRender(lightIndex, mesh) {
        if (!this.shadowMeshes[lightIndex]) this.shadowMeshes[lightIndex] = [];
        this.shadowMeshes[lightIndex].push(mesh);
    }

    // --- Debug Quad (bottom-right Shadow Map overlay) ---
    _setupDebugQuad() {
        if (this._debugQuadReady) return;
        const gl = this.gl;

        const debugShader = new Shader(gl,
            DebugShadowMapVertexShader,
            DebugShadowMapFragmentShader,
            { uniforms: ['uShadowMap'], attribs: ['aPosition', 'aTexCoord'] }
        );
        this._debugShader = debugShader;

        const vertices = new Float32Array([
            0.5, -0.5,  0.0, 1.0,
            1.0, -0.5,  1.0, 1.0,
            1.0, -1.0,  1.0, 0.0,
            0.5, -1.0,  0.0, 0.0,
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

        gl.bindBuffer(gl.ARRAY_BUFFER, this._debugQuadVBO);
        const FLOAT_SIZE = 4;
        const stride = 4 * FLOAT_SIZE;
        gl.vertexAttribPointer(prog.attribs.aPosition, 2, gl.FLOAT, false, stride, 0);
        gl.enableVertexAttribArray(prog.attribs.aPosition);
        gl.vertexAttribPointer(prog.attribs.aTexCoord, 2, gl.FLOAT, false, stride, 2 * FLOAT_SIZE);
        gl.enableVertexAttribArray(prog.attribs.aTexCoord);

        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, fboTexture);
        gl.uniform1i(prog.uniforms.uShadowMap, 0);

        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this._debugQuadIBO);
        gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);

        gl.bindBuffer(gl.ARRAY_BUFFER, null);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);
        gl.enable(gl.DEPTH_TEST);
    }

    // Update per-light uniforms on a material for the current light pass
    _updateLightUniforms(meshRender, light, isFirstLight) {
        // Recalculate light MVP for moving lights
        let t = meshRender.mesh.transform.translate;
        let s = meshRender.mesh.transform.scale;
        let mvp = light.CalcLightMVP([t[0], t[1], t[2]], [s[0], s[1], s[2]]);

        meshRender.material.uniforms.uLightMVP.value = mvp;
        meshRender.material.uniforms.uShadowMap.value = light.fbo;
        meshRender.material.uniforms.uLightIntensity.value = light.mat.GetIntensity();
        meshRender.material.uniforms.uApplyAmbient.value = isFirstLight ? 1.0 : 0.0;
    }

    render() {
        const gl = this.gl;

        gl.clearColor(0.0, 0.0, 0.0, 1.0);
        gl.clearDepth(1.0);
        gl.enable(gl.DEPTH_TEST);
        gl.depthFunc(gl.LEQUAL);

        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        let isFirstLight = true;

        for (let l = 0; l < this.lights.length; l++) {
            let light = this.lights[l].entity;

            // Draw light cube
            this.lights[l].meshRender.mesh.transform.translate = light.lightPos;
            this.lights[l].meshRender.draw(this.camera);

            // --- Shadow Pass for this light ---
            if (light.hasShadowMap && this.shadowMeshes[l]) {
                gl.bindFramebuffer(gl.FRAMEBUFFER, light.fbo);
                gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
                for (let i = 0; i < this.shadowMeshes[l].length; i++) {
                    let sm = this.shadowMeshes[l][i];
                    // Update light MVP for shadow pass (moving lights)
                    let t = sm.mesh.transform.translate;
                    let s = sm.mesh.transform.scale;
                    sm.material.uniforms.uLightMVP.value = light.CalcLightMVP([t[0], t[1], t[2]], [s[0], s[1], s[2]]);
                    sm.draw(this.camera);
                }
            }

            // --- Camera Pass ---
            // Subsequent lights use additive blending (no ambient)
            if (!isFirstLight) {
                gl.enable(gl.BLEND);
                gl.blendFunc(gl.ONE, gl.ONE);
            }

            for (let i = 0; i < this.meshes.length; i++) {
                let mr = this.meshes[i];
                gl.useProgram(mr.shader.program.glShaderProgram);
                gl.uniform3fv(mr.shader.program.uniforms.uLightPos, light.lightPos);

                // Update per-light uniforms (dynamic MVP, shadow map, intensity, ambient flag)
                this._updateLightUniforms(mr, light, isFirstLight);

                // Debug uniforms
                if (mr.material.uniforms.uDebugShowBlocker) {
                    mr.material.uniforms.uDebugShowBlocker.value = window.debugShowBlocker ? 1 : 0;
                }

                mr.draw(this.camera);
            }

            if (!isFirstLight) {
                gl.disable(gl.BLEND);
            }
            isFirstLight = false;
        }

        // --- Debug: Shadow Map overlay ---
        if (window.debugShowShadowMap && this.lights.length > 0 && this.lights[0].entity.fbo) {
            this._renderDebugShadowMap(this.lights[0].entity.fbo.texture);
        }
    }
}