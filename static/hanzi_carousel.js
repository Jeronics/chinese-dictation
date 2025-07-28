// Minimalist Cylindrical Hanzi Carousel
class CylindricalHanziCarousel {
    constructor() {
        this.currentIndex = 0;
        this.hanziList = [];
        this.isOpen = false;
        this.createCarousel();
    }

    createCarousel() {
        // Create carousel container
        this.carousel = document.createElement('div');
        this.carousel.id = 'hanzi-carousel';
        this.carousel.className = 'hanzi-carousel';
        
        // Create carousel content - minimal version
        this.carousel.innerHTML = `
            <div class="carousel-cylinder">
                <div class="carousel-track" id="carousel-track">
                    <!-- Hanzi cards will be inserted here -->
                </div>
            </div>
            <div class="carousel-controls">
                <button class="carousel-nav carousel-prev" id="carousel-prev">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                <button class="carousel-nav carousel-next" id="carousel-next">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
            <button class="carousel-close" id="carousel-close">&times;</button>
        `;
        
        document.body.appendChild(this.carousel);
        this.bindEvents();
    }

    bindEvents() {
        // Close button
        document.getElementById('carousel-close').addEventListener('click', () => {
            this.close();
        });

        // Navigation buttons
        document.getElementById('carousel-prev').addEventListener('click', () => {
            this.prev();
        });

        document.getElementById('carousel-next').addEventListener('click', () => {
            this.next();
        });

        // Close on overlay click
        this.carousel.addEventListener('click', (e) => {
            if (e.target === this.carousel) {
                this.close();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!this.isOpen) return;
            
            switch(e.key) {
                case 'Escape':
                    this.close();
                    break;
                case 'ArrowLeft':
                    if (e.shiftKey) {
                        this.scrollLeft(); // Fast scroll with Shift
                    } else {
                        this.prev();
                    }
                    break;
                case 'ArrowRight':
                    if (e.shiftKey) {
                        this.scrollRight(); // Fast scroll with Shift
                    } else {
                        this.next();
                    }
                    break;
                case 'Home':
                    this.goTo(0); // Jump to first
                    break;
                case 'End':
                    this.goTo(this.hanziList.length - 1); // Jump to last
                    break;
            }
        });

        // Touch/swipe support
        let startX = 0;
        let endX = 0;
        let startTime = 0;

        this.carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startTime = Date.now();
        });

        this.carousel.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            const duration = Date.now() - startTime;
            const velocity = Math.abs(diff) / duration;
            
            if (Math.abs(diff) > 30) { // Reduced minimum swipe distance
                if (diff > 0) {
                    if (velocity > 0.5) { // Fast swipe
                        this.scrollRight();
                    } else {
                        this.next();
                    }
                } else {
                    if (velocity > 0.5) { // Fast swipe
                        this.scrollLeft();
                    } else {
                        this.prev();
                    }
                }
            }
        });
    }

    show(hanziList, startIndex = 0) {
        this.hanziList = hanziList;
        this.currentIndex = Math.max(0, Math.min(startIndex, hanziList.length - 1));
        this.isOpen = true;
        
        this.createHanziCards();
        this.updateDisplay();
        this.carousel.classList.add('carousel-open');
        
        // Trigger animation for the initial focused card
        setTimeout(() => {
            this.triggerAnimationForCard(this.currentIndex);
        }, 100);
    }

    close() {
        this.isOpen = false;
        this.carousel.classList.remove('carousel-open');
        this.hanziList = [];
        
        // Stop all animations when closing
        this.stopAllAnimations();
        
        // Clear any pending animation timeouts
        if (this.animationTimeout) {
            clearTimeout(this.animationTimeout);
            this.animationTimeout = null;
        }
    }

    prev() {
        if (this.hanziList.length <= 1) return;
        this.currentIndex = Math.max(0, this.currentIndex - 1);
        this.updateDisplay();
    }

    next() {
        if (this.hanziList.length <= 1) return;
        this.currentIndex = Math.min(this.hanziList.length - 1, this.currentIndex + 1);
        this.updateDisplay();
    }

    // Smooth scroll methods for faster navigation
    scrollLeft() {
        if (this.hanziList.length <= 1) return;
        this.currentIndex = Math.max(0, this.currentIndex - 3); // Jump 3 positions
        this.updateDisplay();
    }

    scrollRight() {
        if (this.hanziList.length <= 1) return;
        this.currentIndex = Math.min(this.hanziList.length - 1, this.currentIndex + 3); // Jump 3 positions
        this.updateDisplay();
    }

    goTo(index) {
        if (index >= 0 && index < this.hanziList.length) {
            this.currentIndex = index;
            this.updateDisplay();
        }
    }

    createHanziCards() {
        const track = document.getElementById('carousel-track');
        track.innerHTML = '';
        
        console.log('Creating hanzi cards for:', this.hanziList);
        
        this.hanziList.forEach((hanzi, index) => {
            const card = document.createElement('div');
            card.className = 'hanzi-card';
            card.dataset.index = index;
            
            card.innerHTML = `
                <div class="stroke-container" id="stroke-${index}"></div>
            `;
            
            track.appendChild(card);
            console.log(`Created card ${index} for hanzi: ${hanzi}`);
        });
        
        console.log('Total cards created:', track.children.length);
        
        // Create static HanziWriter instances for all cards
        this.createStaticHanziWriters();
    }

    createStaticHanziWriters() {
        if (typeof HanziWriter === 'undefined') return;
        
        const isMobile = window.innerWidth <= 768;
        const writerSize = isMobile ? 110 : 130;
        
        this.hanziList.forEach((hanzi, index) => {
            const strokeContainer = document.getElementById(`stroke-${index}`);
            if (!strokeContainer) return;
            
            // Create static HanziWriter instance (gray outline, no animation)
            const writer = HanziWriter.create(strokeContainer, hanzi, {
                width: writerSize,
                height: writerSize,
                showOutline: true,
                showCharacter: false,
                padding: 0,
                strokeColor: '#808080', // Gray color for static state
                outlineColor: '#808080',
                strokeAnimationSpeed: 0, // No animation
                delayBetweenStrokes: 0
            });
            
            // Store the writer instance for this card
            if (!this.writers) this.writers = {};
            this.writers[index] = writer;
        });
    }

    updateDisplay() {
        if (this.hanziList.length === 0) return;

        // Update card positions for cylindrical effect
        this.updateCardPositions();
        
        // Update navigation buttons
        this.updateNavigation();
    }

        updateCardPositions() {
        const cards = document.querySelectorAll('.hanzi-card');
        const totalCards = cards.length;
        
        console.log('Updating card positions for', totalCards, 'cards');
        
        // Free-flowing horizontal layout
        cards.forEach((card, index) => {
            const offset = index - this.currentIndex;
            const cardWidth = 140; // Reduced spacing between cards
            const x = offset * cardWidth;
            
            // Visibility logic - show all cards with varying opacity
            let opacity = Math.max(0.8, 1 - Math.abs(offset) * 0.1); // Much higher minimum opacity
            let scale = Math.max(0.8, 1 - Math.abs(offset) * 0.05); // Higher minimum scale
            let isFocused = Math.abs(offset) === 0;
            
            console.log(`Card ${index}: x=${x}, scale=${scale}, opacity=${opacity}, focused=${isFocused}`);
            
            card.style.transform = `translateX(${x}px) scale(${scale})`;
            card.style.opacity = opacity;
            card.style.zIndex = 1000 - Math.abs(offset);
            
            // Always show background, but with different styling for focused vs unfocused
            if (isFocused) {
                card.style.background = 'var(--bg-secondary)';
                card.style.filter = 'none';
            } else {
                card.style.background = 'var(--bg-secondary)';
                card.style.filter = 'grayscale(0.3) brightness(0.9)'; // Much less gray and brighter
            }
            
            // Handle animation for focused vs unfocused cards
            if (isFocused) {
                this.triggerAnimationForCard(index);
            } else {
                // Restore static gray outline for unfocused cards
                this.restoreStaticWriter(index);
            }
        });
    }

    triggerAnimationForCard(cardIndex) {
        // Clear any existing timeout
        if (this.animationTimeout) {
            clearTimeout(this.animationTimeout);
        }
        
        // Stop any current animations immediately
        this.stopAllAnimations();
        
        // Set a timeout to trigger animation after a brief delay
        this.animationTimeout = setTimeout(() => {
            this.updateStrokeOrder();
        }, 300); // 300ms delay before triggering animation
    }

    restoreStaticWriter(cardIndex) {
        if (!this.writers || !this.writers[cardIndex]) return;
        
        const card = document.querySelector(`.hanzi-card[data-index="${cardIndex}"]`);
        if (!card) return;
        
        const strokeContainer = card.querySelector('.stroke-container');
        if (!strokeContainer) return;
        
        // Clear the container and recreate the static writer
        strokeContainer.innerHTML = '';
        
        const hanzi = this.hanziList[cardIndex];
        const isMobile = window.innerWidth <= 768;
        const writerSize = isMobile ? 110 : 130;
        
        // Recreate static HanziWriter instance
        const writer = HanziWriter.create(strokeContainer, hanzi, {
            width: writerSize,
            height: writerSize,
            showOutline: true,
            showCharacter: false,
            padding: 0,
            strokeColor: '#808080', // Gray color for static state
            outlineColor: '#808080',
            strokeAnimationSpeed: 0, // No animation
            delayBetweenStrokes: 0
        });
        
        // Update the stored writer instance
        this.writers[cardIndex] = writer;
    }

    updateStrokeOrder() {
        // Stop the current animation first
        this.stopAllAnimations();
        
        const currentCard = document.querySelector(`.hanzi-card[data-index="${this.currentIndex}"]`);
        if (!currentCard) return;
        
        const strokeContainer = currentCard.querySelector('.stroke-container');
        const hanzi = this.hanziList[this.currentIndex];
        
        // Clear the current card's stroke container
        strokeContainer.innerHTML = '';
        
        if (typeof HanziWriter !== 'undefined') {
            // Detect screen size to adjust HanziWriter size
            const isMobile = window.innerWidth <= 768;
            const writerSize = isMobile ? 110 : 130;
            
            // Create animated writer for the focused card
            const writer = HanziWriter.create(strokeContainer, hanzi, {
                width: writerSize,
                height: writerSize,
                showOutline: true,
                showCharacter: false,
                padding: 0,
                strokeAnimationSpeed: 1,
                delayBetweenStrokes: 200,
                strokeColor: '#ffffff', // White for animated strokes
                outlineColor: '#808080',
            });
            
            // Store the writer instance for potential stopping
            this.currentWriter = writer;
            
            // Start the animation
            writer.animateCharacter();
        }
    }

    stopAllAnimations() {
        // Stop the current writer animation if it exists
        if (this.currentWriter && typeof this.currentWriter.cancelAnimation === 'function') {
            this.currentWriter.cancelAnimation();
        }
        
        // Don't clear stroke containers - just stop the animation
        // This keeps the static gray outlines visible
        this.currentWriter = null;
    }



    updateNavigation() {
        const prevBtn = document.getElementById('carousel-prev');
        const nextBtn = document.getElementById('carousel-next');
        
        prevBtn.style.display = this.hanziList.length <= 1 ? 'none' : 'block';
        nextBtn.style.display = this.hanziList.length <= 1 ? 'none' : 'block';
    }
}

