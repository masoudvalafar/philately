function addItem(item, elem) {
    const div = document.createElement('div');

    div.className = 'item';
    div.innerHTML += `<p class="item-title">${item.title}</p>`;
    div.innerHTML += `<p>${item.description}</p>`;
    div.innerHTML += `<div class="row">
                        <div class="column">
                            <img src="./images/${item.id}_front.jpg" style="width:100%">
                        </div>
                        <div class="column">
                            <img src="./images/${item.id}_back.jpg" style="width:100%">
                        </div>
                    </div>`;

    document.getElementById(elem).appendChild(div);
}

function getMenus(activeMenu) {
    const pages = [
        ["Home", "./index.html"],
        ["Education", "./education.html"],
        ["Rate", "./rate.html"],
        // ["Forgeries", "./forgery.html"],
        ["Collection", "./collection.html"],
        ["Resources", "./resources.html"],
    ]

    const div = document.createElement('div');
    div.className = 'topnav';

    for (let i = 0; i < pages.length; i++) {
        if (activeMenu === pages[i][0]) {
            div.innerHTML += ` <a href="` + pages[i][1] + `" class="activenav">` + pages[i][0] + `</a>`
        } else {
            div.innerHTML += ` <a href="` + pages[i][1] + `">` + pages[i][0] + `</a>`
        }
    }
    document.getElementById("main-main").appendChild(div);
}