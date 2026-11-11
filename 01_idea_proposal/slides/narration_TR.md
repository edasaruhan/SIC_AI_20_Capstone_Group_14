# Fatura Dedektifi sunum metni

## 1. Açılış

Merhaba, ben Mert Güngör.

Bu videoda Samsung Innovation Campus capstone projesi için fikrimi anlatacağım.

Projenin adı Fatura Dedektifi.

Şu soruya cevap arıyor: Evde elektriği hangi cihaz harcıyor?

## 2. Problem

Elektrik faturasında tek bir toplam yazar.

Hangi cihazın ne kadar harcadığını göstermez, bu yüzden nereden tasarruf edeceğimizi bilemeyiz.

Enerji maliyeti Türkiye'de ciddi bir yük. Eurostat'a göre 2025'te nüfusun yüzde 19,5'i evini yeterince ısıtamadı.

Her cihaza ayrı sayaç takmak ise pahalı ve zahmetli.

## 3. Gerçek bir gün

Bu grafik gerçek bir evin bir günü. Veriyi indirip kendim çizdim.

Gri çizgi sayacın gördüğü toplam tüketim.

Renkli alanlar aynı gün cihazların tek tek çektiği güç: bulaşık makinesi, çamaşır makinesi, su ısıtıcı ve buzdolabı.

O gün evin harcadığı elektriğin dörtte biri bulaşık makinesine gitmiş.

## 4. Proje fikri

Önerim, yalnızca gri çizgiye bakarak renkli alanları tahmin eden bir yapay zekâ modeli.

Tek sayaçtan beş cihazın tüketimini ayıracak: buzdolabı, çamaşır makinesi, bulaşık makinesi, su ısıtıcı ve mikrodalga.

Bunu basit bir kuralla yapmak zor, çünkü cihazlar aynı anda çalışıyor ve çektikleri güç birbirine benziyor.

Bu evde çamaşır makinesinin ısıtıcısı 2,1, bulaşık makinesininki 2,2 kilovat çekiyor. Sayaçta neredeyse aynı görünüyorlar.

## 5. SDG ile ilişkisi

Proje, Sürdürülebilir Kalkınma Amaçları'ndan yedincisine, yani erişilebilir ve temiz enerjiye bağlı.

En çok enerji verimliliği hedefine hizmet ediyor, çünkü insanlar ancak görebildikleri tüketimi azaltabilir.

Sorumlu tüketim ve iklim eylemi amaçlarına da dolaylı katkısı var.

## 6. Literatür

Literatürde iki temel çalışma buldum.

Kelly ve Knottenbelt 2015'te bu probleme derin sinir ağlarını uygulamış ve klasik yöntemlerden daha iyi sonuç almış.

Zhang ve arkadaşları 2018'de, toplam sinyalin bir penceresinden tek bir cihazın o andaki gücünü tahmin eden bir yöntem önermiş.

İkisi de araştırma çalışması. Özetlerinde ev halkına yönelik bir araç ya da maliyet hesabı yok.

Ben modeli hiç görmediği evlerde test edip sonucu kilovatsaat ve lira olarak göstermek istiyorum.

## 7. Veri

Veri seti REFIT. İngiltere'de 20 evde iki yıla yakın süre toplanmış.

Açık lisanslı ve ücretsiz.

Her evde toplam güç ve dokuz cihazın gücü yaklaşık 8 saniyede bir ölçülmüş.

Toplam yaklaşık 120 milyon satır var.

İki evi ayrıntılı inceledim. Birinde dakikaların dörtte birinde veri yok.

Bu boşlukları ayıklamam, evleri de eğitim ve test olarak ayırmam gerekiyor.

## 8. Yaklaşım

Yaklaşım olarak derin öğrenmeyi seçtim, çünkü girdi ham bir zaman serisi ve modelin her cihazın çalışma şeklini öğrenmesi gerekiyor.

Her cihaz için küçük bir evrişimli sinir ağı eğiteceğim.

Kıyaslamak için önce iki basit yöntem denedim. Bir evde eğitip başka bir evde test ettim.

Su ısıtıcıda ortalamayı tahmin etmek 45 watt yanılıyor. Klasik makine öğrenmesi bunu 18 watta indiriyor.

Çamaşır makinesinde ise klasik yöntem neredeyse hiç iyileştirmiyor, hata 44 wattta kalıyor.

Derin öğrenmenin fark yaratmasını beklediğim yer burası.

Hedefim, beş cihazın en az dördünde klasik yöntemden daha düşük hata almak.

## 9. Demo, sınırlar ve kapanış

Dönem sonunda tarayıcıdan açılan bir demo olacak.

Bir günün sayaç verisini yükleyince hangi cihazın kaç kilovatsaat ve kaç lira harcadığını gösterecek.

Projenin sınırları da var. Veri İngiltere'deki evlerden, Türkiye'deki evlerde cihazlar farklı olabilir.

Faturanın hangi cihaza gittiğini gören bir ev, tasarrufa nereden başlayacağını bilir.

Dinlediğiniz için teşekkür ederim.
