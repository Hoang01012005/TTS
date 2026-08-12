document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const textInput = document.getElementById("text-input");
    const charCountDisplay = document.getElementById("char-count");
    const clearBtn = document.getElementById("clear-btn");
    
    const lengthScaleSlider = document.getElementById("length-scale");
    const lengthScaleVal = document.getElementById("length-scale-val");
    const noiseScaleSlider = document.getElementById("noise-scale");
    const noiseScaleVal = document.getElementById("noise-scale-val");
    const noiseWSlider = document.getElementById("noise-w");
    const noiseWVal = document.getElementById("noise-w-val");
    
    const generateBtn = document.getElementById("generate-btn");
    const themeToggleBtn = document.getElementById("theme-toggle");
    
    // Audio Player Elements
    const audioPlayer = document.getElementById("audio-element");
    const playerWrapper = document.getElementById("player-wrapper");
    const playPauseBtn = document.getElementById("play-pause-btn");
    const currentTimeDisplay = document.getElementById("current-time");
    const totalTimeDisplay = document.getElementById("total-time");
    const progressBar = document.getElementById("progress-bar");
    const progressContainer = document.getElementById("progress-container");
    const downloadBtn = document.getElementById("download-btn");
    
    // Stats Elements
    const resultDetails = document.getElementById("result-details");
    const durationVal = document.getElementById("duration-val");
    const elapsedVal = document.getElementById("elapsed-val");
    const rtfVal = document.getElementById("rtf-val");
    
    // Visualizer Elements
    const canvas = document.getElementById("waveform-canvas");
    const canvasCtx = canvas.getContext("2d");
    const visualizerIdleMsg = document.getElementById("visualizer-idle-msg");
    
    // History Elements
    const historyList = document.getElementById("history-list");

    // Audio Context for Web Audio API Visualizer
    let audioCtx = null;
    let analyser = null;
    let source = null;
    let animationId = null;
    let isVisualizerRunning = false;

    // Load History from localStorage
    let history = JSON.parse(localStorage.getItem("tts_history") || "[]");

    // Theme Management
    const savedTheme = localStorage.getItem("tts_theme") || "dark";
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
    }

    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("light-theme");
        const currentTheme = document.body.classList.contains("light-theme") ? "light" : "dark";
        localStorage.setItem("tts_theme", currentTheme);
        // Redraw waveform static line in new theme colors if visualizer is not running
        if (!isVisualizerRunning) {
            drawStaticWaveform();
        }
    });

    // Initialize Canvas Size
    function resizeCanvas() {
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * window.devicePixelRatio;
        canvas.height = rect.height * window.devicePixelRatio;
        canvasCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Initial state: draw static waveform line
    drawStaticWaveform();

    // ──────────────────────── Event Listeners: Inputs ────────────────────────
    // Character count updater
    textInput.addEventListener("input", () => {
        const len = textInput.value.length;
        charCountDisplay.textContent = `${len} / 1000 ký tự`;
    });

    // Clear text button
    clearBtn.addEventListener("click", () => {
        textInput.value = "";
        charCountDisplay.textContent = "0 / 1000 ký tự";
        textInput.focus();
    });

    // Update Slider value displays
    lengthScaleSlider.addEventListener("input", (e) => {
        lengthScaleVal.textContent = `${e.target.value}x`;
    });
    
    noiseScaleSlider.addEventListener("input", (e) => {
        noiseScaleVal.textContent = e.target.value;
    });

    noiseWSlider.addEventListener("input", (e) => {
        noiseWVal.textContent = e.target.value;
    });

    // ──────────────────────── API Call: Synthesize ────────────────────────────
    generateBtn.addEventListener("click", async () => {
        const text = textInput.value.trim();
        if (!text) {
            alert("Vui lòng nhập văn bản cần chuyển đổi!");
            return;
        }

        // Show loading state
        generateBtn.classList.add("loading");
        generateBtn.disabled = true;

        try {
            const response = await fetch("/api/synthesize", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    text: text,
                    length_scale: parseFloat(lengthScaleSlider.value),
                    noise_scale: parseFloat(noiseScaleSlider.value),
                    noise_w: parseFloat(noiseWSlider.value)
                })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.error || "Không thể tổng hợp giọng nói!");
            }

            // Update stats
            durationVal.textContent = `${result.duration}s`;
            elapsedVal.textContent = `${result.elapsed}s`;
            rtfVal.textContent = result.rtf;
            resultDetails.style.display = "block";

            // Prepare Audio Player
            audioPlayer.src = result.audio_url;
            playerWrapper.style.display = "block";
            
            // Show Download
            downloadBtn.onclick = () => {
                const link = document.createElement("a");
                link.href = result.audio_url;
                link.download = result.filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            };

            // Play newly generated audio
            audioPlayer.play().catch(e => console.log("Auto-play blocked:", e));

            // Hide visualizer overlay
            visualizerIdleMsg.style.display = "none";

            // Add to history
            addToHistory(text, result.audio_url, result.filename, result.duration);

        } catch (error) {
            console.error(error);
            alert(`Lỗi: ${error.message}`);
        } finally {
            generateBtn.classList.remove("loading");
            generateBtn.disabled = false;
        }
    });

    // ──────────────────────── Audio Player Logic ─────────────────────────────
    // Initialize Web Audio API on first user interaction with audio player
    function initVisualizer() {
        if (audioCtx) return;
        
        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 256;
            
            source = audioCtx.createMediaElementSource(audioPlayer);
            source.connect(analyser);
            analyser.connect(audioCtx.destination);
        } catch (e) {
            console.error("Web Audio API is not supported or failed to initialize:", e);
        }
    }

    playPauseBtn.addEventListener("click", () => {
        initVisualizer();
        
        // Resume AudioContext if suspended
        if (audioCtx && audioCtx.state === "suspended") {
            audioCtx.resume();
        }

        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    });

    audioPlayer.addEventListener("play", () => {
        playPauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
        startVisualizer();
    });

    audioPlayer.addEventListener("pause", () => {
        playPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        isVisualizerRunning = false;
    });

    audioPlayer.addEventListener("ended", () => {
        playPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        progressBar.style.width = "0%";
        currentTimeDisplay.textContent = "0:00";
        isVisualizerRunning = false;
    });

    // Time update and progress bar syncing
    audioPlayer.addEventListener("timeupdate", () => {
        const current = audioPlayer.currentTime;
        const duration = audioPlayer.duration || 0;
        
        progressBar.style.width = `${(current / duration) * 100}%`;
        currentTimeDisplay.textContent = formatTime(current);
    });

    // Loaded metadata to set total duration
    audioPlayer.addEventListener("loadedmetadata", () => {
        totalTimeDisplay.textContent = formatTime(audioPlayer.duration);
    });

    // Seek on progress bar click
    progressContainer.addEventListener("click", (e) => {
        const rect = progressContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const duration = audioPlayer.duration;
        
        if (duration) {
            audioPlayer.currentTime = (clickX / width) * duration;
        }
    });

    function formatTime(seconds) {
        if (isNaN(seconds)) return "0:00";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // ──────────────────────── Audio Visualizer ──────────────────────────────
    function drawStaticWaveform() {
        const w = canvas.width / window.devicePixelRatio;
        const h = canvas.height / window.devicePixelRatio;
        
        const style = getComputedStyle(document.body);
        const primaryColor = style.getPropertyValue('--primary-color').trim() || '#7052ff';
        
        canvasCtx.clearRect(0, 0, w, h);
        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = primaryColor + "40"; // adds ~25% alpha
        
        canvasCtx.beginPath();
        canvasCtx.moveTo(0, h / 2);
        canvasCtx.lineTo(w, h / 2);
        canvasCtx.stroke();
    }

    function startVisualizer() {
        if (isVisualizerRunning) return;
        isVisualizerRunning = true;
        
        const w = canvas.width / window.devicePixelRatio;
        const h = canvas.height / window.devicePixelRatio;
        
        // Fallback animation if Analyser isn't ready
        if (!analyser) {
            let phase = 0;
            function animateFallback() {
                if (!isVisualizerRunning) {
                    drawStaticWaveform();
                    return;
                }
                
                canvasCtx.clearRect(0, 0, w, h);
                canvasCtx.lineWidth = 2.5;
                
                const style = getComputedStyle(document.body);
                const pColor = style.getPropertyValue('--primary-color').trim() || '#7052ff';
                const sColor = style.getPropertyValue('--secondary-color').trim() || '#00f2fe';
                
                // Draw decorative synth sine waves
                const gradient = canvasCtx.createLinearGradient(0, 0, w, 0);
                gradient.addColorStop(0, pColor);
                gradient.addColorStop(1, sColor);
                canvasCtx.strokeStyle = gradient;
                
                canvasCtx.beginPath();
                for (let x = 0; x < w; x += 2) {
                    const y = h / 2 + Math.sin(x * 0.03 + phase) * 15 * Math.sin(x * 0.005);
                    if (x === 0) canvasCtx.moveTo(x, y);
                    else canvasCtx.lineTo(x, y);
                }
                canvasCtx.stroke();
                
                phase += 0.15;
                requestAnimationFrame(animateFallback);
            }
            animateFallback();
            return;
        }

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        function draw() {
            if (!isVisualizerRunning) {
                drawStaticWaveform();
                return;
            }

            requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);

            canvasCtx.clearRect(0, 0, w, h);

            const style = getComputedStyle(document.body);
            const pColor = style.getPropertyValue('--primary-color').trim() || '#7052ff';
            const sColor = style.getPropertyValue('--secondary-color').trim() || '#00f2fe';

            // Setup gradient styling
            const gradient = canvasCtx.createLinearGradient(0, 0, w, 0);
            gradient.addColorStop(0, pColor);
            gradient.addColorStop(0.5, pColor + '80');
            gradient.addColorStop(1, sColor);
            
            // Draw bars symmetrical from the center line
            const barWidth = (w / bufferLength) * 1.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * h * 0.8;

                // Max cap on minimum height to keep visualizer alive/dynamic
                if (barHeight < 3) barHeight = 3;

                canvasCtx.fillStyle = gradient;
                
                // Draw rounded top and bottom bars centered vertically
                const y = (h - barHeight) / 2;
                
                // Draw vertical capsules
                canvasCtx.beginPath();
                canvasCtx.roundRect(x, y, barWidth - 1.5, barHeight, 3);
                canvasCtx.fill();

                x += barWidth;
            }
        }
        
        draw();
    }

    // ──────────────────────── History Management ────────────────────────────
    function updateHistoryUI() {
        if (history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-history">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>Chưa có lịch sử. Hãy tạo giọng nói trước!</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = "";
        
        history.forEach((item, index) => {
            const historyItem = document.createElement("div");
            historyItem.className = "history-item";
            
            historyItem.innerHTML = `
                <div class="history-item-info">
                    <div class="history-item-text" title="${escapeHtml(item.text)}">${escapeHtml(item.text)}</div>
                    <div class="history-item-meta">
                        <span><i class="fa-solid fa-clock"></i> ${item.time}</span>
                        <span><i class="fa-solid fa-hourglass-start"></i> ${item.duration}s</span>
                    </div>
                </div>
                <div class="history-item-actions">
                    <button class="history-action-btn play-btn" title="Nghe lại"><i class="fa-solid fa-play"></i></button>
                    <button class="history-action-btn download-btn" title="Tải xuống WAV"><i class="fa-solid fa-download"></i></button>
                    <button class="history-action-btn delete-btn" title="Xóa"><i class="fa-solid fa-xmark"></i></button>
                </div>
            `;

            // Play history audio click
            historyItem.querySelector(".play-btn").addEventListener("click", () => {
                initVisualizer();
                if (audioCtx && audioCtx.state === "suspended") {
                    audioCtx.resume();
                }

                // Show player if hidden
                playerWrapper.style.display = "block";
                visualizerIdleMsg.style.display = "none";
                
                // Load stats from history item into UI details
                durationVal.textContent = `${item.duration}s`;
                elapsedVal.textContent = "--";
                rtfVal.textContent = "--";
                resultDetails.style.display = "block";

                audioPlayer.src = item.url;
                audioPlayer.play();
                
                // Hook up the current download button
                downloadBtn.onclick = () => {
                    const link = document.createElement("a");
                    link.href = item.url;
                    link.download = item.filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                };
            });

            // Download audio click
            historyItem.querySelector(".download-btn").addEventListener("click", () => {
                const link = document.createElement("a");
                link.href = item.url;
                link.download = item.filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });

            // Delete item click
            historyItem.querySelector(".delete-btn").addEventListener("click", () => {
                deleteFromHistory(index);
            });

            historyList.appendChild(historyItem);
        });
    }

    function addToHistory(text, url, filename, duration) {
        const timeString = new Date().toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit"
        });

        // Add to front of history array
        history.unshift({
            text: text,
            url: url,
            filename: filename,
            duration: duration,
            time: timeString
        });

        // Max history length = 15 items
        if (history.length > 15) {
            history.pop();
        }

        localStorage.setItem("tts_history", JSON.stringify(history));
        updateHistoryUI();
    }

    function deleteFromHistory(index) {
        history.splice(index, 1);
        localStorage.setItem("tts_history", JSON.stringify(history));
        updateHistoryUI();
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Populate initial UI
    updateHistoryUI();
});
