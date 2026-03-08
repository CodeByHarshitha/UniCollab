// UniCollab Global JS Config
document.addEventListener("DOMContentLoaded", () => {
    // Add glowing hover effects dynamically
    const cards = document.querySelectorAll('.glass-panel-hover');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            // Can add subtle JS-driven animations here if needed
        });
    });

    // Implement simple Kanban drag-and-drop mechanics for workspace page
    const draggables = document.querySelectorAll('.kanban-task');
    const containers = document.querySelectorAll('.kanban-column');

    if (draggables.length > 0 && containers.length > 0) {
        draggables.forEach(draggable => {
            draggable.addEventListener('dragstart', () => {
                draggable.classList.add('dragging');
                draggable.style.opacity = '0.5';
            });

            draggable.addEventListener('dragend', () => {
                draggable.classList.remove('dragging');
                draggable.style.opacity = '1';
                // Trigger form submission or API call to update status naturally
                const newStatus = draggable.closest('.kanban-column').dataset.status;
                const form = draggable.querySelector('form.status-update-form');
                if (form) {
                    form.querySelector('input[name="status"]').value = newStatus;
                    form.submit();
                }
            });
        });

        containers.forEach(container => {
            container.addEventListener('dragover', e => {
                e.preventDefault();
                const afterElement = getDragAfterElement(container, e.clientY);
                const draggable = document.querySelector('.dragging');
                if (draggable) {
                    if (afterElement == null) {
                        container.querySelector('.flex-1').appendChild(draggable);
                    } else {
                        container.querySelector('.flex-1').insertBefore(draggable, afterElement);
                    }
                }
            });
        });

        function getDragAfterElement(container, y) {
            const draggableElements = [...container.querySelectorAll('.kanban-task:not(.dragging)')];

            return draggableElements.reduce((closest, child) => {
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;
                if (offset < 0 && offset > closest.offset) {
                    return { offset: offset, element: child };
                } else {
                    return closest;
                }
            }, { offset: Number.NEGATIVE_INFINITY }).element;
        }
    }
});
