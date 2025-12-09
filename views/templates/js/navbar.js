let lastScrollTop = 0;
let hideTimeout = null;

// Ẩn/hiện navbar khi cuộn (chạy trên tất cả trang)
window.addEventListener('scroll', function() {
  const navbar = document.querySelector('.navbar');
  const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;

  // Xử lý ẩn/hiện navbar
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }

  if (currentScrollTop < lastScrollTop) {
    navbar.classList.remove('hidden');
  } else if (currentScrollTop > lastScrollTop && currentScrollTop > 0) {
    hideTimeout = setTimeout(() => {
      navbar.classList.add('hidden');
    }, 500);
  }

  lastScrollTop = currentScrollTop <= 0 ? 0 : currentScrollTop;
});

// Tô sáng liên kết nav (chỉ chạy trên index.html)
if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
  // Chọn các liên kết nav
  const navLinks = {
    home: document.querySelector('.nav-home'),
    about: document.querySelector('.nav-about'),
    products: document.querySelector('.nav-products'),
    media: document.querySelector('.nav-media'),
    account: document.querySelector('.nav-account')
  };

  // Chọn các phần
  const sections = {
    about: document.querySelector('#about-section'),
    media: document.querySelector('#gallery-wrapper')
  };

  // Theo dõi liên kết đang được tô sáng
  let currentHighlightedLink = null;

  // Tạo hoặc cập nhật style element cho hover và viền mặc định
  let styleElement = document.getElementById('nav-hover-styles');
  if (!styleElement) {
    styleElement = document.createElement('style');
    styleElement.id = 'nav-hover-styles';
    document.head.appendChild(styleElement);
  }

  // Đặt viền đen mặc định cho tất cả liên kết
  Object.values(navLinks).forEach(link => {
    if (link) {
      link.style.border = '1px solid black';
    }
  });

  // Đặt lại kiểu cho tất cả liên kết trừ liên kết đang được tô sáng
  function resetNavLinksExceptHighlighted(highlightedKey) {
    Object.keys(navLinks).forEach(key => {
      if (key !== highlightedKey && navLinks[key]) {
        navLinks[key].style.backgroundColor = 'rgb(255, 255, 255)';
        navLinks[key].style.color = '#000';
        navLinks[key].style.border = '1px solid black';
      }
    });
  }

  // Cập nhật hover styles cho các liên kết không được tô sáng
  function updateHoverStyles(activeSection) {
    let hoverStyles = '';
    Object.keys(navLinks).forEach(key => {
      if (key !== activeSection && navLinks[key]) {
        hoverStyles += `
          .nav-${key}:hover {
            background-color: black !important;
            color: white !important;
            border: 1px solid black !important;
          }
        `;
      }
    });
    styleElement.textContent = hoverStyles;
  }

  // Tô sáng một liên kết cụ thể
  function highlightNavLink(linkKey) {
    if (currentHighlightedLink !== linkKey) {
      resetNavLinksExceptHighlighted(linkKey);
      updateHoverStyles(linkKey);
      if (navLinks[linkKey]) {
        navLinks[linkKey].style.backgroundColor = 'black';
        navLinks[linkKey].style.color = 'white';
        navLinks[linkKey].style.border = '1px solid black';
        currentHighlightedLink = linkKey;
      }
    }
  }

  // Intersection Observer để phát hiện khi phần hiển thị
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -30% 0px',
    threshold: 0.3
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const sectionId = entry.target.id;
        if (sectionId === 'about-section') {
          highlightNavLink('about');
        } else if (sectionId === 'gallery-wrapper') {
          highlightNavLink('media');
        }
      }
    });
  }, observerOptions);

  // Quan sát tất cả phần
  Object.values(sections).forEach(section => {
    if (section) {
      observer.observe(section);
    }
  });

  // Dự phòng: Tô sáng home khi ở đầu trang, kiểm tra vị trí media
  window.addEventListener('scroll', function() {
    const mediaSection = sections.media;
    if (mediaSection) {
      const mediaRect = mediaSection.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      // Tô sáng media nếu phần này gần trung tâm khung nhìn
      if (mediaRect.top >= 0 && mediaRect.top <= windowHeight * 0.5) {
        highlightNavLink('media');
      } else if (window.pageYOffset < 100) {
        highlightNavLink('home');
      }
    } else if (window.pageYOffset < 100) {
      highlightNavLink('home');
    }
  });

  // Tô sáng ban đầu cho home nếu ở đầu trang
  if (window.pageYOffset < 100) {
    highlightNavLink('home');
  }
}