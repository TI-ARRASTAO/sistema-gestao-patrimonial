/**
 * Utilitários Modernos para Interface
 * Microinterações, animações e feedback aprimorado
 */

class ModernUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupSmoothScrolling();
        this.setupEnhancedTooltips();
        this.setupKeyboardShortcuts();
        this.setupContextMenus();
        this.setupDragAndDrop();
    }

    // Scroll suave para âncoras
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Tooltips aprimorados com posições dinâmicas
    setupEnhancedTooltips() {
        const tooltips = document.querySelectorAll('.tooltip');

        tooltips.forEach(tooltip => {
            tooltip.addEventListener('mouseenter', (e) => {
                this.positionTooltip(e.target);
            });
        });
    }

    positionTooltip(element) {
        const tooltip = element.querySelector('::before');
        if (!tooltip) return;

        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();

        // Ajusta posição se sair da tela
        if (rect.left + tooltipRect.width > window.innerWidth) {
            tooltip.style.left = 'auto';
            tooltip.style.right = '0';
            tooltip.style.transform = 'translateX(0)';
        }
    }

    // Atalhos de teclado
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K: Focus na busca
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('#search-input');
                if (searchInput) {
                    searchInput.focus();
                    this.showNotification('Busca ativada - digite para pesquisar', 'info', 2000);
                }
            }

            // Escape: Fecha modais/dropdowns
            if (e.key === 'Escape') {
                this.closeAllModals();
                this.closeAllDropdowns();
            }

            // Ctrl/Cmd + /: Mostra atalhos
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.showKeyboardShortcuts();
            }
        });
    }

    // Menus de contexto personalizados
    setupContextMenus() {
        document.addEventListener('contextmenu', (e) => {
            // Só previne em elementos específicos
            if (e.target.closest('.context-menu-enabled')) {
                e.preventDefault();
                this.showContextMenu(e, e.target.closest('.context-menu-enabled'));
            }
        });

    // Fecha menu ao clicar fora
        document.addEventListener('click', () => {
            const existingMenu = document.querySelector('.context-menu');
            if (existingMenu) existingMenu.remove();
        });
    }

    showContextMenu(event, element) {
        const existingMenu = document.querySelector('.context-menu');
        if (existingMenu) existingMenu.remove();

        const menu = document.createElement('div');
        menu.className = 'context-menu glass fade-in';
        menu.style.cssText = `
            position: fixed;
            left: ${event.clientX}px;
            top: ${event.clientY}px;
            z-index: 1000;
            min-width: 200px;
        `;

        // Adiciona opções baseadas no elemento
        const actions = this.getContextMenuActions(element);
        menu.innerHTML = actions.map(action => `
            <button class="context-menu-item" onclick="${action.action}">
                <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    ${action.icon}
                </svg>
                ${action.label}
            </button>
        `).join('');

        document.body.appendChild(menu);

        // Anima entrada
        setTimeout(() => menu.classList.add('visible'), 10);
    }

    getContextMenuActions(element) {
        // Retorna ações baseadas no tipo de elemento
        if (element.classList.contains('equipment-item')) {
            return [
                {
                    label: 'Editar',
                    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>',
                    action: `editEquipment(${element.dataset.id})`
                },
                {
                    label: 'Duplicar',
                    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>',
                    action: `duplicateEquipment(${element.dataset.id})`
                },
                {
                    label: 'Excluir',
                    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>',
                    action: `deleteEquipment(${element.dataset.id})`
                }
            ];
        }

        return [];
    }

    // Drag and drop aprimorado
    setupDragAndDrop() {
        const draggables = document.querySelectorAll('.draggable');
        const dropzones = document.querySelectorAll('.dropzone');

        draggables.forEach(draggable => {
            draggable.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', draggable.id);
                draggable.classList.add('dragging');
            });

            draggable.addEventListener('dragend', () => {
                draggable.classList.remove('dragging');
            });
        });

        dropzones.forEach(dropzone => {
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.classList.add('drag-over');
            });

            dropzone.addEventListener('dragleave', () => {
                dropzone.classList.remove('drag-over');
            });

            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('drag-over');

                const draggedId = e.dataTransfer.getData('text/plain');
                const draggedElement = document.getElementById(draggedId);

                if (draggedElement && dropzone !== draggedElement.parentElement) {
                    dropzone.appendChild(draggedElement);
                    this.showNotification('Item movido com sucesso!', 'success');
                }
            });
        });
    }

    // Utilitários
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    closeAllDropdowns() {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.classList.add('hidden');
        });
    }

    showKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Ctrl+K', action: 'Focar na busca' },
            { key: 'Escape', action: 'Fechar modais' },
            { key: 'Ctrl+/', action: 'Mostrar atalhos' },
            { key: 'Tab', action: 'Navegar entre elementos' }
        ];

        const modal = document.createElement('div');
        modal.className = 'modal fade-in';
        modal.innerHTML = `
            <div class="modal-content glass">
                <div class="modal-header">
                    <h3>Atalhos de Teclado</h3>
                    <button onclick="this.closest('.modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    ${shortcuts.map(s => `
                        <div class="flex justify-between py-2">
                            <span>${s.action}</span>
                            <kbd class="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded text-sm">${s.key}</kbd>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    showNotification(message, type = 'info', duration = 3000) {
        // Usa a função existente do base.html
        if (window.showNotification) {
            window.showNotification(message, type, duration);
        }
    }
}

// Funções globais para uso nos templates
window.editEquipment = (id) => {
    window.location.href = `/equipamentos/${id}/edit`;
};

window.duplicateEquipment = (id) => {
    if (confirm('Deseja duplicar este equipamento?')) {
        // Implementar lógica de duplicação
        window.showNotification('Funcionalidade em desenvolvimento', 'info');
    }
};

window.deleteEquipment = (id) => {
    if (confirm('Tem certeza que deseja excluir este equipamento?')) {
        // Implementar lógica de exclusão
        window.showNotification('Equipamento excluído', 'success');
    }
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    window.modernUI = new ModernUI();
});