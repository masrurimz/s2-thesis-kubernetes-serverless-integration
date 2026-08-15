// ============================================================================
// Chapter 2 figures — native Typst diagrams (cetz 0.4.0).
//
// Four architecture figures redrawn as crisp vector diagrams, replacing the
// blurry raster PNGs previously embedded in ch02-literature.typ:
//   fig-k8s-architecture   — Kubernetes cluster architecture (official docs)
//   fig-serverless-architecture — serverless execution model (@mampage2022holistic)
//   fig-cloud-services     — cloud service-model responsibility matrix (@kavis2014)
//   fig-elax-architecture  — ElaX system architecture (@yang2019elax)
//
// Each function returns a cetz canvas (no #figure wrapper; the caption and
// <fig:...> label stay in ch02-literature.typ at the call site).
// ============================================================================
#import "@preview/cetz:0.4.0"

// ---- palette ---------------------------------------------------------------
#let c-cp = rgb("#dbeafe")          // control plane light blue
#let c-cp-edge = rgb("#1d4ed8")     // control plane border
#let c-dp = rgb("#dcfce7")          // data plane light green
#let c-dp-edge = rgb("#15803d")     // data plane border
#let c-box = rgb("#ffffff")         // neutral box fill
#let c-box-edge = rgb("#475569")    // neutral box border
#let c-arrow = rgb("#334155")       // arrow / line colour
#let c-note = rgb("#6b7280")        // small annotation text
#let c-orange = rgb("#fef3c7")      // warm / accent fill
#let c-orange-edge = rgb("#b45309") // warm / accent border
#let c-gray = rgb("#f3f4f6")        // secondary fill
#let c-gray-edge = rgb("#9ca3af")   // secondary border
#let c-customer = rgb("#bfdbfe")    // customer responsibility (blue)
#let c-vendor = rgb("#e5e7eb")      // vendor responsibility (grey)

// ---- helpers ---------------------------------------------------------------
// Centred, labelled box.
#let dbox(center, w, h, fill, edge, body, size: 8pt) = {
  let (x, y) = center
  cetz.draw.rect(
    (x - w / 2, y - h / 2), (x + w / 2, y + h / 2),
    fill: fill, stroke: edge, radius: 0.12,
  )
  cetz.draw.content((x, y), text(size: size, body), anchor: "center")
}

// Arrow from a to b with optional label at the midpoint offset.
#let darrow(a, b, edge: c-arrow, label: none, label-dy: 0.0, size: 7pt) = {
  let (ax, ay) = a
  let (bx, by) = b
  cetz.draw.line(a, b, mark: (end: "stealth", fill: edge), stroke: edge)
  if label != none {
    cetz.draw.content(
      ((ax + bx) / 2, (ay + by) / 2 + label-dy),
      text(size: size, fill: c-note, label),
      anchor: "center",
    )
  }
}

// Dashed arrow (feedback / data path).
#let darrow-dash(a, b, edge: c-arrow, label: none, label-dy: 0.0, size: 7pt) = {
  let (ax, ay) = a
  let (bx, by) = b
  cetz.draw.line(
    a, b,
    mark: (end: "stealth", fill: edge),
    stroke: (paint: edge, thickness: 0.7pt, dash: "dashed"),
  )
  if label != none {
    cetz.draw.content(
      ((ax + bx) / 2, (ay + by) / 2 + label-dy),
      text(size: size, fill: c-note, label),
      anchor: "center",
    )
  }
}

