function openCategorizeModal(subscriptionId, feedTitle) {
    document.getElementById('modal-subscription-id').value = subscriptionId;
    document.getElementById('modal-feed-title').textContent = feedTitle;
    
    const form = document.getElementById('categorizeForm');
    form.action = `/feeds/${subscriptionId}/categories/`;

    document.getElementById('categorizeModal').style.display = 'block'; // makes the modal visible
    document.getElementById('existing-category-select').value = '';
    document.getElementById('new-category-input').value = '';
    
}

function closeModal() {
    document.getElementById('categorizeModal').style.display = 'none';
}

function toggleCategoryFields() {
    const choice = document.querySelector('input[name="category_choice"]:checked').value;
    const existingSelect = document.getElementById('existing-category-select');
    const newInput = document.getElementById('new-category-input');

    if (choice === 'existing') {
        existingSelect.style.display = 'block';
        newInput.style.display = 'none';
    } else {
        existingSelect.style.display = 'none';
        newInput.style.display = 'block';
    }
}

window.onclick = function(event) {
    const modal = document.getElementById('categorizeModal');
    if (event.target === modal) {
        closeModal();
    }
}
