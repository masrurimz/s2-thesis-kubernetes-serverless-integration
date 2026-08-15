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
  // ---- Control Plane (left) ------------------------------------------------
  cetz.draw.rect(
    (0.15, 0.25), (6.15, 8.45),
    fill: c-cp, stroke: c-cp-edge, radius: 0.18,
  )
  cetz.draw.content(
    (3.15, 7.85), text(size: 8.5pt, weight: "bold", fill: c-cp-edge, [Control Plane]),
    anchor: "center",
  )

  // components stacked (centred x = 3.15)
  dbox((3.15, 6.55), 4.6, 1.0, c-box, c-box-edge, [kube-apiserver])
  dbox((3.15, 5.05), 4.6, 1.0, c-box, c-box-edge, [etcd])
  dbox((3.15, 3.55), 4.6, 1.0, c-box, c-box-edge, [kube-scheduler])
  dbox((3.15, 2.05), 4.6, 1.0, c-box, c-box-edge, [kube-controller-manager])

  // apiserver <-> etcd (persist + read)
  cetz.draw.line(
    (3.15, 6.05), (3.15, 5.55),
    mark: (start: "stealth", end: "stealth", fill: c-arrow),
    stroke: c-arrow,
  )

  // ---- Data Plane (right) --------------------------------------------------
  cetz.draw.rect(
    (7.35, 0.25), (13.0, 8.45),
    fill: c-dp, stroke: c-dp-edge, radius: 0.18,
  )
  cetz.draw.content(
    (10.175, 7.85), text(size: 8.5pt, weight: "bold", fill: c-dp-edge, [Worker Node(s)]),
    anchor: "center",
  )

  dbox((10.175, 6.55), 4.4, 1.0, c-box, c-box-edge, [kubelet])
  dbox((10.175, 5.05), 4.4, 1.0, c-box, c-box-edge, [kube-proxy])

  // Pods group (dashed container) with two containers inside
  cetz.draw.rect(
    (7.95, 0.75), (12.4, 4.15),
    fill: rgb("#ffffff"), stroke: (paint: c-dp-edge, thickness: 0.7pt, dash: "dashed"),
    radius: 0.12,
  )
  cetz.draw.content(
    (10.175, 3.75), text(size: 7.5pt, weight: "bold", fill: c-dp-edge, [Pods]),
    anchor: "center",
  )
  dbox((9.0, 2.15), 1.7, 1.5, c-gray, c-gray-edge, [container], size: 7pt)
  dbox((11.35, 2.15), 1.7, 1.5, c-gray, c-gray-edge, [container], size: 7pt)
  cetz.draw.content(
    (10.175, 1.05), text(size: 6.5pt, fill: c-note, [container runtime]),
    anchor: "center",
  )

  // ---- cross-plane arrows ---------------------------------------------------
  // kube-apiserver -> kubelet (kubelet talks to apiserver)
  darrow((5.45, 6.55), (7.975, 6.55), label: none)
  cetz.draw.content(
    (6.71, 7.15), text(size: 7pt, fill: c-note, [kubelet watches apiserver]),
    anchor: "center",
  )

  // kubelet -> pods (kubelet manages containers)
  darrow((10.175, 6.05), (10.175, 4.15), label: none)

  // kube-proxy -> pods (network rules)
  darrow((10.175, 4.55), (10.175, 4.15), label: none)
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
  let left-x = 0.15
  let left-w = 5.0            // "Cloud Stack" column (layer + components)
  let col-w = 2.4             // each model column
  let col-y = 8.05            // model column header top
  let col-h = 0.6             // model column header height
  let body-top = 7.35         // top of the row band
  let row-h = 1.55            // each row height
  let rows = (
    (name: [User], comp: [Login, Registration,\ Administration, Authentication,\ Authorization], iaas: "C", paas: "C", saas: "C"),
    (name: [Application], comp: [User Interface,\ Transactions, Reports,\ Dashboard], iaas: "C", paas: "C", saas: "V"),
    (name: [Application Stack], comp: [OS, Programming Language,\ App Server, Middleware,\ Database, Monitoring], iaas: "C", paas: "V", saas: "V"),
    (name: [Infrastructure], comp: [Servers, Storage,\ Networking, Virtualization], iaas: "V", paas: "V", saas: "V"),
  )
  let col0 = left-x + left-w            // IaaS column left edge
  let col1 = col0 + col-w               // PaaS
  let col2 = col1 + col-w               // SaaS
  let body-bot = body-top - rows.len() * row-h

  // ---- outer frame ---------------------------------------------------------
  cetz.draw.rect(
    (left-x, body-bot - 0.45), (col2 + col-w, col-y + col-h),
    fill: rgb("#ffffff"), stroke: c-box-edge, radius: 0.1,
  )

  // ---- header: Cloud Stack | (Service Models -> IaaS PaaS SaaS) ------------
  cetz.draw.content(
    (left-x + left-w / 2, col-y + col-h / 2),
    text(size: 8pt, weight: "bold", [Cloud Stack]), anchor: "center",
  )
  cetz.draw.content(
    ((col0 + col2 + col-w) / 2, col-y + col-h + 0.42),
    text(size: 8pt, weight: "bold", [Service Models]), anchor: "center",
  )
  cetz.draw.content(
    (col0 + col-w / 2, col-y + col-h / 2),
    text(size: 8pt, weight: "bold", [IaaS]), anchor: "center",
  )
  cetz.draw.content(
    (col1 + col-w / 2, col-y + col-h / 2),
    text(size: 8pt, weight: "bold", [PaaS]), anchor: "center",
  )
  cetz.draw.content(
    (col2 + col-w / 2, col-y + col-h / 2),
    text(size: 8pt, weight: "bold", [SaaS]), anchor: "center",
  )

  // ---- rows ----------------------------------------------------------------
  for (i, row) in rows.enumerate() {
    let ytop = body-top - i * row-h
    let ymid = ytop - row-h / 2

    // left cell: layer name + components
    cetz.draw.content(
      (left-x + left-w / 2, ytop - 0.16),
      text(size: 8pt, weight: "bold", row.name), anchor: "north",
    )
    cetz.draw.content(
      (left-x + left-w / 2, ytop - 0.55),
      text(size: 6.3pt, fill: c-note, row.comp), anchor: "north",
    )

    // responsibility cells
    let cells = ((col0, row.iaas), (col1, row.paas), (col2, row.saas))
    for cell in cells {
      let cx = cell.at(0)
      let v = cell.at(1)
      let fill = if v == "C" { c-customer } else { c-vendor }
      let edge = if v == "C" { c-cp-edge } else { c-gray-edge }
      let word = if v == "C" { [Customer] } else { [Vendor] }
      cetz.draw.rect(
        (cx + 0.1, ytop - row-h + 0.08), (cx + col-w - 0.1, ytop - 0.08),
        fill: fill, stroke: edge, radius: 0.08,
      )
      cetz.draw.content(
        (cx + col-w / 2, ymid),
        text(size: 7pt, weight: "bold", fill: edge, word), anchor: "center",
      )
    }
  }

  // ---- legend --------------------------------------------------------------
  cetz.draw.rect(
    (left-x, body-bot - 0.4), (left-x + 1.0, body-bot - 0.1),
    fill: c-customer, stroke: c-cp-edge, radius: 0.06,
  )
  cetz.draw.content(
    (left-x + 1.35, body-bot - 0.25), text(size: 6.5pt, fill: c-note, [Customer responsible]),
    anchor: "west",
  )
  cetz.draw.rect(
    (left-x + 4.0, body-bot - 0.4), (left-x + 5.0, body-bot - 0.1),
    fill: c-vendor, stroke: c-gray-edge, radius: 0.06,
  )
  cetz.draw.content(
    (left-x + 5.35, body-bot - 0.25), text(size: 6.5pt, fill: c-note, [Vendor responsible]),
    anchor: "west",
  )
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
