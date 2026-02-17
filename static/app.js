let tg = window.Telegram.WebApp;
tg.expand(); // Fullscreen

let cart = [];
let products = [];

// 1. Mahsulotlarni yuklash
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        products = await response.json();
        renderProducts(products);
    } catch (error) {
        console.error("Xatolik:", error);
    }
}

function renderProducts(list) {
    const grid = document.getElementById('products-grid');
    grid.innerHTML = "";
    
    list.forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-card';
        // Rasm: Agar admin rasm yuklagan bo'lsa URL, bo'lmasa placeholder
        const imgUrl = product.image_url || 'https://via.placeholder.com/150'; 
        
        card.innerHTML = `
            <img src="${imgUrl}" class="product-img">
            <div class="product-info">
                <h4>${product.name}</h4>
                <div class="price">${product.price.toLocaleString()} so'm</div>
                <button class="btn-add" onclick="addToCart('${product._id}')">Savatga</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// 2. Savat funksiyalari
function addToCart(productId) {
    const product = products.find(p => p._id === productId);
    const existing = cart.find(i => i._id === productId);
    
    if (existing) {
        existing.qty++;
    } else {
        cart.push({...product, qty: 1});
    }
    
    updateCartUI();
    tg.HapticFeedback.impactOccurred('light'); // Telefonda titrash beradi
}

function updateCartUI() {
    document.getElementById('cart-count').innerText = cart.reduce((a, b) => a + b.qty, 0);
}

// 3. Checkout logikasi
function proceedToCheckout() {
    document.getElementById('cart-modal').classList.add('hidden');
    document.getElementById('checkout-modal').classList.remove('hidden');
}

function togglePayment(type) {
    const select = document.getElementById('payment-method');
    select.innerHTML = "";
    
    if (type === 'taxi') {
        // Taxi bo'lsa: Karta yoki Nasiya
        select.add(new Option("Karta orqali", "card"));
        select.add(new Option("Nasiya (Qarzga)", "credit"));
    } else {
        // Olib ketish: Naqd yoki Karta
        select.add(new Option("Naqd to'lov", "cash"));
        select.add(new Option("Karta orqali", "card"));
    }
}

function submitOrder() {
    const deliveryType = document.querySelector('input[name="delivery"]:checked').value;
    const paymentType = document.getElementById('payment-method').value;
    const phone = document.getElementById('user-phone').value;

    if (!phone) {
        tg.showAlert("Iltimos, telefon raqamingizni kiriting!");
        return;
    }

    const orderData = {
        cart: cart,
        delivery: deliveryType,
        payment: paymentType,
        phone: phone,
        user_id: tg.initDataUnsafe?.user?.id
    };

    // Botga ma'lumot yuborish
    tg.sendData(JSON.stringify(orderData));
    tg.close();
}

// Dastur yuklanganda
loadProducts();
