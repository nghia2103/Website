const rangeInput = document.getElementById('price-range');
const priceValue = document.querySelector('.price-values');
const categoryLinks = document.querySelectorAll('.sidebar a[data-category]');
const modal = document.getElementById('productModal');
const modalClose = document.querySelector('.modal-close');
const mainImage = document.getElementById('mainImage');
const thumbnailList = document.getElementById('thumbnailList');
const productTitle = document.getElementById('productTitle');
const productSKU = document.getElementById('productSKU');
const currentPrice = document.getElementById('currentPrice');
const originalPrice = document.getElementById('originalPrice');
const discount = document.getElementById('discount');
const productDescription = document.getElementById('productDescription');
const quantityInput = document.getElementById('quantityInput');
const sizeSelect = document.getElementById('sizeSelect');
const minusBtn = document.querySelector('.quantity-minus');
const plusBtn = document.querySelector('.quantity-plus');
const addToCartBtn = document.querySelector('.add-to-cart');
const buyNowBtn = document.querySelector('.buy-now');
const cartBtn = document.getElementById('cartBtn');
const cartPopup = document.getElementById('cartPopup');
const cartOverlay = document.getElementById('cartOverlay');
const cartClose = document.querySelector('.cart-close');
const cartItems = document.getElementById('cartItems');
const cartEmpty = document.getElementById('cartEmpty');
const totalPrice = document.getElementById('totalPrice');
const checkoutBtn = document.getElementById('checkoutBtn');
const sortSelect = document.getElementById('sortSelect');
const togglePriceFilterBtn = document.querySelector('.toggle-price-filter');
const priceFilterSection = document.querySelector('.price-filter-section');
const reviewsList = document.querySelector('.reviews-list');
const noReviews = document.querySelector('.no-reviews');
const noReviewsMessage = document.querySelector('.no-reviews-message');
const showReviewsBtn = document.querySelector('.show-reviews-btn');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const pageInfo = document.getElementById('pageInfo');

let selectedCategory = 'all';
let cart = [];
let reviews = {};
let originalOrder = [];
let products = {};
let sizeMap = {};
let currentPage = 1;
const productsPerPage = 12;

const categoryMap = {
    'all': 'all',
    'coffees': 'Coffees',
    'drinks': 'Drinks',
    'foods': 'Foods',
    'yogurts': 'Yogurts',
    'top10': 'top10'
};

