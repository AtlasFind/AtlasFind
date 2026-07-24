const root = document.documentElement;
const themeButton = document.getElementById("themeButton");
const themeIcon = document.getElementById("themeIcon");
const searchInput = document.getElementById("searchInput");
const heroVisual = document.getElementById("heroVisual");
const menuButton = document.getElementById("menuButton");
const primaryNavigation = document.getElementById("primaryNavigation");
const liveStatus = document.getElementById("liveStatus");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function updateThemeControl() {
    if (!themeButton || !themeIcon) return;
    const isLight = root.classList.contains("light-theme");
    themeIcon.textContent = isLight ? "☀" : "☾";
    themeButton.setAttribute("aria-pressed", String(isLight));
    themeButton.setAttribute("aria-label", isLight ? "Switch to dark theme" : "Switch to light theme");
}

updateThemeControl();

themeButton?.addEventListener("click", () => {
    root.classList.toggle("light-theme");
    const isLight = root.classList.contains("light-theme");
    localStorage.setItem("atlas-theme", isLight ? "light" : "dark");
    updateThemeControl();
});

function closeMenu() {
    if (!menuButton || !primaryNavigation) return;
    primaryNavigation.classList.remove("is-open");
    menuButton.classList.remove("is-open");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.setAttribute("aria-label", "Open navigation menu");
    document.body.classList.remove("menu-open");
}

menuButton?.addEventListener("click", () => {
    const isOpen = primaryNavigation?.classList.toggle("is-open") ?? false;
    menuButton.classList.toggle("is-open", isOpen);
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute("aria-label", isOpen ? "Close navigation menu" : "Open navigation menu");
    document.body.classList.toggle("menu-open", isOpen);
});

primaryNavigation?.querySelectorAll("a").forEach(link => link.addEventListener("click", closeMenu));

document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeMenu();
    const ctrlPressed = event.ctrlKey || event.metaKey;
    if (ctrlPressed && event.key.toLowerCase() === "k" && searchInput) {
        event.preventDefault();
        searchInput.focus();
        searchInput.select();
    }
});

document.addEventListener("click", event => {
    if (!primaryNavigation?.classList.contains("is-open")) return;
    if (!primaryNavigation.contains(event.target) && !menuButton?.contains(event.target)) closeMenu();
});

if (heroVisual && !reducedMotion.matches) {
    heroVisual.addEventListener("mousemove", event => {
        if (window.innerWidth < 900) return;
        const rect = heroVisual.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        heroVisual.style.transform = `rotateY(${x * 5}deg) rotateX(${y * -5}deg)`;
    });
    heroVisual.addEventListener("mouseleave", () => {
        heroVisual.style.transform = "rotateY(0deg) rotateX(0deg)";
    });
}

document.querySelectorAll(".match-progress-fill").forEach(bar => {
    const value = Number(bar.dataset.match || 0);
    requestAnimationFrame(() => { bar.style.width = `${Math.min(100, Math.max(0, value))}%`; });
});

document.querySelectorAll("[data-loading-form]").forEach(form => {
    form.addEventListener("submit", () => {
        const button = form.querySelector("button[type='submit']");
        if (!button) return;
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
        button.dataset.originalText = button.innerHTML;
        button.textContent = button.dataset.loadingText || "Loading…";
        if (liveStatus) liveStatus.textContent = button.textContent;
    });
});

window.addEventListener("pageshow", () => {
    document.querySelectorAll("[data-loading-form] button[type='submit']").forEach(button => {
        button.disabled = false;
        button.removeAttribute("aria-busy");
        if (button.dataset.originalText) button.innerHTML = button.dataset.originalText;
    });
});


const filterToggle = document.getElementById("filterToggle");
const filterPanel = document.getElementById("filterPanel");
filterToggle?.addEventListener("click", () => {
    const isOpen = filterPanel?.classList.toggle("is-open") ?? false;
    filterToggle.setAttribute("aria-expanded", String(isOpen));
});
