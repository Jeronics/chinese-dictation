// Story audio modal logic
window.onload = function() {
    const input = document.getElementById("user_input");
    if (input) input.focus();
};

// Only require input for the Submit button

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('dictation-form');
    const userInput = document.getElementById('user_input');
    const submitBtn = document.getElementById('submit-answer-btn');

    if (form && userInput && submitBtn) {
        form.addEventListener('submit', function(e) {
            // Only require input if the submit button was used
            if (document.activeElement === submitBtn) {
                if (!userInput.value.trim()) {
                    e.preventDefault();
                    userInput.focus();
                    userInput.setCustomValidity('Please enter your answer.');
                    userInput.reportValidity();
                } else {
                    userInput.setCustomValidity('');
                }
            } else {
                // For other form submissions, allow empty input
                userInput.setCustomValidity('');
            }
        });
    }
    // Also clear custom validity on input
    if (userInput) {
        userInput.addEventListener('input', function() {
            userInput.setCustomValidity('');
        });
    }

    // Story audio modal logic
    const openModalBtn = document.getElementById('open-story-audio-modal');
    const modal = document.getElementById('story-audio-modal');
    const closeModalBtn = document.getElementById('close-story-audio-modal');
    const audioElement = document.getElementById('story-audio');
    if (openModalBtn && modal && closeModalBtn && audioElement) {
        const audioFiles = window.storyAudioFiles || [];
        let currentIdx = 0;

        function highlightCurrent(idx) {
            for (let i = 0; i < audioFiles.length; i++) {
                const item = document.getElementById('playlist-item-' + i);
                if (item) {
                    item.style.fontWeight = (i === idx) ? 'bold' : 'normal';
                    item.style.color = (i === idx) ? '#1976d2' : '#fff';
                    item.style.background = (i === idx) ? '#e3f2fd' : '';
                    item.style.borderRadius = (i === idx) ? '4px' : '';
                    item.style.padding = (i === idx) ? '0.1em 0.4em' : '';
                }
            }
        }

        highlightCurrent(currentIdx);

        openModalBtn.addEventListener('click', function() {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scroll
        });
        closeModalBtn.addEventListener('click', function() {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        });
        // Close modal on background click
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
                document.body.style.overflow = '';
            }
        });

        audioElement.addEventListener('ended', function() {
            if (currentIdx < audioFiles.length - 1) {
                currentIdx++;
                audioElement.src = '/static/' + audioFiles[currentIdx];
                audioElement.play();
                highlightCurrent(currentIdx);
            }
        });

        audioElement.addEventListener('seeked', function() {
            if (audioElement.currentTime === 0 && currentIdx !== 0) {
                currentIdx = 0;
                audioElement.src = '/static/' + audioFiles[0];
                highlightCurrent(currentIdx);
            }
        });
    }
});

// Toggle translations for story context
function toggleTranslations() {
    const button = document.querySelector('.toggle-button');
    const pinyinElements = document.querySelectorAll('.context-pinyin');
    const translationElements = document.querySelectorAll('.context-translation');
    if (!pinyinElements.length || !translationElements.length) return;
    const pinyinHidden = pinyinElements[0].classList.contains('hidden');
    const translationHidden = translationElements[0].classList.contains('hidden');
    if (pinyinHidden && translationHidden) {
        // First click: Show pinyin only
        pinyinElements.forEach(el => el.classList.remove('hidden'));
        translationElements.forEach(el => el.classList.add('hidden'));
        button.textContent = 'Show English';
        button.classList.add('active');
    } else if (!pinyinHidden && translationHidden) {
        // Second click: Show both pinyin and English
        pinyinElements.forEach(el => el.classList.remove('hidden'));
        translationElements.forEach(el => el.classList.remove('hidden'));
        button.textContent = 'Hide All';
        button.classList.add('active');
    } else {
        // Third click: Hide everything
        pinyinElements.forEach(el => el.classList.add('hidden'));
        translationElements.forEach(el => el.classList.add('hidden'));
        button.textContent = 'Show Pinyin';
        button.classList.remove('active');
    }
} 