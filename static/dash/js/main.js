
const guild_switcher = document.querySelector('.guild-selector')
guild_switcher.addEventListener('click', function() {
  guild_switcher.classList.toggle('active');
});

function TooltipText(e, txt) {
  navigator.clipboard.writeText(txt);

  e.querySelector('.tooltiptext').innerHTML = 'Copied'
  setTimeout(() => {
    e.querySelector('.tooltiptext').innerHTML = 'Copy'
  }, 2000)
}

// Navbar - side menu
var navbar_item = document.querySelectorAll('.navbar-item');

window.addEventListener('load', function() {
  var currentURL = window.location.pathname;

  navbar_item.forEach((item) => {
    var itemURL = item.querySelector('.navbar-link').dataset.href
    var isActive = itemURL === currentURL;

    item.dataset.active = isActive ? "True" : "False";
  });
});

navbar_item.forEach((item) => {
  item.addEventListener('click', (e) => {
    var currentURL = window.location.pathname;
    var link = item.querySelector('.navbar-link')

    const aClassPrem = link.classList.contains('p-True') // is the plugin premium
    const isPremium = link.dataset.isPremium // server check - True if hasPrem else False

    if (aClassPrem === true && isPremium === 'False') {
      const PremiumModal = new bootstrap.Modal(document.getElementById('PremiumModal'));
      PremiumModal.show();
    } else {
      var url = link.dataset.href;
      var isActive = url === currentURL;
      e.target.dataset.active = isActive ? "True" : "False";

      document.location.href = url;
    }
  });
});

function handlePremiumOnClick(event) {
  var currentURL = window.location.pathname;
  var link = event.currentTarget;
  
  // p_fae9dd is premium - p_a2b8c9 is not premium
  const aClassPrem = link.classList.contains('p_fae9dd') // is the plugin premium

  const isPremium = link.dataset.isPremium // server check - True if hasPrem else False

  if (aClassPrem === true && isPremium === 'False') {
    const PremiumModal = new bootstrap.Modal(document.getElementById('PremiumModal'));
    PremiumModal.show();
  } else {
    var url = link.dataset.href;
    var isActive = url === currentURL;
    event.target.dataset.active = isActive ? "True" : "False";

    document.location.href = url;
  }
}

try {
  var Switch = document.querySelector("input[role='switch'][name='plugin-status']")
  if (Switch) {
    Switch.addEventListener('change', (e) => {
      const currentURL = window.location.pathname;
      const URL = currentURL.split('/')
      var PlugIn = URL[URL.length - 1]
      
      const navBarLink = document.querySelector(`.navbar-link.${PlugIn}`);
      const dataHref = navBarLink.getAttribute('data-href');
      if (window.location.pathname === dataHref) {
        navBarLink.setAttribute('data-enable', e.target.checked ? 'True' : 'False');
      }
    })
  }
} catch (error) {}


