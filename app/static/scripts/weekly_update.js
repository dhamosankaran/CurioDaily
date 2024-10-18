document.addEventListener('DOMContentLoaded', function() {
    const readMoreLinks = document.querySelectorAll('.read-more');
    
    readMoreLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const updateId = this.getAttribute('data-id');
            fetchFullUpdate(updateId);
        });
    });
});

function fetchFullUpdate(updateId) {
    fetch(`/api/newsletters/${updateId}`)
        .then(response => response.json())
        .then(data => {
            displayFullUpdate(data);
        })
        .catch(error => console.error('Error:', error));
}

function displayFullUpdate(updateData) {
    // Create and show a modal or expand the current card with full content
    // This is a placeholder for the actual implementation
    alert(`Full update: ${updateData.title}\n\n${updateData.content}`);
}