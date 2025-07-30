// Play individual sentence audio
function playSentenceAudio(audioFile) {
    if (!audioFile) {
        console.error('No audio file provided');
        return;
    }
    
    // Stop any currently playing audio
    if (window.currentAudio) {
        window.currentAudio.pause();
        clearActiveStates();
    }
    
    // Create and play new audio
    window.currentAudio = new Audio(`/static/${audioFile}`);
    
    // Find and highlight the corresponding input and play button
    const speakerCircles = document.querySelectorAll('.speaker-circle');
    speakerCircles.forEach(circle => {
        const onclickAttr = circle.getAttribute('onclick');
        if (onclickAttr && onclickAttr.includes(audioFile)) {
            highlightActiveElements(circle);
        }
    });
    
    window.currentAudio.addEventListener('ended', () => {
        clearActiveStates();
    });
    
    window.currentAudio.play().catch(error => {
        console.error('Error playing sentence audio:', error);
        clearActiveStates();
    });
}

// Play conversation audio - all sentences in sequence
function playConversationAudio() {
    // Get all audio files from the conversation
    const audioInputs = document.querySelectorAll('.chat-input-bubble');
    const audioFiles = [];
    
    audioInputs.forEach(input => {
        const sentenceId = input.getAttribute('data-sentence-id');
        // Find the corresponding speaker circle to get the audio file
        const speakerCircle = input.parentElement.querySelector('.speaker-circle');
        if (speakerCircle && speakerCircle.onclick) {
            // Extract audio file from onclick attribute
            const onclickAttr = speakerCircle.getAttribute('onclick');
            const match = onclickAttr.match(/playSentenceAudio\('([^']+)'\)/);
            if (match) {
                audioFiles.push(match[1]);
            }
        }
    });
    
    if (audioFiles.length === 0) {
        console.error('No audio files found');
        return;
    }
    
    // Stop any currently playing audio
    if (window.currentAudio) {
        window.currentAudio.pause();
        clearActiveStates();
    }
    
    // Play all audio files in sequence
    playAudioSequence(audioFiles, 0);
}

// Helper function to play audio files in sequence
function playAudioSequence(audioFiles, index) {
    if (index >= audioFiles.length) {
        clearActiveStates();
        return; // Finished playing all audio
    }
    
    const audioFile = audioFiles[index];
    window.currentAudio = new Audio(`/static/${audioFile}`);
    
    // Find and highlight the corresponding input and play button
    const speakerCircles = document.querySelectorAll('.speaker-circle');
    speakerCircles.forEach(circle => {
        const onclickAttr = circle.getAttribute('onclick');
        if (onclickAttr && onclickAttr.includes(audioFile)) {
            highlightActiveElements(circle);
        }
    });
    
    window.currentAudio.addEventListener('ended', () => {
        clearActiveStates();
        // Play next audio file after current one ends
        playAudioSequence(audioFiles, index + 1);
    });
    
    window.currentAudio.addEventListener('error', () => {
        console.error('Error playing audio:', audioFile);
        clearActiveStates();
        // Continue with next audio file even if current one fails
        playAudioSequence(audioFiles, index + 1);
    });
    
    window.currentAudio.play().catch(error => {
        console.error('Error playing conversation audio:', error);
        clearActiveStates();
        // Continue with next audio file even if current one fails
        playAudioSequence(audioFiles, index + 1);
    });
}

// Highlight active elements (input field and play button)
function highlightActiveElements(activeCircle) {
    // Clear any existing active states
    clearActiveStates();
    
    // Add active class to the circle
    activeCircle.classList.add('speaker-circle-active');
    
    // Find and highlight the corresponding input field
    const chatMessage = activeCircle.closest('.chat-message');
    const inputField = chatMessage.querySelector('.chat-input-bubble');
    if (inputField) {
        inputField.classList.add('chat-input-active');
    }
}

// Clear all active states
function clearActiveStates() {
    // Remove active classes from all elements
    document.querySelectorAll('.speaker-circle-active').forEach(circle => {
        circle.classList.remove('speaker-circle-active');
    });
    
    document.querySelectorAll('.chat-input-active').forEach(input => {
        input.classList.remove('chat-input-active');
    });
} 