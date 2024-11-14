document.addEventListener('DOMContentLoaded', function() {
  const menuButton = document.getElementById('user-menu-button');
  const menuDropdown = document.querySelector('[aria-labelledby="user-menu-button"]');
  
  // Exit if elements aren't found
  if (!menuButton || !menuDropdown) {
      console.error('Menu elements not found');
      return;
  }

  // Initially hide the dropdown
  menuDropdown.style.display = 'none';
  let isOpen = false;

  // Toggle menu when clicking the button
  menuButton.addEventListener('click', function(e) {
      e.stopPropagation();
      toggleMenu();
  });

  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
      if (!menuButton.contains(e.target) && !menuDropdown.contains(e.target) && isOpen) {
          closeMenu();
      }
  });

  // Handle escape key
  document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && isOpen) {
          closeMenu();
      }
  });

  function toggleMenu() {
      isOpen = !isOpen;
      menuButton.setAttribute('aria-expanded', isOpen);
      
      if (isOpen) {
          // Show menu
          menuDropdown.style.display = 'block';
          // Use requestAnimationFrame to ensure display:block is processed before adding classes
          requestAnimationFrame(() => {
              menuDropdown.classList.add('transform', 'opacity-100', 'scale-100');
              menuDropdown.classList.remove('opacity-0', 'scale-95');
          });
          
          // Focus the first menu item
          const firstMenuItem = menuDropdown.querySelector('[role="menuitem"]');
          if (firstMenuItem) firstMenuItem.focus();
      } else {
          // Hide menu
          menuDropdown.classList.add('opacity-0', 'scale-95');
          menuDropdown.classList.remove('opacity-100', 'scale-100');
          
          // Use setTimeout to match the transition duration
          setTimeout(() => {
              if (!isOpen) menuDropdown.style.display = 'none';
          }, 200); // 200ms matches the duration-200 class
      }
  }

  function closeMenu() {
      isOpen = false;
      menuButton.setAttribute('aria-expanded', 'false');
      menuDropdown.classList.add('opacity-0', 'scale-95');
      menuDropdown.classList.remove('opacity-100', 'scale-100');
      
      setTimeout(() => {
          if (!isOpen) menuDropdown.style.display = 'none';
      }, 200);
  }

  // Add keyboard navigation within the menu
  menuDropdown.addEventListener('keydown', function(e) {
      const menuItems = [...menuDropdown.querySelectorAll('[role="menuitem"]')];
      const currentIndex = menuItems.indexOf(document.activeElement);

      let nextIndex;
      switch (e.key) {
          case 'ArrowDown':
              e.preventDefault();
              nextIndex = currentIndex + 1;
              if (nextIndex >= menuItems.length) nextIndex = 0;
              menuItems[nextIndex].focus();
              break;
          case 'ArrowUp':
              e.preventDefault();
              nextIndex = currentIndex - 1;
              if (nextIndex < 0) nextIndex = menuItems.length - 1;
              menuItems[nextIndex].focus();
              break;
          case 'Home':
              e.preventDefault();
              menuItems[0].focus();
              break;
          case 'End':
              e.preventDefault();
              menuItems[menuItems.length - 1].focus();
              break;
      }
  });
});