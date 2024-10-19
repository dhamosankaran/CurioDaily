/*const API_BASE = getApiBaseUrl();

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


 function getApiBaseUrl() {
    if (window.location.hostname === 'www.thecuriodaily.com' || window.location.hostname === 'thecuriodaily.com') {
        return 'https://www.thecuriodaily.com';
    } else if (window.location.hostname === 'autonomous-newsletter-457954888435.us-central1.run.app') {
        return 'https://autonomous-newsletter-457954888435.us-central1.run.app';
    } else {
        return 'https://localhost:8443';
    }
}
 */


/**
 * Configuration for API base URLs.
 * @constant {Object}
 */
const API_URLS = {
    PROD: 'https://www.thecuriodaily.com',
    CLOUD_RUN: 'https://autonomous-newsletter-457954888435.us-central1.run.app',
    LOCAL: 'https://localhost:8443'
};

/**
 * Determines the appropriate API base URL based on the current hostname.
 * @returns {string} The API base URL.
 */
function getApiBaseUrl() {
    const hostname = window.location.hostname;
    switch(hostname) {
        case 'www.thecuriodaily.com':
        case 'thecuriodaily.com':
            return API_URLS.PROD;
        case 'autonomous-newsletter-457954888435.us-central1.run.app':
            return API_URLS.CLOUD_RUN;
        case 'localhost':
            return API_URLS.LOCAL;
        default:
            console.warn(`Unexpected hostname: ${hostname}. Defaulting to local URL.`);
            return API_URLS.LOCAL;
    }
}

// Define API_BASE in the global scope
let API_BASE;

