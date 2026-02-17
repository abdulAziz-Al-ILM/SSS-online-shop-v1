const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

let allProducts = [];
let cart = [];
let currentProduct = null;
let currentQty = 1;

// 1. Dastur ishga tushganda
async function init() {
    try {
        const res = await fetch('/api/products');
        allProducts = await res.json();
        renderGrid(allProducts);
    } catch (e) {
        tg.showAlert("Internet bilan aloqa yo'q yoki server ishlamayapti.");
    }
}

// 2. Mahsulotlarni chizish
function renderGrid(products) {
    const grid = document.getElementById('products-grid');
    if (products.length === 0) {
        grid.innerHTML = "<p style='grid-column: 1/-1; text-align:center; color:#888'>Mahsulotlar topilmadi.</p>";
        return;
    }
    grid.innerHTML = products.map(p => `
        <div class="card" onclick="openProductModal('${p._id}')">
            <img src="${p.image_url}" onerror="this.src='https://via.placeholder.com/400x400?text=No+Image'">
            <div class="card-info">
                <div>
                    <h3 class="card-title">${p.name}</h3>
                    <p class="card-price">${p.price.toLocaleString()} so'm</p>
                </div>
                <button class="card-btn">Savatga</button>
            </div>
        </div>
    `).join('');
}

// 3. Qidiruv
function filterProducts() {
    const query = document.getElementById('search').value.toLowerCase();
    const filtered = allProducts.filter(p => p.name.toLowerCase().includes(query));
    renderGrid(filtered);
}

// 4. Mahsulot oynasini ochish (MODAL)
function openProductModal(id) {
    currentProduct = allProducts.find(p => p._id === id);
    currentQty = 1; // Har doim 1 dan boshlanadi
    
    document.getElementById('pm-img').src = currentProduct.image_url || 'https://via.placeholder.com/400';
    document.getElementById('pm-title').innerText = currentProduct.name;
    document.getElementById('pm-price').innerText = currentProduct.price.toLocaleString() + " so'm";
    document.getElementById('pm-desc').innerText = currentProduct.description || "Tavsif mavjud emas.";
    
    // INPUTGA QIYMAT YOZAMIZ
    document.getElementById('pm-qty').value = currentQty;
    
    const tagsDiv = document.getElementById('pm-tags');
    tagsDiv.innerHTML = (currentProduct.tags || []).map(t => `<span class="tag">#${t}</span>`).join('');

    document.getElementById('product-modal').classList.remove('hidden');
}

function closeProductModal() {
    document.getElementById('product-modal').classList.add('hidden');
}

// YANGI: Input qiymatini o'zgartirish (+/- tugmalari uchun)
function changeModalQty(delta) {
    const input = document.getElementById('pm-qty');
    let val = parseInt(input.value) || 0;
    val += delta;
    if (val < 1) val = 1;
    
    // Ombordagi sondan oshib ketmasligi kerak (ixtiyoriy)
    if (currentProduct.stock && val > currentProduct.stock) {
        val = currentProduct.stock;
        tg.showAlert(`Omborda faqat ${val} ta qoldi!`);
    }
    
    input.value = val;
    currentQty = val;
}

// YANGI: Qo'lda yozganda tekshirish
function validQty(el) {
    if (el.value === "") return; 
    let val = parseInt(el.value);
    if (val < 1) val = 1;
    // Stock tekshiruvi
    if (currentProduct && currentProduct.stock && val > currentProduct.stock) {
        val = currentProduct.stock;
    }
    currentQty = val;
}

// Savatga qo'shish (Inputdagi raqamni oladi)
function addToCartFromModal() {
    const input = document.getElementById('pm-qty');
    currentQty = parseInt(input.value); 
    
    if (!currentQty || currentQty < 1) currentQty = 1;

    const existing = cart.find(i => i._id === currentProduct._id);
    if (existing) {
        existing.qty += currentQty;
    } else {
        cart.push({...currentProduct, qty: currentQty});
    }
    updateCartIcon();
    closeProductModal();
    tg.HapticFeedback.notificationOccurred('success');
}

// 5. Savat mantiqi
function updateCartIcon() {
    const count = cart.reduce((sum, item) => sum + item.qty, 0);
    const badge = document.getElementById('cart-badge');
    badge.innerText = count;
    badge.classList.toggle('hidden', count === 0);
}

function openCartModal() {
    renderCartItems();
    document.getElementById('cart-modal').classList.remove('hidden');
}

function closeCartModal() {
    document.getElementById('cart-modal').classList.add('hidden');
}

function renderCartItems() {
    const container = document.getElementById('cart-items-list');
    let total = 0;
    
    container.innerHTML = cart.map((item, index) => {
        total += item.price * item.qty;
        return `
            <div class="cart-item">
                <img src="${item.image_url}">
                <div class="cart-info">
                    <div style="font-weight:bold">${item.name}</div>
                    <div style="color:var(--primary); font-size:12px;">${item.price.toLocaleString()} so'm</div>
                </div>
                <div class="cart-actions">
                    <button onclick="updateCartQty(${index}, -1)">-</button>
                    <span>${item.qty}</span>
                    <button onclick="updateCartQty(${index}, 1)">+</button>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('cart-total-price').innerText = total.toLocaleString() + " so'm";
    document.getElementById('cart-total-items').innerText = `(${cart.length})`;
    
    if (cart.length === 0) container.innerHTML = "<p style='text-align:center; color:#888; padding:20px;'>Savatingiz bo'sh</p>";
}

function updateCartQty(index, delta) {
    cart[index].qty += delta;
    if (cart[index].qty <= 0) cart.splice(index, 1);
    renderCartItems();
    updateCartIcon();
}

// 6. Buyurtmani rasmiylashtirish
function openCheckout() {
    if (cart.length === 0) return;
    closeCartModal();
    document.getElementById('checkout-modal').classList.remove('hidden');
}

function updatePaymentMethods() {
    const type = document.querySelector('input[name="delivery"]:checked').value;
    const select = document.getElementById('payment-method');
    select.innerHTML = "";
    
    if (type === 'taxi') {
        select.add(new Option("Karta orqali", "card"));
        select.add(new Option("Nasiya savdo (Qarz)", "credit"));
    } else {
        select.add(new Option("Naqd to'lov", "cash"));
        select.add(new Option("Karta orqali", "card"));
    }
}

function submitOrder() {
    const phone = document.getElementById('phone').value;
    if (phone.length < 7) {
        tg.showAlert("Iltimos, telefon raqamingizni to'g'ri kiriting!");
        return;
    }
    
    const data = {
        cart: cart,
        delivery: document.querySelector('input[name="delivery"]:checked').value,
        payment: document.getElementById('payment-method').value,
        phone: phone,
        total_sum: document.getElementById('cart-total-price').innerText,
        user_id: tg.initDataUnsafe?.user?.id
    };
    
    tg.sendData(JSON.stringify(data));
    tg.close();
}

// Ilovani ishga tushirish
init();