// ============================================================================
// 1. Kubernetes cluster architecture
//    Source: Kubernetes official documentation, Components page.
// ============================================================================
#let fig-k8s-architecture() = cetz.canvas({
  // ---- geometry ------------------------------------------------------------
  let cp-x0 = 0.15            // control plane left
  let cp-x1 = 5.5             // control plane right
  let cp-cx = 2.925           // control plane centre x
  let node-cx = 10.9          // worker node centre x
  let node-w = 4.8            // worker node panel width
  let node-half = node-w / 2

  // ---- Control Plane (left) ------------------------------------------------
  cetz.draw.rect(
    (cp-x0, 0.25), (cp-x1, 8.7),
    fill: c-cp, stroke: c-cp-edge, radius: 0.18,
  )
  cetz.draw.content(
    (cp-cx, 8.1), text(size: 8.5pt, weight: "bold", fill: c-cp-edge, [Control Plane]),
    anchor: "center",
  )

  dbox((cp-cx, 6.9), 4.6, 0.9, c-box, c-box-edge, [kube-apiserver])
  dbox((cp-cx, 5.5), 4.6, 0.9, c-box, c-box-edge, [etcd])
  dbox((cp-cx, 4.1), 4.6, 0.9, c-box, c-box-edge, [kube-scheduler])
  dbox((cp-cx, 2.7), 4.6, 0.9, c-box, c-box-edge, [kube-controller-manager])

  // apiserver <-> etcd (double arrow)
  cetz.draw.line(
    (cp-cx, 6.45), (cp-cx, 5.95),
    mark: (start: "stealth", end: "stealth", fill: c-arrow),
    stroke: c-arrow,
  )

  // ---- helper: one worker node panel ---------------------------------------
  let draw-node(cx, top, bot, label) = {
    cetz.draw.rect(
      (cx - node-half, bot), (cx + node-half, top),
      fill: c-dp, stroke: c-dp-edge, radius: 0.12,
    )
    cetz.draw.content(
      (cx, top - 0.34), text(size: 8pt, weight: "bold", fill: c-dp-edge, label),
      anchor: "center",
    )
    dbox((cx, top - 1.05), 4.3, 0.72, c-box, c-box-edge, [kubelet], size: 7.5pt)
    dbox((cx, top - 1.9), 4.3, 0.72, c-box, c-box-edge, [kube-proxy], size: 7.5pt)

    // Pods group (dashed) with two containers + runtime label
    let ptop = top - 2.5
    let pbot = bot + 0.1
    cetz.draw.rect(
      (cx - 1.95, pbot), (cx + 1.95, ptop),
      fill: rgb("#ffffff"),
      stroke: (paint: c-dp-edge, thickness: 0.7pt, dash: "dashed"),
      radius: 0.1,
    )
    cetz.draw.content(
      (cx, ptop - 0.28), text(size: 7pt, weight: "bold", fill: c-dp-edge, [Pods]),
      anchor: "center",
    )
    let cy = (ptop + pbot) / 2
    dbox((cx - 0.9, cy), 1.6, 0.75, c-gray, c-gray-edge, [container], size: 6.5pt)
    dbox((cx + 0.9, cy), 1.6, 0.75, c-gray, c-gray-edge, [container], size: 6.5pt)
    cetz.draw.content(
      (cx, pbot + 0.22), text(size: 6pt, fill: c-note, [container runtime]),
      anchor: "center",
    )

    // kubelet / kube-proxy -> pods
    darrow((cx, top - 1.41), (cx, ptop + 0.02), label: none)
    darrow((cx, top - 2.26), (cx, ptop + 0.02), label: none)
  }

  // ---- two worker nodes (Node 1 above Node 2) ------------------------------
  draw-node(node-cx, 8.7, 4.55, [Node 1])
  draw-node(node-cx, 4.35, 0.2, [Node 2])

  // ---- kube-apiserver -> both kubelets -------------------------------------
  darrow((cp-cx + 2.3, 6.9), (node-cx - 2.15, 8.7 - 1.05), label: none)
  darrow((cp-cx + 2.3, 6.9), (node-cx - 2.15, 4.35 - 1.05), label: none)
  cetz.draw.content(
    (6.95, 5.4), text(size: 6.5pt, fill: c-note, [kubelet watches apiserver]),
    anchor: "center",
  )
})

