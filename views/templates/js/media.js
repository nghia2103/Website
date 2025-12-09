const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const closeBtn = document.querySelector('.modal-close');
    const zoomBtn = document.querySelector('.modal-zoom');
    const prevBtn = document.querySelector('.modal-prev');
    const nextBtn = document.querySelector('.modal-next');
    const images = document.querySelectorAll('.gallery-item img');
    let currentIndex = 0;
    let isZoomed = false;

    images.forEach((img, index) => {
      img.addEventListener('click', () => {
        modal.style.display = 'flex';
        modalImg.src = img.src;
        currentIndex = index;
      });
    });

    closeBtn.addEventListener('click', () => {
      modal.style.display = 'none';
      if (document.fullscreenElement) {
        document.exitFullscreen();
      }
      isZoomed = false;
      zoomBtn.textContent = '⤢';
      modalImg.classList.remove('zoomed');
    });

    zoomBtn.addEventListener('click', () => {
      if (!isZoomed) {
        if (modal.requestFullscreen) {
          modal.requestFullscreen();
        }
        zoomBtn.textContent = '⯀';
      } else if (document.fullscreenElement) {
        document.exitFullscreen();
        zoomBtn.textContent = '⤢';
      }
      isZoomed = !isZoomed;
      if (isZoomed) {
        modalImg.classList.add('zoomed');
      } else {
        modalImg.classList.remove('zoomed');
      }
    });

    prevBtn.addEventListener('click', () => {
      currentIndex = (currentIndex - 1 + images.length) % images.length;
      modalImg.src = images[currentIndex].src;
      if (isZoomed && !modalImg.classList.contains('zoomed')) {
        modalImg.classList.add('zoomed');
        if (modal.requestFullscreen && !document.fullscreenElement) {
          modal.requestFullscreen();
        }
      }
    });

    nextBtn.addEventListener('click', () => {
      currentIndex = (currentIndex + 1) % images.length;
      modalImg.src = images[currentIndex].src;
      if (isZoomed && !modalImg.classList.contains('zoomed')) {
        modalImg.classList.add('zoomed');
        if (modal.requestFullscreen && !document.fullscreenElement) {
          modal.requestFullscreen();
        }
      }
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        if (document.fullscreenElement) {
          document.exitFullscreen();
        }
        isZoomed = false;
        zoomBtn.textContent = '⤢';
        modalImg.classList.remove('zoomed');
      }
    });

    const sectionDonkies = document.querySelector('.section-donkies');
    const video = document.querySelector('.donkies-video-scroll video');
    const videoHeight = window.innerHeight;
    const startTranslateY = 300;
    const endTranslateY = 0;

    function updateVideoPosition() {
      const rect = sectionDonkies.getBoundingClientRect();
      const scrollProgress = Math.max(0, Math.min(1, -rect.top / (rect.height - videoHeight)));
      const translateY = startTranslateY - (startTranslateY - endTranslateY) * scrollProgress;
      video.style.transform = `translateY(${translateY}px)`;
    }

    window.addEventListener('scroll', updateVideoPosition);
    window.addEventListener('resize', updateVideoPosition);
    updateVideoPosition();