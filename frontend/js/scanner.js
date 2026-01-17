// Barcode scanner using QuaggaJS
// Continuous scanning with live detection

let onScanCallback = null;
let isScanning = false;
let lastResult = null;
let lastResultTime = 0;

const scanner = {
    async start(onScan) {
        if (isScanning) return;
        
        onScanCallback = onScan;
        
        return new Promise((resolve, reject) => {
            Quagga.init({
                inputStream: {
                    name: "Live",
                    type: "LiveStream",
                    target: document.querySelector('#reader'),
                    constraints: {
                        facingMode: "environment",
                        width: { min: 1280, ideal: 1920 },
                        height: { min: 720, ideal: 1080 }
                    }
                },
                decoder: {
                    readers: [
                        "ean_reader",
                        "ean_8_reader",
                        "upc_reader",
                        "upc_e_reader",
                        "code_128_reader",
                        "code_39_reader"
                    ]
                },
                locate: true,
                locator: {
                    patchSize: "medium",
                    halfSample: true
                },
                frequency: 10
            }, (err) => {
                if (err) {
                    console.error('Quagga init error:', err);
                    reject(err);
                    return;
                }
                
                console.log('Quagga initialized');
                Quagga.start();
                isScanning = true;
                resolve();
            });
            
            // Detection handler
            Quagga.onDetected((result) => {
                if (!result || !result.codeResult) return;
                
                const code = result.codeResult.code;
                const now = Date.now();
                
                // Debounce: ignore same code within 2 seconds
                if (code === lastResult && (now - lastResultTime) < 2000) {
                    return;
                }
                
                // Confidence check - require multiple reads to confirm
                // QuaggaJS provides error correction info
                const errors = result.codeResult.decodedCodes
                    ?.filter(x => x.error !== undefined)
                    ?.map(x => x.error) || [];
                const avgError = errors.length ? errors.reduce((a, b) => a + b) / errors.length : 1;
                
                if (avgError > 0.25) {
                    console.log('Low confidence scan, ignoring:', code, 'error:', avgError);
                    return;
                }
                
                console.log('✓ Detected:', code, 'format:', result.codeResult.format, 'confidence:', (1 - avgError).toFixed(2));
                
                lastResult = code;
                lastResultTime = now;
                
                // Vibrate feedback
                if (navigator.vibrate) {
                    navigator.vibrate([100, 50, 100]);
                }
                
                if (onScanCallback) {
                    onScanCallback(code);
                }
            });
            
            // Optional: draw detection boxes for debugging
            Quagga.onProcessed((result) => {
                const drawingCtx = Quagga.canvas.ctx.overlay;
                const drawingCanvas = Quagga.canvas.dom.overlay;
                
                if (!drawingCtx || !drawingCanvas) return;
                
                drawingCtx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);
                
                if (result && result.boxes) {
                    result.boxes.filter(box => box !== result.box).forEach(box => {
                        Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, { color: "yellow", lineWidth: 2 });
                    });
                }
                
                if (result && result.box) {
                    Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, { color: "#00ff00", lineWidth: 3 });
                }
                
                if (result && result.codeResult && result.codeResult.code) {
                    Quagga.ImageDebug.drawPath(result.line, { x: 'x', y: 'y' }, drawingCtx, { color: 'red', lineWidth: 3 });
                }
            });
        });
    },
    
    async stop() {
        if (!isScanning) return;
        
        Quagga.stop();
        isScanning = false;
        lastResult = null;
        
        // Clean up the reader div
        const reader = document.querySelector('#reader');
        if (reader) {
            reader.innerHTML = '';
        }
    },
    
    isActive() {
        return isScanning;
    },
    
    isUsingNative() {
        return false;
    },
    
    pause() {
        if (isScanning) {
            Quagga.pause();
        }
    },
    
    resume() {
        if (isScanning) {
            Quagga.start();
        }
    }
};
