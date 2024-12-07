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
   //alert("..."+1)
    fetch('/api/weekly-newsletter-topics/active')
        .then(response => response.json())
        .then(topics => {
            const topicsList = document.getElementById('weeklyTopicsList');
            topicsList.innerHTML = ''; // Clear existing items
            
            // First add My Personal Diary as a special entry
            const diaryLi = document.createElement('li');
            diaryLi.innerHTML = `
                <a href="/api/blog" class="menu-item" data-page="personal-diary">
                    <i class="fas fa-book"></i> My Personal Diary
                </a>
            `;
            // Add diary click handler
            diaryLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                // Track the page view
             
                // Navigate to diary page
                window.location.href = `${API_BASE}/api/blog`;
                // Close the side menu if it's open
                const sideMenu = document.getElementById('sideMenu');
                const overlay = document.querySelector('.menu-overlay');
                if (sideMenu && sideMenu.classList.contains('active')) {
                    sideMenu.classList.remove('active');
                    overlay.classList.remove('active');
                }
            });
            topicsList.appendChild(diaryLi);
            
            // Add a divider
            const divider = document.createElement('li');
            divider.className = 'menu-divider';
            topicsList.appendChild(divider);
            
            topics.forEach(topic => {
                const iconWeeklyClass = getWeeklyTopicIcon(topic.name);
                const li = document.createElement('li');
                li.innerHTML = `
                    <a href="#" class="menu-item" data-topic-id="${topic.id}">
                        <i class="${iconWeeklyClass}"></i> ${topic.name}
                    </a>
                `;
                li.querySelector('a').addEventListener('click', (e) => {
                    e.preventDefault();
                    openWeeklyNewsletter(topic.id);
                });
                topicsList.appendChild(li);
            });
            
            // Then add all other weekly topics
            /*topics.forEach(topic => {
                const iconWeeklyClass = getWeeklyTopicIcon(topic.name);
                const li = document.createElement('li');
                li.innerHTML = `<a href="#" class="menu-item"><i class="${iconWeeklyClass}"></i> ${topic.name}</a>`;
                li.querySelector('a').addEventListener('click', (e) => {
                    e.preventDefault();
                    openWeeklyNewsletter(topic.id);
                });
                topicsList.appendChild(li);
            });*/
            setupWeeklyTopicsListeners();
        })
        .catch(error => {
            console.error('Error fetching weekly topics:', error);
            // Add error handling UI if needed
            const topicsList = document.getElementById('weeklyTopicsList');
            topicsList.innerHTML = `
                <li class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    Failed to load topics. Please try again later.
                </li>
            `;
        });
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
        return;
    }

    const baseUrl = window.location.origin;
    const encodedTopicId = encodeURIComponent(topicId);
    const newsletterUrl = `${baseUrl}/api/weekly-newsletter/topic/${encodedTopicId}/render`;
    
    console.log('Navigating to weekly newsletter URL:', newsletterUrl);
    
    try {
        // Track the page view before navigation
        const topicName = document.querySelector(`[data-topic-id="${topicId}"]`)?.textContent || 'Weekly Newsletter';
      

        // Close the side menu if it's open
        const sideMenu = document.getElementById('sideMenu');
        const overlay = document.querySelector('.menu-overlay');
        if (sideMenu && sideMenu.classList.contains('active')) {
            sideMenu.classList.remove('active');
            overlay?.classList.remove('active');
        }

        // Navigate to the newsletter in the same tab
        window.location.href = newsletterUrl;

    } catch (error) {
        console.error('Error navigating to weekly newsletter:', error);
        alert('An error occurred while trying to open the newsletter. Please try again.');
    }
}

// Add event listener for browser back/forward navigation
window.addEventListener('popstate', (event) => {
    if (event.state?.topicId) {
        openWeeklyNewsletter(event.state.topicId);
    }
});

/*function openWeeklyNewsletter(topicId) {
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
}*/

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
    initializeSubscribeForm();
    fetchTopicsAndArticles();
    setupHomeButton();

    const subscribeModal = document.getElementById('subscribeModal');
    const subscribeBtn = document.getElementById('subscribeBtn');
    const closeBtn = document.getElementsByClassName('close')[0];
    const footerSubscribeBtn = document.getElementById('footerSubscribeBtn');
    const footerEmailInput = document.getElementById('footerEmailInput');
    const mainHeader = document.querySelector('header'); // Added header reference

    const menuBtn = document.getElementById('menuBtn');
    const menuClose = document.getElementById('menuClose');
    const sideMenu = document.getElementById('sideMenu');
    const overlay = document.querySelector('.menu-overlay');

    // Updated modal display functions
    const showModal = () => {
        subscribeModal.style.display = 'block';
        if (mainHeader) mainHeader.style.display = 'none';
        window.scrollTo(0, 0);
    };

    const hideModal = () => {
        subscribeModal.style.display = 'none';
        if (mainHeader) mainHeader.style.display = 'block';
    };

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

    // Updated subscribe button handler
    if (subscribeBtn) {
        subscribeBtn.onclick = () => {
            showModal();
        };
    } else {
        console.warn('Subscribe button not found');
    }

    // Updated close button handler
    if (closeBtn) {
        closeBtn.onclick = () => {
            hideModal();
        };
    } else {
        console.warn('Close button not found');
    }

    // Updated window click handler
    window.onclick = (event) => {
        if (event.target == subscribeModal) {
            hideModal();
        }
    }

    // Updated footer subscribe button handler
    if (footerSubscribeBtn && footerEmailInput) {
        footerSubscribeBtn.addEventListener('click', () => {
            if (validateEmail(footerEmailInput.value)) {
                document.getElementById('emailInput').value = footerEmailInput.value;
                showModal();
            } else {
                showValidationMessage(footerEmailInput, 'Please enter a valid email address.');
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

    // Updated auto-open modal
    let hasShownModal = sessionStorage.getItem('hasShownModal');
    if (!hasShownModal) {
        setTimeout(() => {
            showModal();
            sessionStorage.setItem('hasShownModal', 'true');
        }, 20000);
    }

    // Add escape key handler for modal
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && subscribeModal.style.display === 'block') {
            hideModal();
        }
    });
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
    const mainHeader = document.querySelector('header'); // Get header reference
    
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
            if (mainHeader) mainHeader.style.display = 'block'; // Show header
        } else {
            if (response.status === 400 && data.detail.includes("already exists")) {
                const updateSubscription = confirm('This email is already subscribed. Would you like to update your topic preferences?');
                if (updateSubscription) {
                    console.log('Updating subscription for:', email);
                }
            } else {
                throw new Error(data.detail || 'Subscription failed');
            }
        }
    } catch (error) {
        console.error('Subscription error:', error);
        alert(`An error occurred: ${error.message}`);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateEmail,
        formatDate,
        getApiBaseUrl,
    
    };
}


