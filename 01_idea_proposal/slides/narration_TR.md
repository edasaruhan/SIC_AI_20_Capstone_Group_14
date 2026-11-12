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

Çamaşır makinesinde ise klasik yöntem neredeyse hiç iyileştirmiyor, hata 44 watt'ta kalıyor.

Derin öğrenmenin fark yaratmasını beklediğim yer burası.

Hedefim, beş cihazın en az dördünde klasik yöntemden daha düşük hata almak.

## 9. Türkiye'de fatura

Maliyeti Türkiye'nin tarifesiyle hesaplıyorum. Üç zamanlı tarifede elektriğin kilovatsaati gece 3 lira 26 kuruş, gündüz 4 lira 92 kuruş, akşam puant saatlerinde 7 lira.

Tek zamanlı tarifede ise günde 8 kilovatsaate kadar 3 lira 24 kuruş, üstü 4 lira 86 kuruş.

Az önceki günü iki tarifeyle de fiyatladım. Tek zamanlıda 37 lira, üç zamanlıda 50 lira tutuyor.

Öğlenki bulaşık ve sabahki çamaşır geceye kaydırılırsa üç zamanlı fatura 46 liraya iniyor.

Yani bu ev için tek zamanlı tarife daha ucuz. Demo bu karşılaştırmayı her ev için yapacak ve hangi tarifenin, hangi saatin daha ucuz olduğunu söyleyecek.

## 10. İngiltere verisinden Türkiye'ye

Veri İngiltere'den. Ama iki ülkede de şebeke 230 volt ve 50 hertz, hedeflediğim beş cihaz da Türk evlerinde var.

İlk adımda modeli başka bir veri setinde de test edeceğim. Literatürde hata aynı ülke içinde pek artmıyor, başka ülkeye geçince artıyor.

İkinci adımda Türk evlerinde yaygın olan klima, termosifon ve çay makinesi gibi yükleri eğitim verisine yapay olarak ekleyeceğim.

Üçüncü adımda modeli saatlik veride de ölçeceğim, çünkü Türkiye'deki akıllı sayaçlar saatlik veri veriyor.

Son adımda bir Türk evinde akıllı prizlerle birkaç hafta ölçüm alıp modelin hatasını gerçek Türk verisinde raporlayacağım.

## 11. Demo, sınır ve kapanış

Dönem sonunda tarayıcıdan açılan bir demo olacak.

Bir günün sayaç verisini yükleyince cihaz bazında tüketimi, iki tarifedeki faturayı ve geceye kaydırılabilecek cihazı gösterecek.

Bir sınırı var. Türkiye'den etiketli açık veri bulamadım, bu yüzden kendi ölçümüm küçük bir kontrol olacak.

Faturanın hangi cihaza gittiğini gören bir ev, tasarrufa nereden başlayacağını bilir.

Dinlediğiniz için teşekkür ederim.
