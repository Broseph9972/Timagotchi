// ReactBits-inspired Carousel Implementation
class Carousel {
    constructor(containerId, trackId, indicatorsId) {
        this.container = document.getElementById(containerId);
        this.track = document.getElementById(trackId);
        this.indicatorsContainer = document.getElementById(indicatorsId);
        this.items = Array.from(this.track.children);
        this.currentIndex = 0;
        this.isDragging = false;
        this.startPos = 0;
        this.currentTranslate = 0;
        this.prevTranslate = 0;
        this.animationID = null;
        this.autoplayInterval = null;
        
        this.init();
    }
    
    init() {
        this.createIndicators();
        this.attachEventListeners();
        this.updateCarousel();
        this.startAutoplay();
    }
    
    createIndicators() {
        this.items.forEach((_, index) => {
            const indicator = document.createElement('div');
            indicator.classList.add('carousel-indicator');
            if (index === 0) indicator.classList.add('active');
            indicator.addEventListener('click', () => this.goToSlide(index));
            this.indicatorsContainer.appendChild(indicator);
        });
        this.indicators = Array.from(this.indicatorsContainer.children);
    }
    
    attachEventListeners() {
        // Mouse events
        this.track.addEventListener('mousedown', this.touchStart.bind(this));
        this.track.addEventListener('mouseup', this.touchEnd.bind(this));
        this.track.addEventListener('mouseleave', this.touchEnd.bind(this));
        this.track.addEventListener('mousemove', this.touchMove.bind(this));
        
        // Touch events
        this.track.addEventListener('touchstart', this.touchStart.bind(this));
        this.track.addEventListener('touchend', this.touchEnd.bind(this));
        this.track.addEventListener('touchmove', this.touchMove.bind(this));
        
        // Prevent context menu
        this.track.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // Stop autoplay on user interaction
        this.container.addEventListener('mouseenter', () => this.stopAutoplay());
        this.container.addEventListener('mouseleave', () => this.startAutoplay());
    }
    
    touchStart(event) {
        this.isDragging = true;
        this.startPos = this.getPositionX(event);
        this.animationID = requestAnimationFrame(this.animation.bind(this));
        this.track.style.cursor = 'grabbing';
        this.stopAutoplay();
    }
    
    touchMove(event) {
        if (this.isDragging) {
            const currentPosition = this.getPositionX(event);
            this.currentTranslate = this.prevTranslate + currentPosition - this.startPos;
        }
    }
    
    touchEnd() {
        this.isDragging = false;
        cancelAnimationFrame(this.animationID);
        
        const movedBy = this.currentTranslate - this.prevTranslate;
        
        // Threshold for slide change (50px)
        if (movedBy < -50 && this.currentIndex < this.items.length - 1) {
            this.currentIndex += 1;
        }
        
        if (movedBy > 50 && this.currentIndex > 0) {
            this.currentIndex -= 1;
        }
        
        this.updateCarousel();
        this.track.style.cursor = 'grab';
        this.startAutoplay();
    }
    
    getPositionX(event) {
        return event.type.includes('mouse') ? event.pageX : event.touches[0].clientX;
    }
    
    animation() {
        this.setSliderPosition();
        if (this.isDragging) requestAnimationFrame(this.animation.bind(this));
    }
    
    setSliderPosition() {
        this.track.style.transform = `translateX(${this.currentTranslate}px)`;
    }
    
    updateCarousel() {
        const itemWidth = this.items[0].offsetWidth + 16; // item width + gap
        this.currentTranslate = -this.currentIndex * itemWidth;
        this.prevTranslate = this.currentTranslate;
        
        this.track.style.transition = 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
        this.setSliderPosition();
        
        // Update 3D rotation effect
        this.items.forEach((item, index) => {
            const offset = index - this.currentIndex;
            const rotation = offset * 5; // Subtle 3D rotation
            const scale = 1 - Math.abs(offset) * 0.05;
            const opacity = 1 - Math.abs(offset) * 0.3;
            
            item.style.transform = `rotateY(${rotation}deg) scale(${scale})`;
            item.style.opacity = Math.max(opacity, 0.4);
        });
        
        // Update indicators
        this.indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentIndex);
        });
        
        setTimeout(() => {
            this.track.style.transition = '';
        }, 500);
    }
    
    goToSlide(index) {
        this.currentIndex = index;
        this.updateCarousel();
        this.stopAutoplay();
        this.startAutoplay();
    }
    
    next() {
        if (this.currentIndex < this.items.length - 1) {
            this.currentIndex++;
        } else {
            this.currentIndex = 0; // Loop back to start
        }
        this.updateCarousel();
    }
    
    prev() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
        } else {
            this.currentIndex = this.items.length - 1; // Loop to end
        }
        this.updateCarousel();
    }
    
    startAutoplay() {
        this.stopAutoplay(); // Clear any existing interval
        this.autoplayInterval = setInterval(() => {
            this.next();
        }, 3000); // 3 seconds
    }
    
    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
    }
}

// Initialize carousel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const carousel = new Carousel('carouselContainer', 'carouselTrack', 'carouselIndicators');
});
