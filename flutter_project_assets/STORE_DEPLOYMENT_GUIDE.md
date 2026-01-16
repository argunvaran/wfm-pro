# Mobile App Store Deployment Guide

## 1. Android (Google Play Store) - Detaylı Anlatım

Bu bölüm, Windows bilgisayarınızda sıfırdan "Production" (Canlı) sürüm oluşturup Google Play'e yüklemeniz için gereken her adımı içerir.

### Adım 1: İmza Anahtarı (Keystore) Oluşturma
Android uygulamalarının sizin tarafınızdan yapıldığını kanıtlayan gizli bir dosyadır.

1.  Bilgisayarınızda kolay ulaşabileceğiniz bir klasör belirleyin (Örn: `C:\Users\argun\keystore\`).
2.  Terminali açın ve şu komutu yapıştırın (Şifre soracaktır, **unutmayacağınız** bir şifre belirleyin):

    ```powershell
    keytool -genkey -v -keystore c:\Users\argun\upload-keystore.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias upload
    ```
    
    *Size İsim, Organizasyon vb. soracak. Bunları doldurun veya Enter ile geçin. Sonunda "yes" yazıp onaylayın.*

### Adım 2: Flutter Projesine Tanıtma
Flutter'ın bu anahtarı nerede bulacağını ve şifresinin ne olduğunu bilmesi gerekir.

1.  Projenizin içinde `android/key.properties` adında **yeni bir dosya** oluşturun.
2.  İçine şu bilgileri yapıştırın (Şifreleri kendi belirlediğinizle değiştirin):

    ```properties
    storePassword=BELIRLEDIGINIZ_SIFRE
    keyPassword=BELIRLEDIGINIZ_SIFRE
    keyAlias=upload
    storeFile=c:/Users/argun/upload-keystore.jks
    ```
    *(Not: Windows olsa bile dosya yolunda `/` işareti kullanın)*

3.  `android/app/build.gradle` dosyasını açın. `android { ... }` bloğunun hemen **öncesine** şunu ekleyin:

    ```gradle
    def keystoreProperties = new Properties()
    def keystorePropertiesFile = rootProject.file('key.properties')
    if (keystorePropertiesFile.exists()) {
        keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
    }
    ```

4.  Aynı dosyada `buildTypes` kısmını bulun ve `signingConfig` ekleyin:

    ```gradle
    buildTypes {
        release {
            // İMZA AYARINI BURAYA EKLİYORUZ:
            signingConfig signingConfigs.create("release") {
                keyAlias = keystoreProperties['keyAlias']
                keyPassword = keystoreProperties['keyPassword']
                storeFile = keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
                storePassword = keystoreProperties['storePassword']
            }
            minifyEnabled false
            shrinkResources false
        }
    }
    ```

### Adım 3: Derleme (Build)
Artık her şey hazır. Terminalde proje klasörünüze gelip şu komutu çalıştırın:

```bash
flutter build appbundle
```

*   Bu işlem 2-5 dakika sürebilir.
*   İşlem bittiğinde dosyanız şurada oluşacak:
    `build\app\outputs\bundle\release\app-release.aab`

### Adım 4: Google Play Console Yükleme

1.  [Google Play Console](https://play.google.com/console) adresine gidin.
    *   Hesabınız yoksa $25 ödeyip açın (Tek seferliktir, aylık değildir).
2.  **"Uygulama Oluştur"** butonuna basın.
    *   Uygulama Adı: `WFM Pro`
    *   Dil: Türkçe
    *   Uygulama mı Oyun mu: Uygulama
    *   Ücretli mi Ücretsiz mi: Ücretsiz (veya sisteminiz nasılsa).
3.  Uygulama oluşturulduktan sonra sol menüden **"Test etme ve yayınlama" -> "Üretim" (Production)** sayfasına gidin.
4.  **"Yeni sürüm oluştur"** deyin.
5.  "App Bundle'lar" kısmına, az önce oluşturduğunuz `app-release.aab` dosyasını sürükleyip bırakın.
6.  Dosya yüklenince "Sürüm Adı" otomatik gelir (Örn: 1.0.0).
7.  **"İleri"** ve ardından **"Kaydet"** diyerek işlemi tamamlayın.

Tebrikler! Sürümünüz incelemeye gönderildi. İlk seferde onaylanması 1-3 gün sürebilir.

---

## 2. iOS (Apple App Store) - Özet
*(iOS için Mac bilgisayar şarttır)*
1.  Terminalde `flutter build ipa` çalıştırın.
2.  Oluşan `.ipa` dosyasını "Transporter" uygulaması ile Apple'a gönderin.
3.  App Store Connect web sitesinden yayına alın.