// Initialize carousel
let hanziCarousel;

document.addEventListener('DOMContentLoaded', function() {
    hanziCarousel = new CylindricalHanziCarousel();
});

// Function to show carousel with multiple hanzi
function showHanziCarousel(hanziList, startIndex = 0) {
    if (!hanziCarousel) {
        hanziCarousel = new CylindricalHanziCarousel();
    }
    hanziCarousel.show(hanziList, startIndex);
}

// Enhanced clickable hanzi function
function showStrokeOrder(hanzi) {
    console.log('showStrokeOrder called with:', hanzi);
    
    // Extract all hanzi from the correct sentence only
    let allHanzi = [hanzi];
    let startIndex = 0;
    
    // Find the paragraph containing "Correct sentence"
    const paragraphs = document.querySelectorAll('.result p');
    for (const p of paragraphs) {
        const text = p.textContent || p.innerText;
        if (text.includes('Correct sentence:')) {
            // Extract hanzi from this specific paragraph
            const hanziRegex = /[\u4e00-\u9fff]/g;
            const extractedHanzi = text.match(hanziRegex);
            
            if (extractedHanzi && extractedHanzi.length > 0) {
                allHanzi = extractedHanzi;
                // Find the index of the clicked hanzi
                startIndex = allHanzi.indexOf(hanzi);
                if (startIndex === -1) startIndex = 0; // Fallback to first if not found
                console.log('Extracted hanzi:', allHanzi, 'starting at index:', startIndex);
            }
            break;
        }
    }
    
    // Show carousel with all hanzi, starting at the clicked position
    console.log('Showing carousel with:', allHanzi, 'at index:', startIndex);
    showHanziCarousel(allHanzi, startIndex);
} 