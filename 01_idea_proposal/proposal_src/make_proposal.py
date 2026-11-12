"""Builds the one-page idea proposal in English and Turkish (docx). usage: python make_proposal.py <en|tr> <out.docx>"""
import sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor

REFS = [
    "[1] Eurostat, Inability to keep home adequately warm (ilc_mdes01), Türkiye, 2025. https://ec.europa.eu/eurostat/databrowser/view/ilc_mdes01/default/table",
    "[2] Kelly, J., & Knottenbelt, W. (2015). Neural NILM: Deep Neural Networks Applied to Energy Disaggregation. ACM BuildSys '15. https://doi.org/10.1145/2821650.2821672",
    "[3] Zhang, C., Zhong, M., Wang, Z., Goddard, N., & Sutton, C. (2018). Sequence-to-point learning with neural networks for non-intrusive load monitoring. AAAI-18. https://doi.org/10.1609/aaai.v32i1.11873",
    "[4] Murray, D., Stankovic, L., & Stankovic, V. (2017). An electrical load measurements dataset of United Kingdom households from a two-year longitudinal study. Scientific Data, 4, 160122. https://doi.org/10.1038/sdata.2016.122",
    "[5] D'Incecco, M., Squartini, S., & Zhong, M. (2019). Transfer Learning for Non-Intrusive Load Monitoring. IEEE Transactions on Smart Grid, 11(2), 1419-1429. https://doi.org/10.1109/TSG.2019.2938068",
    "[6] EPDK, tariff tables for electricity bills, residential low-voltage tariff valid from 4 April 2026. https://www.epdk.gov.tr/Detay/Icerik/3-1327/elektrik-faturalarina-esas-tarife-tablolari",
]