// ============================================================================
// 2. Serverless computing architecture
//    Source: @mampage2022holistic (holistic resource-management taxonomy).
// ============================================================================
#let fig-serverless-architecture() = cetz.canvas({
  // 1 — Event Trigger (title + sources)
  cetz.draw.rect(
    (0.15, 3.15), (3.05, 5.85), fill: c-box, stroke: c-box-edge, radius: 0.12,
  )
  cetz.draw.content((1.6, 5.4), text(size: 8.5pt, weight: "bold", [Event Trigger]), anchor: "center")
  cetz.draw.content(
    (1.6, 4.65), text(size: 6.5pt, fill: c-note, [HTTP request\ message queue\ file upload\ cron schedule]), anchor: "north",
  )

  // 2 — Function Invocation
  dbox((4.45, 4.5), 2.3, 1.4, c-box, c-box-edge, [Function\ Invocation], size: 8pt)

  // 3 — Container Provisioning (warm / cold inside)
  cetz.draw.rect(
    (5.85, 3.0), (9.35, 6.05), fill: c-box, stroke: c-box-edge, radius: 0.12,
  )
  cetz.draw.content((7.6, 5.95), text(size: 8pt, weight: "bold", [Container\ Provisioning]), anchor: "north")
  cetz.draw.rect(
    (6.05, 4.5), (9.15, 5.15), fill: c-dp, stroke: c-dp-edge, radius: 0.08,
  )
  cetz.draw.content(
    (7.6, 4.825), text(size: 6.5pt, fill: c-dp-edge, [warm instance (reuse)]), anchor: "center",
  )
  cetz.draw.rect(
    (6.05, 3.2), (9.15, 4.35), fill: c-orange, stroke: c-orange-edge, radius: 0.08,
  )
  cetz.draw.content(
    (7.6, 3.775), text(size: 6.5pt, fill: c-orange-edge, [cold start (provision + init)]), anchor: "center",
  )

  // 4 — Function Execution
  dbox((10.55, 4.5), 1.9, 1.4, c-box, c-box-edge, [Function\ Execution], size: 8pt)

  // 5 — Response
  dbox((12.6, 4.5), 1.7, 1.4, c-box, c-box-edge, [Response], size: 8pt)

  // flow arrows
  darrow((3.05, 4.5), (3.3, 4.5), label: none)
  darrow((5.6, 4.5), (5.85, 4.5), label: none)
  darrow((9.35, 4.5), (9.6, 4.5), label: none)
  darrow((11.5, 4.5), (11.75, 4.5), label: none)

  // scale-to-zero note
  darrow-dash((7.6, 3.05), (7.6, 1.6), edge: c-note, label: none)
  cetz.draw.rect(
    (4.9, 0.6), (10.3, 1.6), fill: c-gray, stroke: c-gray-edge, radius: 0.12,
  )
  cetz.draw.content(
    (7.6, 1.1),
    text(size: 7pt, fill: c-note, [scale to zero when idle (no instances, no cost)]),
    anchor: "center",
  )
})

