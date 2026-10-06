(function() {
    var current = 0;
    var total = {{ TOTAL_PAGES }};
    var dashId = "{{ DASH_ID }}";
    var titles = {{ TITLES_JSON }};

    var btnPrev = document.getElementById("eda-prev-" + dashId);
    var btnNext = document.getElementById("eda-next-" + dashId);
    var titleSpan = document.getElementById("eda-title-" + dashId);
    var counterSpan = document.getElementById("eda-counter-" + dashId);

    if (btnPrev) btnPrev.disabled = false;
    if (btnNext) btnNext.disabled = false;

    function updateView() {
        for(var i=0; i<total; i++) {
            var page = document.getElementById("eda-page-" + dashId + "-" + i);
            if(page) page.style.display = (i === current) ? "block" : "none";
        }
        if (titleSpan) titleSpan.innerText = titles[current];
        if (counterSpan) counterSpan.innerText = (current + 1);
    }

    if (btnPrev) {
        btnPrev.onclick = function() { 
            current = (current === 0) ? total - 1 : current - 1; 
            updateView(); 
        };
    }

    if (btnNext) {
        btnNext.onclick = function() { 
            current = (current === total - 1) ? 0 : current + 1; 
            updateView(); 
        };
    }
})();