EN = dict(
    title="Idea Proposal: Fatura Dedektifi (Bill Detective)",
    sub="Finding which appliance uses the electricity from a single household meter",
    by="Mert Güngör, Group 14, Samsung Innovation Campus, Artificial Intelligence Course",
    meta_title="Idea Proposal: Fatura Dedektifi",
    refs="References",
    sections=[
        ("1. Project Idea", [
            "An electricity bill shows one total. It does not show which appliance used how much, so a household cannot tell where to save or which tariff suits it. Energy costs are a real burden in Türkiye. In 2025, 19.5% of the population could not afford to keep their home adequately warm [1]. Heating is mostly gas, but electricity is the bill a household can cut appliance by appliance. A separate meter on every appliance is expensive and impractical.",
            "I want to build a model that takes only the total power signal of a home and estimates how much the fridge, the washing machine, the dishwasher, the kettle and the microwave used (non-intrusive load monitoring, NILM). The result will be a web demo that turns one day of meter data into kWh and TL per appliance. It will price the day with Türkiye's single-rate and three-rate (day, peak, night) tariffs, say which one is cheaper, and name the appliance worth moving to the night. I will measure success per appliance with the mean absolute error in watts (MAE) and the error in total energy, on homes the model never saw in training.",
        ]),
        ("2. Relevance to the Sustainable Development Goals", [
            "The project serves SDG 7, Affordable and Clean Energy. It relates most to target 7.3 (improve energy efficiency), because people can only reduce the consumption they can see, and more loosely to target 7.1 (affordable energy services), by helping households lower their bills. It also supports SDG 12.8 (information and awareness for sustainable lifestyles) and SDG 13, since lower electricity use means lower emissions.",
        ]),
        ("3. Literature Examples", [
            "Kelly and Knottenbelt (2015) [2] applied three deep neural networks to this task for five appliances in UK homes. The networks achieved better average F1 scores than the classical methods (combinatorial optimisation and factorial hidden Markov models) and also worked on a house not seen in training. Zhang et al. (2018) [3] proposed sequence-to-point learning: a convolutional network reads a window of the total signal and predicts the power of one appliance at the midpoint. They report improvements of 84% and 92% on two error measures.",
            "Both papers evaluate models on research benchmarks. Neither turns the result into a tool or a cost breakdown for a household. My project tests on several unseen homes at 1-minute resolution and shows the result in kWh and TL under Turkish tariffs.",
        ]),
        ("4. Data", [
            "I will use REFIT Electrical Load Measurements (Cleaned) from the University of Strathclyde, free under CC BY 4.0 [4]. It covers 20 UK homes between 2013 and 2015, with the total power and 9 appliance channels in watts about every 8 seconds, as one CSV file per home (514 MB archive, 6.9 GB and 119.5 million rows unpacked). I downloaded and checked it. A fridge or freezer is monitored in 20 homes, a washing machine in 19, a microwave in 16, a dishwasher in 15 and a kettle in 15. In House 2 the nine monitored appliances explain 32% of the energy and about 25% of the minutes have no data. I will resample to 1 minute, remove windows with gaps, map each home's columns to common appliance names, scale the values, and split by home to avoid leakage.",
            "The homes are British and I found no open appliance-level data from Türkiye, so I will adapt in four steps. Both countries use 230 V at 50 Hz, and the five target appliances are also used in Turkish homes. First, I will test the model on a second dataset. D'Incecco et al. [5] report that a model trained on REFIT has an MAE of 11.8 W on another UK dataset but 32.1 W on US homes, where a model trained locally reaches 23.7 W. Second, I will add loads that are common in Turkish homes and missing in REFIT (air conditioner, electric water heater, tea maker) to the training data artificially. Third, I will evaluate at 1-minute, 15-minute and hourly resolution, because the smart meters now being installed in Türkiye are reported to give hourly data. Fourth, I will measure one Turkish home with smart plugs for a few weeks and report the error on that data.",
        ]),
        ("5. Approach: Deep Learning", [
            "I choose deep learning with a machine learning baseline. The input is a raw time series in which appliances overlap and draw similar power: in House 2 the heaters of the washing machine and the dishwasher draw about 2.1 and 2.2 kW. A model has to learn the shape of each appliance's cycle, which suits a 1D convolutional network (sequence-to-point), one small network per appliance, trained on free Colab. I already computed two baselines by training on House 2 and testing on House 5. Predicting the average power gives an MAE of 44.9 W for the kettle and 107.1 W for the dishwasher, and gradient boosting on window statistics lowers these to 17.6 W and 67.6 W. It does not help for the washing machine (44.3 to 43.6 W), because window statistics lose the order of the phases in a cycle, which a convolutional network keeps. My target is to beat gradient boosting on the same test homes for at least four of the five appliances.",
            "For the cost I use EPDK's regulated residential tariff valid from 4 April 2026 [6], with taxes added by calculation. The three-rate tariff costs 3.26 TL per kWh at night (22:00 to 06:00), 4.92 TL in the day and 7.00 TL in the evening peak (17:00 to 22:00). The single-rate tariff costs 3.24 TL up to 8 kWh a day and 4.86 TL above that. I priced one real day of House 2 (10.34 kWh): 37.28 TL on the single rate and 49.95 TL on the three-rate tariff. Moving the dishwasher and washing machine runs to the night lowers the three-rate bill to 45.74 TL, so for this home the single rate stays cheaper. The demo will make the same comparison for any home.",
        ]),
    ],
)