// Search bar
/* <div class="search-bar search-bar-show">
  <form class="search-form d-flex align-items-center">
    <i class="bi bi-search"></i>
    <!-- <input type="text" name="query" placeholder="Search" title="Enter search keyword" disabled> -->
    <span title="Enter search keyword">Search</span>
    <div class="shortcut">ctrl</div>
  </form>
</div> */
/* var search_bar = document.querySelector('.search-bar');
search_bar.addEventListener('click', () => {
  
  // create the search bar modal
  var modal = document.createElement('div');
  modal.classList.add('search-bar-modal');

  // search bar modal header
  var modal_header = document.createElement('div');
  modal_header.classList.add('search-bar-modal__header');
  
  var icon = document.createElement('i'); // search bar modal header icon
  icon.classList.add('bi', 'bi-search');
  modal_header.appendChild(icon);

  var input = document.createElement('input'); // search bar modal header input
  input.classList.add('search-bar-input');
  input.placeholder = 'Search';
  input.style.width = '100%';
  modal_header.appendChild(input);

  modal.appendChild(modal_header);
  
  // search bar modal body
  var body = document.createElement('div');
  body.classList.add('search-bar-modal__body');
  modal.appendChild(body);

  var footer = document.createElement('div');
  footer.classList.add('search-bar-modal__footer');

  var footer_text = document.createElement('p');

  var pro_tip = document.createElement('span');
  pro_tip.classList.add('pro-tip');
  pro_tip.innerHTML = 'Protip:';
  footer_text.appendChild(pro_tip);

  var p1 = document.createElement('span');
  p1.innerHTML = 'Start searches with ';
  footer_text.appendChild(p1);

  var code = document.createElement('code');
  code.setAttribute('data-bs-toggle', 'tooltip');
  code.setAttribute('data-bs-placement', 'top');
  code.setAttribute('data-bs-title', 'Servers');
  code.setAttribute('title', 'Servers')
  code.innerHTML = '*';
  footer_text.appendChild(code);

  var p2 = document.createElement('span');
  p2.innerHTML = ' to search all servers.';
  footer_text.appendChild(p2);
  
  footer.appendChild(footer_text);
  modal.appendChild(footer);
  
  document.body.appendChild(modal);

  input.focus(); // focus the input after creating the modal
  
  // modal background
  var modal_bg = document.createElement('div');
  modal_bg.classList.add('search-bar-modal-bg');
  modal_bg.addEventListener('click', () => {
    modal.remove();
    modal_bg.remove();
  });
  document.body.appendChild(modal_bg);


  // search event
  input.addEventListener('input', () => {
    var search = input.value.toLowerCase();
    var plugins = document.querySelectorAll('.plugin');

    if (search === '') {
      body.innerHTML = '';
      return;
    }

    plugins.forEach((plugin) => {
      var plugin_name = plugin.querySelector('.navbar-link').querySelector('p').innerHTML;

      var plugin_info = {
        name: plugin_name,
        url: plugin.querySelector('.navbar-link').dataset.href,
        icon: {
          mi: plugin.querySelector('.navbar-link').querySelector('.material-icons')?.innerHTML || null,
          bi: plugin.querySelector('.navbar-link').querySelector('.bi')?.classList.value.split(' ')[1] || null,
        },
        isEnable: plugin.querySelector('.navbar-link').dataset.enable,
        isPremium: plugin.querySelector('.navbar-link').classList.contains('p-True'), // is the plugin premium
        hasPremium: plugin.querySelector('.navbar-link').dataset.isPremium === 'True' ? true : false, // server check - True if hasPrem else False
      }
      
      var plugin_card = document.createElement('div');
      plugin_card.classList.add('plugin-card');
      plugin_card.innerHTML = `
        <a href="${plugin_info.url}">
          <div class="plugin-card">
            <div class="d-flex align-items-center" style="gap: 8px;">
              <div class="plugin-card__icon">
                ${
                  plugin_info.icon.mi ? `<span class="material-icons">${plugin_info.icon.mi}</span>` : 
                  plugin_info.icon.bi && `<i class="bi ${plugin_info.icon.bi}"></i>`
                }
              </div>
              <div class="plugin-card__header">
                <div class="plugin-card__name">${plugin_info.name}</div>
                <div class="plugin-card__url">${plugin_info.url}</div>
              </div>
            </div>

            <div class="plugin-card__icons2">
              ${ plugin_info.isPremium && !plugin_info.hasPremium ? `<i class="bi bi-star-fill"></i>` : `` }
              <i class="bi bi-arrow-return-left"></i>
            </div>
          </div>
        </a>
      `;
      body.appendChild(plugin_card);

      if (plugin_name.toLowerCase().includes(search)) {
        console.log(plugin_info)
        body.insertBefore(plugin_card, body.firstChild);

        // clear the duplicates
        var plugin_cards = document.querySelectorAll('.plugin-card');
        var plugin_cards_arr = Array.from(plugin_cards);
        var duplicates = plugin_cards_arr.filter((item, index) => plugin_cards_arr.indexOf(item) != index);
        duplicates.forEach((duplicate) => {
          duplicate.remove();
        });
      } else {
        plugin_card.remove();
      }
    });

    if (search.startsWith('*')) {
      console.log('search for all servers')
      
      fetch('/get_user_guilds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
        .then(response => response.json())
        .then(data => {
          const guilds = JSON.parse(data.guilds);

          var guild_sorted = guilds.sort((a, b) => {
            if (a.active < b.active) { return 1; }
            if (a.active > b.active) { return -1; }
            return 0;
          });

          guild_sorted.forEach((guild) => {
            var guild_card = document.createElement('div');
            guild_card.innerHTML = `
              <a href="/dashboard/${guild.id}">
                <div class="plugin-card">
                  <div class="d-flex align-items-center" style="gap: 8px;">
                    <div class="plugin-card__icon">
                      <img src="${guild.icon}" alt="Guild Icon" class="guild-icon" style="width: 32px;border-radius: 8px;">
                    </div>
                    <div class="plugin-card__header">
                      <div class="plugin-card__name">${guild.name}</div>
                      <div class="plugin-card__url">/dashboard/${guild.id}</div>
                    </div>
                  </div>

                  <div class="plugin-card__icons2">
                    ${guild.active && !guild.unavailable ? `<i class="bi bi-check-circle-fill"></i>` : ''}
                    ${guild.unavailable ? `<i class="bi bi-exclamation-circle-fill" style="color: red;"></i>` : ''}
                  </div>
                </div>
              </a>
            `;
            body.appendChild(guild_card);
          });
        })
    }
  });
}) */