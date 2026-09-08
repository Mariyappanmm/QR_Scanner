document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle Logic
    const themeToggle = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    
    // Check saved theme or system preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        
        if (theme === 'dark') {
            lightIcon.classList.add('d-none');
            darkIcon.classList.remove('d-none');
        } else {
            lightIcon.classList.remove('d-none');
            darkIcon.classList.add('d-none');
        }
    }

    // 2. Global Toast Helper
    window.showToast = function(message, type = 'success') {
        const toastEl = document.getElementById('liveToast');
        const toastMsg = document.getElementById('toastMessage');
        const toastIcon = document.getElementById('toastIcon');
        
        if (!toastEl) return;
        
        toastMsg.textContent = message;
        
        // Reset classes
        toastEl.className = 'toast align-items-center border-0 shadow-lg';
        toastIcon.className = 'bi fs-5';
        
        if (type === 'success') {
            toastEl.classList.add('text-bg-success');
            toastIcon.classList.add('bi-check-circle-fill');
        } else if (type === 'danger' || type === 'error') {
            toastEl.classList.add('text-bg-danger');
            toastIcon.classList.add('bi-exclamation-triangle-fill');
        } else if (type === 'warning') {
            toastEl.classList.add('text-bg-warning');
            toastIcon.classList.add('bi-exclamation-circle-fill');
        } else {
            toastEl.classList.add('text-bg-primary');
            toastIcon.classList.add('bi-info-circle-fill');
        }
        
        const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
        toast.show();
    };

    // 3. Web Audio API Synthesized sound alerts
    window.playScanSound = function(type) {
        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) {
                console.warn("Web Audio API not supported by this browser.");
                return;
            }
            const audioCtx = new AudioContextClass();
            
            if (type === 'success') {
                // Success: crisp high double beep (chime)
                const osc1 = audioCtx.createOscillator();
                const osc2 = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();
                
                osc1.type = 'sine';
                osc2.type = 'sine';
                
                // Frequency values
                osc1.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
                osc2.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.12); // E5
                
                gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
                
                osc1.connect(gainNode);
                osc2.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                
                osc1.start();
                osc1.stop(audioCtx.currentTime + 0.15);
                
                osc2.start(audioCtx.currentTime + 0.12);
                osc2.stop(audioCtx.currentTime + 0.35);
                
            } else if (type === 'denied') {
                // Denied: low buzz/sawtooth wave
                const osc = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();
                
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(130.81, audioCtx.currentTime); // C3
                osc.frequency.linearRampToValueAtTime(80, audioCtx.currentTime + 0.45);
                
                gainNode.gain.setValueAtTime(0.15, audioCtx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.45);
                
                osc.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                
                osc.start();
                osc.stop(audioCtx.currentTime + 0.45);
            }
        } catch (error) {
            console.error("Error playing scan sound alert via Web Audio API: ", error);
        }
    };
});
