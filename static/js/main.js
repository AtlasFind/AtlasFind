const atlasI18n = window.ATLAS_I18N || {};
const atlasT = (key, fallback) => atlasI18n[key] || fallback;
const atlasLocalLogoExtensions = ["webp", "png", "jpg", "jpeg", "svg", "ico"];

function showAtlasIconMonogram(img) {
    if (!img) return;
    img.hidden = true;
    img.removeAttribute("src");
    const monogram = img.parentElement?.querySelector(".tool-icon-fallback");
    if (monogram) monogram.hidden = false;
}

function tryAtlasIconFallback(img) {
    if (!img || img.dataset.iconFinished === "1") return;
    const localBase = img.dataset.localLogoBase;
    const localIndex = Number.parseInt(img.dataset.localLogoIndex || "-1", 10);
    const nextLocalIndex = localIndex + 1;
    if (localBase && nextLocalIndex < atlasLocalLogoExtensions.length) {
        img.dataset.localLogoIndex = String(nextLocalIndex);
        img.src = `${localBase}.${atlasLocalLogoExtensions[nextLocalIndex]}`;
        return;
    }
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
    if (!img || img.hidden || !img.complete) return;
    const width = img.naturalWidth || 0;
    const height = img.naturalHeight || 0;
    const ratio = height ? width / height : 0;
    const minimumSize = img.dataset.localLogoBase ? 16 : 32;
    const invalidSize = width < minimumSize || height < minimumSize;
    const invalidRatio = ratio < 0.25 || ratio > 4;
    if (!width || !height || invalidSize || invalidRatio) {
        tryAtlasIconFallback(img);
        return;
    }
    img.dataset.iconFinished = "1";
    img.parentElement?.classList.add("icon-ready");
}

function initializeAtlasIcons(scope = document) {
    scope.querySelectorAll("img[data-atlas-icon]").forEach((img) => {
        if (img.dataset.iconBound === "1") return;
        img.dataset.iconBound = "1";
        img.addEventListener("error", () => tryAtlasIconFallback(img));
        img.addEventListener("load", () => validateAtlasIcon(img));
        if (img.dataset.localLogoBase && img.currentSrc.includes("/icons/generated/")) {
            img.dataset.fallbackSrc = img.currentSrc || img.src;
            img.dataset.localLogoIndex = "0";
            img.src = `${img.dataset.localLogoBase}.webp`;
            return;
        }
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
const moreNavigation = document.getElementById("moreNavigation");
const liveStatus = document.getElementById("liveStatus");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function updateThemeControl() {
    if (!themeButton || !themeIcon) return;
    const isLight = root.classList.contains("light-theme");
    themeIcon.textContent = isLight ? "☀" : "☾";
    themeButton.setAttribute("aria-pressed", String(isLight));
    themeButton.setAttribute("aria-label", isLight ? atlasT("js.theme.dark", "Switch to dark theme") : atlasT("js.theme.light", "Switch to light theme"));
}

updateThemeControl();

themeButton?.addEventListener("click", () => {
    root.classList.toggle("light-theme");
    const isLight = root.classList.contains("light-theme");
    localStorage.setItem("atlas-theme", isLight ? "light" : "dark");
    updateThemeControl();
});

function closeMenu() {
    if (!menuButton || !moreNavigation) return;
    moreNavigation.classList.remove("is-open");
    menuButton.classList.remove("is-open");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.setAttribute("aria-label", atlasT("js.menu.open", "Open navigation menu"));
    document.body.classList.remove("menu-open");
}

menuButton?.addEventListener("click", () => {
    const isOpen = moreNavigation?.classList.toggle("is-open") ?? false;
    menuButton.classList.toggle("is-open", isOpen);
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute("aria-label", isOpen ? atlasT("js.menu.close", "Close navigation menu") : atlasT("js.menu.open", "Open navigation menu"));
    document.body.classList.toggle("menu-open", isOpen);
});

moreNavigation?.querySelectorAll("a").forEach(link => link.addEventListener("click", closeMenu));

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
    if (!moreNavigation?.classList.contains("is-open")) return;
    if (!moreNavigation.contains(event.target) && !menuButton?.contains(event.target)) closeMenu();
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
        button.textContent = button.dataset.loadingText || atlasT("js.loading", "Loading…");
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
        copyComparisonLink.textContent = copyComparisonLink.dataset.copySuccess || atlasT("js.copy.success", "Link copied");
    } catch (error) {
        window.prompt(atlasT("js.copy.prompt", "Copy this comparison link:"), window.location.href);
    }
    window.setTimeout(() => { copyComparisonLink.textContent = originalText; }, 1800);
});

