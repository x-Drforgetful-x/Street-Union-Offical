document.addEventListener('DOMContentLoaded', () => {
  const orderTypeField = document.querySelector('select[name="order_type"]');
  const zoneField = document.querySelector('select[name="delivery_zone"]')?.closest('.col-md-6');
  const addressField = document.querySelector('textarea[name="delivery_address"]')?.closest('.col-12');

  const toggleDeliveryFields = () => {
    if (!orderTypeField || !zoneField || !addressField) return;
    const isDelivery = orderTypeField.value === 'delivery';
    zoneField.style.display = isDelivery ? '' : 'none';
    addressField.style.display = isDelivery ? '' : 'none';
  };

  if (orderTypeField) {
    toggleDeliveryFields();
    orderTypeField.addEventListener('change', toggleDeliveryFields);
  }

  document.querySelectorAll('.product-buy-form, .panel form').forEach((form) => {
    const input = form.querySelector('.qty-input');
    const minus = form.querySelector('.js-qty-minus');
    const plus = form.querySelector('.js-qty-plus');
    if (!input || !minus || !plus) return;

    minus.addEventListener('click', () => {
      const current = parseInt(input.value || '1', 10);
      input.value = Math.max(1, current - 1);
    });

    plus.addEventListener('click', () => {
      const current = parseInt(input.value || '1', 10);
      input.value = Math.max(1, current + 1);
    });
  });

  const playBeep = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.value = 880;
      gain.gain.value = 0.05;
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 0.18);
    } catch (err) {
      console.debug('Audio notification unavailable', err);
    }
  };

  const renderOrderCard = (order, kitchen = false) => {
    const items = order.items.map((item) => `
      <li>
        <div class="${kitchen ? 'fw-semibold' : ''}">${item.quantity} × ${item.name}</div>
        ${item.extras ? `<div class="small text-light-emphasis">${item.extras}</div>` : ''}
      </li>
    `).join('');

    if (kitchen) {
      return `
      <div class="col-md-6 col-xxl-4" data-order-id="${order.id}">
        <div class="panel p-4 h-100 kitchen-card">
          <div class="d-flex justify-content-between align-items-start gap-3 mb-3">
            <div>
              <div class="section-kicker mb-1">${order.order_type}</div>
              <h2 class="fw-bold mb-1">${order.order_number}</h2>
              <div class="text-light-emphasis">${order.customer_name} · ${order.phone_number}</div>
            </div>
            <span class="status-badge">${order.status_label}</span>
          </div>
          <div class="mini-panel p-3 mb-3 h-100">
            <ul class="list-unstyled mb-0 d-grid gap-3 kitchen-item-list">${items}</ul>
          </div>
          <form method="post" action="/dashboard/orders/${order.id}/status/" class="d-grid gap-2 mt-auto">
            <input type="hidden" name="csrfmiddlewaretoken" value="${window.csrfToken || ''}">
            <input type="hidden" name="next" value="${window.location.pathname}">
            <select name="status" class="form-select form-select-lg">
              ${statusOptions(order.status)}
            </select>
            <div class="d-grid gap-2 d-sm-flex">
              <button class="btn btn-warning btn-lg flex-fill" type="submit">Save status</button>
              <a href="/dashboard/orders/${order.id}/whatsapp/status/" target="_blank" class="btn btn-outline-success btn-lg flex-fill">WhatsApp update</a>
            </div>
          </form>
        </div>
      </div>`;
    }

    return `
    <div class="col-12" data-order-id="${order.id}">
      <div class="panel p-4 order-board-card">
        <div class="d-flex justify-content-between align-items-start gap-3 flex-wrap mb-3">
          <div>
            <div class="section-kicker mb-1">${order.order_type}</div>
            <h4 class="fw-bold mb-1">${order.order_number}</h4>
            <div class="text-light-emphasis">${order.customer_name} · ${order.phone_number}</div>
          </div>
          <div class="text-end">
            <div class="price-pill">R${order.total}</div>
            <div class="small text-light-emphasis mt-2">${order.created_at}</div>
          </div>
        </div>
        <div class="row g-3 align-items-start">
          <div class="col-lg-5">
            <div class="mini-panel p-3 h-100">
              <div class="fw-semibold mb-2">Items</div>
              <ul class="list-unstyled small mb-0 d-grid gap-2">${items}</ul>
            </div>
          </div>
          <div class="col-lg-7">
            <div class="d-flex flex-wrap gap-2 mb-3">
              <span class="status-badge">${order.status_label}</span>
            </div>
            <form method="post" action="/dashboard/orders/${order.id}/status/" class="row g-2 align-items-end mb-3">
              <input type="hidden" name="csrfmiddlewaretoken" value="${window.csrfToken || ''}">
              <input type="hidden" name="next" value="${window.location.pathname}">
              <div class="col-sm-6 col-md-4">
                <label class="form-label small">Status</label>
                <select name="status" class="form-select form-select-sm">
                  ${statusOptions(order.status)}
                </select>
              </div>
              <div class="col-sm-6 col-md-3">
                <button class="btn btn-outline-light btn-sm w-100" type="submit">Update</button>
              </div>
            </form>
            <div class="d-flex gap-2 flex-wrap">
              <a href="/dashboard/orders/${order.id}/whatsapp/confirm/" class="btn btn-success btn-sm" target="_blank">Send confirm</a>
              <a href="/dashboard/orders/${order.id}/whatsapp/status/" class="btn btn-outline-success btn-sm" target="_blank">Send status</a>
              <a href="/dashboard/orders/${order.id}/create-quote/" class="btn btn-outline-light btn-sm">Create quote</a>
              <a href="/dashboard/orders/${order.id}/create-invoice/" class="btn btn-warning btn-sm">Create invoice</a>
            </div>
          </div>
        </div>
      </div>
    </div>`;
  };

  const statusOptions = (currentStatus) => {
    const options = [
      ['received', 'Received'],
      ['preparing', 'Preparing'],
      ['ready', 'Ready'],
      ['out-for-delivery', 'Out for Delivery'],
      ['completed', 'Completed'],
      ['cancelled', 'Cancelled'],
    ];
    return options.map(([value, label]) => `<option value="${value}" ${currentStatus === value ? 'selected' : ''}>${label}</option>`).join('');
  };

  const feedUrl = window.orderFeedUrl;
  const orderGrid = document.getElementById('liveOrderGrid');
  const kitchenGrid = document.getElementById('kitchenOrderGrid');
  const manualRefreshBtn = document.getElementById('manualRefreshBtn');
  window.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

  let lastKnownTopOrder = null;
  const refreshOrders = async () => {
    if (!feedUrl || (!orderGrid && !kitchenGrid)) return;
    try {
      const response = await fetch(feedUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!response.ok) return;
      const payload = await response.json();
      const firstOrder = payload.orders[0]?.order_number || null;
      if (lastKnownTopOrder && firstOrder && firstOrder !== lastKnownTopOrder) {
        playBeep();
      }
      lastKnownTopOrder = firstOrder;
      if (orderGrid) {
        orderGrid.innerHTML = payload.orders.length
          ? payload.orders.map((order) => renderOrderCard(order, false)).join('')
          : '<div class="col-12"><div class="empty-panel">No orders available.</div></div>';
      }
      if (kitchenGrid) {
        const activeOrders = payload.orders.filter((order) => !['completed', 'cancelled'].includes(order.status));
        kitchenGrid.innerHTML = activeOrders.length
          ? activeOrders.map((order) => renderOrderCard(order, true)).join('')
          : '<div class="col-12"><div class="empty-panel">Kitchen is clear right now.</div></div>';
      }
    } catch (error) {
      console.debug('Could not refresh order feed', error);
    }
  };

  if (manualRefreshBtn) {
    manualRefreshBtn.addEventListener('click', refreshOrders);
  }

  if (window.enableLiveOrderBoard || window.enableKitchenBoard) {
    refreshOrders();
    setInterval(refreshOrders, 15000);
  }
});
