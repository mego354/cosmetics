/**
 * LUMÉ Luxury Egyptian Beauty Store — Master Client Script
 * Modular Vanilla JavaScript with Fetch API & AJAX
 */

// Helper to obtain Django CSRF Token
function getCsrfToken() {
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
  return cookieValue || (window.LUME_CONFIG ? window.LUME_CONFIG.csrfToken : '');
}

// Global Toast Notifications
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    const isRtl = window.LUME_CONFIG ? window.LUME_CONFIG.isRtl : document.documentElement.getAttribute('dir') === 'rtl';
    container.className = `fixed bottom-5 ${isRtl ? 'left-5' : 'right-5'} z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4`;
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const isSuccess = type === 'success';
  toast.className = `lume-toast pointer-events-auto p-4 rounded-2xl shadow-luxury-card border flex items-center gap-3 text-xs md:text-sm font-medium transition-all ${
    isSuccess
      ? 'bg-[#2A1D1A] text-[#FDFBF7] border-primary/40'
      : 'bg-red-900 text-white border-red-500'
  }`;

  const iconName = isSuccess ? 'auto_awesome' : 'error';
  toast.innerHTML = `
    <span class="material-symbols-outlined text-[20px] text-primary-fixed-dim">${iconName}</span>
    <span class="flex-1 leading-snug">${message}</span>
    <button class="opacity-60 hover:opacity-100 transition-opacity p-1" onclick="this.parentElement.remove()">
      <span class="material-symbols-outlined text-[16px]">close</span>
    </button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// --- CART DRAWER WORKFLOW ---
function openCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  const overlay = document.getElementById('cart-drawer-overlay');
  const panel = document.getElementById('cart-drawer-panel');
  if (!drawer) return;

  drawer.classList.remove('pointer-events-none');
  overlay.classList.remove('opacity-0');
  panel.classList.remove('translate-x-full', '-translate-x-full');
  document.body.style.overflow = 'hidden';
  fetchCartDrawer();
}

function closeCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  const overlay = document.getElementById('cart-drawer-overlay');
  const panel = document.getElementById('cart-drawer-panel');
  if (!drawer) return;

  const isRtl = window.LUME_CONFIG ? window.LUME_CONFIG.isRtl : document.documentElement.getAttribute('dir') === 'rtl';
  overlay.classList.add('opacity-0');
  panel.classList.add(isRtl ? '-translate-x-full' : 'translate-x-full');
  setTimeout(() => {
    drawer.classList.add('pointer-events-none');
    document.body.style.overflow = '';
  }, 300);
}

function updateCartBadges(count, subtotal) {
  const currency = window.LUME_CONFIG ? window.LUME_CONFIG.currency : 'ج.م';
  document.querySelectorAll('.cart-badge-count').forEach(el => {
    el.textContent = count;
    el.classList.toggle('hidden', count === 0);
  });
  document.querySelectorAll('.cart-badge-subtotal').forEach(el => {
    el.textContent = `${subtotal} ${currency}`;
  });
}

function fetchCartDrawer() {
  fetch('/api/cart/drawer/')
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        const container = document.getElementById('cart-drawer-items-container');
        if (container) container.innerHTML = data.drawer_html;
        updateCartBadges(data.total_items, data.subtotal);
      }
    })
    .catch(err => console.error('Error fetching cart:', err));
}

function addToCart(productId, variantId = null, quantity = 1, triggerBtn = null) {
  if (triggerBtn) {
    triggerBtn.disabled = true;
    triggerBtn.classList.add('opacity-75');
  }

  fetch('/api/cart/add/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({
      product_id: productId,
      variant_id: variantId,
      quantity: quantity,
    }),
  })
    .then(r => r.json())
    .then(data => {
      if (triggerBtn) {
        triggerBtn.disabled = false;
        triggerBtn.classList.remove('opacity-75');
      }
      if (data.success) {
        showToast(data.message, 'success');
        updateCartBadges(data.total_items, data.subtotal);
        const container = document.getElementById('cart-drawer-items-container');
        if (container) container.innerHTML = data.drawer_html;
        openCartDrawer();
      } else {
        showToast(data.message || (window.LUME_CONFIG?.i18n?.networkError || 'Error adding item'), 'error');
      }
    })
    .catch(err => {
      if (triggerBtn) {
        triggerBtn.disabled = false;
        triggerBtn.classList.remove('opacity-75');
      }
      showToast(window.LUME_CONFIG?.i18n?.networkError || 'Network error', 'error');
      console.error(err);
    });
}

function updateCartItem(itemId, newQty) {
  fetch('/api/cart/update/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ item_id: itemId, quantity: newQty }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        updateCartBadges(data.total_items, data.subtotal);
        const container = document.getElementById('cart-drawer-items-container');
        if (container) container.innerHTML = data.drawer_html;
        
        // If on cart page, update page elements without full reload
        const pageSubtotal = document.getElementById('cart-page-subtotal');
        if (pageSubtotal) {
          location.reload();
        }
      } else {
        showToast(data.message, 'error');
      }
    });
}

function removeCartItem(itemId) {
  fetch('/api/cart/remove/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ item_id: itemId }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        showToast(data.message || (window.LUME_CONFIG?.i18n?.cartRemoved || 'Removed'), 'success');
        updateCartBadges(data.total_items, data.subtotal);
        const container = document.getElementById('cart-drawer-items-container');
        if (container) container.innerHTML = data.drawer_html;
        if (document.getElementById('cart-page-subtotal')) location.reload();
      }
    });
}

// --- WISHLIST WORKFLOW ---
function toggleWishlist(productId, btn) {
  fetch('/api/wishlist/toggle/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ product_id: productId }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        const icon = btn.querySelector('.material-symbols-outlined');
        if (icon) {
          if (data.in_wishlist) {
            icon.classList.add('fill-active', 'text-primary');
          } else {
            icon.classList.remove('fill-active', 'text-primary');
          }
        }
        document.querySelectorAll('.wishlist-badge-count').forEach(el => {
          el.textContent = data.wishlist_count;
          el.classList.toggle('hidden', data.wishlist_count === 0);
        });

        // If on wishlist page and item removed, remove card smoothly
        if (btn.classList.contains('wishlist-btn') && !data.in_wishlist) {
          const card = btn.closest('.group');
          if (card) {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            setTimeout(() => card.remove(), 300);
          }
        }
      }
    })
    .catch(err => {
      showToast(window.LUME_CONFIG?.i18n?.networkError || 'Network error', 'error');
      console.error(err);
    });
}

// Quick Add from Wishlist to Bag
function quickAddToCart(productId, variantId, qty) {
  addToCart(productId, variantId, qty);
}

// --- DYNAMIC FRONTEND CATALOG FILTERING (NO PAGE RELOAD) ---
let catalogFilterAbortController = null;

function triggerCatalogFilter(page = 1, pushHistory = true) {
  const gridContainer = document.getElementById('product-grid-container');
  if (!gridContainer) return;

  const spinner = document.getElementById('filter-loading-spinner');
  
  // Abort any ongoing request
  if (catalogFilterAbortController) {
    catalogFilterAbortController.abort();
  }
  catalogFilterAbortController = new AbortController();

  // Collect filter form data
  const form = document.getElementById('catalog-filter-form');
  const sortSelect = document.getElementById('sortBy');
  const params = new URLSearchParams();

  if (form) {
    const formData = new FormData(form);
    for (const [key, value] of formData.entries()) {
      if (value && value !== 'all') {
        params.append(key, value);
      }
    }
  }

  // Add sort
  if (sortSelect && sortSelect.value) {
    params.append('sort', sortSelect.value);
  }

  // Add page
  if (page > 1) {
    params.append('page', page);
  }

  // Active quick chip express_only
  const activeExpressChip = document.querySelector('.quick-chip-btn[data-filter="express_only"].bg-primary');
  if (activeExpressChip) {
    params.append('express_only', '1');
  }

  // Search query if present
  const searchInput = document.getElementById('filter-search-query');
  if (searchInput && searchInput.value) {
    params.append('q', searchInput.value);
  }

  // AJAX flag
  const fetchParams = new URLSearchParams(params.toString());
  fetchParams.append('ajax', '1');

  // Visual loading feedback
  gridContainer.style.opacity = '0.4';
  gridContainer.style.pointerEvents = 'none';
  if (spinner) spinner.classList.remove('hidden');

  fetch(`${window.location.pathname}?${fetchParams.toString()}`, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json',
    },
    signal: catalogFilterAbortController.signal,
  })
    .then(r => r.json())
    .then(data => {
      gridContainer.style.opacity = '1';
      gridContainer.style.pointerEvents = '';
      if (spinner) spinner.classList.add('hidden');

      if (data.success) {
        gridContainer.innerHTML = data.html;

        const countEl = document.getElementById('product-total-count');
        if (countEl) countEl.textContent = data.total_count;

        // Push state to browser URL without page reload
        if (pushHistory) {
          const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
          window.history.pushState({ path: newUrl }, '', newUrl);
        }
      }
    })
    .catch(err => {
      if (err.name !== 'AbortError') {
        gridContainer.style.opacity = '1';
        gridContainer.style.pointerEvents = '';
        if (spinner) spinner.classList.add('hidden');
        console.error('Filter error:', err);
      }
    });
}

function applyQuickFilter(key, val) {
  if (key === 'express_only') {
    const chip = document.querySelector('.quick-chip-btn[data-filter="express_only"]');
    if (chip) {
      chip.classList.toggle('bg-primary');
      chip.classList.toggle('text-white');
      chip.classList.toggle('border-primary');
    }
  } else if (key === 'ritual') {
    const radio = document.querySelector(`input[name="ritual"][value="${val}"]`);
    if (radio) radio.checked = true;
  } else if (key === 'skin_type') {
    const radio = document.querySelector(`input[name="skin_type"][value="${val}"]`);
    if (radio) radio.checked = true;
  } else if (key === 'max_price') {
    const maxInput = document.getElementById('filter-max-price');
    if (maxInput) maxInput.value = val;
  }

  triggerCatalogFilter(1, true);
}

function resetCatalogFilters() {
  const form = document.getElementById('catalog-filter-form');
  if (form) form.reset();

  const minPrice = document.getElementById('filter-min-price');
  if (minPrice) minPrice.value = '';

  const maxPrice = document.getElementById('filter-max-price');
  if (maxPrice) maxPrice.value = '';

  const allRitual = document.querySelector('input[name="ritual"][value="all"]');
  if (allRitual) allRitual.checked = true;

  const allSkin = document.querySelector('input[name="skin_type"][value="all"]');
  if (allSkin) allSkin.checked = true;

  document.querySelectorAll('.quick-chip-btn').forEach(b => {
    b.classList.remove('bg-primary', 'text-white', 'border-primary');
  });

  triggerCatalogFilter(1, true);
}

function goToCatalogPage(pageNum) {
  triggerCatalogFilter(pageNum, true);
  window.scrollTo({ top: 350, behavior: 'smooth' });
}

// Mobile Filter Drawer Controls
function openMobileFilterDrawer() {
  const drawer = document.getElementById('mobile-filter-drawer');
  const overlay = document.getElementById('mobile-filter-overlay');
  const panel = document.getElementById('mobile-filter-panel');
  if (!drawer) return;

  drawer.classList.remove('hidden', 'pointer-events-none');
  setTimeout(() => {
    overlay.classList.remove('opacity-0');
    panel.classList.remove('translate-x-full', '-translate-x-full');
  }, 10);
  document.body.style.overflow = 'hidden';
}

function closeMobileFilterDrawer() {
  const drawer = document.getElementById('mobile-filter-drawer');
  const overlay = document.getElementById('mobile-filter-overlay');
  const panel = document.getElementById('mobile-filter-panel');
  if (!drawer) return;

  const isRtl = window.LUME_CONFIG ? window.LUME_CONFIG.isRtl : document.documentElement.getAttribute('dir') === 'rtl';
  overlay.classList.add('opacity-0');
  panel.classList.add(isRtl ? 'translate-x-full' : '-translate-x-full');
  setTimeout(() => {
    drawer.classList.add('hidden', 'pointer-events-none');
    document.body.style.overflow = '';
  }, 300);
}

function applyMobileFilters() {
  const selectedMobileRitual = document.querySelector('input[name="mobile_ritual"]:checked');
  if (selectedMobileRitual) {
    const desktopRadio = document.querySelector(`input[name="ritual"][value="${selectedMobileRitual.value}"]`);
    if (desktopRadio) desktopRadio.checked = true;
  }

  const mobileMin = document.getElementById('mobile-min-price');
  const desktopMin = document.getElementById('filter-min-price');
  if (mobileMin && desktopMin) desktopMin.value = mobileMin.value;

  const mobileMax = document.getElementById('mobile-max-price');
  const desktopMax = document.getElementById('filter-max-price');
  if (mobileMax && desktopMax) desktopMax.value = mobileMax.value;

  closeMobileFilterDrawer();
  triggerCatalogFilter(1, true);
}

// Handle Browser History Back / Forward for Filters
window.addEventListener('popstate', () => {
  if (document.getElementById('product-grid-container')) {
    triggerCatalogFilter(1, false);
  }
});

// --- PREDICTIVE SEARCH AUTOCOMPLETE ---
let searchDebounceTimer = null;
function initSearchAutocomplete() {
  const inputs = document.querySelectorAll('.lume-search-input');
  const dropdown = document.getElementById('search-predictive-dropdown');
  const resultsContainer = document.getElementById('search-predictive-results');

  if (!inputs.length || !dropdown || !resultsContainer) return;

  const currency = window.LUME_CONFIG ? window.LUME_CONFIG.currency : 'ج.م';
  const noResultsText = window.LUME_CONFIG?.i18n?.noSearchResults || 'No artifacts found.';

  inputs.forEach(input => {
    input.addEventListener('input', e => {
      const query = e.target.value.trim();
      clearTimeout(searchDebounceTimer);

      if (query.length < 2) {
        dropdown.classList.add('hidden');
        return;
      }

      searchDebounceTimer = setTimeout(() => {
        fetch(`/api/search/?q=${encodeURIComponent(query)}`)
          .then(r => r.json())
          .then(data => {
            if (data.results && data.results.length > 0) {
              resultsContainer.innerHTML = data.results
                .map(
                  p => `
                <a href="${p.url}" class="flex items-center gap-3 p-2.5 rounded-xl hover:bg-surface-container transition-colors group">
                  <div class="w-12 h-14 rounded-lg bg-surface-container overflow-hidden shrink-0 border editorial-border">
                    <img src="${p.image_url}" alt="${p.name_ar}" class="w-full h-full object-cover">
                  </div>
                  <div class="flex-1 min-w-0">
                    <span class="text-[10px] text-primary font-mono block">${p.category_name}</span>
                    <h4 class="text-xs font-bold text-on-surface truncate group-hover:text-primary transition-colors">${p.name_ar}</h4>
                    <span class="text-xs font-mono font-bold text-primary mt-0.5 block">${p.price} ${currency}</span>
                  </div>
                </a>
              `
                )
                .join('');
              dropdown.classList.remove('hidden');
            } else {
              resultsContainer.innerHTML = `<p class="text-xs text-outline text-center py-4">${noResultsText}</p>`;
              dropdown.classList.remove('hidden');
            }
          });
      }, 250);
    });

    document.addEventListener('click', e => {
      if (!dropdown.contains(e.target) && !input.contains(e.target)) {
        dropdown.classList.add('hidden');
      }
    });
  });
}

// --- PRODUCT DETAILS PAGE (PDP) CONTROLS ---
function switchEditorialImage(btn, targetImgId, captionText) {
  const targetImg = document.getElementById(targetImgId);
  const btnImg = btn.querySelector('img');
  if (targetImg && btnImg) {
    targetImg.src = btnImg.src;
    targetImg.alt = btnImg.alt;
  }
  const plateIndicator = document.getElementById('plate-indicator');
  if (plateIndicator) plateIndicator.textContent = captionText;

  // Active state on thumbnail
  btn.parentElement.querySelectorAll('button').forEach(b => {
    b.classList.remove('border-2', 'border-primary');
    b.classList.add('border', 'border-outline-variant');
  });
  btn.classList.add('border-2', 'border-primary');
  btn.classList.remove('border-outline-variant');
}

let selectedVariantId = null;
function selectBottleSize(btn, title, price, comparePrice = null, variantId = null) {
  selectedVariantId = variantId;
  const currency = window.LUME_CONFIG ? window.LUME_CONFIG.currency : 'ج.م';
  const container = document.getElementById('size-toggle-container');
  if (container) {
    container.querySelectorAll('button').forEach(b => {
      b.className = 'border border-outline-variant rounded-xl p-3 text-start hover:border-primary transition-all bg-surface hover:bg-surface-container-low flex flex-col justify-between';
    });
  }
  btn.className = 'relative border-2 border-primary bg-secondary-container/40 rounded-xl p-3 text-start transition-all shadow-sm flex flex-col justify-between ring-1 ring-primary/20';

  const priceDisplay = document.getElementById('pdp-price-display');
  if (priceDisplay) priceDisplay.innerHTML = `${price} <span class="text-2xl font-normal">${currency}</span>`;

  // Update sticky bar price if exists
  const stickyPrice = document.getElementById('sticky-pdp-price');
  if (stickyPrice) stickyPrice.textContent = `${price} ${currency}`;
}

function adjustQty(delta) {
  const el = document.getElementById('product-qty');
  if (!el) return;
  let val = parseInt(el.textContent) || 1;
  val = Math.max(1, val + delta);
  el.textContent = val;
}

function addCurrentProductToBag(productId) {
  const qtyEl = document.getElementById('product-qty');
  const qty = qtyEl ? parseInt(qtyEl.textContent) || 1 : 1;
  const btn = document.getElementById('btn-add-pdp-bag');
  addToCart(productId, selectedVariantId, qty, btn);
}

// --- CHECKOUT ESTIMATOR & COUPON ---
function updateGovernorateShipping(selectEl) {
  const value = selectEl.value;
  const noteEl = document.getElementById('governorate-delivery-note');
  if (!noteEl) return;

  const i18n = window.LUME_CONFIG?.i18n;
  if (value === 'cairo' || value === 'giza') {
    noteEl.innerHTML = `<span class="text-[#4A6B53] font-bold">${i18n?.cairoGizaShipping || '24h Delivery'}</span>`;
  } else if (value === 'alexandria' || value === 'beheira' || value === 'dakahlia' || value === 'sharqia') {
    noteEl.innerHTML = `<span class="text-primary font-bold">${i18n?.deltaAlexShipping || '48h Delivery'}</span>`;
  } else {
    noteEl.innerHTML = `<span class="text-secondary font-bold">${i18n?.upperEgyptShipping || '3-4 Days Delivery'}</span>`;
  }
}

function applyCoupon(inputSelector, resultSelector) {
  const input = document.querySelector(inputSelector);
  const result = document.querySelector(resultSelector);
  if (!input || !result) return;

  const code = input.value.trim();
  if (!code) return;

  const currency = window.LUME_CONFIG ? window.LUME_CONFIG.currency : 'ج.م';

  fetch('/api/checkout/validate-coupon/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ code: code }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.valid) {
        result.className = 'text-xs text-[#4A6B53] font-bold mt-2 flex items-center gap-1';
        result.innerHTML = `<span class="material-symbols-outlined text-[16px]">check_circle</span> ${data.message}`;
        showToast(data.message, 'success');
        const discountEl = document.getElementById('checkout-discount-amount');
        if (discountEl) discountEl.textContent = `-${data.discount_amount} ${currency}`;
        const totalEl = document.getElementById('checkout-total-amount');
        if (totalEl) totalEl.textContent = `${data.new_total} ${currency}`;
      } else {
        result.className = 'text-xs text-red-600 font-bold mt-2 flex items-center gap-1';
        result.innerHTML = `<span class="material-symbols-outlined text-[16px]">error</span> ${data.message}`;
        showToast(data.message, 'error');
      }
    });
}

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initSearchAutocomplete();
});