const shareRecommendationResults = document.getElementById("shareRecommendationResults");
shareRecommendationResults?.addEventListener("click", async () => {
    const originalText = shareRecommendationResults.textContent;
    const payload = {
        title: document.title,
        text: document.documentElement.lang === "tr"
            ? "AtlasFind bana uygun araçları sıraladı."
            : "AtlasFind ranked the best tools for my needs.",
        url: window.location.href
    };
    try {
        if (navigator.share) {
            await navigator.share(payload);
        } else {
            await navigator.clipboard.writeText(payload.url);
            shareRecommendationResults.textContent = shareRecommendationResults.dataset.shared || atlasT("js.copy.success", "Link copied");
            window.setTimeout(() => { shareRecommendationResults.textContent = originalText; }, 1800);
        }
    } catch (error) {
        if (error?.name !== "AbortError") {
            window.prompt(atlasT("js.copy.prompt", "Copy this link:"), payload.url);
        }
    }
});


const compareToolSelects = Array.from(document.querySelectorAll("[data-compare-tool-select]"));
const compareMoreTools = document.getElementById("compareMoreTools");
const optionalCompareFields = Array.from(document.querySelectorAll(".compare-tool-optional"));
const compareSelectEnhancers = new Map();

function splitCompareOptionLabel(label) {
    const parts = label.split(" · ");
    return { name: parts.shift() || label, detail: parts.join(" · ") };
}

function closeCompareComboboxes(except = null) {
    compareSelectEnhancers.forEach((enhancer) => {
        if (enhancer !== except) enhancer.close();
    });
}

function enhanceCompareSelect(select) {
    const root = document.createElement("div");
    root.className = "compare-combobox";

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "compare-combobox-trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");

    const panel = document.createElement("div");
    panel.className = "compare-combobox-panel";
    panel.hidden = true;

    const search = document.createElement("input");
    search.type = "search";
    search.className = "compare-combobox-search";
    search.placeholder = document.documentElement.lang === "tr" ? "Araç ara…" : "Search tools…";
    search.autocomplete = "off";
    search.setAttribute("aria-label", search.placeholder);

    const results = document.createElement("div");
    results.className = "compare-combobox-options";
    results.setAttribute("role", "listbox");
    panel.append(search, results);
    root.append(trigger, panel);
    select.classList.add("is-enhanced");
    select.insertAdjacentElement("afterend", root);

    function updateTrigger() {
        const selected = select.selectedOptions[0];
        const label = selected?.textContent?.trim() || "";
        const parts = splitCompareOptionLabel(label);
        trigger.replaceChildren();
        const text = document.createElement("span");
        const name = document.createElement("strong");
        name.textContent = parts.name;
        text.append(name);
        if (parts.detail) {
            const detail = document.createElement("small");
            detail.textContent = parts.detail;
            text.append(detail);
        }
        const chevron = document.createElement("i");
        chevron.setAttribute("aria-hidden", "true");
        trigger.append(text, chevron);
        trigger.classList.toggle("is-placeholder", !select.value);
    }

    function renderOptions() {
        const query = search.value.trim().toLocaleLowerCase(document.documentElement.lang || undefined);
        results.replaceChildren();
        const available = Array.from(select.options).filter((option) => {
            if (option.hidden || (option.disabled && option.value !== select.value)) return false;
            return !query || option.textContent.toLocaleLowerCase(document.documentElement.lang || undefined).includes(query);
        });
        available.forEach((option) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "compare-combobox-option";
            button.setAttribute("role", "option");
            button.setAttribute("aria-selected", String(option.value === select.value));
            const parts = splitCompareOptionLabel(option.textContent.trim());
            const name = document.createElement("strong");
            name.textContent = parts.name;
            button.append(name);
            if (parts.detail) {
                const detail = document.createElement("small");
                detail.textContent = parts.detail;
                button.append(detail);
            }
            button.addEventListener("click", () => {
                select.value = option.value;
                select.dispatchEvent(new Event("change", { bubbles: true }));
                close();
                trigger.focus();
            });
            results.append(button);
        });
        if (!available.length) {
            const empty = document.createElement("p");
            empty.className = "compare-combobox-empty";
            empty.textContent = document.documentElement.lang === "tr" ? "Eşleşen araç bulunamadı." : "No matching tools found.";
            results.append(empty);
        }
    }

    function open() {
        closeCompareComboboxes(enhancer);
        panel.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
        root.classList.add("is-open");
        search.value = "";
        renderOptions();
        window.setTimeout(() => search.focus(), 0);
    }

    function close() {
        panel.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
        root.classList.remove("is-open");
    }

    const enhancer = { root, trigger, panel, search, updateTrigger, renderOptions, open, close };
    trigger.addEventListener("click", () => panel.hidden ? open() : close());
    search.addEventListener("input", renderOptions);
    root.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            close();
            trigger.focus();
        }
    });
    compareSelectEnhancers.set(select, enhancer);
    updateTrigger();
}

