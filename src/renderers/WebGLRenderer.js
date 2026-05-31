class WebGLRenderer {
    meshes = [];
    shadowMeshes = [];
    lights = [];

    constructor(gl, camera) {
        this.gl = gl;
        this.camera = camera;
    }

    addLight(light) {
        this.lights.push({
            entity: light,
            meshRender: new MeshRender(this.gl, light.mesh, light.mat)
        });
    }
    addMeshRender(mesh) { this.meshes.push(mesh); }
    addShadowMeshRender(mesh) { this.shadowMeshes.push(mesh); }

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

                // Debug uniforms (from global state, defaults to 0 if not set)
                if (this.meshes[i].shader.program.uniforms.uDebugShowShadowMap) {
                    this.gl.uniform1i(this.meshes[i].shader.program.uniforms.uDebugShowShadowMap, window.debugShowShadowMap ? 1 : 0);
                    this.gl.uniform1i(this.meshes[i].shader.program.uniforms.uDebugShowBlocker, window.debugShowBlocker ? 1 : 0);
                    this.gl.uniform1f(this.meshes[i].shader.program.uniforms.uScreenWidth, window.screen.width);
                    this.gl.uniform1f(this.meshes[i].shader.program.uniforms.uScreenHeight, window.screen.height);
                }

                this.meshes[i].draw(this.camera);
            }
        }
    }
}