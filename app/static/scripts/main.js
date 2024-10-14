const API_BASE = getApiBaseUrl();

const PROD_URL = 'https://www.thecuriodaily.com';
const CLOUD_RUN_URL = 'https://autonomous-newsletter-457954888435.us-central1.run.app';
const LOCAL_URL = 'https://localhost:8443';


function getApiBaseUrl() {
    switch(window.location.hostname) {
      case 'www.thecuriodaily.com':
      case 'thecuriodaily.com':
        return PROD_URL;
      case 'autonomous-newsletter-457954888435.us-central1.run.app':
        return CLOUD_RUN_URL;
      default:
        console.warn(`Unexpected hostname: ${window.location.hostname}. Defaulting to local URL.`);
        return LOCAL_URL;
    }
  }

function unsubscribe(subscriptionId) {
    // For GET requests (when clicked from email)
    if (window.location.search.includes('unsubscribe=success')) {
        showUnsubscribeMessage();
        return;
    }

    // For PUT requests (when triggered from the website)
    fetch(`${API_BASE}/api/subscriptions/${subscriptionId}/unsubscribe`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            showUnsubscribeMessage();
        } else {
            throw new Error('Failed to unsubscribe');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while trying to unsubscribe. Please try again later.');
    });
}

function showUnsubscribeMessage() {
    const messageElement = document.getElementById('unsubscribeMessage');
    if (messageElement) {
        messageElement.style.display = 'block';
        window.scrollTo(0, 0);
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 5000);
    }
}