// ============================================================================
// 3. Cloud service-model responsibility matrix
//    Source: @kavis2014 (Kavis 2014, Fig 9.1).
// ============================================================================
#let fig-cloud-services() = cetz.canvas({
  // ---- geometry ------------------------------------------------------------
  let mx = 0.15
  let x0 = mx                 // Service Models left
  let x1 = 2.15               // Service Models right / Cloud Stack left
  let x2 = 4.55               // Cloud Stack right / Stack Components left
  let x3 = 9.35               // Stack Components right / Who Is Responsible left
  let x4 = 13.55              // Who Is Responsible right

  let ytop = 8.0              // body top (top of User layer)
  let y_ua = 6.7              // User | Application boundary
  let y_as = 4.8              // Application | Application Stack boundary
  let y_si = 2.9              // Application Stack | Infrastructure boundary
  let ybot = 1.2              // body bottom (bottom of Infrastructure)

  let hdr_top = 8.9
  let hdr_bot = 8.0
  let hdr_mid = (hdr_top + hdr_bot) / 2

  let c-dark = rgb("#1f2937")

  // ---- helper: plain grid cell ---------------------------------------------
  let cell(x0, x1, y0, y1, body, size: 6pt, fill: c-box, edge: c-gray-edge, bold: false) = {
    cetz.draw.rect((x0, y0), (x1, y1), fill: fill, stroke: edge, radius: 0.03)
    let t = if bold {
      text(size: size, weight: "bold", body)
    } else {
      text(size: size, body)
    }
    cetz.draw.content(((x0 + x1) / 2, (y0 + y1) / 2), t, anchor: "center")
  }

  // ---- header row -----------------------------------------------------------
  cetz.draw.line((mx, hdr_bot), (x4, hdr_bot), stroke: c-gray-edge)
  cetz.draw.content(((x0 + x1) / 2, hdr_mid), text(size: 7.5pt, weight: "bold", [Service Models]), anchor: "center")
  cetz.draw.content(((x1 + x2) / 2, hdr_mid), text(size: 7.5pt, weight: "bold", [Cloud Stack]), anchor: "center")
  cetz.draw.content(((x2 + x3) / 2, hdr_mid), text(size: 7.5pt, weight: "bold", [Stack Components]), anchor: "center")
  cetz.draw.content(((x3 + x4) / 2, hdr_mid), text(size: 7.5pt, weight: "bold", [Who Is Responsible]), anchor: "center")

  // ---- column 2: Cloud Stack (4 tall cells, one layer name each) -----------
  cell(x1, x2, y_ua, ytop, [User], size: 8pt, bold: true)
  cell(x1, x2, y_as, y_ua, [Application], size: 8pt, bold: true)
  cell(x1, x2, y_si, y_as, [Application\ Stack], size: 7.5pt, bold: true)
  cell(x1, x2, ybot, y_si, [Infrastructure], size: 7.5pt, bold: true)

  // ---- column 3: Stack Components grid --------------------------------------
  // User layer: 3 stacked rows
  let u_row = (ytop - y_ua) / 3
  cell(x2, x3, ytop - u_row, ytop, [Login])
  cell(x2, x3, ytop - 2 * u_row, ytop - u_row, [Registration])
  cell(x2, x3, ytop - 3 * u_row, ytop - 2 * u_row, [Administration])

  // Application layer: 2 cols x 3 rows
  let hw = (x3 - x2) / 2
  let ar = (y_ua - y_as) / 3
  cell(x2, x2 + hw, y_ua - ar, y_ua, [Authentication])
  cell(x2 + hw, x3, y_ua - ar, y_ua, [Authorization])
  cell(x2, x2 + hw, y_ua - 2 * ar, y_ua - ar, [User Interface])
  cell(x2 + hw, x3, y_ua - 2 * ar, y_ua - ar, [Transactions])
  cell(x2, x2 + hw, y_ua - 3 * ar, y_ua - 2 * ar, [Reports])
  cell(x2 + hw, x3, y_ua - 3 * ar, y_ua - 2 * ar, [Dashboard])

  // Application Stack layer: 2 cols x 3 rows
  let sr = (y_as - y_si) / 3
  cell(x2, x2 + hw, y_as - sr, y_as, [OS])
  cell(x2 + hw, x3, y_as - sr, y_as, [Programming Language])
  cell(x2, x2 + hw, y_as - 2 * sr, y_as - sr, [App Svr])
  cell(x2 + hw, x3, y_as - 2 * sr, y_as - sr, [Middleware])
  cell(x2, x2 + hw, y_as - 3 * sr, y_as - 2 * sr, [Database])
  cell(x2 + hw, x3, y_as - 3 * sr, y_as - 2 * sr, [Monitoring])

  // Infrastructure layer: dark block
  cetz.draw.rect((x2, ybot), (x3, y_si), fill: c-dark, stroke: c-dark, radius: 0.03)
  cetz.draw.content(((x2 + x3) / 2, 2.45), text(size: 9pt, weight: "bold", fill: white, [IaaS]), anchor: "center")
  cetz.draw.content(((x2 + x3) / 2, 1.95), text(size: 6pt, fill: white, [Vendor Supplies – Infrastructure Security]), anchor: "center")

  // ---- column 1: Service Models (3 vertical bars, SaaS tallest) ------------
  let bw = 0.55
  let gap = 0.1
  let bx = x0 + 0.1
  // SaaS (tallest) -> PaaS -> IaaS (shortest)
  cetz.draw.rect((bx, ybot), (bx + bw, y_ua), fill: rgb("#e5e7eb"), stroke: c-gray-edge, radius: 0.03)
  cetz.draw.content((bx + bw / 2, (ybot + y_ua) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-box-edge, [SaaS])), anchor: "center")
  cetz.draw.rect((bx + bw + gap, ybot), (bx + 2 * bw + gap, y_as), fill: rgb("#d1d5db"), stroke: c-gray-edge, radius: 0.03)
  cetz.draw.content((bx + 1.5 * bw + gap, (ybot + y_as) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-box-edge, [PaaS])), anchor: "center")
  cetz.draw.rect((bx + 2 * (bw + gap), ybot), (bx + 3 * bw + 2 * gap, y_si), fill: rgb("#9ca3af"), stroke: c-gray-edge, radius: 0.03)
  cetz.draw.content((bx + 2.5 * bw + 2 * gap, (ybot + y_si) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-box-edge, [IaaS])), anchor: "center")

  // ---- column 4: Who Is Responsible ----------------------------------------
  let w_r = 1.32
  let g_r = 0.06
  let iaas_x0 = x3 + 0.05
  let iaas_x1 = iaas_x0 + w_r
  let paas_x0 = iaas_x1 + g_r
  let paas_x1 = paas_x0 + w_r
  let saas_x0 = paas_x1 + g_r
  let saas_x1 = saas_x0 + w_r

  // IaaS: Customer = User+Application+AppStack, Vendor = Infrastructure
  cetz.draw.rect((iaas_x0, y_si), (iaas_x1, ytop), fill: c-customer, stroke: c-cp-edge, radius: 0.03)
  cetz.draw.rect((iaas_x0, ybot), (iaas_x1, y_si), fill: c-vendor, stroke: c-gray-edge, radius: 0.03)
  cetz.draw.content(((iaas_x0 + iaas_x1) / 2, (ytop + y_si) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-cp-edge, [Customer])), anchor: "center")
  cetz.draw.content(((iaas_x0 + iaas_x1) / 2, (y_si + ybot) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-gray-edge, [Vendor])), anchor: "center")

  // PaaS: Customer = User+Application, Vendor = AppStack+Infrastructure
  cetz.draw.rect((paas_x0, y_as), (paas_x1, ytop), fill: c-customer, stroke: c-cp-edge, radius: 0.03)
  cetz.draw.rect((paas_x0, ybot), (paas_x1, y_as), fill: c-vendor, stroke: c-gray-edge, radius: 0.03)
  cetz.draw.content(((paas_x0 + paas_x1) / 2, (ytop + y_as) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-cp-edge, [Customer])), anchor: "center")
  cetz.draw.content(((paas_x0 + paas_x1) / 2, (y_as + ybot) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-gray-edge, [Vendor])), anchor: "center")

  // SaaS: Customer = User, Vendor = Application+AppStack+Infrastructure
  cetz.draw.rect((saas_x0, y_ua), (saas_x1, ytop), fill: c-customer, stroke: c-cp-edge, radius: 0.03)
  cetz.draw.rect((saas_x0, ybot), (saas_x1, y_ua), fill: c-vendor, stroke: c-gray-edge, radius: 0.03)
  cetz.draw.content(((saas_x0 + saas_x1) / 2, (ytop + y_ua) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-cp-edge, [Customer])), anchor: "center")
  cetz.draw.content(((saas_x0 + saas_x1) / 2, (y_ua + ybot) / 2), rotate(-90deg, text(size: 7pt, weight: "bold", fill: c-gray-edge, [Vendor])), anchor: "center")

  // ---- legend ---------------------------------------------------------------
  cetz.draw.rect((x0, 0.5), (x0 + 0.9, 0.85), fill: c-customer, stroke: c-cp-edge, radius: 0.04)
  cetz.draw.content((x0 + 1.15, 0.675), text(size: 6.5pt, fill: c-note, [Customer managed]), anchor: "west")
  cetz.draw.rect((x0 + 3.4, 0.5), (x0 + 4.3, 0.85), fill: c-vendor, stroke: c-gray-edge, radius: 0.04)
  cetz.draw.content((x0 + 4.55, 0.675), text(size: 6.5pt, fill: c-note, [Vendor managed]), anchor: "west")
})