try {
    API_BASE = getApiBaseUrl();
    console.log(`API Base URL: ${API_BASE}`);
} catch (error) {
    console.error('Error determining API base URL:', error);
    // Set a default value in case of an error
    API_BASE = API_URLS.LOCAL;
}

  function unsubscribe(subscriptionId) {
    if (window.location.search.includes('unsubscribe=success')) {
        showUnsubscribeMessage();
        return;
    }

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
    if (typeof gtag !== 'undefined') {
        gtag('config', 'G-583RG4CHLK', {
            'page_path': url,
            'page_title': title
        });
    }
    console.log(`Page viewed: ${url}, Title: ${title}`);
    
    fetch(`${API_BASE}/api/analytics/track-pageview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, title }),
    }).catch(error => console.error('Error tracking page view:', error));
}

function trackEvent(category, action, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
    
    console.log(`Event: Category - ${category}, Action - ${action}, Label - ${label}`);
    
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
    //alert(section.innerHTML);

    addReadMoreEventListeners(section, [latestArticle, ...recentPreviousArticles]);

    return section;
}

function getTopicIcon(topicName) {
    const iconMap = {
        'AI': 'fas fa-robot',
        'Technology': 'fas fa-microchip',
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

    return iconMap[topicName] || 'fas fa-newspaper';
}

function getWeeklyTopicIcon(topicName) {
    const iconMap = {
        'AI Weekly Roundup': 'fas fa-robot',
        'Business & Finance Weekly': 'fas fa-chart-line',
        'Tech Industry Highlights': 'fas fa-microchip',
        'Startup & Innovation Pulse': 'fas fa-lightbulb',
        'China Insights Weekly': 'fas fa-dragon',
        'Global Affairs Digest': 'fas fa-globe',
        'Crypto & Blockchain Digest': 'fas fa-coins',
        'Gadget Roundup of the Week': 'fas fa-mobile-alt',
        'Health & Wellness Update': 'fas fa-heartbeat',
        'Deals of the Week': 'fas fa-tags',
        'Top Podcasts This Week': 'fas fa-podcast',
        'Climate & Environment Report': 'fas fa-leaf',
        'Biotech Breakthroughs Weekly': 'fas fa-dna',
        'Space Exploration News': 'fas fa-rocket',
        'Renewable Energy Update': 'fas fa-solar-panel',
        'Consumer Trends Weekly': 'fas fa-shopping-bag',
        'AI Research Highlights': 'fas fa-brain',
        'Cybersecurity Weekly': 'fas fa-shield-alt',
        'Future of Work Insights': 'fas fa-briefcase'
    };

    return iconMap[topicName] || 'fas fa-newspaper';
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

function openArticle(article) {
    const baseUrl = window.location.origin;
    const articleUrl = `${baseUrl}/api/newsletters/${article.id}`;
    
    console.log('Opening article URL:', articleUrl);
    window.open(articleUrl, '_blank');
}

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

function fetchWeeklyTopics() {
    fetch('/api/weekly-newsletter-topics/active')
        .then(response => response.json())
        .then(topics => {
            const topicsList = document.getElementById('weeklyTopicsList');
            topicsList.innerHTML = ''; // Clear existing items
            topics.forEach(topic => {
                const iconWeeklyClass = getWeeklyTopicIcon(topic.name);
                const li = document.createElement('li');
                li.innerHTML = `<a href="#" class="menu-item"><i class="${iconWeeklyClass}"></i> ${topic.name}</a>`;
                li.querySelector('a').addEventListener('click', (e) => {
                    e.preventDefault();
                    openWeeklyNewsletter(topic.id);
                });
                topicsList.appendChild(li);
            });
            setupWeeklyTopicsListeners();
        })
        .catch(error => console.error('Error fetching weekly topics:', error));
}

function setupWeeklyTopicsListeners() {
    document.querySelectorAll('#weeklyTopicsList a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const topicId = this.getAttribute('data-topic-id');
            if (topicId) {
                openWeeklyNewsletter(topicId);
            } else {
                console.warn('No topic ID found for this weekly topic');
            }
            // Close the menu after clicking (for mobile)
            document.getElementById('sideMenu').classList.remove('active');
            document.querySelector('.menu-overlay').classList.remove('active');
        });
    });
}

function openWeeklyNewsletter(topicId) {
    if (!topicId) {
        console.error('Invalid topicId provided');
        return null;
    }

    const baseUrl = window.location.origin;
    const encodedTopicId = encodeURIComponent(topicId);
    const newsletterUrl = `${baseUrl}/api/weekly-newsletter/topic/${encodedTopicId}/render`;
    
    console.log('Opening weekly newsletter URL:', newsletterUrl);
    
    try {
        const newWindow = window.open(newsletterUrl, '_blank');
        if (!newWindow) {
            console.warn('Popup blocker may have prevented opening the newsletter');
        }
        return newWindow;
    } catch (error) {
        console.error('Error opening weekly newsletter:', error);
        return null;
    }
}

function populateTopicGroups(topics) {
    const topicGroupsContainer = document.getElementById('topicGroups');
    if (!topicGroupsContainer) {
        console.warn('Topic groups container not found');
        return;
    }
    topicGroupsContainer.innerHTML = '';

    const predefinedGroups = {
        'News & Current Affairs': ['AI', 'Technology', 'Business', 'Science'],
        'Lifestyle & Wellness': ['Travel', 'Yoga', 'Nutrition', 'Fitness', 'Mental Health', 'Meditation', 'Sleep Science'],
        'Entertainment & Culture': ['Entertainment', 'Sports', 'Games', 'Social Media & Viral News'],
        'Science & Technology': ['Education', 'Space', 'Psychology', 'Gadgets']
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

        if (groupDiv.childElementCount > 1) {
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

    // Hide the message after 3 seconds
    if (message) {
        setTimeout(() => {
            validationMessage.style.display = 'none';
        }, 3000);
    }
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


document.addEventListener('DOMContentLoaded', fetchWeeklyTopics);

document.addEventListener('DOMContentLoaded', () => {
    trackPageView('/', 'CurioDaily - Your Daily Dose of Interesting');
    
    initializeSubscribeForm();
    fetchTopicsAndArticles();
    setupHomeButton();

    const subscribeModal = document.getElementById('subscribeModal');
    const subscribeBtn = document.getElementById('subscribeBtn');
    const closeBtn = document.getElementsByClassName('close')[0];
    const footerSubscribeBtn = document.getElementById('footerSubscribeBtn');
    const footerEmailInput = document.getElementById('footerEmailInput');

    const menuBtn = document.getElementById('menuBtn');
    const menuClose = document.getElementById('menuClose');
    const sideMenu = document.getElementById('sideMenu');
    const overlay = document.querySelector('.menu-overlay');

    function openMenu() {
        sideMenu.classList.add('active');
        overlay.classList.add('active');
    }

    function closeMenu() {
        sideMenu.classList.remove('active');
        overlay.classList.remove('active');
    }

    if (menuBtn && sideMenu && overlay && menuClose) {
        menuBtn.addEventListener('click', openMenu);
        menuClose.addEventListener('click', closeMenu);
        overlay.addEventListener('click', closeMenu);

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && sideMenu.classList.contains('active')) {
                closeMenu();
            }
        });
    } else {
        console.error('One or more menu elements are missing.');
    }

    const newsletterForm = document.querySelector('.newsletter-signup');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Thank you for signing up!');
        });
    }

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

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('unsubscribe') === 'success') {
        showUnsubscribeMessage();
    }

    const subscribeForm = document.getElementById('subscribeForm');
    if (subscribeForm) {
        subscribeForm.addEventListener('submit', handleSubscribeFormSubmit);
    } else {
        console.warn('Subscribe form not found');
    }

    handleEmailUnsubscribe();

    // Auto-open modal after 5 seconds
    let hasShownModal = sessionStorage.getItem('hasShownModal');
    if (!hasShownModal) {
        setTimeout(() => {
            subscribeModal.style.display = 'block';
            sessionStorage.setItem('hasShownModal', 'true');
            trackEvent('Subscription', 'Auto Open Modal', 'Timed');
        }, 10000);
    }
});

function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

function handleEmailUnsubscribe() {
    const unsubscribeEmail = getUrlParameter('unsubscribe');
    if (unsubscribeEmail) {
        const decodedEmail = decodeURIComponent(unsubscribeEmail);
        if (confirm(`Are you sure you want to unsubscribe ${decodedEmail}?`)) {
            unsubscribe(decodedEmail);
        }
    }
}

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

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateEmail,
        formatDate,
        getApiBaseUrl,
        trackPageView,
        trackEvent,
    };
}