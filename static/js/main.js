const themeButton = document.getElementById("themeButton");
const themeIcon = document.getElementById("themeIcon");
const searchInput = document.getElementById("searchInput");
const heroVisual = document.getElementById("heroVisual");

const savedTheme = localStorage.getItem("atlas-theme");


function updateThemeIcon() {
    const lightThemeEnabled =
        document.body.classList.contains("light-theme");

    themeIcon.textContent = lightThemeEnabled ? "☀" : "☾";
}


if (savedTheme === "light") {
    document.body.classList.add("light-theme");
}

updateThemeIcon();


themeButton.addEventListener("click", function () {
    document.body.classList.toggle("light-theme");

    const lightThemeEnabled =
        document.body.classList.contains("light-theme");

    localStorage.setItem(
        "atlas-theme",
        lightThemeEnabled ? "light" : "dark"
    );

    updateThemeIcon();
});


const filterButtons = document.querySelectorAll(
    ".quick-filters button"
);


filterButtons.forEach(function (button) {
    button.addEventListener("click", function () {
        const filter =
            button.getAttribute("data-filter");

        window.location.href =
            "/?q=" + encodeURIComponent(filter);
    });
});


document.addEventListener("keydown", function (event) {
    const ctrlPressed =
        event.ctrlKey || event.metaKey;

    if (ctrlPressed && event.key.toLowerCase() === "k") {
        event.preventDefault();

        searchInput.focus();
        searchInput.select();
    }
});


if (heroVisual) {
    document.addEventListener("mousemove", function (event) {
        if (window.innerWidth < 900) {
            return;
        }

        const mouseX =
            event.clientX / window.innerWidth - 0.5;

        const mouseY =
            event.clientY / window.innerHeight - 0.5;

        heroVisual.style.transform =
            `rotateY(${mouseX * 5}deg)
             rotateX(${mouseY * -5}deg)`;
    });


    document.addEventListener("mouseleave", function () {
        heroVisual.style.transform =
            "rotateY(0deg) rotateX(0deg)";
    });
}
document.querySelectorAll(".match-progress-fill").forEach(bar => {
    const value = bar.dataset.match || 0;
    bar.style.width = value + "%";
});