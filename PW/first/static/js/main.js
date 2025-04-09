document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const searchBtn = document.getElementById('search-btn');
    const originInput = document.getElementById('origin-input');
    const destinationInput = document.getElementById('destination-input');
    const loadingElement = document.getElementById('loading');
    const routeInfo = document.getElementById('route-info');
    const mapElement = document.getElementById('map');
    const distanceValue = document.getElementById('distance-value');
    const originValue = document.getElementById('origin-value');
    const destinationValue = document.getElementById('destination-value');
    const popularDestinationsElement = document.getElementById('popular-destinations');

    // Fetch popular destinations
    fetchPopularDestinations();

    // Event listeners
    searchBtn.addEventListener('click', findRoute);
    destinationInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            findRoute();
        }
    });

    // Function to find a route
    function findRoute() {
        // Show loading
        loadingElement.classList.remove('is-hidden');
        routeInfo.classList.add('is-hidden');
        
        // Get values
        const origin = originInput.value || 'Bejaia, Algeria';
        const destination = destinationInput.value;
        
        if (!destination) {
            showError('Please enter a destination');
            loadingElement.classList.add('is-hidden');
            return;
        }

        // Send request to server
        fetch('/get_route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                origin: origin,
                destination: destination
            }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Server error');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading
            loadingElement.classList.add('is-hidden');
            
            // Display map
            mapElement.innerHTML = data.map_html;
            
            // Update route info
            distanceValue.textContent = data.distance;
            originValue.textContent = data.origin.name;
            destinationValue.textContent = data.destination.name;
            
            // Show route info with animation
            routeInfo.classList.remove('is-hidden');
            routeInfo.style.opacity = '0';
            setTimeout(() => {
                routeInfo.style.opacity = '1';
            }, 10);
        })
        .catch(error => {
            loadingElement.classList.add('is-hidden');
            showError(error.message);
        });
    }

    // Function to fetch popular destinations
    function fetchPopularDestinations() {
        fetch('/popular_destinations')
            .then(response => response.json())
            .then(destinations => {
                popularDestinationsElement.innerHTML = '';
                destinations.forEach(dest => {
                    const tag = document.createElement('span');
                    tag.className = 'tag is-medium destination-tag m-1';
                    tag.textContent = dest.name;
                    tag.title = dest.description;
                    tag.addEventListener('click', () => {
                        destinationInput.value = dest.name;
                        findRoute();
                    });
                    popularDestinationsElement.appendChild(tag);
                });
            })
            .catch(error => {
                console.error('Error fetching popular destinations:', error);
            });
    }

    // Function to show errors
    function showError(message) {
        const notification = document.createElement('div');
        notification.className = 'notification is-danger is-light';
        
        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete';
        deleteButton.addEventListener('click', () => {
            notification.remove();
        });
        
        notification.appendChild(deleteButton);
        notification.appendChild(document.createTextNode(message));
        
        // Insert after the search button
        searchBtn.parentNode.parentNode.insertAdjacentElement('afterend', notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
});