function createArticlePageContent(article) {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
          <meta name="description" content="${article.title} - CurioDaily">
          <meta name="keywords" content="daily news, AI news, tech updates, business insights, science discoveries">
          <title>${article.title} - CurioDaily</title>
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
          <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap">
          <link rel="stylesheet" href="/static/styles/main.css">
          <link rel="stylesheet" href="/static/styles/newsletter.css">
      </head>
      <body>
          <!-- Header -->
          <header>
              <div class="container">
                  <div class="logo-title">
                      <img src="https://storage.googleapis.com/curiodaily_image/logo.jpeg" alt="CurioDaily Logo" class="logo">
                      <h1>CurioDaily: Your Daily Dose of Interesting</h1>
                  </div>
                  <a href="${API_BASE}" class="subscribe-btn">CurioDaily Home</a>
                  <div class="menu-container">
                      <button id="menuBtn" class="menu-btn">
                          <i class="fas fa-bars"></i>
                      </button>
                      <nav id="sideMenu" class="side-menu">
                          <div class="menu-header">
                              <h2>CurioDaily</h2>
                              <button class="menu-close" id="menuClose">&times;</button>
                          </div>
                          <h3 class="menu-section-title">This Week's Top Stories</h3>
                          <ul id="weeklyTopicsList"></ul>
                          <div class="menu-footer">
                              <div class="social-links">
                                  <a href="#"><i class="fab fa-twitter"></i></a>
                                  <a href="#"><i class="fab fa-linkedin"></i></a>
                                  <a href="#"><i class="fab fa-github"></i></a>
                              </div>
                          </div>
                      </nav>
                      <div class="menu-overlay"></div>
                  </div>
              </div>
          </header>
  
          <!-- Main Content -->
          <main class="container article-container">
              <article class="full-article">
                  <div class="article-content">
                      ${article.content}
                  </div>

              </article>
          </main>
  
          <!-- Footer -->
          <footer>
              <div class="footer-content">
                  <div class="footer-logo">
                      <img src="https://storage.googleapis.com/curiodaily_image/logo.jpeg" alt="CurioDaily Logo" class="logo">
                      <h2>CurioDaily</h2>
                  </div>
                  <p>Get your daily dose of interesting news and updates on AI, Tech, Business, Science, and more. Join our community of curious minds!</p>
  \
              </div>
              <div class="footer-bottom">
                  <p>&copy; ${new Date().getFullYear()} CurioDaily. All rights reserved.</p>
                  <div>
                      <a href="#">Privacy Policy</a>
                      <a href="#">Terms of Use</a>
                  </div>
              </div>
          </footer>
  
          <!-- Scripts -->
          <script src="/static/scripts/main.js"></script>
          <script async src="https://www.googletagmanager.com/gtag/js?id=G-583RG4CHLK"></script>
          <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', 'G-583RG4CHLK');
          </script>
      </body>
      </html>
    `;
  }
  
  function openArticle(article) {
    // Update document title
    document.title = `${article.title} - CurioDaily`;
    
    // Update URL
    window.history.pushState(
        { type: 'article', article: article },
        article.title,
        `/article/${encodeURIComponent(article.title.toLowerCase().replace(/\s+/g, '-'))}`
    );

    // Replace page content
    document.body.innerHTML = createArticlePageContent(article);

    // Reinitialize event listeners
    initializeEventListeners();
    fetchWeeklyTopics();

    // Scroll to top
    window.scrollTo(0, 0);
}

function initializeEventListeners() {
    // Reinitialize menu functionality
    const menuBtn = document.getElementById('menuBtn');
    const menuClose = document.getElementById('menuClose');
    const sideMenu = document.getElementById('sideMenu');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            sideMenu.classList.add('active');
        });
    }
    
    if (menuClose) {
        menuClose.addEventListener('click', () => {
            sideMenu.classList.remove('active');
        });
    }

}
/*
// Handle browser back/forward navigation
window.addEventListener('popstate', (event) => {
    if (event.state && event.state.type === 'article') {
        openArticle(event.state.article);
    } else {
        window.location.href = '/';
    }
});
*/