function trackPageView(url, title) {
    // Google Analytics pageview tracking
    if (typeof gtag !== 'undefined') {
        gtag('config', 'G-583RG4CHLK', {
            'page_path': url,
            'page_title': title
        });
    }
    // Custom tracking
    console.log(`Page viewed: ${url}, Title: ${title}`);
    
    // Send data to backend
    fetch(`${API_BASE}/api/analytics/track-pageview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, title }),
    }).catch(error => console.error('Error tracking page view:', error));
}

function trackEvent(category, action, label) {
    // Google Analytics event tracking
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
    
    // Custom tracking
    console.log(`Event: Category - ${category}, Action - ${action}, Label - ${label}`);
    
    // Send data to backend
    fetch(`${API_BASE}/api/analytics/track-event`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ category, action, label }),
    }).catch(error => console.error('Error tracking event:', error));
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}




// Fetch and display topics and articles
async function fetchTopicsAndArticles() {
    try {
        const topics = await fetchTopics();
        const topicGrid = document.getElementById('topicGrid');
        if (!topicGrid) {
            console.warn('Topic grid element not found');
            return;
        }

        for (const topic of topics) {
            const articles = await fetchArticlesForTopic(topic.id);
            if (articles.length === 0) continue;

            const section = createTopicSection(topic, articles);
            topicGrid.appendChild(section);
        }
    } catch (error) {
        console.error('Error fetching topics and articles:', error);
    }
}

async function fetchArticlesForTopic(topicId) {
    try {
        const response = await fetch(`${API_BASE}/api/newsletters/topic/${topicId}`);
        if (!response.ok) {
            if (response.status === 404) {
                console.log(`No articles found for topic ID ${topicId}`);
                return [];
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const articles = await response.json();
        return articles.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } catch (error) {
        console.error(`Error fetching articles for topic ID ${topicId}:`, error);
        return [];
    }
}

function createTopicSection(topic, articles) {
    const section = document.createElement('section');
    section.className = `topic-section ${topic.name.toLowerCase().replace(/[&\s]+/g, '-')}`;

    const today = new Date();
    const threeDaysAgo = new Date(today.getTime() - (3 * 24 * 60 * 60 * 1000));
    const formattedToday = formatDate(today);

    const [latestArticle, ...previousArticles] = articles;
    const recentPreviousArticles = previousArticles
        .filter(article => new Date(article.created_at) >= threeDaysAgo)
        .slice(0, 3);

    const iconClass = getTopicIcon(topic.name);
    
    section.innerHTML = `
        <h2>
            <i class="${iconClass}" aria-hidden="true"></i>
            <span>${topic.name}</span>
        </h2>
        ${createTodayUpdateHTML(latestArticle, formattedToday)}
        ${createPreviousUpdatesHTML(recentPreviousArticles)}
    `;

    addReadMoreEventListeners(section, [latestArticle, ...recentPreviousArticles]);

    return section;
}

function getTopicIcon(topicName) {
    const iconMap = {
        'AI': 'fas fa-robot',
        'Technology': 'fas fa-microchip',  // Add this line
        'Business': 'fas fa-briefcase',
        'Science': 'fas fa-flask',
        'Politics': 'fas fa-landmark',
        'Finance': 'fas fa-money-bill-wave',
        'Health': 'fas fa-heartbeat',
        'Travel': 'fas fa-plane',
        'Yoga': 'fas fa-om',
        'Nutrition': 'fas fa-apple-alt',
        'Fitness': 'fas fa-dumbbell',
        'Mental Health': 'fas fa-brain',
        'Meditation': 'fas fa-spa',
        'Sleep Science': 'fas fa-bed',
        'Entertainment': 'fas fa-film',
        'Sports': 'fas fa-football-ball',
        'Games': 'fas fa-gamepad',
        'Social Media & Viral News': 'fas fa-share-alt',
        'Education': 'fas fa-graduation-cap',
        'Space': 'fas fa-rocket',
        'Psychology': 'fas fa-user-md',
        'Gadgets': 'fas fa-mobile-alt'
    };

    return iconMap[topicName] || 'fas fa-newspaper'; // Default icon if not found
}

function createTodayUpdateHTML(article, formattedDate) {
    return `
        <div class="today-update">
            <h3>Today's Update (${formattedDate})</h3>
            <ul class="article-list">
                <li>
                    ${article.title}
                    <a href="#" class="read-more" data-article-id="0">Read More</a>
                </li>
            </ul>
        </div>
    `;
}

function createPreviousUpdatesHTML(articles) {
    if (articles.length === 0) return '';

    const listItems = articles.map((article, index) => `
        <li>
            ${article.title}
            <a href="#" class="read-more" data-article-id="${index + 1}">Read More</a>
            <span class="article-date">(${formatDate(article.created_at)})</span>
        </li>
    `).join('');

    return `
        <div class="previous-updates">
            <h3>Previous Updates</h3>
            <ul class="article-list">
                ${listItems}
            </ul>
        </div>
    `;
}

function addReadMoreEventListeners(section, articles) {
    section.querySelectorAll('.read-more').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const articleId = parseInt(e.target.getAttribute('data-article-id'), 10);
            const article = articles[articleId];
            
            // Fetch the full article content if it's not already available
            if (!article.content) {
                fetch(`${getApiBaseUrl()}/api/newsletters/${article.id}`)
                    .then(response => response.json())
                    .then(data => {
                        article.content = data.content;
                        openArticle(article);
                    })
                    .catch(error => console.error('Error fetching article:', error));
            } else {
                openArticle(article);
            }
        });
    });
}


function openArticle(articleId) {


    const baseUrl = window.location.origin;
    const articleUrl = `${baseUrl}/api/newsletters/${articleId.id}`;
    
    console.log('Opening article URL:', articleUrl);

    // Open the URL directly in a new tab
    window.open(articleUrl, '_blank');
}

// Subscribe form functionality
async function fetchTopics() {
    try {
        const response = await fetch(`${API_BASE}/api/topics`);
        const topics = await response.json();
        return topics.sort((a, b) => a.id - b.id);
    } catch (error) {
        console.error('Error fetching topics:', error);
        return [];
    }
}

function populateTopicGroups(topics) {
    const topicGroupsContainer = document.getElementById('topicGroups');
    if (!topicGroupsContainer) {
        console.warn('Topic groups container not found');
        return;
    }
    topicGroupsContainer.innerHTML = '';

    /*const predefinedGroups = {
        'News & Current Affairs': ['AI', 'Technology', 'Business', 'Science', 'Politics', 'Finance'],
        'Lifestyle & Wellness': ['Health', 'Travel', 'Yoga', 'Nutrition', 'Fitness', 'Mental Health', 'Meditation', 'Sleep Science'],
        'Entertainment & Culture': ['Entertainment', 'Sports', 'Games', 'Social Media & Viral News'],
        'Science & Technology': ['Education', 'Space', 'Psychology', 'Gadgets']
    };*/

    const predefinedGroups = {
        'News & Current Affairs': ['AI', 'Technology', 'Business', 'Science'],
        'Lifestyle & Wellness': ['Travel', 'Nutrition', 'Fitness','Mental Health'],
        'Entertainment & Culture': ['Entertainment', 'Sports','Social Media & Viral News'],
        'Science & Tech': ['Education', 'Space']
    };

    for (const [groupName, groupTopics] of Object.entries(predefinedGroups)) {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'topic-group';
        groupDiv.innerHTML = `<h3>${groupName}</h3>`;

        groupTopics.forEach(topicName => {
            const topic = topics.find(t => t.name === topicName);
            if (topic) {
                const label = document.createElement('label');
                label.innerHTML = `<input type="checkbox" name="topics" value="${topic.id}"> ${topic.name}`;
                groupDiv.appendChild(label);
            }
        });

        if (groupDiv.childElementCount > 1) { // Only add group if it has topics
            topicGroupsContainer.appendChild(groupDiv);
        }
    }
}

function validateForm() {
    const name = document.getElementById('nameInput').value;
    const email = document.getElementById('emailInput').value;
    const topics = document.querySelectorAll('input[name="topics"]:checked');
    const subscribeButton = document.querySelector('#subscribeForm button');
    
    const isNameValid = name.trim() !== '';
    const isEmailValid = validateEmail(email);
    const isTopicSelected = topics.length > 0;
    
    const isValid = isNameValid && isEmailValid && isTopicSelected;
    subscribeButton.disabled = !isValid;

    // Show validation messages
    showValidationMessage(document.getElementById('nameInput'), isNameValid ? '' : 'Please enter your name.');
    showValidationMessage(document.getElementById('emailInput'), isEmailValid ? '' : 'Please enter a valid email address.');
    showValidationMessage(document.getElementById('topicGroups'), isTopicSelected ? '' : 'Please select at least one topic.');

    return isValid;
}

function showValidationMessage(element, message) {
    let validationMessage = element.nextElementSibling;
    if (!validationMessage || !validationMessage.classList.contains('validation-message')) {
        validationMessage = document.createElement('div');
        validationMessage.classList.add('validation-message');
        element.parentNode.insertBefore(validationMessage, element.nextSibling);
    }
    validationMessage.textContent = message;
    validationMessage.style.display = message ? 'block' : 'none';
}

async function initializeSubscribeForm() {
    try {
        const topics = await fetchTopics();
        populateTopicGroups(topics);
    } catch (error) {
        console.error('Error initializing subscribe form:', error);
    }
}
function goToHomePage() {
    window.location.href = API_BASE;
}

function setupHomeButton() {
    const homeBtn = document.getElementById('HomeBtn');
    if (homeBtn) {
        homeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            goToHomePage();
        });
    } else {
        console.warn('Home button not found in the DOM');
    }
}

// Event listeners and initialization
document.addEventListener('DOMContentLoaded', () => {
    // Track homepage view
    trackPageView('/', 'CurioDaily - Your Daily Dose of Interesting');
    
    const menuBtn = document.getElementById('menuBtn');
    const sideMenu = document.getElementById('sideMenu');

    if (menuBtn && sideMenu) {
        menuBtn.addEventListener('click', () => {
            sideMenu.classList.toggle('active');
            trackEvent('Navigation', 'Toggle Menu', sideMenu.classList.contains('active') ? 'Open' : 'Close');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!sideMenu.contains(event.target) && event.target !== menuBtn) {
                sideMenu.classList.remove('active');
            }
        });

        // Add event listeners for menu items
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            item.addEventListener('click', (event) => {
                event.preventDefault();
                const itemName = item.textContent;
                trackEvent('Navigation', 'Menu Item Click', itemName);
                // Implement the action for each menu item here
                console.log(`Clicked on ${itemName}`);
                sideMenu.classList.remove('active');
            });
        });
    }

    initializeSubscribeForm();
    fetchTopicsAndArticles();

    setupHomeButton();

    const subscribeModal = document.getElementById('subscribeModal');
    const subscribeBtn = document.getElementById('subscribeBtn');
    const closeBtn = document.getElementsByClassName('close')[0];
    const footerSubscribeBtn = document.getElementById('footerSubscribeBtn');
    const footerEmailInput = document.getElementById('footerEmailInput');


    if (subscribeBtn) {
        subscribeBtn.onclick = () => {
            subscribeModal.style.display = 'block';
            trackEvent('Subscription', 'Open Modal', 'Header Button');
        };
    } else {
        console.warn('Subscribe button not found');
    }

    if (closeBtn) {
        closeBtn.onclick = () => {
            subscribeModal.style.display = 'none';
            trackEvent('Subscription', 'Close Modal', 'X Button');
        };
    } else {
        console.warn('Close button not found');
    }

    window.onclick = (event) => {
        if (event.target == subscribeModal) {
            subscribeModal.style.display = 'none';
            trackEvent('Subscription', 'Close Modal', 'Outside Click');
        }
    }

    if (footerSubscribeBtn && footerEmailInput) {
        footerSubscribeBtn.addEventListener('click', () => {
            if (validateEmail(footerEmailInput.value)) {
                subscribeModal.style.display = 'block';
                document.getElementById('emailInput').value = footerEmailInput.value;
                trackEvent('Subscription', 'Open Modal', 'Footer Button');
            } else {
                showValidationMessage(footerEmailInput, 'Please enter a valid email address.');
                trackEvent('Subscription', 'Validation Error', 'Footer Email');
            }
        });
    } else {
        console.warn('Footer subscribe button or email input not found');
    }

    // Check for unsubscribe success parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('unsubscribe') === 'success') {

        showUnsubscribeMessage();
    }

    // Set up subscribe form submission handler
    const subscribeForm = document.getElementById('subscribeForm');
    if (subscribeForm) {
        subscribeForm.addEventListener('submit', handleSubscribeFormSubmit);
    } else {
        console.warn('Subscribe form not found');
    }

    // Set up unsubscribe link handler
    //document.body.addEventListener('click', handleUnsubscribeClick);

    // Handle email unsubscribe
    handleEmailUnsubscribe();
});

// Utility function to get URL parameters
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// Function to handle unsubscribe from email link
function handleEmailUnsubscribe() {
    const unsubscribeEmail = getUrlParameter('unsubscribe');
    if (unsubscribeEmail) {
        const decodedEmail = decodeURIComponent(unsubscribeEmail);
        if (confirm(`Are you sure you want to unsubscribe ${decodedEmail}?`)) {
            unsubscribe(decodedEmail);
        }
    }
}

// Export functions for testing or external use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateEmail,
        formatDate,
        getApiBaseUrl,
        trackPageView,
        trackEvent,
        // Add other functions you want to export
    };
}

// ... (previous code remains the same)

async function handleSubscribeFormSubmit(e) {
    e.preventDefault();
    if (!validateForm()) return;

    const name = document.getElementById('nameInput').value;
    const email = document.getElementById('emailInput').value;
    const selectedTopicIds = Array.from(document.querySelectorAll('input[name="topics"]:checked')).map(el => parseInt(el.value));
    
    try {
        const response = await fetch(`${API_BASE}/api/subscriptions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                email: email,
                topic_ids: selectedTopicIds,
                is_active: true
            }),
        });
        
        const data = await response.json();

        if (response.ok) {
            alert('Thank you for subscribing to CurioDaily!');
            document.getElementById('subscribeModal').style.display = 'none';
            trackEvent('Subscription', 'Success', email);
        } else {
            if (response.status === 400 && data.detail.includes("already exists")) {
                const updateSubscription = confirm('This email is already subscribed. Would you like to update your topic preferences?');
                if (updateSubscription) {
                    console.log('Updating subscription for:', email);
                    trackEvent('Subscription', 'Update', email);
                    // Here you would add logic to update existing subscriptions
                    // For now, we'll just log it
                }
            } else {
                throw new Error(data.detail || 'Subscription failed');
            }
        }
    } catch (error) {
        console.error('Subscription error:', error);
        alert(`An error occurred: ${error.message}`);
        trackEvent('Subscription', 'Error', error.message);
    }
}



// Export functions for testing or external use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateEmail,
        formatDate,
        getApiBaseUrl,
        trackPageView,
        trackEvent,
        // Add other functions you want to export
    };
}

// Add this near the top of the file, after other initializations
let hasShownModal = sessionStorage.getItem('hasShownModal');

// Add this to the DOMContentLoaded event listener
if (!hasShownModal) {
    setTimeout(() => {
        subscribeModal.style.display = 'block';
        sessionStorage.setItem('hasShownModal', 'true');
        trackEvent('Subscription', 'Auto Open Modal', 'Timed');
    }, 5000);
}