TR = dict(
    title="Fikir Önerisi: Fatura Dedektifi",
    sub="Evdeki tek sayaçtan hangi cihazın ne kadar elektrik harcadığını bulmak",
    by="Mert Güngör, Grup 14, Samsung Innovation Campus, Yapay Zekâ Kursu",
    meta_title="Fikir Önerisi: Fatura Dedektifi",
    refs="Kaynaklar",
    sections=[
        ("1. Proje Fikri", [
            "Elektrik faturasında tek bir toplam yazar. Hangi cihazın ne kadar harcadığını göstermez, bu yüzden bir hane nereden tasarruf edeceğini ya da hangi tarifenin ona uygun olduğunu bilemez. Enerji maliyeti Türkiye'de ciddi bir yük. 2025'te nüfusun %19,5'i evini yeterince ısıtmaya gücünün yetmediğini söyledi [1]. Isınmada çoğunlukla doğal gaz kullanılıyor, ama cihaz cihaz azaltılabilen fatura elektrik faturası. Her cihaza ayrı sayaç takmak ise pahalı ve zahmetli.",
            "Yalnızca evin toplam güç sinyaline bakarak buzdolabının, çamaşır makinesinin, bulaşık makinesinin, su ısıtıcının ve mikrodalganın ne kadar harcadığını tahmin eden bir model geliştirmek istiyorum (non-intrusive load monitoring, NILM). Sonuç, bir günün sayaç verisini cihaz bazında kWh ve TL'ye çeviren bir web demosu olacak. Demo günü Türkiye'nin tek zamanlı ve üç zamanlı (gündüz, puant, gece) tarifeleriyle fiyatlayacak, hangisinin daha ucuz olduğunu söyleyecek ve geceye kaydırmaya değer cihazı gösterecek. Başarıyı, modelin eğitimde hiç görmediği evlerde, her cihaz için watt cinsinden ortalama mutlak hata (MAE) ve toplam enerji hatasıyla ölçeceğim.",
        ]),
        ("2. Sürdürülebilir Kalkınma Amaçlarıyla İlişkisi", [
            "Proje SDG 7'ye, Erişilebilir ve Temiz Enerji amacına hizmet ediyor. En çok hedef 7.3 (enerji verimliliğini artırmak) ile ilgili, çünkü insanlar ancak görebildikleri tüketimi azaltabilir. Hanelerin faturasını düşürmesine yardım ettiği için hedef 7.1 (uygun fiyatlı enerji hizmetleri) ile de dolaylı bir bağı var. Ayrıca SDG 12.8'i (sürdürülebilir yaşam için bilgi ve farkındalık) ve SDG 13'ü destekliyor, çünkü daha az elektrik tüketimi daha az emisyon demek.",
        ]),
        ("3. Literatür Örnekleri", [
            "Kelly ve Knottenbelt (2015) [2] bu probleme üç farklı derin sinir ağı uyguladı ve İngiltere'deki evlerde beş cihaz üzerinde denedi. Ağlar, klasik yöntemlerden (combinatorial optimisation ve factorial hidden Markov model) daha yüksek ortalama F1 skoru aldı ve eğitimde görülmeyen bir evde de çalıştı. Zhang ve ark. (2018) [3] sequence-to-point öğrenmeyi önerdi: bir evrişimli ağ toplam sinyalin bir penceresini okuyor ve pencerenin ortasındaki anda tek bir cihazın gücünü tahmin ediyor. İki hata ölçütünde %84 ve %92 iyileşme bildiriyorlar.",
            "İki çalışma da modelleri araştırma veri setlerinde değerlendiriyor. İkisi de sonucu haneler için bir araca ya da maliyet dökümüne çevirmiyor. Benim projem modeli birden fazla görülmemiş evde 1 dakikalık çözünürlükte test edecek ve sonucu Türkiye tarifeleriyle kWh ve TL olarak gösterecek.",
        ]),
        ("4. Veri", [
            "Strathclyde Üniversitesi'nin REFIT Electrical Load Measurements (Cleaned) veri setini kullanacağım. CC BY 4.0 lisansıyla ücretsiz [4]. 2013 ile 2015 arasında İngiltere'de 20 evi kapsıyor. Her evde toplam güç ve 9 cihaz kanalı watt cinsinden, yaklaşık 8 saniyede bir kaydedilmiş, her ev için bir CSV dosyası var (arşiv 514 MB, açıldığında 6,9 GB ve 119,5 milyon satır). Veriyi indirip kontrol ettim. Buzdolabı ya da dondurucu 20 evde, çamaşır makinesi 19, mikrodalga 16, bulaşık makinesi 15 ve su ısıtıcı 15 evde ölçülmüş. Ev 2'de ölçülen dokuz cihaz enerjinin %32'sini açıklıyor ve dakikaların yaklaşık %25'inde veri yok. Veriyi 1 dakikaya yeniden örnekleyeceğim, boşluk içeren pencereleri çıkaracağım, her evin sütunlarını ortak cihaz adlarına eşleyeceğim, değerleri ölçekleyeceğim ve veri sızıntısını önlemek için ayırmayı ev bazında yapacağım.",
            "Evler İngiltere'de ve Türkiye'den cihaz düzeyinde açık bir veri bulamadım, bu yüzden uyarlamayı dört adımda yapacağım. İki ülkede de şebeke 230 V ve 50 Hz, hedeflediğim beş cihaz Türk evlerinde de kullanılıyor. Birincisi, modeli ikinci bir veri setinde test edeceğim. D'Incecco ve ark. [5], REFIT ile eğitilen bir modelin başka bir İngiltere veri setinde 11,8 W, ABD evlerinde ise 32,1 W MAE verdiğini bildiriyor. ABD verisiyle eğitilen model orada 23,7 W'a iniyor. İkincisi, Türk evlerinde yaygın olup REFIT'te bulunmayan yükleri (klima, termosifon, çay makinesi) eğitim verisine yapay olarak ekleyeceğim. Üçüncüsü, modeli 1 dakikalık, 15 dakikalık ve saatlik çözünürlükte ölçeceğim, çünkü Türkiye'de kurulmakta olan akıllı sayaçların saatlik veri verdiği bildiriliyor. Dördüncüsü, bir Türk evinde akıllı prizlerle birkaç hafta ölçüm alıp hatayı o veri üzerinde raporlayacağım.",
        ]),
        ("5. Yaklaşım: Derin Öğrenme", [
            "Bir makine öğrenmesi referansıyla birlikte derin öğrenmeyi seçiyorum. Girdi ham bir zaman serisi, cihazlar üst üste çalışıyor ve benzer güç çekiyor: Ev 2'de çamaşır makinesinin ve bulaşık makinesinin ısıtıcıları yaklaşık 2,1 ve 2,2 kW çekiyor. Modelin her cihazın çalışma döngüsünün şeklini öğrenmesi gerekiyor, bu da tek boyutlu evrişimli ağa (sequence-to-point) uygun. Her cihaz için küçük bir ağı ücretsiz Colab'de eğiteceğim. İki referans yöntemi şimdiden hesapladım: Ev 2'de eğitip Ev 5'te test ettim. Ortalama gücü tahmin etmek su ısıtıcıda 44,9 W, bulaşık makinesinde 107,1 W MAE veriyor, pencere istatistikleri üzerinde gradient boosting bunları 17,6 W ve 67,6 W'a indiriyor. Çamaşır makinesinde ise işe yaramıyor (44,3'ten 43,6 W'a), çünkü pencere istatistikleri bir döngüdeki aşamaların sırasını kaybediyor, evrişimli ağ ise koruyor. Hedefim, aynı test evlerinde beş cihazın en az dördünde gradient boosting'i geçmek.",
            "Maliyet için EPDK'nın 4 Nisan 2026'dan itibaren geçerli mesken tarifesini kullanıyorum [6], vergileri hesaplayarak ekledim. Üç zamanlı tarifede kWh gece (22:00-06:00) 3,26 TL, gündüz 4,92 TL, akşam puant saatlerinde (17:00-22:00) 7,00 TL. Tek zamanlı tarifede günde 8 kWh'e kadar 3,24 TL, üstü 4,86 TL. Ev 2'nin gerçek bir gününü (10,34 kWh) fiyatladım: tek zamanlıda 37,28 TL, üç zamanlıda 49,95 TL tutuyor. Bulaşık ve çamaşır makinesi geceye kaydırılırsa üç zamanlı fatura 45,74 TL'ye iniyor, yani bu ev için tek zamanlı tarife yine daha ucuz. Demo aynı karşılaştırmayı her ev için yapacak.",
        ]),
    ],
)

L = EN if sys.argv[1] == "en" else TR
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.2)
sec.left_margin = sec.right_margin = Cm(1.5)
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(9)
st.paragraph_format.space_after = Pt(2)
st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0


def para(text, size=None, after=None, color=None, bold=False, before=None):
    p = doc.add_paragraph()
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    if before is not None:
        p.paragraph_format.space_before = Pt(before)
    r = p.add_run(text)
    r.bold = bold
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor(*color)
    return p


para(L["title"], size=14, after=0, bold=True)
para(L["sub"], size=10.5, after=0)
para(L["by"], size=8.5, after=1, color=(0x55, 0x55, 0x55))
for head, paras in L["sections"]:
    para(head, size=10, after=1, color=(0x0B, 0x4F, 0x8A), bold=True, before=3)
    for t in paras:
        para(t)
para(L["refs"], size=10, after=1, color=(0x0B, 0x4F, 0x8A), bold=True, before=3)
for r in REFS:
    para(r, size=7.5, after=0)
doc.core_properties.author = "Mert Güngör"
doc.core_properties.last_modified_by = "Mert Güngör"
doc.core_properties.title = L["meta_title"]
doc.core_properties.comments = ""
doc.save(sys.argv[2])
