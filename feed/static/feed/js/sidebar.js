document.addEventListener("DOMContentLoaded", () => {

    const categoryItems = document.querySelectorAll(".category-item");

    categoryItems.forEach(item => {

        const button = item.querySelector(".toggle-btn");
        const feedList = item.querySelector(".feed-list");
        const categorySlug = item.dataset.category;

        if (!button || !feedList) {
            return;
        }

        const isOpen = localStorage.getItem(categorySlug) === "true";

        if (isOpen) {
            feedList.classList.remove("hidden");
            button.textContent = "▼";
            button.setAttribute("aria-expanded", "true");
        }

        button.addEventListener("click", () => {
            
            feedList.classList.toggle("hidden");

            const nowOpen = !feedList.classList.contains("hidden");

            button.textContent = nowOpen ? "▼" : "▶";
            button.setAttribute("aria-expanded", nowOpen);

            localStorage.setItem(categorySlug, nowOpen);

        });
    });

    const menuButton = document.getElementById("menu-button");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    
    if (menuButton && sidebar && overlay) {
        menuButton.addEventListener("click", () => {
            console.log("clicked");
            sidebar.classList.toggle("open");
            overlay.classList.toggle("show");
        });

        overlay.addEventListener("click", () => {
            sidebar.classList.remove("open");
            overlay.classList.remove("show");
        });

        sidebar.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                sidebar.classList.remove("open");
                overlay.classList.remove("show");
            });
        });
    }
});
