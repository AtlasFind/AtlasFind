function showAtlasIconMonogram(img) {
    if (!img) return;
    img.hidden = true;
    img.removeAttribute("src");
    const monogram = img.parentElement?.querySelector(".tool-icon-fallback");
    if (monogram) monogram.hidden = false;
}

function tryAtlasIconFallback(img) {
    if (!img || img.dataset.iconFinished === "1") return;
    const fallback = img.dataset.fallbackSrc;
    const fallbackAlreadyTried = img.dataset.fallbackTried === "1";

    if (fallback && !fallbackAlreadyTried) {
        img.dataset.fallbackTried = "1";
        img.src = fallback;
        return;
    }

    img.dataset.iconFinished = "1";
    showAtlasIconMonogram(img);
}

function validateAtlasIcon(img) {
    if (!img || img.hidden) return;
    if (!img.complete) return;
    if (!img.naturalWidth || !img.naturalHeight || img.naturalWidth < 32 || img.naturalHeight < 32) {
        tryAtlasIconFallback(img);
    }
}

function initializeAtlasIcons(scope = document) {
    scope.querySelectorAll("img[data-atlas-icon]").forEach((img) => {
        if (img.dataset.iconBound === "1") return;
        img.dataset.iconBound = "1";
        img.addEventListener("error", () => tryAtlasIconFallback(img));
        img.addEventListener("load", () => validateAtlasIcon(img));
        if (img.complete) validateAtlasIcon(img);
    });
}

document.addEventListener("DOMContentLoaded", () => initializeAtlasIcons());


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

const copyComparisonLink = document.getElementById("copyComparisonLink");
copyComparisonLink?.addEventListener("click", async () => {
    const originalText = copyComparisonLink.textContent;
    try {
        await navigator.clipboard.writeText(window.location.href);
        copyComparisonLink.textContent = copyComparisonLink.dataset.copySuccess || "Link copied";
    } catch (error) {
        window.prompt("Copy this comparison link:", window.location.href);
    }
    window.setTimeout(() => { copyComparisonLink.textContent = originalText; }, 1800);
});


const compareToolSelects = Array.from(document.querySelectorAll("[data-compare-tool-select]"));

function syncCompareToolOptions() {
    const selectedValues = compareToolSelects
        .map((select) => select.value)
        .filter(Boolean);

    compareToolSelects.forEach((select) => {
        Array.from(select.options).forEach((option) => {
            if (!option.value) {
                option.disabled = false;
                return;
            }

            option.disabled = option.value !== select.value && selectedValues.includes(option.value);
        });
    });
}

compareToolSelects.forEach((select) => {
    select.addEventListener("change", syncCompareToolOptions);
});

syncCompareToolOptions();


// v0.3.0 smart search suggestions
const searchSuggestions = document.getElementById("searchSuggestions");
let searchSuggestionTimer;
let activeSuggestionIndex = -1;
let currentSuggestions = [];

function closeSearchSuggestions() {
    if (!searchSuggestions || !searchInput) return;
    searchSuggestions.hidden = true;
    searchSuggestions.innerHTML = "";
    searchInput.setAttribute("aria-expanded", "false");
    activeSuggestionIndex = -1;
    currentSuggestions = [];
}

function renderSearchSuggestions(items) {
    if (!searchSuggestions || !searchInput || !items.length) {
        closeSearchSuggestions();
        return;
    }
    currentSuggestions = items;
    searchSuggestions.innerHTML = items.map((item, index) => `
        <button type="button" role="option" data-suggestion-index="${index}" aria-selected="false">
            <span>${item.label}</span><small>${item.type === "tool" ? "Tool" : "Search"}</small>
        </button>
    `).join("");
    searchSuggestions.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
}

function chooseSearchSuggestion(index) {
    const item = currentSuggestions[index];
    if (!item || !searchInput) return;
    searchInput.value = item.value;
    closeSearchSuggestions();
    searchInput.form?.requestSubmit();
}

searchInput?.addEventListener("input", () => {
    window.clearTimeout(searchSuggestionTimer);
    const query = searchInput.value.trim();
    if (query.length < 2) {
        closeSearchSuggestions();
        return;
    }
    searchSuggestionTimer = window.setTimeout(async () => {
        try {
            const response = await fetch(`/api/search-suggestions?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error("Suggestion request failed");
            renderSearchSuggestions(await response.json());
        } catch (error) {
            closeSearchSuggestions();
        }
    }, 180);
});

searchSuggestions?.addEventListener("click", event => {
    const button = event.target.closest("[data-suggestion-index]");
    if (button) chooseSearchSuggestion(Number(button.dataset.suggestionIndex));
});

searchInput?.addEventListener("keydown", event => {
    if (!currentSuggestions.length) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        const direction = event.key === "ArrowDown" ? 1 : -1;
        activeSuggestionIndex = (activeSuggestionIndex + direction + currentSuggestions.length) % currentSuggestions.length;
        searchSuggestions?.querySelectorAll("[role='option']").forEach((option, index) => {
            option.setAttribute("aria-selected", String(index === activeSuggestionIndex));
        });
    } else if (event.key === "Enter" && activeSuggestionIndex >= 0) {
        event.preventDefault();
        chooseSearchSuggestion(activeSuggestionIndex);
    } else if (event.key === "Escape") {
        closeSearchSuggestions();
    }
});

document.addEventListener("click", event => {
    if (!searchSuggestions?.contains(event.target) && event.target !== searchInput) closeSearchSuggestions();
});


// v0.8.1 essential-storage notice
const cookieNotice = document.getElementById("cookieNotice");
const cookieAccept = document.getElementById("cookieAccept");
if (cookieNotice && localStorage.getItem("atlas-cookie-notice") !== "accepted") cookieNotice.hidden = false;
cookieAccept?.addEventListener("click", () => { localStorage.setItem("atlas-cookie-notice", "accepted"); cookieNotice.hidden = true; });
