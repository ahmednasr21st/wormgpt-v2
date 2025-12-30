// subscribe.js
document.addEventListener('DOMContentLoaded', () => {
    const monthlyBtn = document.getElementById('monthlyBtn');
    const yearlyBtn = document.getElementById('yearlyBtn');
    const planPrices = document.querySelectorAll('.plan-card .price');
    const subscribeBtns = document.querySelectorAll('.plan-button.subscribe-btn');

    function updatePrices(isYearly) {
        planPrices.forEach(priceElement => {
            const monthlyPrice = priceElement.dataset.monthly;
            const yearlyPrice = priceElement.dataset.yearly;
            const displayedPrice = isYearly ? yearlyPrice : monthlyPrice;
            priceElement.querySelector('span').textContent = displayedPrice;
            priceElement.innerHTML = `<span>${displayedPrice}</span> / ${isYearly ? 'year' : 'month'}`;
        });
    }

    monthlyBtn.addEventListener('click', () => {
        monthlyBtn.classList.add('active');
        yearlyBtn.classList.remove('active');
        updatePrices(false);
    });

    yearlyBtn.addEventListener('click', () => {
        yearlyBtn.classList.add('active');
        monthlyBtn.classList.remove('active');
        updatePrices(true);
    });

    // Initial price set to monthly
    updatePrices(false);

    subscribeBtns.forEach(button => {
        button.addEventListener('click', (e) => {
            const plan = e.target.dataset.plan;
            const period = monthlyBtn.classList.contains('active') ? 'monthly' : 'yearly';
            const priceElement = e.target.closest('.plan-card').querySelector('.price');
            const price = priceElement.querySelector('span').textContent; // Get current displayed price

            alert(`You selected the ${plan.toUpperCase()} plan (${period}) for ${price}. Proceeding to cryptocurrency payment gateway... (This is a mock payment for demonstration)`);

            // In a real application, this would redirect to a payment processor
            // Example: window.location.href = `/payment/initiate?plan=${plan}&period=${period}`;
        });
    });

    // Logout functionality (reused from auth.js, ensure auth.js is loaded)
    const logoutBtnSub = document.getElementById('logoutBtnSub');
    if (logoutBtnSub) {
        logoutBtnSub.addEventListener('click', async (e) => {
            e.preventDefault();
            localStorage.removeItem('token');
            window.location.href = 'index.html';
        });
    }
});
