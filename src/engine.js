var cameraPosition = [30, 30, 30]

//生成的纹理的分辨率，纹理必须是标准的尺寸 256*256 1024*1024  2048*2048
var resolution = 8192;
var fbo;

GAMES202Main();

function GAMES202Main() {
	// Init canvas and gl
	const canvas = document.querySelector('#glcanvas');
	canvas.width = window.screen.width;
	canvas.height = window.screen.height;
	const gl = canvas.getContext('webgl');
	if (!gl) {
		alert('Unable to initialize WebGL. Your browser or machine may not support it.');
		return;
	}

	// Add camera
	const camera = new THREE.PerspectiveCamera(75, gl.canvas.clientWidth / gl.canvas.clientHeight, 1e-2, 1000);
	camera.position.set(cameraPosition[0], cameraPosition[1], cameraPosition[2]);

	// Add resize listener
	function setSize(width, height) {
		camera.aspect = width / height;
		camera.updateProjectionMatrix();
	}
	setSize(canvas.clientWidth, canvas.clientHeight);
	window.addEventListener('resize', () => setSize(canvas.clientWidth, canvas.clientHeight));

	// Add camera control
	const cameraControls = new THREE.OrbitControls(camera, canvas);
	cameraControls.enableZoom = true;
	cameraControls.enableRotate = true;
	cameraControls.enablePan = true;
	cameraControls.rotateSpeed = 0.3;
	cameraControls.zoomSpeed = 1.0;
	cameraControls.panSpeed = 0.8;
	cameraControls.target.set(0, 0, 0);

	// Add renderer
	const renderer = new WebGLRenderer(gl, camera);

	// Add lights — two directional lights with shadows
	let focalPoint = [0, 0, 0];
	let lightUp = [0, 1, 0];

	// Light 0: stationary main light (top-right)
	const light0 = new DirectionalLight(3000, [1.0, 0.95, 0.9], [0, 80, 80], focalPoint, lightUp, true, renderer.gl);
	renderer.addLight(light0);

	// Light 1: orbiting light (will animate in mainLoop)
	const light1 = new DirectionalLight(2500, [0.7, 0.8, 1.0], [80, 70, 0], focalPoint, lightUp, true, renderer.gl);
	renderer.addLight(light1);

	// Add shapes
	let floorTransform = setTransform(0, 0, -30, 4, 4, 4);
	let obj1Transform = setTransform(0, 0, 0, 20, 20, 20);
	let obj2Transform = setTransform(40, 0, -40, 10, 10, 10);

	loadOBJ(renderer, 'assets/mary/', 'Marry', 'PhongMaterial', obj1Transform);
	loadOBJ(renderer, 'assets/mary/', 'Marry', 'PhongMaterial', obj2Transform);
	loadOBJ(renderer, 'assets/floor/', 'floor', 'PhongMaterial', floorTransform);

	function createGUI() {
		const gui = new dat.gui.GUI();
		const debugCfg = {
			showShadowMap: false,
			showBlocker: false,
			animateLight: true,
		};
		window.debugShowShadowMap = false;
		window.debugShowBlocker = false;
		window.animateLight = true;

		const debugFolder = gui.addFolder('Debug');
		debugFolder.add(debugCfg, 'showShadowMap').name('Show Shadow Map').onChange(function(v) {
			window.debugShowShadowMap = v;
		});
		debugFolder.add(debugCfg, 'showBlocker').name('Show Blocker Search').onChange(function(v) {
			window.debugShowBlocker = v;
		});
		debugFolder.add(debugCfg, 'animateLight').name('Animate Light 1').onChange(function(v) {
			window.animateLight = v;
		});
		debugFolder.open();
	}
	createGUI();

	function mainLoop(now) {
		cameraControls.update();

		// Animate orbiting light
		if (window.animateLight) {
			let angle = now * 0.0005;
			let radius = 100;
			light1.lightPos[0] = Math.cos(angle) * radius;
			light1.lightPos[2] = Math.sin(angle) * radius;
		}

		renderer.render();
		requestAnimationFrame(mainLoop);
	}
	requestAnimationFrame(mainLoop);
}

function setTransform(t_x, t_y, t_z, s_x, s_y, s_z) {
	return {
		modelTransX: t_x,
		modelTransY: t_y,
		modelTransZ: t_z,
		modelScaleX: s_x,
		modelScaleY: s_y,
		modelScaleZ: s_z,
	};
}