// ============================================================================
// 4. ElaX system architecture
//    Source: @yang2019elax (Yang et al. 2019, Fig. 2) — three-phase pipeline.
// ============================================================================
#let fig-elax-architecture() = cetz.canvas({
  // phase titles
  cetz.draw.content((2.45, 9.35), text(size: 8pt, weight: "bold", [1. Workload Prediction]), anchor: "center")
  cetz.draw.content((6.65, 9.35), text(size: 8pt, weight: "bold", [2. Resource Reservation]), anchor: "center")
  cetz.draw.content((10.9, 9.35), text(size: 8pt, weight: "bold", [3. Online Controller]), anchor: "center")

  // ---- Phase 1: Workload Prediction ----------------------------------------
  dbox((2.45, 8.2), 3.4, 0.9, c-box, c-box-edge, [Request History], size: 8pt)
  dbox((2.45, 6.55), 3.8, 1.0, c-box, c-box-edge, [Singular Spectrum\ Analysis], size: 7.5pt)
  cetz.draw.content((2.45, 5.95), text(size: 6pt, fill: c-note, [trace data denoising]), anchor: "center")
  dbox((2.45, 4.65), 3.4, 0.9, c-box, c-box-edge, [LSTM Training], size: 8pt)

  // decision making (with three sub-items)
  cetz.draw.rect((0.55, 1.0), (4.35, 3.8), fill: c-cp, stroke: c-cp-edge, radius: 0.14)
  cetz.draw.content((2.45, 3.5), text(size: 7.5pt, weight: "bold", fill: c-cp-edge, [Decision Making]), anchor: "center")
  dbox((2.45, 2.8), 3.4, 0.55, c-box, c-box-edge, [heterogeneous capacity], size: 6.5pt)
  dbox((2.45, 2.15), 3.4, 0.55, c-box, c-box-edge, [performance bottleneck], size: 6.5pt)
  dbox((2.45, 1.5), 3.4, 0.55, c-box, c-box-edge, [burst peak workload], size: 6.5pt)

  // phase 1 vertical arrows
  darrow((2.45, 7.75), (2.45, 7.05), label: none)
  darrow((2.45, 5.6), (2.45, 5.1), label: none)
  darrow((2.45, 4.2), (2.45, 3.8), label: none)

  // ---- Phase 2: Resource Reservation ---------------------------------------
  dbox((6.65, 6.9), 2.4, 1.0, c-box, c-box-edge, [Scale-out], size: 8pt)
  dbox((6.65, 5.5), 2.4, 1.0, c-box, c-box-edge, [Scale-up], size: 8pt)

  // ---- Phase 3: Online Controller ------------------------------------------
  dbox((10.9, 8.2), 4.0, 0.9, c-box, c-box-edge, [SLO slack feedback], size: 7.5pt)
  dbox((10.9, 6.55), 4.0, 0.9, c-box, c-box-edge, [Elasticity Provisioning], size: 7.5pt)

  // servers group (dashed container)
  cetz.draw.rect(
    (8.6, 4.2), (13.2, 5.8),
    fill: rgb("#ffffff"), stroke: (paint: c-box-edge, thickness: 0.7pt, dash: "dashed"),
    radius: 0.12,
  )
  cetz.draw.content((10.9, 5.55), text(size: 7pt, weight: "bold", fill: c-note, [Servers]), anchor: "center")
  dbox((8.9, 4.75), 1.4, 0.8, c-box, c-box-edge, [Server 1], size: 6.5pt)
  dbox((10.9, 4.75), 1.4, 0.8, c-box, c-box-edge, [Server 2], size: 6.5pt)
  dbox((12.9, 4.75), 1.4, 0.8, c-box, c-box-edge, [Server 3], size: 6.5pt)

  // resource + platform stack
  dbox((10.9, 3.15), 4.0, 0.7, c-orange, c-orange-edge, [CPU / RAM / Disk / Network], size: 7pt)
  dbox((10.9, 2.2), 4.0, 0.7, c-dp, c-dp-edge, [Docker Engine], size: 7pt)
  dbox((10.9, 1.25), 4.0, 0.7, c-gray, c-gray-edge, [Operating System], size: 7pt)

  // phase 3 vertical arrows
  darrow((10.9, 7.75), (10.9, 7.0), label: none)
  darrow((10.9, 6.1), (10.9, 5.8), label: none)
  darrow((10.9, 4.2), (10.9, 3.5), label: none)
  darrow((10.9, 2.8), (10.9, 2.55), label: none)
  darrow((10.9, 1.85), (10.9, 1.6), label: none)

  // ---- inter-phase arrows (left -> right) ----------------------------------
  // Decision Making -> Scale-out / Scale-up
  darrow((4.35, 2.5), (5.45, 6.9), edge: c-arrow)
  darrow((4.35, 2.5), (5.45, 5.5), edge: c-arrow)

  // Scale-out / Scale-up -> Elasticity Provisioning
  darrow((7.85, 6.9), (8.9, 6.55), edge: c-arrow)
  darrow((7.85, 5.5), (8.9, 6.55), edge: c-arrow)

  // ---- feedback: SLO slack (controller -> reservation) ----------------------
  darrow-dash((8.9, 8.2), (7.85, 6.9), edge: c-note, label: none)

  // ---- "Request History Data" dashed spine across the top -------------------
  cetz.draw.line(
    (0.6, 8.95), (12.6, 8.95),
    stroke: (paint: c-note, thickness: 0.7pt, dash: "dashed"),
  )
  cetz.draw.content((6.6, 9.15), text(size: 6.5pt, fill: c-note, [Request History Data]), anchor: "center")
  darrow((3.0, 8.95), (2.7, 8.65), edge: c-note)
})
