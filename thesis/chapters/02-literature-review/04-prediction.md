## 2.4 Algoritma dan Model Prediksi (Prediction Algorithms and Models)

Workload prediction transforms reactive scaling (responding to current metrics) into proactive scaling (preparing for anticipated demand). Time-series forecasting using recurrent neural networks has demonstrated effectiveness for cloud workload prediction tasks [5], [6].

### 2.4.1 LSTM (Long Short-Term Memory)

LSTM, introduced by Hochreiter and Schmidhuber [15], is a recurrent neural network architecture designed to learn long-term dependencies in sequential data. The key innovation is the **cell state**—a conveyor belt of information that runs through the entire sequence—regulated by three gating mechanisms:

```
           ┌───────────────────────────────────────────┐
           │              LSTM Cell                     │
           │  ┌─────────┐ ┌─────────┐ ┌─────────┐      │
    x_t ───┼─►│ Forget  │ │ Input   │ │ Output  │      │
           │  │ Gate    │ │ Gate    │ │ Gate    │      │
           │  └────┬────┘ └────┬────┘ └────┬────┘      │
           │       │           │           │            │
           │       ▼           ▼           ▼            │
           │  ┌────────────────────────────────────┐   │
h_{t-1} ───┼─►│         Cell State (C_t)           │───┼──► h_t
           │  └────────────────────────────────────┘   │
           └───────────────────────────────────────────┘
```

**Figure 2-5: LSTM Cell Architecture**

- **Forget Gate**: Decides what information to discard from the cell state.
- **Input Gate**: Decides what new information to store in the cell state.
- **Output Gate**: Decides what to output based on the cell state.

LSTM has been widely applied to cloud workload prediction [5], [16]. However, its three-gate architecture introduces substantial computational overhead: for a hidden state of size $h$, each LSTM cell requires $4h(h + x) + 4h$ parameters (where $x$ is the input dimension), resulting in slower training and higher inference latency compared to simpler alternatives.

### 2.4.2 GRU (Gated Recurrent Unit)

GRU, proposed by Cho et al. [6], simplifies the LSTM architecture by combining the forget and input gates into a single **update gate** and merging the cell state and hidden state:

```
           ┌───────────────────────────────────────────┐
           │              GRU Cell                      │
           │  ┌─────────┐ ┌─────────┐                  │
    x_t ───┼─►│ Reset   │ │ Update  │                  │
           │  │ Gate    │ │ Gate    │                  │
           │  └────┬────┘ └────┬────┘                  │
           │       │           │                        │
           │       ▼           ▼                        │
           │  ┌────────────────────────────────────┐   │
h_{t-1} ───┼─►│      Hidden State (h_t)            │───┼──► h_t
           │  └────────────────────────────────────┘   │
           └───────────────────────────────────────────┘
```

**Figure 2-6: GRU Cell Architecture**

- **Reset Gate**: Controls how much past information to forget.
- **Update Gate**: Controls the balance between previous hidden state and candidate activation, serving the combined role of LSTM's forget and input gates.

### LSTM vs GRU Comparison

Chung et al. [6] conducted an empirical evaluation of gated recurrent networks and found that GRU achieves comparable or superior performance to LSTM on many sequence modeling tasks while using approximately 25% fewer parameters. Mondal et al. [5] specifically evaluated both architectures for Kubernetes workload prediction and confirmed similar accuracy with significant computational savings.

**Table 2-5: LSTM vs GRU Comparison (based on [5], [6])**

| Aspect | LSTM | GRU |
|--------|------|-----|
| Gates | 3 (forget, input, output) | 2 (reset, update) |
| State vectors | 2 (cell state + hidden) | 1 (hidden only) |
| Parameters per cell | $4h(h+x) + 4h$ | $3h(h+x) + 3h$ |
| Training speed | Baseline | ~25% faster |
| Memory usage | Higher | Lower |
| Prediction accuracy | Reference | Comparable |
| Real-time suitability | Moderate | High |

For the workload prediction task in this research—short-horizon (30-second) HTTP traffic forecasting with a real-time latency constraint (<50ms inference)—GRU's lower computational cost and comparable accuracy make it the preferred architecture. The reduced parameter count also mitigates overfitting risk given the limited training data available from synthetic workload patterns [5], [16].
