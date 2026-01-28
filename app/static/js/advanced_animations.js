/**
 * ANIMAÇÕES AVANÇADAS - Sistema de Gestão Patrimonial
 * Animações complexas, microinterações e efeitos visuais modernos
 */

class AdvancedAnimations {
    constructor() {
        this.init();
        this.setupIntersectionObserver();
        this.setupAdvancedEffects();
    }

    init() {
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.isMobile = window.innerWidth <= 768;
        this.animationQueue = [];
        this.runningAnimations = new Set();
    }

    setupIntersectionObserver() {
        const observerOptions = {
            threshold: [0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0],
            rootMargin: '50px 0px -50px 0px'
        };

        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const element = entry.target;
                const ratio = entry.intersectionRatio;

                if (entry.isIntersecting) {
                    this.handleElementEnter(element, ratio);
                } else {
                    this.handleElementExit(element);
                }
            });
        }, observerOptions);

        // Observar elementos animáveis
        this.observeAnimatableElements();
    }

    observeAnimatableElements() {
        const selectors = [
            '.animate-on-scroll',
            '.stagger-item',
            '.fade-in-up',
            '.fade-in-down',
            '.fade-in-left',
            '.fade-in-right',
            '.scale-in',
            '.slide-in-up',
            '.slide-in-down',
            '.slide-in-left',
            '.slide-in-right',
            '.rotate-in',
            '.bounce-in'
        ];

        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                this.intersectionObserver.observe(element);
            });
        });
    }

    handleElementEnter(element, ratio) {
        if (this.prefersReducedMotion) return;

        const animationType = this.getAnimationType(element);
        const delay = parseFloat(element.dataset.delay) || 0;
        const duration = parseFloat(element.dataset.duration) || 0.6;
        const easing = element.dataset.easing || 'cubic-bezier(0.4, 0, 0.2, 1)';

        // Animação baseada no tipo
        switch (animationType) {
            case 'fade-in-up':
                this.animateFadeInUp(element, duration, delay, easing);
                break;
            case 'fade-in-down':
                this.animateFadeInDown(element, duration, delay, easing);
                break;
            case 'fade-in-left':
                this.animateFadeInLeft(element, duration, delay, easing);
                break;
            case 'fade-in-right':
                this.animateFadeInRight(element, duration, delay, easing);
                break;
            case 'scale-in':
                this.animateScaleIn(element, duration, delay, easing);
                break;
            case 'slide-in-up':
                this.animateSlideInUp(element, duration, delay, easing);
                break;
            case 'slide-in-down':
                this.animateSlideInDown(element, duration, delay, easing);
                break;
            case 'rotate-in':
                this.animateRotateIn(element, duration, delay, easing);
                break;
            case 'bounce-in':
                this.animateBounceIn(element, duration, delay, easing);
                break;
            default:
                this.animateFadeIn(element, duration, delay, easing);
        }
    }

    handleElementExit(element) {
        // Reset animation if needed
        if (element.dataset.resetOnExit === 'true') {
            element.style.opacity = '0';
            element.style.transform = this.getInitialTransform(element);
        }
    }

    getAnimationType(element) {
        const classes = element.classList;
        const animationClasses = [
            'fade-in-up', 'fade-in-down', 'fade-in-left', 'fade-in-right',
            'scale-in', 'slide-in-up', 'slide-in-down', 'slide-in-left', 'slide-in-right',
            'rotate-in', 'bounce-in'
        ];

        for (const cls of animationClasses) {
            if (classes.contains(cls)) {
                return cls;
            }
        }

        return 'fade-in';
    }

    getInitialTransform(element) {
        const animationType = this.getAnimationType(element);

        switch (animationType) {
            case 'fade-in-up':
            case 'slide-in-up':
                return 'translateY(30px)';
            case 'fade-in-down':
            case 'slide-in-down':
                return 'translateY(-30px)';
            case 'fade-in-left':
            case 'slide-in-left':
                return 'translateX(-30px)';
            case 'fade-in-right':
            case 'slide-in-right':
                return 'translateX(30px)';
            case 'scale-in':
                return 'scale(0.8)';
            case 'rotate-in':
                return 'rotate(-10deg) scale(0.9)';
            case 'bounce-in':
                return 'scale(0.3)';
            default:
                return 'translateY(20px)';
        }
    }

    // Animações específicas
    animateFadeIn(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateY(20px)', 'translateY(0)']
        }, duration, delay, easing);
    }

    animateFadeInUp(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateY(30px)', 'translateY(0)']
        }, duration, delay, easing);
    }

    animateFadeInDown(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateY(-30px)', 'translateY(0)']
        }, duration, delay, easing);
    }

    animateFadeInLeft(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateX(-30px)', 'translateX(0)']
        }, duration, delay, easing);
    }

    animateFadeInRight(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateX(30px)', 'translateX(0)']
        }, duration, delay, easing);
    }

    animateScaleIn(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['scale(0.8)', 'scale(1)']
        }, duration, delay, easing);
    }

    animateSlideInUp(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateY(100%)', 'translateY(0)']
        }, duration, delay, easing);
    }

    animateSlideInDown(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['translateY(-100%)', 'translateY(0)']
        }, duration, delay, easing);
    }

    animateRotateIn(element, duration, delay, easing) {
        this.animateElement(element, {
            opacity: [0, 1],
            transform: ['rotate(-10deg) scale(0.9)', 'rotate(0deg) scale(1)']
        }, duration, delay, easing);
    }

    animateBounceIn(element, duration, delay, easing) {
        // Animação bounce complexa
        const keyframes = [
            { opacity: 0, transform: 'scale(0.3)' },
            { opacity: 1, transform: 'scale(1.05)' },
            { transform: 'scale(0.9)' },
            { transform: 'scale(1)' }
        ];

        const timings = {
            duration: duration * 1000,
            delay: delay * 1000,
            easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
            fill: 'forwards'
        };

        element.animate(keyframes, timings);
    }

    animateElement(element, properties, duration, delay, easing) {
        const animationId = `anim_${Date.now()}_${Math.random()}`;

        if (this.runningAnimations.has(element)) {
            return; // Evitar animações duplicadas
        }

        this.runningAnimations.add(element);

        const keyframes = [];
        const propertyNames = Object.keys(properties);

        // Criar keyframes baseado nas propriedades
        const steps = 60; // 60fps
        for (let i = 0; i <= steps; i++) {
            const keyframe = {};
            const progress = i / steps;

            propertyNames.forEach(prop => {
                const [from, to] = properties[prop];
                if (typeof from === 'number' && typeof to === 'number') {
                    keyframe[prop] = from + (to - from) * progress;
                } else if (typeof from === 'string') {
                    // Para transforms e outras strings, interpolar se possível
                    keyframe[prop] = progress < 0.5 ? from : to;
                }
            });

            keyframes.push(keyframe);
        }

        const animation = element.animate(keyframes, {
            duration: duration * 1000,
            delay: delay * 1000,
            easing: easing,
            fill: 'forwards'
        });

        animation.addEventListener('finish', () => {
            this.runningAnimations.delete(element);
            element.classList.add('animated');
        });

        return animation;
    }

    // Sistema de animações escalonadas
    animateStaggered(elements, options = {}) {
        const {
            delay = 0.1,
            duration = 0.6,
            animation = 'fade-in-up',
            reverse = false
        } = options;

        const elementArray = Array.from(elements);
        if (reverse) elementArray.reverse();

        elementArray.forEach((element, index) => {
            element.dataset.delay = (index * delay).toString();
            element.dataset.duration = duration.toString();
            element.classList.add('animate-on-scroll', animation);
        });

        this.observeAnimatableElements();
    }

    // Animações de microinterações
    setupAdvancedEffects() {
        this.setupHoverEffects();
        this.setupClickEffects();
        this.setupFocusEffects();
        this.setupLoadingAnimations();
    }

    setupHoverEffects() {
        // Efeitos de hover avançados
        document.querySelectorAll('.hover-lift').forEach(element => {
            element.addEventListener('mouseenter', () => {
                this.animateElement(element, {
                    transform: ['translateY(0)', 'translateY(-8px) scale(1.02)']
                }, 0.3, 0, 'cubic-bezier(0.34, 1.56, 0.64, 1)');
            });

            element.addEventListener('mouseleave', () => {
                this.animateElement(element, {
                    transform: ['translateY(-8px) scale(1.02)', 'translateY(0) scale(1)']
                }, 0.3, 0, 'cubic-bezier(0.34, 1.56, 0.64, 1)');
            });
        });

        // Efeitos de glow
        document.querySelectorAll('.hover-glow').forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.style.boxShadow = '0 0 30px rgba(59, 130, 246, 0.5)';
            });

            element.addEventListener('mouseleave', () => {
                element.style.boxShadow = '';
            });
        });
    }

    setupClickEffects() {
        // Ripple effect aprimorado
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.btn-ripple');
            if (button) {
                this.createAdvancedRipple(e, button);
            }
        });

        // Pulse effect
        document.querySelectorAll('.click-pulse').forEach(element => {
            element.addEventListener('click', () => {
                this.animateElement(element, {
                    transform: ['scale(1)', 'scale(0.95)', 'scale(1)']
                }, 0.2, 0, 'ease-in-out');
            });
        });
    }

    createAdvancedRipple(event, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 2;
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: radial-gradient(circle, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
            border-radius: 50%;
            transform: scale(0);
            animation: advanced-ripple 0.8s ease-out forwards;
            pointer-events: none;
            z-index: 10;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => ripple.remove(), 800);
    }

    setupFocusEffects() {
        // Animações de foco acessíveis
        document.querySelectorAll('input, button, select, textarea').forEach(element => {
            element.addEventListener('focus', () => {
                if (!this.prefersReducedMotion) {
                    element.style.transform = 'scale(1.02)';
                    element.style.transition = 'transform 0.2s ease';
                }
            });

            element.addEventListener('blur', () => {
                element.style.transform = '';
            });
        });
    }

    setupLoadingAnimations() {
        // Spinner avançado
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            this.createAdvancedSpinner(spinner);
        });

        // Skeleton loading aprimorado
        document.querySelectorAll('.skeleton-wave').forEach(skeleton => {
            this.animateSkeletonWave(skeleton);
        });
    }

    createAdvancedSpinner(element) {
        element.innerHTML = `
            <div class="advanced-spinner">
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
                <div class="spinner-center"></div>
            </div>
        `;

        // Adicionar estilos dinamicamente se não existirem
        if (!document.querySelector('#advanced-spinner-styles')) {
            const styles = document.createElement('style');
            styles.id = 'advanced-spinner-styles';
            styles.textContent = `
                .advanced-spinner {
                    position: relative;
                    width: 40px;
                    height: 40px;
                }
                .spinner-ring {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border: 3px solid transparent;
                    border-top: 3px solid #3b82f6;
                    border-radius: 50%;
                    animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
                }
                .spinner-ring:nth-child(2) {
                    animation-delay: 0.2s;
                    border-top-color: #10b981;
                }
                .spinner-ring:nth-child(3) {
                    animation-delay: 0.4s;
                    border-top-color: #f59e0b;
                }
                .spinner-center {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 8px;
                    height: 8px;
                    background: #3b82f6;
                    border-radius: 50%;
                    transform: translate(-50%, -50%);
                    animation: pulse 1.5s ease-in-out infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    animateSkeletonWave(element) {
        const wave = document.createElement('div');
        wave.className = 'skeleton-wave-overlay';
        wave.style.cssText = `
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            animation: skeleton-wave 2s infinite;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(wave);

        if (!document.querySelector('#skeleton-wave-styles')) {
            const styles = document.createElement('style');
            styles.id = 'skeleton-wave-styles';
            styles.textContent = `
                @keyframes skeleton-wave {
                    0% { left: -100%; }
                    100% { left: 100%; }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    // Animações de página
    animatePageTransition(fromPage, toPage, direction = 'forward') {
        const duration = 0.4;
        const easing = 'cubic-bezier(0.4, 0, 0.2, 1)';

        // Animação de saída
        this.animateElement(fromPage, {
            opacity: [1, 0],
            transform: ['translateX(0)', `translateX(${direction === 'forward' ? '-20px' : '20px'})`]
        }, duration, 0, easing);

        // Animação de entrada
        setTimeout(() => {
            this.animateElement(toPage, {
                opacity: [0, 1],
                transform: [`translateX(${direction === 'forward' ? '20px' : '-20px'})`, 'translateX(0)']
            }, duration, 0, easing);
        }, duration * 500);
    }

    // Animações de notificação
    animateNotification(notification, type = 'info') {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 1000;
            transform: translateX(100%);
            opacity: 0;
        `;

        document.body.appendChild(notification);

        // Animação de entrada
        this.animateElement(notification, {
            opacity: [0, 1],
            transform: ['translateX(100%)', 'translateX(0)']
        }, 0.3, 0, 'cubic-bezier(0.34, 1.56, 0.64, 1)');

        // Animação de saída
        setTimeout(() => {
            this.animateElement(notification, {
                opacity: [1, 0],
                transform: ['translateX(0)', 'translateX(100%)']
            }, 0.3, 0, 'cubic-bezier(0.34, 1.56, 0.64, 1)');

            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Utilitários
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
}

// Funções globais para uso nos templates
window.animateStaggered = (selector, options) => {
    const elements = document.querySelectorAll(selector);
    if (window.advancedAnimations) {
        window.advancedAnimations.animateStaggered(elements, options);
    }
};

window.animatePageTransition = (fromSelector, toSelector, direction) => {
    const fromPage = document.querySelector(fromSelector);
    const toPage = document.querySelector(toSelector);
    if (window.advancedAnimations && fromPage && toPage) {
        window.advancedAnimations.animatePageTransition(fromPage, toPage, direction);
    }
};

window.createAdvancedNotification = (message, type) => {
    const notification = document.createElement('div');
    notification.textContent = message;
    if (window.advancedAnimations) {
        window.advancedAnimations.animateNotification(notification, type);
    }
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    window.advancedAnimations = new AdvancedAnimations();
});