/**
 * AuraHealth AI - Smart Nutrition & Food Tracker Controller
 * Handles dynamic search, live portion scaling previews, and AJAX meal logging.
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('foodSearchInput');
    const categorySelect = document.getElementById('categoryFilter');
    const vegFilterCheck = document.getElementById('vegFilterCheck');
    const foodResultsContainer = document.getElementById('foodSearchResults');

    // Modal elements
    const logModalElem = document.getElementById('logMealModal');
    const logModal = logModalElem ? new bootstrap.Modal(logModalElem) : null;
    
    const modalFoodId = document.getElementById('modalFoodId');
    const modalFoodName = document.getElementById('modalFoodName');
    const modalServingInfo = document.getElementById('modalServingInfo');
    const modalMultiplier = document.getElementById('modalMultiplier');
    const previewCalories = document.getElementById('previewCalories');
    const previewProtein = document.getElementById('previewProtein');
    const previewCarbs = document.getElementById('previewCarbs');
    const previewFat = document.getElementById('previewFat');

    let currentSelectedFood = null;
    let debounceTimer = null;

    // --- Dynamic Food Search Function ---
    function performFoodSearch() {
        const query = searchInput ? searchInput.value.trim() : '';
        const catId = categorySelect ? categorySelect.value : '';
        const isVeg = vegFilterCheck ? vegFilterCheck.checked : false;

        let url = `/api/v1/nutrition/search?q=${encodeURIComponent(query)}`;
        if (catId) url += `&category_id=${encodeURIComponent(catId)}`;
        if (isVeg) url += `&veg_only=true`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.status !== 'success' || !foodResultsContainer) return;

                if (data.items.length === 0) {
                    foodResultsContainer.innerHTML = `
                        <div class="col-12 text-center py-4 text-muted">
                            <i class="bi bi-search fs-3 d-block mb-2"></i>
                            <p class="small mb-2">No matching dishes found in the verified database.</p>
                            <button class="btn btn-outline-forest btn-sm" data-bs-toggle="modal" data-bs-target="#customFoodModal">
                                <i class="bi bi-plus-circle me-1"></i> Add Custom Food Item
                            </button>
                        </div>
                    `;
                    return;
                }

                foodResultsContainer.innerHTML = data.items.map(item => `
                    <div class="col-md-6 col-lg-4">
                        <div class="card h-100 border p-3 rounded-3 shadow-sm food-item-card" 
                             style="cursor: pointer; border-color: var(--color-border) !important;"
                             onclick='window.openLogModal(${JSON.stringify(item)})'>
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <h6 class="fw-bold mb-0 text-dark" style="font-size: 0.95rem;">${item.food_name}</h6>
                                    ${item.native_name ? `<small class="text-muted font-italic">(${item.native_name})</small>` : ''}
                                </div>
                                <span class="badge ${item.is_vegetarian ? 'bg-success' : 'bg-danger'} bg-opacity-10 ${item.is_vegetarian ? 'text-success' : 'text-danger'} border px-2 py-1" style="font-size: 0.7rem;">
                                    ${item.is_vegetarian ? 'Veg' : 'Non-Veg'}
                                </span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mt-auto pt-2 border-top small text-muted">
                                <span><strong class="text-forest">${item.calories}</strong> kcal</span>
                                <span>P: <strong class="text-success">${item.protein_g}g</strong></span>
                                <span>C: ${item.carbs_g}g</span>
                                <span>F: ${item.fat_g}g</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            })
            .catch(err => console.error("Search failed:", err));
    }

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(performFoodSearch, 250);
        });
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', performFoodSearch);
    }

    if (vegFilterCheck) {
        vegFilterCheck.addEventListener('change', performFoodSearch);
    }

    // --- Modal Live Macro Calculation ---
    window.openLogModal = function (item) {
        currentSelectedFood = item;
        if (!logModal) return;

        modalFoodId.value = item.id;
        modalFoodName.textContent = item.food_name;
        modalServingInfo.textContent = `Standard Portion: ${item.serving_unit} (${item.serving_size_grams}g)`;
        modalMultiplier.value = "1.0";

        updateLiveMacroPreview(1.0);
        logModal.show();
    };

    function updateLiveMacroPreview(multiplier) {
        if (!currentSelectedFood) return;

        const mult = parseFloat(multiplier) || 1.0;
        previewCalories.textContent = (currentSelectedFood.calories * mult).toFixed(1);
        previewProtein.textContent = (currentSelectedFood.protein_g * mult).toFixed(1) + 'g';
        previewCarbs.textContent = (currentSelectedFood.carbs_g * mult).toFixed(1) + 'g';
        previewFat.textContent = (currentSelectedFood.fat_g * mult).toFixed(1) + 'g';
    }

    if (modalMultiplier) {
        modalMultiplier.addEventListener('input', (e) => {
            updateLiveMacroPreview(e.target.value);
        });
    }

    // Quick multiplier buttons (.btn-portion)
    const portionButtons = document.querySelectorAll('.btn-portion');
    portionButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            portionButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const val = btn.getAttribute('data-value');
            if (modalMultiplier) {
                modalMultiplier.value = val;
                updateLiveMacroPreview(val);
            }
        });
    });

    // Initial search load
    performFoodSearch();
});
