(function() {
  if (window.__app_graphs_initialized) return;
  window.__app_graphs_initialized = true;

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        return resolve();
      }
      const s = document.createElement('script');
      s.src = src;
      s.onload = () => resolve();
      s.onerror = (e) => reject(e);
      document.head.appendChild(s);
    });
  }

  const VIZ_CDN = 'https://cdn.jsdelivr.net/npm/@viz-js/viz@3.11.0/lib/viz-standalone.js';

  loadScript(VIZ_CDN).catch((err) => console.warn('Viz.js load status:', err));

  const WORKFLOW_GRAPHVIZ = `digraph Workflow {
    graph [
        rankdir=TB,
        bgcolor="transparent",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        nodesep=0.4,
        ranksep=0.6,
        pad="0.4"
    ];
    node [
        shape=box,
        style="rounded,filled",
        fillcolor="#27272a",
        fontcolor="#f4f4f5",
        color="#3f3f46",
        penwidth=1.5,
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontsize=12,
        margin="0.25,0.12"
    ];
    edge [
        color="#71717a",
        penwidth=1.5,
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontsize=10,
        fontcolor="#a1a1aa"
    ];

    Start [shape=oval, fillcolor="#27272a", fontcolor="#f4f4f5", color="#3f3f46", label="Start", width=1.1];
    End [shape=oval, fillcolor="#27272a", fontcolor="#f4f4f5", color="#3f3f46", label="End", width=1.1];

    Start -> classify_intent;
    clarification_engine -> End [style=dashed, label="clarification_needed"];
    clarification_engine -> load_schema [style=dashed, label="resolved"];
    classify_intent -> clarification_engine [style=dashed, label="ambiguous"];
    classify_intent -> format_meta [style=dashed, label="meta_query"];
    classify_intent -> handle_out_of_scope_query [style=dashed, label="out_of_scope"];
    classify_intent -> load_schema [style=dashed, label="data_query"];
    diagnose_execution_error -> repair_sql;
    execute_sql -> diagnose_execution_error [style=dashed, label="error"];
    execute_sql -> format_answer [style=dashed, label="success"];
    generate_sql -> validate_sql;
    load_schema -> generate_sql;
    repair_sql -> validate_sql;
    validate_sql -> execute_sql [style=dashed, label="valid"];
    validate_sql -> format_answer [style=dashed, label="max_repairs"];
    validate_sql -> repair_sql [style=dashed, label="invalid"];
    format_answer -> End;
    format_meta -> End;
    handle_out_of_scope_query -> End;
}`;

  const SCHEMA_GRAPHVIZ = `digraph DBSchema {
    graph [
        rankdir=LR,
        bgcolor="transparent",
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        nodesep=0.7,
        ranksep=1.0,
        splines=spline,
        pad="0.5"
    ];
    node [
        shape=none,
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontsize=11
    ];
    edge [
        color="#71717a",
        penwidth=1.8,
        arrowhead=crow,
        arrowtail=tee,
        dir=both,
        fontname="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontsize=10,
        fontcolor="#a1a1aa"
    ];

    categories [label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="5" bgcolor="#18181b" color="#3f3f46">
            <tr><td bgcolor="#27272a" colspan="3" align="center"><font color="#f4f4f5" point-size="12"><b>categories</b></font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#f59e0b"><b>PK</b></font></td><td align="left"><font color="#f4f4f5">category_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">name</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">description</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
        </table>
    >];

    products [label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="5" bgcolor="#18181b" color="#3f3f46">
            <tr><td bgcolor="#27272a" colspan="3" align="center"><font color="#f4f4f5" point-size="12"><b>products</b></font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#f59e0b"><b>PK</b></font></td><td align="left"><font color="#f4f4f5">product_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#38bdf8"><b>FK</b></font></td><td align="left"><font color="#f4f4f5">category_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">name</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">price</font></td><td align="right"><font color="#a1a1aa">REAL</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">stock_quantity</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
        </table>
    >];

    customers [label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="5" bgcolor="#18181b" color="#3f3f46">
            <tr><td bgcolor="#27272a" colspan="3" align="center"><font color="#f4f4f5" point-size="12"><b>customers</b></font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#f59e0b"><b>PK</b></font></td><td align="left"><font color="#f4f4f5">customer_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">name</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">email</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">country</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">join_date</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
        </table>
    >];

    orders [label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="5" bgcolor="#18181b" color="#3f3f46">
            <tr><td bgcolor="#27272a" colspan="3" align="center"><font color="#f4f4f5" point-size="12"><b>orders</b></font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#f59e0b"><b>PK</b></font></td><td align="left"><font color="#f4f4f5">order_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#38bdf8"><b>FK</b></font></td><td align="left"><font color="#f4f4f5">customer_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">order_date</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">total_amount</font></td><td align="right"><font color="#a1a1aa">REAL</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">status</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
        </table>
    >];

    order_items [label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="5" bgcolor="#18181b" color="#3f3f46">
            <tr><td bgcolor="#27272a" colspan="3" align="center"><font color="#f4f4f5" point-size="12"><b>order_items</b></font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#f59e0b"><b>PK</b></font></td><td align="left"><font color="#f4f4f5">item_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#38bdf8"><b>FK</b></font></td><td align="left"><font color="#f4f4f5">order_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#38bdf8"><b>FK</b></font></td><td align="left"><font color="#f4f4f5">product_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">quantity</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">unit_price</font></td><td align="right"><font color="#a1a1aa">REAL</font></td></tr>
        </table>
    >];

    reviews [label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="5" bgcolor="#18181b" color="#3f3f46">
            <tr><td bgcolor="#27272a" colspan="3" align="center"><font color="#f4f4f5" point-size="12"><b>reviews</b></font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#f59e0b"><b>PK</b></font></td><td align="left"><font color="#f4f4f5">review_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#38bdf8"><b>FK</b></font></td><td align="left"><font color="#f4f4f5">product_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"><font color="#38bdf8"><b>FK</b></font></td><td align="left"><font color="#f4f4f5">customer_id</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">rating</font></td><td align="right"><font color="#a1a1aa">INTEGER</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">comment</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
            <tr><td align="center" bgcolor="#27272a"></td><td align="left"><font color="#f4f4f5">review_date</font></td><td align="right"><font color="#a1a1aa">TEXT</font></td></tr>
        </table>
    >];

    categories -> products [taillabel="1", headlabel="N", tooltip="categories.category_id -> products.category_id"];
    customers -> orders [taillabel="1", headlabel="N", tooltip="customers.customer_id -> orders.customer_id"];
    customers -> reviews [taillabel="1", headlabel="N", tooltip="customers.customer_id -> reviews.customer_id"];
    orders -> order_items [taillabel="1", headlabel="N", tooltip="orders.order_id -> order_items.order_id"];
    products -> order_items [taillabel="1", headlabel="N", tooltip="products.product_id -> order_items.product_id"];
    products -> reviews [taillabel="1", headlabel="N", tooltip="products.product_id -> reviews.product_id"];
}`;

  let currentType = 'workflow';
  let scale = 1.0;
  let translateX = 0;
  let translateY = 0;
  let isPanning = false;
  let startX = 0;
  let startY = 0;

  function createModal() {
    if (document.getElementById('app-graph-modal-backdrop')) return;
    const backdrop = document.createElement('div');
    backdrop.id = 'app-graph-modal-backdrop';
    backdrop.className = 'app-graph-modal-backdrop';
    backdrop.innerHTML = `
      <div class="app-graph-modal" onclick="event.stopPropagation()">
        <div class="app-modal-header">
          <div class="app-modal-title-wrap">
            <span id="app-modal-title" class="app-modal-title">Workflow Graph</span>
            <span id="app-modal-badge" class="app-modal-badge">LangGraph</span>
          </div>

          <div class="app-modal-actions">
            <button class="app-btn-tool" title="Zoom In" onclick="window.__app_graphs.zoom(1.2)">+</button>
            <button class="app-btn-tool" title="Zoom Out" onclick="window.__app_graphs.zoom(0.8)">−</button>
            <button class="app-btn-tool" title="Reset View" onclick="window.__app_graphs.reset()">↺</button>
            <a id="modal-open-full" href="/public/workflow.html" target="_blank" class="app-btn-tool" title="Open Full Static Page">
              <span>Full Page</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
            <button class="app-btn-close" title="Close (Esc)" onclick="window.__app_graphs.close()">✕</button>
          </div>
        </div>

        <div id="app-modal-body" class="app-modal-body">
          <div id="app-modal-viewport" class="app-modal-viewport"></div>
        </div>

        <div class="app-modal-footer">
          <span>Scroll to Zoom • Drag to Pan</span>
          <span>Interactive Graphviz Diagram</span>
        </div>
      </div>
    `;

    backdrop.addEventListener('click', () => window.__app_graphs.close());
    document.body.appendChild(backdrop);

    const body = document.getElementById('app-modal-body');
    body.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isPanning = true;
      startX = e.clientX - translateX;
      startY = e.clientY - translateY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!isPanning) return;
      translateX = e.clientX - startX;
      translateY = e.clientY - startY;
      applyTransform();
    });

    window.addEventListener('mouseup', () => {
      isPanning = false;
    });

    body.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      window.__app_graphs.zoom(zoomFactor);
    }, { passive: false });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        window.__app_graphs.close();
      }
    });
  }

  function applyTransform() {
    const vp = document.getElementById('app-modal-viewport');
    if (vp) {
      vp.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }
  }

  async function renderGraph() {
    const vp = document.getElementById('app-modal-viewport');
    if (!vp) return;
    vp.innerHTML = '<div style="color:var(--app-muted-fg); font-size: 0.875rem;">Rendering diagram...</div>';

    const isWorkflow = currentType === 'workflow';
    const src = isWorkflow ? WORKFLOW_GRAPHVIZ : SCHEMA_GRAPHVIZ;

    try {
      if (!window.Viz) {
        await loadScript(VIZ_CDN);
      }
      const viz = await window.Viz.instance();
      const svgEl = viz.renderSVGElement(src);
      vp.innerHTML = '';
      vp.appendChild(svgEl);
      resetTransform();
    } catch (err) {
      vp.innerHTML = `<div style="color:#ef4444; padding: 20px;">Graph render error: ${err}</div>`;
    }
  }

  function resetTransform() {
    scale = 1.0;
    translateX = 0;
    translateY = 0;
    applyTransform();
  }

  function setupLinkInterception() {
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (!link) return;
      const href = link.getAttribute('href') || '';

      if (href.includes('workflow.html')) {
        if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
          e.preventDefault();
          window.__app_graphs.open('workflow');
        }
      } else if (href.includes('schema.html')) {
        if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
          e.preventDefault();
          window.__app_graphs.open('schema');
        }
      }
    });
  }

  window.__app_graphs = {
    open: function(type) {
      currentType = type || 'workflow';
      const backdrop = document.getElementById('app-graph-modal-backdrop');
      if (!backdrop) return;

      const titleEl = document.getElementById('app-modal-title');
      const badgeEl = document.getElementById('app-modal-badge');
      const fullLink = document.getElementById('modal-open-full');

      if (currentType === 'workflow') {
        titleEl.textContent = 'Workflow Graph';
        badgeEl.textContent = 'LangGraph';
        fullLink.href = '/public/workflow.html';
      } else {
        titleEl.textContent = 'Database Schema';
        badgeEl.textContent = 'ER Diagram';
        fullLink.href = '/public/schema.html';
      }

      backdrop.classList.add('open');
      renderGraph();
    },

    close: function() {
      const backdrop = document.getElementById('app-graph-modal-backdrop');
      if (backdrop) {
        backdrop.classList.remove('open');
      }
    },

    zoom: function(factor) {
      scale = Math.min(Math.max(scale * factor, 0.2), 5);
      applyTransform();
    },

    reset: function() {
      resetTransform();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      createModal();
      setupLinkInterception();
    });
  } else {
    createModal();
    setupLinkInterception();
  }
})();
