// Barcode scanner using html5-qrcode

let html5QrCode = null;
let isScanning = false;
let onScanCallback = null;

const scanner = {
    async start(onScan) {
        if (isScanning) return;
        
        onScanCallback = onScan;
        
        html5QrCode = new Html5Qrcode("reader");
        
        const config = {
            fps: 10,
            qrbox: { width: 250, height: 100 },
            aspectRatio: 1.5,
            formatsToSupport: [
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.EAN_8,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.UPC_E,
                Html5QrcodeSupportedFormats.CODE_128,
                Html5QrcodeSupportedFormats.CODE_39
            ]
        };
        
        try {
            await html5QrCode.start(
                { facingMode: "environment" },
                config,
                (decodedText, decodedResult) => {
                    // Success callback
                    if (onScanCallback) {
                        onScanCallback(decodedText);
                    }
                },
                (errorMessage) => {
                    // Error callback (ignore - happens constantly while scanning)
                }
            );
            isScanning = true;
        } catch (err) {
            console.error("Error starting scanner:", err);
            throw err;
        }
    },
    
    async stop() {
        if (!isScanning || !html5QrCode) return;
        
        try {
            await html5QrCode.stop();
            isScanning = false;
        } catch (err) {
            console.error("Error stopping scanner:", err);
        }
    },
    
    isActive() {
        return isScanning;
    },
    
    // Pause scanning temporarily (e.g., while showing result)
    async pause() {
        if (html5QrCode && isScanning) {
            await html5QrCode.pause(true);
        }
    },
    
    // Resume scanning
    async resume() {
        if (html5QrCode && isScanning) {
            await html5QrCode.resume();
        }
    }
};
