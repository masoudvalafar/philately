var collapsible = document.getElementsByClassName("collapsible");
addCollapsibleListener(collapsible);

function addCollapsibleListener(coll) {
    var i;

    for (i = 0; i < coll.length; i++) {
        coll[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display === "block") {
                content.style.display = "none";
            } else {
                content.style.display = "block";
            }
        });
    }
}

function addItem(item, elem) {
    const div = document.createElement(elem);

    div.className = 'item-div';
    div.innerHTML = `<p>1 Chahi charity tax was imposed in Tehran during XX/XX/XX to XX/XX/XX. </p>`;

    document.getElementById('bbb').appendChild(div);

}

