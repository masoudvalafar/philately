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