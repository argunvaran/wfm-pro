
# WFM Pro Mobile App (Flutter)

Bu klasör, WFM Pro WFM sisteminin Flutter tabanlı mobil uygulaması için gerekli **kaynak kodları** içerir. Bilgisayarınızda Flutter yüklü olmadığı için projeyi çalıştırılabilir halde değil, "kopyala-yapıştır" yapmaya hazır kod blokları halinde hazırladım.

## Nasıl Kurulur?

1.  **Flutter Kurulumu:** [flutter.dev](https://flutter.dev) adresinden Flutter SDK'sını indirip kurun.
2.  **Proje Oluşturma:** Terminalde şu komutu çalıştırın:
    ```bash
    flutter create wfm_mobile
    ```
3.  **Dosyaları Kopyalama:**
    *   Bu klasördeki `lib` içeriğini, yeni oluşturduğunuz projenin `lib` klasörüne kopyalayın.
    *   `pubspec.yaml` dosyasına şu paketleri ekleyin:
        ```yaml
        dependencies:
          flutter:
            sdk: flutter
          http: ^1.1.0
          shared_preferences: ^2.2.0
          intl: ^0.18.1
        ```
4.  **Çalıştırma:**
    ```bash
    flutter run
    ```

## Yapı

*   `main.dart`: Uygulamanın giriş noktası.
*   `services/api_service.dart`: Django backend ile konuşan servis.
*   `screens/`: Giriş, Dashboard ve Vardiya ekranları.
