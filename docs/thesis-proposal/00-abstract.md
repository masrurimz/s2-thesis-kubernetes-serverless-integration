# Abstract

## Indonesian (Abstrak)

Penggunaan layanan cloud computing telah mengalami pertumbuhan yang signifikan dalam beberapa tahun terakhir, didorong oleh kebutuhan akan skalabilitas, efisiensi biaya, dan fleksibilitas dalam menjalankan aplikasi. Kubernetes, sebagai platform orkestrasi container, dan serverless computing, yang menawarkan model eksekusi tanpa pengelolaan server, menjadi dua teknologi utama dalam ekosistem cloud. Namun, masing-masing memiliki kelebihan dan keterbatasan dalam menangani beban kerja yang dinamis.

Penelitian ini mengusulkan sebuah sistem hybrid yang mengintegrasikan Kubernetes dan serverless computing untuk mengoptimalkan distribusi lalu lintas berdasarkan prediksi beban kerja. Dengan menggunakan algoritma prediksi berbasis Gated Recurrent Unit (GRU), sistem ini dapat memperkirakan pola lalu lintas mendatang dan secara proaktif menyesuaikan alokasi sumber daya antara cluster Kubernetes dan fungsi serverless.

Pendekatan ini diharapkan dapat memberikan keseimbangan antara biaya operasional, kinerja, dan keandalan sistem dengan meminimalkan pelanggaran Service Level Agreement (SLA) dan meningkatkan efisiensi penggunaan sumber daya. Evaluasi akan dilakukan menggunakan dataset nyata dari HTTP trace logs (ClarkNet dan Calgary) untuk memvalidasi efektivitas model prediksi dan mekanisme distribusi lalu lintas yang diusulkan.

**Kata Kunci**: Cloud Computing, Kubernetes, Serverless, Prediksi Beban Kerja, GRU, Distribusi Lalu Lintas, SLA

---

## English (Abstract)

The use of cloud computing services has experienced significant growth in recent years, driven by the need for scalability, cost efficiency, and flexibility in running applications. Kubernetes, as a container orchestration platform, and serverless computing, which offers a server-management-free execution model, are two main technologies in the cloud ecosystem. However, each has advantages and limitations in handling dynamic workloads.

This research proposes a hybrid system that integrates Kubernetes and serverless computing to optimize traffic distribution based on workload prediction. Using a Gated Recurrent Unit (GRU) based prediction algorithm, this system can estimate upcoming traffic patterns and proactively adjust resource allocation between Kubernetes clusters and serverless functions.

This approach is expected to provide a balance between operational costs, performance, and system reliability by minimizing Service Level Agreement (SLA) violations and improving resource utilization efficiency. Evaluation will be conducted using real datasets from HTTP trace logs (ClarkNet and Calgary) to validate the effectiveness of the proposed prediction model and traffic distribution mechanism.

**Keywords**: Cloud Computing, Kubernetes, Serverless, Workload Prediction, GRU, Traffic Distribution, SLA
