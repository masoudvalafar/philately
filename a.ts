<!DOCTYPE html >
    <html lang="en" >
        <head>
        <meta charset="UTF-8" >
            <meta name="viewport" content = "width=device-width, initial-scale=1.0" >
                <title>Image Gallery Component </title>
                    < script src = "https://cdn.tailwindcss.com" > </script>
                        < link href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel = "stylesheet" >
                            <style>
                            body {
    font - family: 'Inter', sans - serif;
}
</style>
    </head>
    < body class="bg-gray-100 p-6" >
        <div class="container mx-auto" >
            <div id="image-components-container" class="space-y-8" >
                </div>
                </div>

                <script>
/**
 * Creates an image gallery component with a title, description, and a grid of images.
 *
 * @param {object} options - Configuration options for the component.
 * @param {string} options.title - The title of the component.
 * @param {string} options.description - The description of the component.
 * @param {array} options.images - An array of image objects.
 * Each object should have a 'url' property (required)
 * and an optional 'alt' and 'description' property.
 *
 * @returns {HTMLElement} - The created image gallery component as a DOM element.
 */
function createImageGalleryComponent(options) {
    const { title, description, images } = options;

    // Create the main container for the component.
    const componentContainer = document.createElement('div');
    componentContainer.classList.add('bg-white', 'rounded-lg', 'shadow-md', 'p-6');

    // Create the title element.
    const titleElement = document.createElement('h2');
    titleElement.classList.add('text-2xl', 'font-semibold', 'text-gray-800', 'mb-4');
    titleElement.textContent = title;

    // Create the description element.
    const descriptionElement = document.createElement('p');
    descriptionElement.classList.add('text-gray-600', 'mb-6');
    descriptionElement.textContent = description;

    // Create the image grid container.
    const imageGrid = document.createElement('div');
    imageGrid.classList.add('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'gap-6');

    // Iterate over the images array and create an image item for each.
    images.forEach(image => {
        const imageItem = createImageItem(image);
        imageGrid.appendChild(imageItem);
    });

    // Append the title, description, and image grid to the component container.
    componentContainer.appendChild(titleElement);
    componentContainer.appendChild(descriptionElement);
    componentContainer.appendChild(imageGrid);

    return componentContainer;
}

/**
 * Creates a single image item with an image and optional description.
 *
 * @param {object} image - The image object.
 * @param {string} image.url - The URL of the image.
 * @param {string} [image.alt] - The alternative text for the image (optional).
 * @param {string} [image.description] - The description of the image (optional).
 *
 * @returns {HTMLElement} - The created image item as a DOM element.
 */
function createImageItem(image) {
    const imageItemContainer = document.createElement('div');
    imageItemContainer.classList.add('rounded-lg', 'overflow-hidden', 'shadow-sm', 'border', 'border-gray-200');

    // Create the image element.
    const imageElement = document.createElement('img');
    imageElement.src = image.url;
    imageElement.alt = image.alt || 'Image'; // Provide a default alt text if none is given.
    imageElement.classList.add('w-full', 'h-auto', 'object-cover');

    // Append the image to the image item container.
    imageItemContainer.appendChild(imageElement);

    // If there's a description, create and append it.
    if (image.description) {
        const imageDescription = document.createElement('p');
        imageDescription.classList.add('text-gray-700', 'text-sm', 'p-4');
        imageDescription.textContent = image.description;
        imageItemContainer.appendChild(imageDescription);
    }

    return imageItemContainer;
}

// Example usage:
const imageComponentsData = [
    {
        title: "Landscapes",
        description: "Beautiful images of various landscapes.",
        images: [
            { url: "https://placehold.co/600x400/008000/FFFFFF", alt: "Green Hills", description: "Rolling green hills at sunset." },
            { url: "https://placehold.co/600x400/0000FF/FFFFFF", alt: "Mountain Range", description: "Snowy mountain range." },
            { url: "https://placehold.co/600x400/FFA500/FFFFFF", alt: "Desert Dunes", description: "Vast desert dunes." },
        ]
    },
    {
        title: "Wildlife",
        description: "Amazing photos of wildlife in their natural habitats.",
        images: [
            { url: "https://placehold.co/600x400/FF0000/FFFFFF", alt: "Lion", description: "A majestic lion." },
            { url: "https://placehold.co/600x400/00FFFF/000000", alt: "Parrot", description: "A colorful parrot." },
        ]
    },
    {
        title: "Architecture",
        description: "Stunning architectural designs.",
        images: [
            { url: "https://placehold.co/600x400/FFFF00/000000", alt: "City Skyline", description: "Modern city skyline." },
            { url: "https://placehold.co/600x400/800080/FFFFFF", alt: "Ancient Ruins", description: "Ancient ruins." },
            { url: "https://placehold.co/600x400/008080/FFFFFF", alt: "Bridge", description: "A beautiful bridge." }
        ]
    }
];

// Get the container element where the image components will be added.
const container = document.getElementById('image-components-container');

// Loop through the data and create a component for each item.
imageComponentsData.forEach(componentData => {
    const component = createImageGalleryComponent(componentData);
    container.appendChild(component);
});
</script>
    </body>
    </html>
