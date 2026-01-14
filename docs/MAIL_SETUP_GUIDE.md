
# WFM Pro - Mail Kurulum Rehberi

## 1. Kurumsal Mail (ZOHO Mail - Insanlar Arasi Iletisim)
Bu adimlar **sadece sirket.com** adresini aldiktan sonra yapilmalidir.

1. [Zoho Mail Free Plan](https://www.zoho.com/mail/zohomail-pricing.html) sayfasina gidin ve 'Forever Free Plan' secin.
2. Alan adinizi (domain) girin.
3. Zoho size 3 adet DNS kaydi verecek (TXT, MX, SPF).
4. Bu kayitlari Godaddy DNS Yonetim panelinize ekleyin.
   - **MX Kayitlari:** Zoho'nun size verdigi `mx.zoho.eu` gibi adresler. Bu kayitlar maillerin Zoho'ya gelmesini saglar.
   - **SPF Kaydi:** `v=spf1 include:zoho.eu ~all` (Bu mailin guvenilir oldugunu kanitlar).

## 2. Otomatik Mailler (AWS SES - Sistem Bildirimleri)
Yazilimimizin sifre sifirlama vb. maillerini gondermesi icin:

1. AWS Konsolu -> **Simple Email Service (SES)** -> **Identities** menusu.
2. **Create Identity** butonuna basin.
3. **Domain** secenegini secin (orn: wfm-pro.com).
4. AWS size 3 adet CNAME kaydi verecek.
5. Bu CNAME kayitlarini Godaddy DNS panelinize ekleyin. (Bu islem DKIM imzasini aktif eder, boylece mailleriniz SPAM'a dusmez).
6. **SMTP Credentials** olusturun ve `AWS_ACCESS_KEY` bilgilerini projenin `.env` dosyasina kaydedin.

## 3. Test
Kurulum bitince su scripti calistirabilirsiniz:
`python scripts/setup_aws_ses.py no-reply@wfm-pro.com`