function refreshCompareComboboxes() {
    compareSelectEnhancers.forEach((enhancer) => {
        enhancer.updateTrigger();
        if (!enhancer.panel.hidden) enhancer.renderOptions();
    });
}

function setOptionalCompareFields(open, clearValues = false) {
    optionalCompareFields.forEach((field) => {
        field.hidden = !open;
        if (!open && clearValues) {
            const select = field.querySelector("select");
            if (select) select.value = "";
        }
    });
    if (compareMoreTools) {
        compareMoreTools.setAttribute("aria-expanded", String(open));
        const icon = compareMoreTools.querySelector("span");
        const label = compareMoreTools.querySelector("b");
        if (icon) icon.textContent = open ? "−" : "+";
        if (label) label.textContent = open ? compareMoreTools.dataset.closeLabel : compareMoreTools.dataset.openLabel;
    }
}

compareMoreTools?.addEventListener("click", () => {
    const nextState = compareMoreTools.getAttribute("aria-expanded") !== "true";
    setOptionalCompareFields(nextState, !nextState);
    syncCompareToolOptions();
    refreshCompareComboboxes();
});

function syncCompareToolOptions() {
    const selectedValues = compareToolSelects
        .map((select) => select.value)
        .filter(Boolean);

    const primaryOption = compareToolSelects[0]?.selectedOptions?.[0];
    const primaryCategory = primaryOption?.dataset?.category || "";

    compareToolSelects.forEach((select, selectIndex) => {
        Array.from(select.options).forEach((option) => {
            if (!option.value) {
                option.disabled = false;
                return;
            }

            const outsideCategory = selectIndex > 0 && primaryCategory && option.dataset.category !== primaryCategory;
            option.hidden = outsideCategory;
            option.disabled = outsideCategory || (option.value !== select.value && selectedValues.includes(option.value));
        });
        if (selectIndex > 0 && select.value && select.selectedOptions[0]?.dataset.category !== primaryCategory) {
            select.value = "";
        }
    });
}

compareToolSelects.forEach((select) => {
    enhanceCompareSelect(select);
    select.addEventListener("change", () => {
        syncCompareToolOptions();
        refreshCompareComboboxes();
    });
});

syncCompareToolOptions();
refreshCompareComboboxes();

document.addEventListener("click", (event) => {
    if (!event.target.closest(".compare-combobox")) closeCompareComboboxes();
});

// Account-free browsing history: stored only in the visitor's browser.
const recentToolsStorageKey = "atlasfind-recent-tools-v1";
const historyTool = document.querySelector("[data-history-tool]");
const recentToolsSection = document.getElementById("recentToolsSection");
const recentToolsGrid = document.getElementById("recentToolsGrid");
const clearRecentTools = document.getElementById("clearRecentTools");