async function fetchProducts() {
    try {
        console.log('Đang lấy dữ liệu sản phẩm từ /api/products...');
        const response = await fetch('/api/products', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

        const data = await response.json();
        console.log('Dữ liệu sản phẩm nhận được:', JSON.stringify(data, null, 2));

        let productsData = Array.isArray(data) ? data : data.products;
        if (!Array.isArray(productsData)) {
            console.error('Dữ liệu không phải là mảng:', productsData);
            throw new Error('Dữ liệu sản phẩm không đúng định dạng mảng');
        }

        if (productsData.length === 0) {
            console.warn('Không có sản phẩm nào từ API');
            const productGrid = document.querySelector('.product-grid');
            if (productGrid) {
                productGrid.innerHTML = '<p>Không có sản phẩm nào để hiển thị.</p>';
            }
            return;
        }

        products = {};
        sizeMap = {};
        productsData.forEach(product => {
            const defaultSize = product.sizes.find(s => s.size === 'S') || product.sizes[0] || { price: 0, size_id: '' };
            const discountedPrice = product.discount ? defaultSize.price * (1 - product.discount / 100) : defaultSize.price;
            products[product.product_id] = {
                title: product.product_name,
                sku: product.product_id.toUpperCase(),
                originalPrice: defaultSize.price,
                currentPrice: discountedPrice,
                discount: product.discount || 0,
                description: product.description || 'Không có mô tả.',
                defaultImg: product.image_url || 'https://via.placeholder.com/600',
                hoverImg: product.image_url_2 || product.image_url || 'https://via.placeholder.com/600',
                stock: product.stock,
                category: (product.category || 'others').toLowerCase(),
                priceValue: discountedPrice,
                sizes: product.sizes.map(s => ({
                    size: s.size,
                    size_id: s.size_id,
                    price: s.price,
                    discountedPrice: product.discount ? s.price * (1 - product.discount / 100) : s.price
                })),
                availableSizes: product.sizes.map(s => s.size)
            };
            product.sizes.forEach(s => {
                sizeMap[`${product.product_id}-${s.size}`] = s.size_id;
            });
        });

        if (selectedCategory === 'top10') {
            await fetchTop10Products();
        } else {
            updateProductCards(productsData);
        }
    } catch (error) {
        console.error('Lỗi khi lấy sản phẩm:', error.message, error.stack);
        const productGrid = document.querySelector('.product-grid');
        if (productGrid) {
            productGrid.innerHTML = `<p>Lỗi khi tải sản phẩm: ${error.message}. Vui lòng thử lại sau.</p>`;
        }
    }
}

async function fetchTop10Products() {
    try {
        console.log('Đang lấy top 10 sản phẩm bán chạy từ /api/top10products...');
        const response = await fetch('/api/top10products', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        console.log('Top 10 sản phẩm nhận được:', data);

        if (!Array.isArray(data) || data.length === 0) {
            console.warn('Không có sản phẩm top 10 nào từ API');
            const productGrid = document.querySelector('.product-grid');
            if (productGrid) {
                productGrid.innerHTML = '<p>Không có sản phẩm top 10 nào để hiển thị.</p>';
            }
            return;
        }

        updateProductCards(data);
    } catch (error) {
        console.error('Lỗi khi lấy top 10 sản phẩm:', error);
        const productGrid = document.querySelector('.product-grid');
        if (productGrid) {
            productGrid.innerHTML = '<p>Lỗi khi tải top 10 sản phẩm. Vui lòng thử lại sau.</p>';
        }
    }
}

async function fetchReviews(productId) {
    try {
        console.log(`Đang lấy đánh giá cho product_id: ${productId}`);
        const response = await fetch(`/api/reviews/product/${productId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        console.log('Dữ liệu đánh giá nhận được:', data);

        reviews[productId] = data.map(review => ({
            name: review.customer_name || 'Anonymous',
            email: 'N/A',
            date: review.review_date ? new Date(review.review_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : new Date().toLocaleDateString('en-US'),
            rating: review.rating || 0,
            title: review.comment || 'No Title',
            content: review.comment || 'No comment',
            image: review.review_img || null
        }));
    } catch (error) {
        console.error('Lỗi khi lấy đánh giá:', error);
        reviews[productId] = [];
    }
}

function displayReviews(productId) {
    reviewsList.innerHTML = '';
    if (reviews[productId] && reviews[productId].length > 0) {
        noReviews.style.display = 'none';
        noReviewsMessage.style.display = 'none';
        reviewsList.style.display = 'block';
        reviews[productId].forEach(review => {
            const reviewDiv = document.createElement('div');
            reviewDiv.className = 'review';
            reviewDiv.innerHTML = `
                <div class="review-header">
                    <span class="reviewer">${review.name}</span>
                    <span class="review-date">${review.date}</span>
                    <span class="review-rating">${'★'.repeat(review.rating)}</span>
                </div>
                <h3 class="review-title">${review.title}</h3>
                <p class="review-content">${review.content}</p>
                ${review.image ? `<img src="${review.image}" alt="Review Image" style="max-width: 100px; margin-top: 10px;">` : ''}
            `;
            reviewsList.appendChild(reviewDiv);
        });
    } else {
        noReviews.style.display = 'block';
        noReviewsMessage.style.display = 'flex';
        reviewsList.style.display = 'none';
    }
}

function updateProductCards(data) {
    const productGrid = document.querySelector('.product-grid');
    if (!productGrid) {
        console.error('Invalid .product-grid');
        return;
    }
    productGrid.innerHTML = '';
    originalOrder = [];

    console.log('Rendering products:', data);
    data.forEach(product => {
        const category = (product.category || '').toLowerCase();
        const defaultSize = product.sizes.find(s => s.size === 'S') || product.sizes[0] || { price: 0 };
        const discountedPrice = product.discount ? defaultSize.price * (1 - product.discount / 100) : defaultSize.price;
        const availableSizes = product.sizes.map(s => s.size);

        const card = document.createElement('div');
        card.className = 'product-card';
        card.dataset.price = discountedPrice;
        card.dataset.category = product.category;
        card.dataset.sizes = JSON.stringify(availableSizes);
        card.dataset.defaultImg = product.image_url || 'https://via.placeholder.com/200';
        card.dataset.hoverImg = product.image_url_2 || product.image_url || 'https://via.placeholder.com/200';
        card.dataset.productId = product.product_id;
        card.dataset.date = new Date().toISOString().split('T')[0];
        card.innerHTML = `
            <div class="image-container">
                <img src="${product.image_url || 'https://via.placeholder.com/200'}" alt="${product.product_id}">
            </div>
            <p>${product.product_name}</p>
            <div class="price">₫${discountedPrice.toLocaleString('vi-VN')}</div>
        `;
        productGrid.appendChild(card);
        originalOrder.push(card);

        const img = card.querySelector('img');
        card.addEventListener('mouseenter', () => {
            if (card.dataset.hoverImg && img.src !== card.dataset.hoverImg) {
                img.src = card.dataset.hoverImg;
            }
        });
        card.addEventListener('mouseleave', () => {
            if (card.dataset.defaultImg && img.src !== card.dataset.defaultImg) {
                img.src = card.dataset.defaultImg;
            }
        });
        card.addEventListener('click', async () => {
            const productId = card.dataset.productId;
            const product = products[productId];

            if (product && modal) {
                productTitle.textContent = product.title;
                productSKU.textContent = `SKU: ${product.sku}`;
                currentPrice.textContent = `₫${product.currentPrice.toLocaleString('vi-VN')}`;
                originalPrice.textContent = `₫${product.originalPrice.toLocaleString('vi-VN')}`;
                discount.textContent = product.discount ? `${product.discount}% OFF` : '0% OFF';
                productDescription.textContent = product.description;

                sizeSelect.innerHTML = '<option value="" disabled selected="true">Select</option>';
                product.sizes.forEach(size => {
                    const option = document.createElement('option');
                    option.value = size.size_id;
                    option.textContent = `${size.size} - ₫${size.discountedPrice.toLocaleString('vi-VN')}`;
                    sizeSelect.appendChild(option);
                });

                thumbnailList.innerHTML = '';
                const thumbnails = [
                    { src: card.dataset.defaultImg, full: card.dataset.defaultImg },
                    { src: card.dataset.hoverImg, full: card.dataset.hoverImg },
                ];
                thumbnails.forEach((thumb, index) => {
                    const img = document.createElement('img');
                    img.src = thumb.src;
                    img.setAttribute('data-full', thumb.full);
                    img.alt = `Thumbnail ${index + 1}`;
                    if (index === 0) img.classList.add('selected');
                    thumbnailList.appendChild(img);
                });

                mainImage.src = thumbnails[0].full;
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
                quantityInput.value = '1';
                sizeSelect.value = '';

                // Reset review display to be hidden by default
                reviewsList.style.display = 'none';
                noReviews.style.display = 'block';
                noReviewsMessage.style.display = 'flex';
            }
        });
    });

    filterProducts();
    console.log('Number of .product-card elements:', originalOrder.length);
}

function sortProducts(cards, sortBy) {
    const sortedCards = Array.from(cards);
    if (sortBy === 'recommended') {
        return originalOrder.filter(card => sortedCards.includes(card));
    } else if (sortBy === 'newest') {
        return sortedCards.sort((a, b) => new Date(b.dataset.date) - new Date(a.dataset.date));
    } else if (sortBy === 'price-low') {
        return sortedCards.sort((a, b) => parseFloat(a.dataset.price) - parseFloat(b.dataset.price));
    } else if (sortBy === 'price-high') {
        return sortedCards.sort((a, b) => parseFloat(b.dataset.price) - parseFloat(a.dataset.price));
    } else if (sortBy === 'name-asc') {
        return sortedCards.sort((a, b) => a.querySelector('p').textContent.localeCompare(b.querySelector('p').textContent));
    } else if (sortBy === 'name-desc') {
        return sortedCards.sort((a, b) => b.querySelector('p').textContent.localeCompare(a.querySelector('p').textContent));
    }
    return sortedCards;
}

function filterProducts() {
    const selectedPrice = parseInt(rangeInput.value);
    const sortBy = sortSelect.value;
    const mappedCategory = categoryMap[selectedCategory] || selectedCategory;

    if (priceValue) {
        priceValue.querySelector('span:last-child').textContent = `₫${selectedPrice.toLocaleString('vi-VN')}`;
    }

    let filteredCards = originalOrder.filter(card => {
        const price = parseFloat(card.dataset.price);
        const category = card.dataset.category.toLowerCase();
        const matchesCategory = mappedCategory === 'all' || mappedCategory === 'top10' || category === mappedCategory.toLowerCase();
        const matchesPrice = price <= selectedPrice;
        return matchesCategory && matchesPrice;
    });

    const sortedCards = sortProducts(filteredCards, sortBy);

    const productGrid = document.querySelector('.product-grid');
    if (productGrid) {
        productGrid.innerHTML = '';
        const totalProducts = sortedCards.length;
        const totalPages = Math.ceil(totalProducts / productsPerPage);
        currentPage = Math.min(currentPage, totalPages || 1);

        const startIndex = (currentPage - 1) * productsPerPage;
        const endIndex = startIndex + productsPerPage;
        const paginatedCards = sortedCards.slice(startIndex, endIndex);

        if (paginatedCards.length === 0) {
            productGrid.innerHTML = `<p>No products found in category "${selectedCategory === 'all' ? 'All' : selectedCategory === 'top10' ? 'Top 10 Best Sellers' : mappedCategory}".</p>`;
        } else {
            paginatedCards.forEach(card => productGrid.appendChild(card));
        }

        updatePaginationControls(totalProducts, totalPages);
    }

    console.log('Selected category:', selectedCategory, 'Mapped:', mappedCategory);
    console.log('Max price:', selectedPrice);
    console.log(`Displayed ${filteredCards.length} products on page ${currentPage}`);
}

function updatePaginationControls(totalProducts, totalPages) {
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    } else {
        console.warn('Element with id="pageInfo" not found');
    }
    if (prevPageBtn) {
        prevPageBtn.disabled = currentPage === 1;
    } else {
        console.warn('Element with id="prevPage" not found');
    }
    if (nextPageBtn) {
        nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
    } else {
        console.warn('Element with id="nextPage" not found');
    }
}

async function fetchCart() {
    try {
        console.log('Fetching cart from /api/cart...');
        const response = await fetch('/api/cart', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const cartData = await response.json();
        console.log('Cart data received:', cartData);
        return cartData;
    } catch (error) {
        console.error('Error fetching cart:', error);
        return [];
    }
}

async function updateCart() {
    cart = await fetchCart();
    cartItems.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        cartEmpty.style.display = 'flex';
        totalPrice.style.display = 'none';
        checkoutBtn.style.display = 'none';
    } else {
        cartEmpty.style.display = 'none';
        totalPrice.style.display = 'block';
        checkoutBtn.style.display = 'block';
        cart.forEach((item, index) => {
            const cartItem = document.createElement('div');
            cartItem.className = 'cart-item';
            cartItem.innerHTML = `
                <input type="checkbox" class="cart-checkbox" data-cart-id="${item.cart_id}" checked>
                <img src="${item.image_url || 'https://via.placeholder.com/50'}" alt="${item.product_name}">
                <div class="cart-details">
                    <span>${item.product_name} (${item.size}, x${item.quantity})</span>
                    <span>₫${(parseFloat(item.discounted_price) * item.quantity).toLocaleString('vi-VN')}</span>
                    <button type="button" class="remove-cart-item" data-index="${index}" data-cart-id="${item.cart_id}">×</button>
                </div>
            `;
            cartItems.appendChild(cartItem);
            total += parseFloat(item.discounted_price) * item.quantity;
        });
    }

    cartBtn.querySelector('span').textContent = `Cart (${cart.reduce((sum, item) => sum + item.quantity, 0)})`;
    totalPrice.textContent = `Total: ₫${total.toLocaleString('vi-VN')}`;
}

function addToCartAPI(productId, quantity, sizeId, callback) {
    if (!sizeId) {
        callback(new Error('Invalid size selected'));
        return;
    }
    fetch('/api/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: quantity, size_id: sizeId })
    })
    .then(res => {
        if (res.status === 401) {
            window.location.href = '/login';
            return Promise.reject(new Error('User not logged in'));
        }
        return res.json();
    })
    .then(data => {
        console.log('API cart response:', data);
        callback(null, data);
    })
    .catch(err => {
        console.error('Error adding to cart:', err);
        callback(err);
    });
}

function removeFromCartAPI(cartId, callback) {
    fetch('/api/cart/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_id: cartId })
    })
    .then(res => res.json())
    .then(data => {
        console.log('API remove cart response:', data);
        callback(null, data);
    })
    .catch(err => {
        console.error('Error removing from cart:', err);
        callback(err);
    });
}

function buyNowByAPI(productId, quantity, sizeId) {
    if (!sizeId) {
        alert('Please select a size!');
        return;
    }
    addToCartAPI(productId, quantity, sizeId, async (err, data) => {
        if (!err && data.message === 'Đã thêm vào giỏ hàng') {
            try {
                // Kiểm tra giỏ hàng để xác nhận sản phẩm đã được thêm
                const cartResponse = await fetch('/api/cart', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                if (!cartResponse.ok) {
                    throw new Error(`Lỗi khi lấy giỏ hàng: ${cartResponse.status}`);
                }
                const cartData = await cartResponse.json();
                if (cartData.length === 0) {
                    alert('Giỏ hàng trống! Vui lòng thử lại.');
                    return;
                }
                // Chuyển hướng tới trang checkout
                window.location.href = '/checkout';
            } catch (error) {
                console.error('Lỗi khi kiểm tra giỏ hàng:', error);
                alert('Lỗi khi kiểm tra giỏ hàng. Vui lòng thử lại!');
            }
        } else if (err && err.message === 'User not logged in') {
            // Không cần alert vì đã chuyển hướng đến trang đăng nhập
        } else {
            alert('Lỗi khi thêm vào giỏ hàng. Vui lòng thử lại!');
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    await fetchProducts();

    categoryLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            categoryLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            selectedCategory = link.dataset.category;
            currentPage = 1;
            if (selectedCategory === 'top10') {
                await fetchTop10Products();
            } else {
                await fetchProducts();
            }
        });
    });

    if (rangeInput) {
        rangeInput.addEventListener('input', () => {
            currentPage = 1;
            filterProducts();
        });
    } else {
        console.error('rangeInput element not found');
    }

    sortSelect.addEventListener('change', () => {
        currentPage = 1;
        filterProducts();
    });

    togglePriceFilterBtn.addEventListener('click', () => {
        priceFilterSection.classList.toggle('expanded');
        togglePriceFilterBtn.textContent = priceFilterSection.classList.contains('expanded') ? '−' : '+';
    });

    modalClose.addEventListener('click', () => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    thumbnailList.addEventListener('click', (e) => {
        if (e.target.tagName === 'IMG') {
            const newSrc = e.target.getAttribute('data-full');
            if (newSrc) {
                mainImage.src = newSrc;
                thumbnailList.querySelectorAll('img').forEach(img => img.classList.remove('selected'));
                e.target.classList.add('selected');
            }
        }
    });

    function updateQuantity() {
        let value = parseInt(quantityInput.value);
        if (isNaN(value) || value < 1) {
            value = 1;
        } else if (value > 10) {
            value = 10;
        }
        quantityInput.value = value;
    }

    minusBtn.addEventListener('click', () => {
        let value = parseInt(quantityInput.value);
        if (value > 1) {
            quantityInput.value = value - 1;
        }
    });

    plusBtn.addEventListener('click', () => {
        let value = parseInt(quantityInput.value);
        if (value < 10) {
            quantityInput.value = value + 1;
        }
    });

    quantityInput.addEventListener('change', updateQuantity);
    quantityInput.addEventListener('input', updateQuantity);

    sizeSelect.addEventListener('change', () => {
        const selectedSizeId = sizeSelect.value;
        const productId = originalOrder.find(card => card.querySelector('p').textContent === productTitle.textContent)?.dataset.productId;
        if (!productId) return;
        const product = products[productId];
        const selectedSizeData = product.sizes.find(s => s.size_id === selectedSizeId);
        if (selectedSizeData) {
            currentPrice.textContent = `₫${selectedSizeData.discountedPrice.toLocaleString('vi-VN')}`;
            originalPrice.textContent = `₫${selectedSizeData.price.toLocaleString('vi-VN')}`;
        } else {
            const defaultSize = product.sizes.find(s => s.size === 'S') || product.sizes[0];
            currentPrice.textContent = `₫${defaultSize.discountedPrice.toLocaleString('vi-VN')}`;
            originalPrice.textContent = `₫${defaultSize.price.toLocaleString('vi-VN')}`;
        }
    });

    addToCartBtn.addEventListener('click', () => {
        const quantity = parseInt(quantityInput.value);
        const sizeId = sizeSelect.value;
        if (!sizeId) {
            alert('Please select a size!');
            return;
        }
        const productId = originalOrder.find(card => card.querySelector('p').textContent === productTitle.textContent)?.dataset.productId;
        if (!productId) {
            alert('Product not found!');
            return;
        }
        addToCartAPI(productId, quantity, sizeId, async (err, data) => {
            if (!err) {
                await updateCart();
                alert(`Added ${quantity} ${products[productId].title} to cart!`);
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            } else if (err.message === 'User not logged in') {
            } else {
                alert('Error adding to cart. Please try again!');
            }
        });
    });

    buyNowBtn.addEventListener('click', () => {
        const qty = parseInt(quantityInput.value);
        const sizeId = sizeSelect.value;
        if (!sizeId) {
            alert('Please select a size!');
            return;
        }
        const productId = originalOrder.find(card => card.querySelector('p').textContent === productTitle.textContent)?.dataset.productId;
        if (!productId) {
            alert('Product not found!');
            return;
        }
        buyNowByAPI(productId, qty, sizeId);
    });

    cartBtn.addEventListener('click', async () => {
        cartPopup.style.display = 'block';
        cartOverlay.style.display = 'block';
        cartBtn.style.display = 'none';
        document.body.classList.add('cart-open');
        cartPopup.classList.add('show');
        await updateCart();
    });

    cartClose.addEventListener('click', () => {
        cartPopup.classList.remove('show');
        setTimeout(() => {
            cartPopup.style.display = 'none';
            cartOverlay.style.display = 'none';
            cartBtn.style.display = 'flex';
            document.body.classList.remove('cart-open');
        }, 300);
    });

    cartOverlay.addEventListener('click', () => {
        cartPopup.classList.remove('show');
        setTimeout(() => {
            cartPopup.style.display = 'none';
            cartOverlay.style.display = 'none';
            cartBtn.style.display = 'flex';
            document.body.classList.remove('cart-open');
        }, 300);
    });

    cartItems.addEventListener('click', async (e) => {
        if (e.target.classList.contains('remove-cart-item')) {
            const cartId = e.target.dataset.cartId;
            removeFromCartAPI(cartId, async (err) => {
                if (!err) {
                    await updateCart();
                    alert('Item removed from cart!');
                } else {
                    alert('Error removing item. Please try again!');
                }
            });
        }
    });

    checkoutBtn.addEventListener('click', async () => {
        const selectedItems = Array.from(document.querySelectorAll('.cart-checkbox:checked')).map(checkbox => ({
            cart_id: checkbox.dataset.cartId
        }));
        if (selectedItems.length === 0) {
            alert('Please select at least one item to checkout!');
            return;
        }
        const cartData = cart.filter(item => selectedItems.some(selected => selected.cart_id === item.cart_id)).map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            size_id: item.size_id
        }));
        try {
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cartData)
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const data = await response.json();
            console.log('Checkout response:', data);
            window.location.href = '/checkout';
        } catch (err) {
            console.error('Checkout error:', err);
            alert('Checkout error. Please try again!');
        }
        cartPopup.classList.remove('show');
        setTimeout(() => {
            cartPopup.style.display = 'none';
            cartOverlay.style.display = 'none';
            cartBtn.style.display = 'flex';
            document.body.classList.remove('cart-open');
        }, 300);
    });

    showReviewsBtn.addEventListener('click', async () => {
        const productId = originalOrder.find(card => card.querySelector('p').textContent === productTitle.textContent)?.dataset.productId;
        if (!productId) {
            console.error('Product ID not found for reviews');
            return;
        }
        await fetchReviews(productId);
        displayReviews(productId);
    });

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            filterProducts();
        }
    });

    nextPageBtn.addEventListener('click', () => {
        const totalProducts = sortProducts(originalOrder, sortSelect.value).length;
        const totalPages = Math.ceil(totalProducts / productsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            filterProducts();
        }
    });
});