function readRecentTools() {
    try {
        const value = JSON.parse(localStorage.getItem(recentToolsStorageKey) || "[]");
        return Array.isArray(value) ? value.slice(0, 6) : [];
    } catch (error) {
        return [];
    }
}

if (historyTool) {
    const current = {
        slug: historyTool.dataset.toolSlug,
        name: historyTool.dataset.toolName,
        category: historyTool.dataset.toolCategory,
        icon: historyTool.dataset.toolIcon,
        url: historyTool.dataset.toolUrl
    };
    if (current.slug && current.name && current.url) {
        const recent = readRecentTools().filter((item) => item?.slug !== current.slug);
        recent.unshift(current);
        try { localStorage.setItem(recentToolsStorageKey, JSON.stringify(recent.slice(0, 6))); } catch (error) { /* Storage may be unavailable. */ }
    }
}

function renderRecentTools() {
    if (!recentToolsSection || !recentToolsGrid) return;
    const recent = readRecentTools();
    recentToolsGrid.replaceChildren();
    recentToolsSection.hidden = recent.length === 0;
    recent.forEach((item) => {
        const link = document.createElement("a");
        link.className = "recent-tool-card";
        link.href = item.url;
        const image = document.createElement("img");
        image.src = item.icon;
        image.alt = "";
        image.width = 46;
        image.height = 46;
        image.loading = "lazy";
        const copy = document.createElement("span");
        const name = document.createElement("strong");
        name.textContent = item.name;
        const category = document.createElement("small");
        category.textContent = item.category || "";
        copy.append(name, category);
        const arrow = document.createElement("b");
        arrow.textContent = "→";
        arrow.setAttribute("aria-hidden", "true");
        link.append(image, copy, arrow);
        recentToolsGrid.append(link);
    });
}

clearRecentTools?.addEventListener("click", () => {
    try { localStorage.removeItem(recentToolsStorageKey); } catch (error) { /* Storage may be unavailable. */ }
    renderRecentTools();
});
renderRecentTools();


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
            <span>${item.label}</span><small>${item.type === "tool" ? atlasT("js.suggestion.tool", "Tool") : atlasT("js.suggestion.search", "Search")}</small>
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


// Analytics is loaded only after explicit visitor consent.
const cookieNotice = document.getElementById("cookieNotice");
const cookieAccept = document.getElementById("cookieAccept");
const cookieReject = document.getElementById("cookieReject");
const analyticsConsentKey = "atlas-analytics-consent";
function loadGoogleAnalytics() {
    if (typeof window.gtag !== "function") return;
    window.gtag("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied"
    });
}
const analyticsConsent = localStorage.getItem(analyticsConsentKey);
if (analyticsConsent === "granted") loadGoogleAnalytics();
else if (cookieNotice && analyticsConsent === null) cookieNotice.hidden = false;
cookieAccept?.addEventListener("click", () => { localStorage.setItem(analyticsConsentKey, "granted"); cookieNotice.hidden = true; loadGoogleAnalytics(); });
cookieReject?.addEventListener("click", () => { localStorage.setItem(analyticsConsentKey, "denied"); cookieNotice.hidden = true; });

// v0.9.2 catalog filters and view preference
const catalogRoot = document.querySelector("[data-catalog-root]");
const catalogGrid = document.querySelector("[data-catalog-grid]");
const catalogViewButtons = Array.from(document.querySelectorAll("[data-catalog-view]"));

function setCatalogView(view) {
    if (!catalogGrid || !["grid", "list"].includes(view)) return;
    catalogGrid.classList.toggle("is-list", view === "list");
    catalogViewButtons.forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.catalogView === view));
    });
    localStorage.setItem("atlas-catalog-view", view);
}

if (catalogRoot && catalogGrid) {
    const savedView = localStorage.getItem("atlas-catalog-view");
    setCatalogView(savedView === "list" ? "list" : "grid");
    catalogViewButtons.forEach((button) => {
        button.addEventListener("click", () => setCatalogView(button.dataset.catalogView));
    });
}

document.querySelectorAll("[data-auto-submit]").forEach((control) => {
    control.addEventListener("change", () => control.form?.requestSubmit());
});
